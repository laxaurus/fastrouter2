#!/usr/bin/env python3
"""Wipe all FastRouter + LiteLLM data for a clean start.

Usage:
    python scripts/fresh_start.py              # Wipe FastRouter DB + Redis + LiteLLM
    python scripts/fresh_start.py --db-only     # Wipe FastRouter DB only
    python scripts/fresh_start.py --yes         # Skip confirmation
    python scripts/fresh_start.py --no-litellm  # Skip LiteLLM cleanup
"""

import argparse
import asyncio
import os
import re
import sys

import asyncpg
import httpx
import redis.asyncio as redis

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.config import get_settings

settings = get_settings()

DB_DSN = settings.database_url.replace("+asyncpg", "")

# LiteLLM uses its own database on the same postgres host
LITELLM_DB_DSN = re.sub(r"/[^/]+$", "/litellm", DB_DSN)

FASTROUTER_TABLES = [
    "usage_logs",
    "api_keys",
    "provider_keys",
    "provider_configs",
    "provider_models",
    "users",
]

LITELLM_TABLES = [
    "LiteLLM_VerificationToken",
    "LiteLLM_SpendLogs",
]


async def wipe_tables(dsn: str, tables: list[str], label: str):
    conn = await asyncpg.connect(dsn)
    try:
        for table in tables:
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1 "
                "AND table_schema = 'public')",
                table,
            )
            if exists:
                await conn.execute(f"TRUNCATE TABLE \"{table}\" CASCADE")
                print(f"  [{label}] TRUNCATE {table}")
            else:
                print(f"  [{label}] SKIP    {table} (does not exist)")
    finally:
        await conn.close()


async def wipe_redis():
    r = await redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await r.flushall()
        print("  [Redis]  FLUSHALL")
    finally:
        await r.aclose()


async def main():
    parser = argparse.ArgumentParser(description="Wipe all FastRouter + LiteLLM data")
    parser.add_argument("--db-only", action="store_true", help="Only wipe FastRouter database")
    parser.add_argument("--redis-only", action="store_true", help="Only wipe Redis")
    parser.add_argument("--no-litellm", action="store_true", help="Skip LiteLLM cleanup")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    targets = []
    if args.redis_only:
        targets = ["Redis"]
    elif args.db_only:
        targets = ["FastRouter DB"]
    else:
        targets = ["FastRouter DB", "Redis"]
        if not args.no_litellm:
            targets.append("LiteLLM DB")

    print("FastRouter Fresh Start")
    print(f"  FastRouter DB:  {DB_DSN}")
    print(f"  LiteLLM DB:     {LITELLM_DB_DSN}")
    print(f"  Redis:          {settings.redis_url}")
    print(f"  Targets:        {', '.join(targets)}")
    print()

    if not args.yes:
        confirm = input("This will DELETE ALL DATA across all targets. Continue? [y/N] ")
        if confirm.lower() not in ("y", "yes"):
            print("Aborted.")
            return

    print("Wiping...")

    if not args.redis_only:
        await wipe_tables(DB_DSN, FASTROUTER_TABLES, "FR")

    if not args.db_only and not args.no_litellm:
        await wipe_tables(LITELLM_DB_DSN, LITELLM_TABLES, "LL")

    if not args.db_only:
        await wipe_redis()

    if not args.db_only and not args.no_litellm:
        print()
        await provision_litellm_admin()

    print("Done. Fresh start ready.")


async def provision_litellm_admin():
    """Ensure LiteLLM has an admin user for UI access after a wipe.

    Uses the master key to create/reset a proxy_admin user. Credentials
    are read from LITELLM_UI_USERNAME / LITELLM_UI_PASSWORD env vars,
    falling back to admin / fastrouter-admin (matching docker-compose).
    """
    username = os.environ.get("LITELLM_UI_USERNAME", "admin")
    password = os.environ.get("LITELLM_UI_PASSWORD", "fastrouter-admin")
    email = f"{username}@fastrouter.dev"

    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            # Check if LiteLLM is reachable
            try:
                resp = await client.get(f"{settings.litellm_url}/health", headers=headers)
                if resp.status_code != 200:
                    print("  LiteLLM not reachable — skip admin provisioning (restart LiteLLM first)")
                    return
            except httpx.ConnectError:
                print("  LiteLLM not reachable — skip admin provisioning (restart LiteLLM first)")
                return

            # Try to create a new admin user
            resp = await client.post(
                f"{settings.litellm_url}/user/new",
                json={"user_email": email, "user_role": "proxy_admin", "password": password},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Created LiteLLM admin user: {email}")
                print(f"    UI login: {username} / {password}")
                return

            # User might already exist — try updating password
            error_msg = resp.json().get("error", {}).get("message", "")
            if "already exists" in str(error_msg):
                # Find the existing user
                resp2 = await client.get(
                    f"{settings.litellm_url}/user/info?user_id=default_user_id",
                    headers=headers,
                )
                user_id = "default_user_id"
                if resp2.status_code != 200:
                    # Try by email
                    resp2 = await client.get(
                        f"{settings.litellm_url}/user/info?user_id={email}",
                        headers=headers,
                    )
                    if resp2.status_code != 200:
                        user_id = email

                resp3 = await client.post(
                    f"{settings.litellm_url}/user/update",
                    json={"user_id": user_id, "password": password},
                    headers=headers,
                )
                if resp3.status_code == 200:
                    print(f"  Reset password for LiteLLM admin: {user_id}")
                    print(f"    UI login: {username} / {password}")
                else:
                    print(f"  Failed to reset admin password: {resp3.text[:200]}")
            else:
                print(f"  Admin provisioning note: {error_msg}")
    except Exception as e:
        print(f"  Admin provisioning skipped: {e}")


if __name__ == "__main__":
    asyncio.run(main())
