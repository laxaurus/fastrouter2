from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.database import init_db, async_session, run_migrations, seed_defaults, ensure_admin_users
from backend.services.routing import router as litellm_router, load_model_map

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redis.from_url(settings.redis_url, decode_responses=True)
    await run_migrations()
    await init_db()
    async with async_session() as session:
        await seed_defaults(session)
        await ensure_admin_users(session)
        await load_model_map(session)
    yield
    # Shutdown
    await litellm_router.close()
    await app.state.redis.close()


app = FastAPI(
    title="FastRouter",
    description="Two-way LLM API routing platform — West→China optimized for AI startups and coding agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


@app.get("/health")
async def health(request: Request):
    redis_ok = False
    try:
        await request.app.state.redis.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "redis": redis_ok,
        "version": "0.1.0",
    }


# Import and include routers
from backend.routes.auth import router as auth_router
from backend.routes.keys import router as keys_router
from backend.routes.provider_keys import router as provider_keys_router
from backend.routes.proxy import router as proxy_router
from backend.routes.billing import router as billing_router
from backend.routes.webhooks import router as webhooks_router
from backend.routes.analytics import router as analytics_router
from backend.routes.admin import router as admin_router

app.include_router(auth_router)
app.include_router(keys_router)
app.include_router(provider_keys_router)
app.include_router(proxy_router)
app.include_router(billing_router)
app.include_router(webhooks_router)
app.include_router(analytics_router)
app.include_router(admin_router)
