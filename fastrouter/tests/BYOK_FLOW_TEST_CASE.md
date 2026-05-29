# BYOK End-to-End Test Case

## Flow: User adds provider key → proxy request → user deletes key

This traces every function call, database write, and HTTP request across all three systems:
FastRouter backend, LiteLLM proxy, and the provider API.

---

## STEP 1: USER ADDS DEEPSEEK KEY (Frontend → Backend → LiteLLM)

### 1a. Frontend: ProviderKeys.jsx

```
User fills form: provider="deepseek", api_key="sk-deepseek-abc123..."
User clicks "Add Key"
  → handleAdd()
    → api.addProviderKey("deepseek", "sk-deepseek-abc123...")
```

**Expected frontend state after success:**
- Provider appears in table with `<Tag color="arcoblue">deepseek</Tag>`
- Key prefix shown as `sk-deep...`
- Synced column shows `<Tag color="green">Ready</Tag>` (if LiteLLM sync worked)
- If sync failed: `<Tag color="orange">Pending</Tag>`
- Test button is enabled only if `synced === true`

### 1b. API Client: api.js

```js
addProviderKey: (provider, apiKey) =>
  request("/providers/keys", {
    method: "POST",
    body: JSON.stringify({ provider, api_key: apiKey })
  })
```

Sends `POST /api/providers/keys` → Vite proxy rewrites to `POST /providers/keys` on backend.

**HTTP request:**
```
POST /providers/keys
Authorization: Bearer <jwt_access_token>
Content-Type: application/json

{"provider": "deepseek", "api_key": "sk-deepseek-abc123..."}
```

### 1c. Backend: routes/provider_keys.py → add_provider_key()

```
1. Validates provider ∈ ["deepseek", "qwen", "kimi", "glm"]
   → If not: 400 "Unsupported provider"

2. Encrypts key:
   encrypt_api_key("sk-deepseek-abc123...") → Fernet AES-256-GCM ciphertext
   
3. Inserts into provider_keys table:
   INSERT INTO provider_keys (
     id, user_id, provider, api_key_encrypted, key_prefix, lite_key, is_active
   ) VALUES (
     <uuid>, <user_uuid>, 'deepseek', '<ciphertext>', 'sk-deeps', NULL, TRUE
   )
   → lite_key is NULL initially

4. Calls LiteKeyManager.create_key():
```

### 1d. Backend: services/lite_key_manager.py → LiteKeyManager.create_key()

```
POST {litellm_url}/key/generate
Authorization: Bearer <litellm_master_key>     ← from LITELLM_MASTER_KEY env var
Content-Type: application/json

{
  "models": ["deepseek-chat", "deepseek-reasoner"],
  "metadata": {
    "user_id": "<user_uuid>",
    "fastrouter_pk_id": "<provider_key_uuid>",
    "provider": "deepseek"
  },
  "litellm_params": {
    "api_key": "sk-deepseek-abc123...",         ← customer's decrypted key
    "api_base": "https://api.deepseek.com/v1"
  }
}
```

### 1e. LiteLLM Proxy: /key/generate

```
1. Validates master key
2. Creates virtual key in LiteLLM's internal DB
3. Virtual key record:
   {
     "token": "sk-liteLLM-virt-abc123...",
     "models": ["deepseek-chat", "deepseek-reasoner"],
     "metadata": {"user_id": "...", "fastrouter_pk_id": "...", "provider": "deepseek"},
     "litellm_params": {
       "api_key": "sk-deepseek-abc123...",
       "api_base": "https://api.deepseek.com/v1"
     }
   }
4. Returns {"key": "sk-liteLLM-virt-abc123..."}
```

### 1f. Backend: routes/provider_keys.py → stores lite_key

```
If LiteLLM returns a key:
  UPDATE provider_keys SET lite_key = 'sk-liteLLM-virt-abc123...' WHERE id = <uuid>
  → Response: {"synced": true, "message": "Provider key added successfully."}

If LiteLLM is unreachable (ConnectError):
  lite_key stays NULL
  → Response: {"synced": false, "message": "Provider key saved but routing sync failed..."}
  → Warning logged: "Failed to create LiteLLM virtual key for provider_key=..."
```

### 1g. Frontend: ProviderKeys.jsx — Post-Add

```
After load() refreshes the list:
  - synced=true → "Ready" tag, Test button enabled
  - synced=false → "Pending" tag, Test button disabled
```

---

## STEP 2: USER TESTS CONNECTIVITY (Optional but Recommended)

### 2a. Frontend: ProviderKeys.jsx → handleTest(id)

```
User clicks "Test" button
  → api.testProviderKey("<provider_key_uuid>")
```

### 2b. Backend: routes/provider_keys.py → test_provider_connection()

```
1. SELECT provider_keys WHERE id=<uuid> AND user_id=<user_uuid>
   → Not found: 404

2. Decrypts api_key_encrypted:
   decrypt_api_key(ciphertext) → "sk-deepseek-abc123..."

3. Resolves api_base from PROVIDER_API_BASES:
   "deepseek" → "https://api.deepseek.com/v1"

4. Makes direct call to provider (NOT through LiteLLM):
   POST https://api.deepseek.com/v1/chat/completions
   Authorization: Bearer sk-deepseek-abc123...
   Content-Type: application/json
   
   {"model": "ignored", "messages": [{"role":"user","content":"Hi"}], "max_tokens": 1}

5. Response analysis:
   - 200 → {reachable: true, authenticated: true, latency_ms: <ms>}
   - 401/403 → {reachable: true, authenticated: false, latency_ms: <ms>}
   - ConnectError → {reachable: false, detail: "Could not connect to..."}
   - Timeout → {reachable: false, detail: "Connection timed out after 15s"}
```

### 2c. Frontend: Alert Display

```
Green:  "Connection successful — 245ms latency"
Yellow: "Provider reached but key was rejected"
Red:    "Connection failed — Could not connect to https://api.deepseek.com/v1"
```

---

## STEP 3: USER CALLS /v1/chat/completions (The Core Proxy Flow)

### 3a. Client sends request

```
POST /v1/chat/completions
Authorization: Bearer sk-fastrouter-api-key   ← FastRouter platform key, NOT provider key
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [{"role": "user", "content": "Write a haiku about routing"}],
  "temperature": 0.7,
  "max_tokens": 4096
}
```

### 3b. Backend: middleware/auth.py → get_current_user()

```
1. Extracts token: "sk-fastrouter-api-key"
2. Token starts with "sk-" → _auth_api_key()
3. key_prefix = token[:8]
4. SELECT * FROM api_keys WHERE is_active=true AND key_prefix='sk-fastr'
5. bcrypt.verify(token, key.key_hash) for each matching row
6. Match found → loads User from users table
7. Updates api_keys.last_used_at = now()
8. Returns User object
```

### 3c. Backend: routes/proxy.py → chat_completions()

```
1. check_subscription_or_free_tier(user):
   - subscription_status == "active" → pass
   - free_requests_used < free_requests_limit → pass
   - else → 402 Payment Required

2. agent_detector.detect(messages, stop) → "chat" | "coding" | "unknown"

3. Prompt cache check:
   cache_key = SHA256({"messages": [...], "model": "deepseek-chat"})
   Redis GET cache:{user_id}:{cache_key}
   → If hit: return cached response (increment free tier counter, log UsageLog)
   → If miss: continue

4. resolve_provider("deepseek-chat"):
   PROVIDER_MODEL_MAP lookup → "deepseek"

5. Circuit breaker:
   breaker.before_call("deepseek")    ← uses provider name, NOT model name
   → State CLOSED: pass
   → State OPEN + recovery_timeout elapsed: transition to HALF_OPEN
   → State OPEN within timeout: raise CircuitOpenError → fallback to qwen-plus
```

### 3d. Backend: services/routing.py → LiteLLMRouter.route()

```
1. get_provider_key(user_id, "deepseek", db):
   SELECT * FROM provider_keys
   WHERE user_id=<uuid> AND provider='deepseek' AND is_active=true
   → Returns (decrypted_api_key, lite_key)
   → e.g. ("sk-deepseek-abc123...", "sk-liteLLM-virt-abc123...")

2. If keys is None: ValueError "No API key found for provider 'deepseek'"

3. Constructs request to LiteLLM:
   POST {litellm_url}/v1/chat/completions
   Authorization: Bearer sk-liteLLM-virt-abc123...    ← virtual key, NOT master key
   Content-Type: application/json
   
   {
     "model": "deepseek-chat",
     "messages": [...],
     "temperature": 0.7,
     "max_tokens": 4096,
     "stream": false
   }

4. If lite_key is None (sync failed):
   - Falls back to Authorization: Bearer <litellm_master_key>
   - Logs WARNING: "No virtual key for user=... provider=deepseek — falling back..."
   - Customer is NOT billed — FastRouter master key pays

5. Response handling:
   - status != 200 → RuntimeError
   - Reads x-litellm-response-cost header → cost_usd
   - Returns dict with provider, model, choices, usage, latency_ms, cost_usd
```

### 3e. LiteLLM Proxy: /v1/chat/completions

```
1. Auth: Bearer sk-liteLLM-virt-abc123...
   → Looks up virtual key in LiteLLM DB
   → Virtual key found with litellm_params: {api_key: "sk-deepseek-abc123...", api_base: "..."}

2. Resolves model "deepseek-chat":
   → config.yaml model entry: model=openai/deepseek-chat, api_base=https://api.deepseek.com/v1
   → Virtual key overrides api_key in litellm_params
   → Final params: model=openai/deepseek-chat, api_key="sk-deepseek-abc123...", api_base="..."

3. Calls DeepSeek API:
   POST https://api.deepseek.com/v1/chat/completions
   Authorization: Bearer sk-deepseek-abc123...
   
   → DeepSeek processes request, charges customer's account

4. LiteLLM tracks cost in x-litellm-response-cost header

5. Returns OpenAI-format response to FastRouter
```

### 3f. Backend: routes/proxy.py — Post-Response

```
1. Caches response in Redis:
   cache.set(user_id, cache_key, result)  → TTL 1 hour

2. Increments free tier counter:
   if user.subscription_status != "active":
     user.free_requests_used += 1

3. Logs usage:
   INSERT INTO usage_logs (
     user_id, provider, model, prompt_tokens, completion_tokens,
     cost_usd, latency_ms, cached, agent_type
   ) VALUES (...)

4. Circuit breaker:
   breaker.on_success("deepseek")
   → INCR cb:deepseek:successes
   → If HALF_OPEN and success_count >= 3: reset to CLOSED

5. Returns to client:
   {
     "id": "chatcmpl-...",
     "object": "chat.completion",
     "model": "deepseek-chat",
     "choices": [...],
     "usage": {...},
     "x_provider": "deepseek",
     "x_cached": false,
     "x_agent_type": "chat"
   }
```

### 3g. Streaming Variant (stream=True)

```
1. Increments free tier counter before returning stream
2. Logs estimated UsageLog (input tokens estimated from message length)
3. Returns StreamingResponse with text/event-stream
4. route_stream() uses same virtual key auth as route()
5. Bytes streamed directly from LiteLLM → FastRouter → Client
```

### 3h. Failure Path

```
If LiteLLM/DeepSeek returns error:
  → RuntimeError raised
  → breaker.on_failure("deepseek")
    → INCR cb:deepseek:failures
    → If failures >= 5: set_state(OPEN), DELETE cb:deepseek:successes
  → HTTPException 502 returned to client
```

---

## STEP 4: USER DELETES DEEPSEEK KEY

### 4a. Frontend: ProviderKeys.jsx → handleDelete(id)

```
User clicks trash icon → Popconfirm "Remove this key?"
User confirms
  → api.deleteProviderKey("<provider_key_uuid>")
```

### 4b. Backend: routes/provider_keys.py → delete_provider_key()

```
1. SELECT * FROM provider_keys WHERE id=<uuid> AND user_id=<user_uuid>
   → Not found: 404

2. Extracts lite_key: "sk-liteLLM-virt-abc123..."

3. DELETE FROM provider_keys WHERE id=<uuid>

4. Calls LiteKeyManager.delete_key(lite_key):
   POST {litellm_url}/key/delete
   Authorization: Bearer <litellm_master_key>
   Content-Type: application/json
   
   {"keys": ["sk-liteLLM-virt-abc123..."]}

5. If delete fails: logs warning, still returns success
```

### 4c. LiteLLM Proxy: /key/delete

```
1. Validates master key
2. Deletes virtual key from internal DB
3. Returns 200
```

### 4d. Frontend: Post-Delete

```
load() refreshes the list → key no longer appears in table
```

---

## Summary: Expected State at Each Step

| Step | provider_keys table | LiteLLM virtual keys | Redis |
|------|-------------------|---------------------|-------|
| Before add | 0 rows for user | 0 keys | empty |
| After add (sync OK) | 1 row, lite_key='sk-liteLLM-...' | 1 key with litellm_params.api_key | empty |
| After add (sync fail) | 1 row, lite_key=NULL | 0 keys | empty |
| After proxy call | 1 row, free_requests_used++ | 1 key | cached response + cb:deepseek:successes=1 |
| After delete | 0 rows | 0 keys | cached response remains (TTL) |

## What Happens If LiteLLM Is Down

| Operation | Behavior |
|-----------|----------|
| Add provider key | Key saved to DB, lite_key=NULL, "synced": false, warning logged. User sees "Pending" tag. |
| Proxy request | Falls back to master key (FastRouter pays). WARNING logged. |
| Test connection | Still works — test endpoint calls provider directly, bypassing LiteLLM. |
| Delete provider key | Key deleted from DB. LiteLLM delete silently fails (warning logged). |

## What Happens If Virtual Key Exists But Customer's Provider Key Is Invalid

| Operation | Behavior |
|-----------|----------|
| Proxy request | LiteLLM calls DeepSeek → DeepSeek returns 401 → RuntimeError → 502 to client |
| Test connection | Direct call to DeepSeek returns 401 → "Provider reached but key rejected" |
| Circuit breaker | on_failure() increments cb:deepseek:failures |
