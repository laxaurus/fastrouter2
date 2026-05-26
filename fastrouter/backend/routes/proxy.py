import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.middleware.auth import get_current_user, check_subscription_or_free_tier
from backend.models.user import User
from backend.models.usage import UsageLog
from backend.services.routing import router as litellm_router, generate_cache_key
from backend.services.agent_detector import AgentDetector
from backend.services.cache import PromptCache
from backend.services.circuit_breaker import CircuitBreaker, CircuitOpenError

router = APIRouter(prefix="/v1", tags=["proxy"])

agent_detector = AgentDetector()


async def get_redis(request: Request):
    return request.app.state.redis


@router.post("/chat/completions", response_model=None)
async def chat_completions(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    redis_client = await get_redis(request)
    cache = PromptCache(redis_client)
    breaker = CircuitBreaker(redis_client)

    model = body.get("model", "deepseek-chat")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens", 4096)
    stop = body.get("stop")

    # Check subscription or free tier
    if not await check_subscription_or_free_tier(user):
        raise HTTPException(
            status_code=402,
            detail="Free tier limit reached. Please subscribe to continue.",
        )

    # Detect agent type
    agent_type = agent_detector.detect(messages, stop)

    # Check prompt cache
    cache_key = generate_cache_key(messages, model)
    cached = await cache.get(str(user.id), cache_key)
    if cached:
        # Log cached usage
        usage_log = UsageLog(
            user_id=user.id,
            provider=cached.get("provider", "unknown"),
            model=cached.get("model", model),
            prompt_tokens=cached.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=cached.get("usage", {}).get("completion_tokens", 0),
            cost_usd=0,
            latency_ms=1,
            cached=True,
            agent_type=agent_type,
        )
        db.add(usage_log)
        await db.commit()

        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": cached["choices"],
            "usage": cached["usage"],
            "x_provider": cached["provider"],
            "x_cached": True,
        }

    # Circuit breaker check
    try:
        await breaker.before_call(model)
    except CircuitOpenError:
        # Try failover to next provider
        fallback = _get_fallback_model(model)
        if fallback:
            model = fallback
            await breaker.before_call(model)

    try:
        if stream:
            # Streaming not cached
            pass
        else:
            result = await litellm_router.route(
                model=model,
                messages=messages,
                user_id=str(user.id),
                db=db,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
            )

            # Cache successful response
            await cache.set(str(user.id), cache_key, result)

            # Increment free tier counter
            if user.subscription_status != "active":
                user.free_requests_used += 1

            # Log usage
            usage_log = UsageLog(
                user_id=user.id,
                provider=result["provider"],
                model=result["model"],
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                cost_usd=result.get("cost_usd", 0),
                latency_ms=result["latency_ms"],
                cached=False,
                agent_type=agent_type,
            )
            db.add(usage_log)
            await db.commit()

            await breaker.on_success(result["provider"])

            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": result["model"],
                "choices": result["choices"],
                "usage": result["usage"],
                "x_provider": result["provider"],
                "x_cached": False,
                "x_agent_type": agent_type,
            }

    except Exception as e:
        # Determine provider for circuit breaker
        provider = "deepseek" if "deepseek" in model.lower() else "qwen"
        await breaker.on_failure(provider)
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")


def _get_fallback_model(model: str) -> str | None:
    if "deepseek" in model.lower():
        return "qwen-plus"
    if "qwen" in model.lower():
        return "deepseek-chat"
    return None


@router.get("/models", response_model=None)
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
            {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
            {"id": "qwen-plus", "object": "model", "owned_by": "qwen"},
            {"id": "qwen-max", "object": "model", "owned_by": "qwen"},
            {"id": "qwen-turbo", "object": "model", "owned_by": "qwen"},
        ],
    }
