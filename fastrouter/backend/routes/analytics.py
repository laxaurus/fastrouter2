from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.models.usage import UsageLog
from backend.services.circuit_breaker import CircuitBreaker

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=None)
async def overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total requests, tokens, and spend
    total_result = await db.execute(
        select(
            func.count(UsageLog.id),
            func.sum(UsageLog.prompt_tokens + UsageLog.completion_tokens),
            func.sum(UsageLog.cost_usd),
        )
        .where(UsageLog.user_id == user.id)
    )
    row = total_result.one()
    total_requests = row[0] or 0
    total_tokens = row[1] or 0
    total_spend = float(row[2] or 0)

    # Cached requests
    cached_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.user_id == user.id,
            UsageLog.cached == True,
        )
    )
    cached_count = cached_result.scalar() or 0

    # Real savings: sum of cost_usd for cached requests (what would have been spent)
    savings_result = await db.execute(
        select(func.sum(UsageLog.cost_usd)).where(
            UsageLog.user_id == user.id,
            UsageLog.cached == True,
        )
    )
    cached_savings = float(savings_result.scalar() or 0)

    free_remaining = max(0, user.free_requests_limit - user.free_requests_used)

    return {
        "total_requests": total_requests,
        "total_tokens": int(total_tokens),
        "total_spend": round(total_spend, 6),
        "cached_requests": cached_count,
        "cached_savings": round(cached_savings, 6),
        "free_requests_used": user.free_requests_used,
        "free_requests_limit": user.free_requests_limit,
        "free_requests_remaining": free_remaining,
    }


@router.get("/usage", response_model=None)
async def usage(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = text("""
        SELECT
            DATE(created_at) as day,
            COUNT(*) as requests,
            SUM(prompt_tokens) as prompt_tokens,
            SUM(completion_tokens) as completion_tokens,
            SUM(prompt_tokens + completion_tokens) as total_tokens,
            SUM(cost_usd) as cost_usd,
            SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_count,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN cached THEN 0 ELSE cost_usd END) as non_cached_cost_usd
        FROM usage_logs
        WHERE user_id = :user_id
          AND created_at >= NOW() - (:days || ' days')::INTERVAL
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    """)

    result = await db.execute(query, {"user_id": user.id, "days": str(days)})
    rows = result.mappings().all()

    return {
        "days": days,
        "data": [
            {
                "day": str(row["day"]),
                "requests": row["requests"],
                "prompt_tokens": int(row["prompt_tokens"] or 0),
                "completion_tokens": int(row["completion_tokens"] or 0),
                "total_tokens": int(row["total_tokens"] or 0),
                "cost_usd": float(row["cost_usd"] or 0),
                "cached_count": row["cached_count"],
                "avg_latency_ms": round(float(row["avg_latency_ms"] or 0), 1),
            }
            for row in rows
        ],
    }


@router.get("/providers", response_model=None)
async def providers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = text("""
        SELECT
            provider,
            COUNT(*) as requests,
            SUM(prompt_tokens + completion_tokens) as total_tokens,
            SUM(cost_usd) as cost_usd,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_count
        FROM usage_logs
        WHERE user_id = :user_id
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY provider
        ORDER BY requests DESC
    """)

    result = await db.execute(query, {"user_id": user.id})
    rows = result.mappings().all()

    return {
        "data": [
            {
                "provider": row["provider"],
                "requests": row["requests"],
                "total_tokens": int(row["total_tokens"] or 0),
                "cost_usd": float(row["cost_usd"] or 0),
                "avg_latency_ms": round(float(row["avg_latency_ms"] or 0), 1),
                "cached_count": row["cached_count"],
            }
            for row in rows
        ],
    }


@router.get("/models", response_model=None)
async def model_spend(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = text("""
        SELECT
            model,
            provider,
            COUNT(*) as requests,
            SUM(prompt_tokens) as prompt_tokens,
            SUM(completion_tokens) as completion_tokens,
            SUM(prompt_tokens + completion_tokens) as total_tokens,
            SUM(cost_usd) as cost_usd,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_count
        FROM usage_logs
        WHERE user_id = :user_id
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY model, provider
        ORDER BY cost_usd DESC
    """)

    result = await db.execute(query, {"user_id": user.id})
    rows = result.mappings().all()

    return {
        "data": [
            {
                "model": row["model"],
                "provider": row["provider"],
                "requests": row["requests"],
                "prompt_tokens": int(row["prompt_tokens"] or 0),
                "completion_tokens": int(row["completion_tokens"] or 0),
                "total_tokens": int(row["total_tokens"] or 0),
                "cost_usd": float(row["cost_usd"] or 0),
                "avg_latency_ms": round(float(row["avg_latency_ms"] or 0), 1),
                "cached_count": row["cached_count"],
            }
            for row in rows
        ],
    }


@router.get("/health", response_model=None)
async def provider_health(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    from backend.models.provider_model import ProviderModel

    redis_client = request.app.state.redis
    breaker = CircuitBreaker(redis_client)
    health_data = await breaker.get_health()
    cb_providers = {h["provider"]: h for h in health_data}

    # Get all active providers from DB
    result = await db.execute(
        select(ProviderModel.provider).where(ProviderModel.is_active == True).distinct()
    )
    all_providers = sorted(row[0] for row in result)

    providers = []
    for prov in all_providers:
        if prov in cb_providers:
            providers.append(cb_providers[prov])
        else:
            providers.append({
                "provider": prov,
                "state": "unknown",
                "failure_count": 0,
            })

    return {"providers": providers}
