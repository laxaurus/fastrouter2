# End-to-End Manual Verification Test Case

## Preconditions

Before starting, verify these services are running:

```bash
# 1. PostgreSQL
docker ps | grep fastrouter-postgres

# 2. Redis
docker ps | grep fastrouter-redis

# 3. LiteLLM proxy (port 4000)
curl -s http://localhost:4000/health | head -1

# 4. FastRouter backend (port 8000)
curl -s http://localhost:8000/health

# 5. Frontend dev server (port 5173)
curl -s http://localhost:5173/ | head -1
```

If any service is missing, run `docker-compose up -d` then `npx vite --host 0.0.0.0 &` from the `frontend/` directory.

### Wipe Previous Data (Recommended)

```bash
python scripts/fresh_start.py --yes
```

This clears all users, keys, usage logs, and Redis data for a clean test.

---

## PHASE 1: REGISTRATION & LOGIN

### Step 1.1: Open the app

| Action | Expected |
|--------|----------|
| Navigate to `http://localhost:5173` | Redirected to `/login` |
| Page shows | FastRouter card with Login/Register tabs |

**Visual check:** The card has a title "FastRouter", two tabs ("Login" / "Register"), email + password fields, and "1,000 free requests included" text at the bottom.

### Step 1.2: Register a new account

| Action | Expected |
|--------|----------|
| Click "Register" tab | Shows "Create Account" button instead of "Login" |
| Enter email: `test@example.com` | |
| Enter password: `test1234` (min 8 chars) | |
| Click "Create Account" | Green toast: "Account created!" |
| | Redirected to `/` (Dashboard) |

**Visual check after redirect:**
- Header shows "FastRouter" on the left
- Header shows `test@example.com` and a **Sign Out** button on the right
- Sidebar has menu items: Dashboard, API Keys, Provider Keys (BYOK), Billing, Settings, Docs

**DB check:**
```sql
SELECT id, email, subscription_status, free_requests_used, free_requests_limit
FROM users WHERE email = 'test@example.com';
-- Expect: 1 row, subscription_status='inactive', free_requests_used=0
```

### Step 1.3: Sign out and log back in

| Action | Expected |
|--------|----------|
| Click "Sign Out" button in header | Green toast: "Signed out" |
| | Redirected to `/login` |
| Click "Login" tab | |
| Enter `test@example.com` / `test1234` | |
| Click "Login" | Green toast: "Welcome back!" |
| | Redirected to Dashboard |

### Step 1.4: Verify token refresh (optional, in DevTools)

| Action | Expected |
|--------|----------|
| Open DevTools → Application → Local Storage | See `access_token` and `refresh_token` keys |
| Wait 30 minutes | Next API call auto-refreshes token silently |

---

## PHASE 2: CREATE PLATFORM API KEY

### Step 2.1: Navigate to API Keys page

| Action | Expected |
|--------|----------|
| Click "API Keys" in sidebar | URL changes to `/keys` |
| | Page title: "API Keys" |
| | "New Key" button visible (blue, top right) |
| | Empty table or "No data" message |

### Step 2.2: Open create key modal

| Action | Expected |
|--------|----------|
| Click "New Key" button | Modal opens titled "Create API Key" |
| | Input field pre-filled with "Default" |
| | "Cancel" and "Create" buttons in footer |

### Step 2.3: Create the key

| Action | Expected |
|--------|----------|
| Change name to "E2E Test Key" | |
| Click "Create" | Modal content changes to show: |
| | **(a)** Yellow warning banner: "Copy this key now — it won't be shown again." |
| | **(b)** Textarea with the full key (starts with `sk-`) |
| | **(c)** Blue "Copy to Clipboard" button (full width) |
| | **(d)** Single "Done" button in footer |

**Visual check:** The warning banner must be yellow/orange with a border. The key must start with `sk-`.

### Step 2.4: Copy the key

| Action | Expected |
|--------|----------|
| Click "Copy to Clipboard" | Button text changes to "Copied!" with check icon |
| | Green toast: "API key copied to clipboard" |
| Click "Done" | Modal closes |

**Verify:** Paste into a text editor — the key should be `sk-` followed by random characters.

### Step 2.5: Verify key appears in table

| Action | Expected |
|--------|----------|
| Look at the keys table | 1 row appears: |

| Name | Prefix | Status | Last Used | Created |
|------|--------|--------|-----------|---------|
| E2E Test Key | `sk-xxxxx...` | **Active** (green tag) | Never | today's date |

**DB check:**
```sql
SELECT id, name, key_prefix, is_active, last_used_at
FROM api_keys WHERE name = 'E2E Test Key';
-- Expect: 1 row, is_active=true, last_used_at=NULL
```

**Save the API key** for Phase 4 testing. You'll need it to call the proxy endpoint.

---

## PHASE 3: ADD PROVIDER KEY (BYOK)

### Step 3.1: Navigate to Provider Keys page

| Action | Expected |
|--------|----------|
| Click "Provider Keys (BYOK)" in sidebar | URL changes to `/providers` |
| | Page title: "Provider Keys (BYOK)" |
| | "Add Key" button visible (blue, top right) |
| | Empty state message: "No provider keys yet. Add your DeepSeek or Qwen API key to start routing." |

### Step 3.2: Open add key modal

| Action | Expected |
|--------|----------|
| Click "Add Key" | Modal opens titled "Add Provider Key" |
| | Provider dropdown (default: "DeepSeek") |
| | Password input for API key |
| | "Add" button in footer |
| | Small text: "Your key is encrypted at rest with AES-256..." |

### Step 3.3: Add a DeepSeek key (sync succeeds)

**Precondition:** LiteLLM must be running on port 4000. If LiteLLM is down, skip to Step 3.5.

| Action | Expected |
|--------|----------|
| Select "DeepSeek" from dropdown | |
| Paste a valid DeepSeek API key (`sk-deepseek-...`) | Input is masked (dots) |
| Click "Add" | Modal closes |
| | Green toast: "Provider key added" |
| | Table refreshes |

### Step 3.4: Verify key appears with "Ready" status

| Action | Expected |
|--------|----------|
| Look at the provider keys table | 1 row appears: |

| Provider | Key Prefix | Synced | Status | Added | Actions |
|----------|-----------|--------|--------|-------|---------|
| **deepseek** (blue tag) | `sk-deeps...` | **Ready** (green tag) | **Active** (green tag) | today | **Test** button + trash icon |

**Key detail:** The "Test" button must be **enabled** (clickable) because `synced === true`.

**DB check:**
```sql
SELECT id, provider, key_prefix, lite_key, is_active
FROM provider_keys;
-- Expect: 1 row, lite_key IS NOT NULL (starts with 'sk-'), is_active=true
```

**LiteLLM check:**
```bash
curl -s http://localhost:4000/key/list \
  -H "Authorization: Bearer sk-master-key-fastrouter" | jq '.keys | length'
# Expect: >= 1
```

### Step 3.5: What happens when LiteLLM is DOWN (failure mode)

| Action | Expected |
|--------|----------|
| Stop LiteLLM: `docker stop fastrouter-litellm-1` | |
| Repeat Step 3.2-3.3 with "Qwen (Alibaba)" and a test key | Modal closes |
| | Green toast: "Provider key added" (still succeeds — key saved to DB) |
| | Table shows Qwen row with **Pending** (orange tag) in Synced column |
| | **Test button is disabled** (greyed out, not clickable) |

**DB check:**
```sql
SELECT provider, lite_key FROM provider_keys WHERE provider = 'qwen';
-- Expect: lite_key IS NULL (sync failed because LiteLLM was down)
```

**Restart LiteLLM after this test:**
```bash
docker start fastrouter-litellm-1
```

---

## PHASE 4: TEST PROVIDER CONNECTIVITY

### Step 4.1: Test a synced key

| Action | Expected |
|--------|----------|
| Click "Test" button on the DeepSeek row | Button shows a spinner while testing |
| | After response: |

**Success case (valid key):**
- Green alert appears above table: "Connection successful — 245ms latency"
- Green toast: "Connected in 245ms"

**Auth failure case (invalid/expired key):**
- Yellow alert appears: "Provider reached but key was rejected"
- Yellow toast: "Provider reached but key rejected (245ms)"

**Connection failure case (wrong API base):**
- Red alert appears: "Connection failed"
- Red toast with detail like "Could not connect to..."

### Step 4.2: Dismiss the test result

| Action | Expected |
|--------|----------|
| Click the "×" on the alert | Alert disappears |

### Step 4.3: Test button stays disabled for unsynced keys

| Action | Expected |
|--------|----------|
| Look at the Qwen row (if you tested Step 3.5) | Test button is greyed out and shows no pointer cursor on hover |
| Click it anyway | Nothing happens |

---

## PHASE 5: PROXY REQUEST (The Core Flow)

### Step 5.1: Make a chat completion request

Replace `<PLATFORM_API_KEY>` with the key from Step 2.4.

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <PLATFORM_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Say hello in exactly 3 words."}],
    "temperature": 0.7,
    "max_tokens": 50
  }' | jq .
```

**Expected response (200):**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": ...,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": ...,
    "completion_tokens": ...,
    "total_tokens": ...
  },
  "x_provider": "deepseek",
  "x_cached": false,
  "x_agent_type": "chat"
}
```

**Verify:**
- `x_provider` is `"deepseek"`
- `x_cached` is `false`
- `x_agent_type` is `"chat"` (or `"unknown"`)

### Step 5.2: Check frontend API key "Last Used" update

| Action | Expected |
|--------|----------|
| Navigate to "API Keys" page | The "E2E Test Key" row now shows **today's date** in "Last Used" column (instead of "Never") |

### Step 5.3: Verify database state after proxy call

```sql
-- Free tier counter incremented
SELECT free_requests_used FROM users WHERE email = 'test@example.com';
-- Expect: >= 1

-- Usage log recorded
SELECT provider, model, prompt_tokens, completion_tokens, cost_usd,
       latency_ms, cached, agent_type
FROM usage_logs WHERE user_id = '<user_uuid>';
-- Expect: 1 row with provider='deepseek', model='deepseek-chat', cached=false

-- LiteLLM cost tracking (check LiteLLM response headers)
-- Look at cost_usd in usage_logs — should be a small decimal like 0.000123
```

### Step 5.4: Test prompt cache (second identical request)

Run the **exact same** curl command from Step 5.1 again.

**Expected response:**
```json
{
  "x_provider": "deepseek",
  "x_cached": true,
  ...
}
```

**Verify:** `x_cached` is `true`. The response returns instantly (latency ~1ms in DB).

```sql
-- Cache hit recorded in usage_logs
SELECT COUNT(*) FROM usage_logs WHERE cached = true;
-- Expect: >= 1
```

### Step 5.5: Test streaming request

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <PLATFORM_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Count from 1 to 5."}],
    "stream": true
  }'
```

**Expected:** SSE stream with `data: {...}` chunks ending with `data: [DONE]`.

### Step 5.6: Test without provider key (error case)

If you haven't added a provider key for `qwen`, this should fail:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <PLATFORM_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Expected:** 502 error with detail "Provider error: No API key found for provider 'qwen'..."

### Step 5.7: Test free tier exhaustion (simulation)

```sql
-- Manually set free_requests_used to 1000
UPDATE users SET free_requests_used = 1000 WHERE email = 'test@example.com';
```

Then repeat Step 5.1:

**Expected:** 402 error — "Free tier limit reached. Please subscribe to continue."

```sql
-- Reset for further testing
UPDATE users SET free_requests_used = 0 WHERE email = 'test@example.com';
```

---

## PHASE 6: DELETE PROVIDER KEY

### Step 6.1: Delete the DeepSeek key

| Action | Expected |
|--------|----------|
| Navigate to "Provider Keys (BYOK)" | See the DeepSeek row |
| Click the trash icon on the DeepSeek row | Popconfirm appears: "Remove this key?" |
| Click "OK" to confirm | Row disappears |
| | Green toast: "Provider key removed" |

**DB check:**
```sql
SELECT COUNT(*) FROM provider_keys WHERE provider = 'deepseek';
-- Expect: 0
```

**LiteLLM check:**
```bash
# Virtual key should be deleted from LiteLLM
curl -s http://localhost:4000/key/list \
  -H "Authorization: Bearer sk-master-key-fastrouter" | jq '.keys | length'
# Expect: fewer keys than before
```

### Step 6.2: Verify proxy request now fails for DeepSeek

Repeat Step 5.1 with `model: "deepseek-chat"`.

**Expected:** 502 error — "No API key found for provider 'deepseek'. Add one in the dashboard."

### Step 6.3: Delete a key when LiteLLM is down

| Action | Expected |
|--------|----------|
| Stop LiteLLM: `docker stop fastrouter-litellm-1` | |
| Delete the Qwen key (trash icon → confirm) | Key still deleted from DB |
| | Green toast still appears |
| | No error shown to user (LiteLLM delete fails silently) |

**DB check:**
```sql
SELECT COUNT(*) FROM provider_keys;
-- Expect: 0
```

Restart LiteLLM: `docker start fastrouter-litellm-1`

---

## PHASE 7: REVOKE PLATFORM API KEY

### Step 7.1: Delete the API key

| Action | Expected |
|--------|----------|
| Navigate to "API Keys" | See "E2E Test Key" row |
| Click trash icon | Popconfirm: "Revoke this key? This cannot be undone." |
| Click "OK" to confirm | Row disappears |
| | Green toast: "Key revoked" |

### Step 7.2: Verify key no longer works

Repeat Step 5.1 with the same platform API key.

**Expected:** 401 error — "Invalid API key"

---

## Summary Checklist

Print this and check off each item during testing:

### Phase 1: Auth
- [ ] Register new user → redirected to Dashboard
- [ ] Header shows email + Sign Out button
- [ ] Sign out → back to login
- [ ] Login → back to Dashboard
- [ ] Password < 8 chars rejected on both login and register

### Phase 2: API Keys
- [ ] Create key modal opens with name input
- [ ] After create: yellow warning banner visible
- [ ] Full key shown in read-only textarea (starts with `sk-`)
- [ ] "Copy to Clipboard" button works, changes to "Copied!"
- [ ] Key row appears in table with green "Active" tag
- [ ] "Last Used" shows "Never"

### Phase 3: Provider Keys (BYOK)
- [ ] Add key modal has provider dropdown (4 options: DeepSeek, Qwen, Kimi, GLM)
- [ ] API key input is masked (password type)
- [ ] With LiteLLM running: "Ready" tag appears, Test button enabled
- [ ] With LiteLLM down: "Pending" tag appears, Test button disabled

### Phase 4: Provider Test
- [ ] Test button shows spinner while testing
- [ ] Valid key → green alert with latency
- [ ] Invalid key → yellow alert "key was rejected"
- [ ] Could not connect → red alert with detail
- [ ] Alert dismissible with × button
- [ ] Test button disabled when synced=false

### Phase 5: Proxy
- [ ] `/v1/chat/completions` returns 200 with valid platform key
- [ ] Response includes `x_provider`, `x_cached`, `x_agent_type`
- [ ] API key "Last Used" updates in frontend table
- [ ] Prompt cache: second identical request returns `x_cached: true`
- [ ] Streaming: SSE chunks with `data: [DONE]` termination
- [ ] Missing provider key → 502 "No API key found"
- [ ] Free tier exhausted → 402 "Please subscribe"

### Phase 6: Delete Provider Key
- [ ] Trash icon → popconfirm → key removed from table
- [ ] LiteLLM virtual key also deleted
- [ ] Proxy request for that provider now fails with 502
- [ ] Delete when LiteLLM down: still succeeds (silent warning)

### Phase 7: Revoke API Key
- [ ] Trash icon → popconfirm → key removed from table
- [ ] Revoked key returns 401 on proxy request

---

## Environment Reset After Testing

```bash
# Reset all data
python scripts/fresh_start.py --yes

# Or reset just Redis (clear cache + circuit breakers)
python scripts/fresh_start.py --redis-only
```
