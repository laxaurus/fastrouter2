# FastRouter Bug Report

Generated during full-scope testing. Critical bugs (1-3) have been fixed.
Remaining items are non-critical issues found during code audit.

---

## CRITICAL (Fixed)

### BUG-001 — API Key Auth: O(N) bcrypt scan on every request
**Status:** FIXED
**File:** `backend/middleware/auth.py:_auth_api_key()`
**Description:** Every API-key-authenticated request fetched ALL active ApiKey rows and
ran bcrypt.verify against each one — O(N) with expensive hashing. Also had dead code
`key_hash = bcrypt.hash(api_key)` that generated a new salted hash each time (never matches).
**Fix:** Added `ApiKey.key_prefix == key_prefix` filter to narrow by first 8 chars of the key,
removed the dead bcrypt.hash call.

### BUG-002 — Streaming returns no response (no-op)
**Status:** FIXED
**File:** `backend/routes/proxy.py:chat_completions()`
**Description:** `if stream: pass` meant streaming requests did nothing. Code would crash on
`NameError: name 'result' is not defined` when reaching the cache-write block after the if/else.
**Fix:** Replaced with actual `StreamingResponse` wrapping `litellm_router.route_stream()`
with `text/event-stream` media type.

### BUG-003 — Stripe webhook returns 200 on signature verification failure
**Status:** FIXED
**File:** `backend/routes/webhooks.py:stripe_webhook()`
**Description:** When `handle_webhook()` returned `{"error": ...}`, the endpoint still
responded with HTTP 200, which would cause Stripe to consider the event delivered successfully.
**Fix:** Added `if "error" in result: return JSONResponse(status_code=400, content=result)`.

---

## HIGH (Not Yet Fixed)

### BUG-004 — Provider key decrypted but not sent to LiteLLM
**Status:** FIXED
**File:** `backend/services/routing.py:LiteLLMRouter.route()`
**Description:** `_get_provider_key()` decrypts the customer's provider API key, but the
Authorization header sent to LiteLLM used `settings.litellm_master_key` instead.
**Fix:** Implemented LiteLLM virtual key architecture. Each provider key gets a corresponding
LiteLLM virtual key with the customer's API key embedded in `litellm_params`. The proxy now
authenticates to LiteLLM with the customer's virtual key, so the customer's provider account
is charged. New files: `backend/services/lite_key_manager.py`. Updated `routing.py`,
`provider_keys.py`, `models/provider_key.py` (added `lite_key` column).

### BUG-005 — Free tier counter doesn't increment on cached responses
**Status:** FIXED
**File:** `backend/routes/proxy.py:chat_completions()`
**Description:** The free tier counter only incremented in the non-cached path.
**Fix:** Added `user.free_requests_used += 1` in the cache-hit branch.

### BUG-006 — Stale circuit breaker successes never expire
**Status:** FIXED
**File:** `backend/services/circuit_breaker.py`
**Description:** `_record_success()` uses `INCR` on `cb:{provider}:successes`, but the
success count was never reset in CLOSED state.
**Fix:** Added `self.redis.delete(f"cb:{provider}:successes")` in `on_failure()` when
transitioning to OPEN state.

---

## MEDIUM (Not Yet Fixed)

### BUG-007 — No per-endpoint rate limiting
**File:** `backend/middleware/rate_limit.py` (module exists but may be incomplete)
**Description:** No rate limiting is applied to auth endpoints (`/auth/login`,
`/auth/register`), making them vulnerable to brute-force and registration abuse.
**Recommendation:** Add rate limiting middleware with Redis-backed sliding window,
especially on auth and proxy endpoints.

### BUG-008 — Streaming doesn't log usage
**Status:** FIXED
**File:** `backend/routes/proxy.py:chat_completions()`
**Description:** When `stream=True`, no `UsageLog` record was created.
**Fix:** Added estimated usage log before returning the StreamingResponse. Token count
is estimated from input message length. Free tier counter also now increments for
streaming requests.

### BUG-009 — Circuit breaker `before_call` uses model name, not provider
**Status:** FIXED
**File:** `backend/routes/proxy.py`
**Description:** `before_call` passed model name (e.g., "deepseek-chat") while
`on_failure` used a different provider resolution. Circuit breaker state was stored
under inconsistent keys.
**Fix:** Provider name is resolved once at the top of the handler via
`litellm_router.resolve_provider(model)` and used consistently for all circuit
breaker calls. The static `resolve_provider` method uses a `PROVIDER_MODEL_MAP`
dict for clean mapping.

### BUG-010 — LiteLLMRouter uses module-level singleton httpx client
**Status:** FIXED
**File:** `backend/services/routing.py`
**Description:** `self.client = httpx.AsyncClient(...)` was created at import time.
If the event loop changes, the client could be bound to a closed loop.
**Fix:** Client is now created lazily via `@property`. The `__init__` sets
`self._client = None` and the first access creates the client. Same pattern
applied to `LiteKeyManager` in `lite_key_manager.py`.

---

## LOW (Not Yet Fixed)

### BUG-011 — `_get_cipher()` re-derives key on every call
**File:** `backend/routes/provider_keys.py`
**Description:** `_get_cipher()` runs `hashlib.sha256().digest()` + `base64.urlsafe_b64encode()`
on every encrypt/decrypt call. The derived key never changes, so this is wasted CPU.
**Recommendation:** Cache the cipher instance at module level using `functools.lru_cache`.

### BUG-012 — No request body size limit on proxy endpoint
**File:** `backend/routes/proxy.py`
**Description:** `chat_completions` accepts `body: dict` with no size validation.
A malicious payload with a giant messages array could exhaust server memory.
**Recommendation:** Add a body size limit or Pydantic model with max_length constraints.

### BUG-013 — Circuit breaker `_get_state` / `_get_last_failure` fails with decode_responses=True
**Status:** FIXED
**File:** `backend/services/circuit_breaker.py`
**Description:** `_get_state()` and `_get_last_failure()` call `.decode()` on Redis values,
but the Redis client is created with `decode_responses=True`. This causes
`AttributeError: 'str' object has no attribute 'decode'` at runtime.
**Fix:** Added `isinstance(val, bytes)` check before calling `.decode()`.

### BUG-014 — Missing minimum password length on register
**Status:** FIXED
**File:** `backend/routes/auth.py`
**Description:** `RegisterRequest.password` had no `min_length` constraint, allowing
empty or 1-character passwords.
**Fix:** Added `Field(min_length=8)` to the password field.

---

## Summary

| ID | Severity | Status | Component |
|----|----------|--------|-----------|
| BUG-001 | Critical | FIXED | Auth middleware |
| BUG-002 | Critical | FIXED | Proxy route |
| BUG-003 | Critical | FIXED | Webhook route |
| BUG-004 | High | Open | Routing service |
| BUG-005 | High | Open | Proxy route |
| BUG-006 | High | Open | Circuit breaker |
| BUG-007 | Medium | Open | Rate limiting |
| BUG-008 | Medium | Open | Streaming |
| BUG-009 | Medium | Open | Circuit breaker |
| BUG-010 | Medium | Open | Routing service |
| BUG-011 | Low | Open | Provider keys |
| BUG-012 | Low | Open | Proxy route |
| BUG-013 | High | FIXED | Circuit breaker |
| BUG-014 | High | FIXED | Auth route |
