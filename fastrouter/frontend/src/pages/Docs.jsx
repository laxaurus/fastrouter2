import { useState } from "react";
import { Typography, Tabs, Card, Divider } from "@arco-design/web-react";

const { Title, Paragraph, Text } = Typography;

const curlSnippet = `# Get your FastRouter key from the API Keys page
export FASTROUTER_KEY="sk-your-fastrouter-key"

# List available models
curl https://api.fastrouter.dev/v1/models \\
  -H "Authorization: Bearer $FASTROUTER_KEY"

# Chat completion
curl https://api.fastrouter.dev/v1/chat/completions \\
  -H "Authorization: Bearer $FASTROUTER_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'

# Streaming
curl https://api.fastrouter.dev/v1/chat/completions \\
  -H "Authorization: Bearer $FASTROUTER_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Write a poem"}],
    "stream": true
  }'`;

const pythonSnippet = `import openai

client = openai.OpenAI(
    base_url="https://api.fastrouter.dev/v1",
    api_key="sk-your-fastrouter-key",
)

# Non-streaming
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")`;

const jsSnippet = `import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.fastrouter.dev/v1",
  apiKey: "sk-your-fastrouter-key",
});

const response = await client.chat.completions.create({
  model: "deepseek-chat",
  messages: [{ role: "user", content: "Hello!" }],
});

console.log(response.choices[0].message.content);`;

const providerSetup = `# DeepSeek
# 1. Go to https://platform.deepseek.com/api_keys
# 2. Create an API key
# 3. Add billing if needed
# 4. Paste into FastRouter → Provider Keys
# Supported models: deepseek-chat, deepseek-reasoner, deepseek-v4-pro, deepseek-v4-flash

# Qwen (Alibaba Cloud)
# 1. Go to https://dashscope.console.aliyun.com/apiKey
# 2. Create an API key
# 3. Paste into FastRouter → Provider Keys
# Supported models: qwen-turbo, qwen-plus, qwen-max

# GLM (Zhipu)
# 1. Go to https://open.bigmodel.cn/usercenter/apikeys
# 2. Create an API key
# 3. Paste into FastRouter → Provider Keys
# Supported models: glm-4, glm-4-flash, GLM-4.5-Air

# Kimi (Moonshot)
# 1. Go to https://platform.moonshot.cn/console/api-keys
# 2. Create an API key
# 3. Paste into FastRouter → Provider Keys
# Supported models: kimi-latest`;

export default function Docs() {
  const [activeTab, setActiveTab] = useState("quickstart");

  return (
    <div style={{ maxWidth: 860, margin: "0 auto" }}>
      <Title heading={3} style={{ marginBottom: 4 }}>Documentation</Title>
      <Paragraph type="secondary" style={{ marginBottom: 24 }}>
        Everything you need to integrate FastRouter into your stack.
      </Paragraph>

      <Tabs activeTab={activeTab} onChange={setActiveTab} style={{ marginBottom: 24 }}>
        <Tabs.TabPane key="quickstart" title="Quickstart" />
        <Tabs.TabPane key="api" title="API Reference" />
        <Tabs.TabPane key="providers" title="Provider Setup" />
        <Tabs.TabPane key="failover" title="Routing & Failover" />
        <Tabs.TabPane key="concepts" title="Concepts" />
      </Tabs>

      <Card>
        {/* ── Quickstart ───────────────────────────────────── */}
        {activeTab === "quickstart" && (
          <div>
            <Title heading={4}>1. Create an account</Title>
            <Paragraph>
              Register at <Text code>fastrouter.dev</Text>. Your first 1,000 requests are free.
            </Paragraph>

            <Title heading={4} style={{ marginTop: 28 }}>2. Add your provider API keys</Title>
            <Paragraph>
              Go to <Text code>Provider Keys</Text> in the dashboard. Add at least one provider key
              (DeepSeek, Qwen, GLM, or Kimi). Keys are encrypted at rest with AES-256.
            </Paragraph>

            <Title heading={4} style={{ marginTop: 28 }}>3. Create a FastRouter API key</Title>
            <Paragraph>
              Go to <Text code>API Keys</Text> and create a new key. This is the key you'll use in
              your application. It starts with <Text code>sk-</Text>.
            </Paragraph>

            <Title heading={4} style={{ marginTop: 28 }}>4. Make your first request</Title>
            <Tabs>
              <Tabs.TabPane key="curl" title="cURL">
                <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
                  {curlSnippet}
                </pre>
              </Tabs.TabPane>
              <Tabs.TabPane key="python" title="Python (OpenAI SDK)">
                <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
                  {pythonSnippet}
                </pre>
              </Tabs.TabPane>
              <Tabs.TabPane key="js" title="JavaScript / TypeScript">
                <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
                  {jsSnippet}
                </pre>
              </Tabs.TabPane>
            </Tabs>

            <Title heading={4} style={{ marginTop: 28 }}>5. Use with coding agents</Title>
            <Paragraph>
              FastRouter works with any OpenAI-compatible client. Configure your coding agent:
            </Paragraph>

            <Tabs>
              <Tabs.TabPane key="cursor" title="Cursor">
                <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
{`# Settings → Models → OpenAI API Key
# Base URL: https://api.fastrouter.dev/v1
# API Key: sk-your-fastrouter-key
# Model: deepseek-chat (or any supported model)`}
                </pre>
              </Tabs.TabPane>
              <Tabs.TabPane key="continue" title="Continue / Cline">
                <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
{`# config.json
{
  "models": [{
    "title": "DeepSeek via FastRouter",
    "provider": "openai",
    "apiBase": "https://api.fastrouter.dev/v1",
    "apiKey": "sk-your-fastrouter-key",
    "model": "deepseek-chat"
  }]
}`}
                </pre>
              </Tabs.TabPane>
            </Tabs>
          </div>
        )}

        {/* ── API Reference ────────────────────────────────── */}
        {activeTab === "api" && (
          <div>
            <Title heading={4}>Authentication</Title>
            <Paragraph>
              All requests require an API key in the <Text code>Authorization</Text> header:
            </Paragraph>
            <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`Authorization: Bearer sk-your-fastrouter-key`}
            </pre>
            <Paragraph type="secondary">
              Keys are managed from the <Text code>API Keys</Text> page in your dashboard.
            </Paragraph>

            <Divider />

            <Title heading={4}>GET /v1/models</Title>
            <Paragraph>List all available models across all configured providers.</Paragraph>
            <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`curl https://api.fastrouter.dev/v1/models \\
  -H "Authorization: Bearer sk-your-key"`}
            </pre>

            <Divider />

            <Title heading={4}>POST /v1/chat/completions</Title>
            <Paragraph>
              OpenAI-compatible chat completions endpoint. Supports both streaming and non-streaming.
            </Paragraph>

            <Title heading={5}>Request body</Title>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e6eb", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>Parameter</th>
                  <th style={{ padding: "8px 12px" }}>Type</th>
                  <th style={{ padding: "8px 12px" }}>Required</th>
                  <th style={{ padding: "8px 12px" }}>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>model</Text></td>
                  <td style={{ padding: "8px 12px" }}>string</td>
                  <td style={{ padding: "8px 12px" }}>Yes</td>
                  <td style={{ padding: "8px 12px" }}>Model name (e.g. deepseek-chat, qwen-max)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>messages</Text></td>
                  <td style={{ padding: "8px 12px" }}>array</td>
                  <td style={{ padding: "8px 12px" }}>Yes</td>
                  <td style={{ padding: "8px 12px" }}>Array of message objects with role and content</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>temperature</Text></td>
                  <td style={{ padding: "8px 12px" }}>number</td>
                  <td style={{ padding: "8px 12px" }}>No</td>
                  <td style={{ padding: "8px 12px" }}>Sampling temperature (0-2, default 0.7)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>max_tokens</Text></td>
                  <td style={{ padding: "8px 12px" }}>integer</td>
                  <td style={{ padding: "8px 12px" }}>No</td>
                  <td style={{ padding: "8px 12px" }}>Maximum tokens in response (default 4096)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>stream</Text></td>
                  <td style={{ padding: "8px 12px" }}>boolean</td>
                  <td style={{ padding: "8px 12px" }}>No</td>
                  <td style={{ padding: "8px 12px" }}>Enable SSE streaming (default false)</td>
                </tr>
              </tbody>
            </table>

            <Title heading={5} style={{ marginTop: 24 }}>Response (non-streaming)</Title>
            <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
{`{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "deepseek-chat",
  "provider": "deepseek",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}`}
            </pre>

            <Title heading={5} style={{ marginTop: 24 }}>Error responses</Title>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e6eb", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>Status</th>
                  <th style={{ padding: "8px 12px" }}>Meaning</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>401</Text></td>
                  <td style={{ padding: "8px 12px" }}>Invalid or missing API key</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>400</Text></td>
                  <td style={{ padding: "8px 12px" }}>No provider key configured for the requested model</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>429</Text></td>
                  <td style={{ padding: "8px 12px" }}>Rate limit exceeded. Check Retry-After header</td>
                </tr>
                <tr style={{ borderBottom: "1px solid #f2f3f5" }}>
                  <td style={{ padding: "8px 12px" }}><Text code>502</Text></td>
                  <td style={{ padding: "8px 12px" }}>Provider returned an error. Automatic failover attempted</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* ── Provider Setup ───────────────────────────────── */}
        {activeTab === "providers" && (
          <div>
            <Title heading={4}>Setting up provider API keys</Title>
            <Paragraph>
              FastRouter is BYOK (Bring Your Own Key). You need API keys from the providers you want
              to use. Keys are encrypted with AES-256 before storage.
            </Paragraph>

            <Title heading={5}>Adding keys in the dashboard</Title>
            <Paragraph>
              Navigate to <Text code>Provider Keys</Text> in the sidebar, select your provider from
              the dropdown, paste your API key, and click Add.
            </Paragraph>

            <Divider />

            <Title heading={4}>Provider-specific instructions</Title>
            <pre style={{ background: "#f7f8fa", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto", lineHeight: 1.6 }}>
              {providerSetup}
            </pre>

            <Divider />

            <Title heading={4} style={{ marginTop: 24 }}>How keys are stored</Title>
            <ul>
              <li><Text strong>Encryption:</Text> Provider keys are encrypted at rest using AES-256-CBC with a per-key random IV. The encryption key is derived from <Text code>FERNET_SECRET</Text>.</li>
              <li><Text strong>In transit:</Text> Keys are passed to LiteLLM (the proxy engine) over an internal Docker network. They never leave your infrastructure.</li>
              <li><Text strong>Never logged:</Text> Decrypted keys are never written to log files or stored in plaintext.</li>
            </ul>

            <Divider />

            <Title heading={4}>Testing your provider keys</Title>
            <Paragraph>
              Use the Test button on the Provider Keys page to verify a key works. You can optionally
              specify a model to test against. The test makes a lightweight API call to confirm
              connectivity.
            </Paragraph>
          </div>
        )}

        {/* ── Routing & Failover ───────────────────────────── */}
        {activeTab === "failover" && (
          <div>
            <Title heading={4}>Model-to-provider resolution</Title>
            <Paragraph>
              When you send a request, FastRouter resolves which provider to use:
            </Paragraph>
            <ol>
              <li><Text strong>Exact model match:</Text> If <Text code>deepseek-chat</Text> is configured with provider <Text code>deepseek</Text>, use that provider key.</li>
              <li><Text strong>Fuzzy model match:</Text> If the exact model isn't found, try substring matching against known models.</li>
              <li><Text strong>Provider name fallback:</Text> If the model name contains a provider name (e.g. <Text code>qwen-*</Text>), route to that provider.</li>
            </ol>

            <Divider />

            <Title heading={4}>Automatic failover</Title>
            <Paragraph>
              If a provider is unreachable or returns errors, FastRouter routes to a healthy
              alternative. Failover is configured in LiteLLM's routing settings:
            </Paragraph>
            <ul>
              <li><Text strong>Circuit breaker:</Text> Opens after 5 consecutive failures. The provider is retried after 60 seconds.</li>
              <li><Text strong>Fallback chain:</Text> deepseek → glm → kimi → qwen. Each provider has a designated backup.</li>
              <li><Text strong>Usage-based routing:</Text> When multiple instances of a model exist, LiteLLM distributes load.</li>
            </ul>

            <Divider />

            <Title heading={4}>Prompt caching</Title>
            <Paragraph>
              FastRouter caches LLM responses for identical prompts (SHA-256 hash of messages + model).
              Benefits:
            </Paragraph>
            <ul>
              <li>Coding agents: system prompt + tool definitions are identical across requests</li>
              <li>CI/CD pipelines: repeated test prompts served from cache</li>
              <li>Development: same prompt during debugging hits cache</li>
            </ul>
            <Paragraph>
              Cache TTL is configurable (default: 1 hour). Cache keys are scoped per user — your cached
              responses are never served to other users.
            </Paragraph>

            <Divider />

            <Title heading={4}>Monitoring provider health</Title>
            <Paragraph>
              The Dashboard shows real-time provider health status:
            </Paragraph>
            <ul>
              <li><Text code>closed</Text> — Provider is healthy and accepting requests</li>
              <li><Text code>open</Text> — Circuit breaker is open; requests are being routed to fallbacks</li>
              <li><Text code>unknown</Text> — No requests have been sent to this provider yet</li>
            </ul>
          </div>
        )}

        {/* ── Concepts ─────────────────────────────────────── */}
        {activeTab === "concepts" && (
          <div>
            <Title heading={4}>FastRouter API Key</Title>
            <Paragraph>
              Your FastRouter key (starting with <Text code>sk-</Text>) authenticates you to the
              FastRouter platform. It does NOT authenticate you directly to LLM providers. Instead,
              FastRouter uses your stored provider keys to forward requests.
            </Paragraph>

            <Divider />

            <Title heading={4}>Provider Key</Title>
            <Paragraph>
              A provider key is your personal API key from a specific LLM provider (DeepSeek, Qwen,
              etc.). FastRouter stores it encrypted and uses it to proxy your requests. You maintain
              billing relationships directly with each provider — FastRouter never marks up API costs.
            </Paragraph>

            <Divider />

            <Title heading={4}>LiteLLM Virtual Key</Title>
            <Paragraph>
              Internally, FastRouter creates a LiteLLM virtual key (a proxy-scoped key with model
              access control) for each of your provider keys. This virtual key is what LiteLLM uses
              to enforce routing policies. You never interact with virtual keys directly.
            </Paragraph>

            <Divider />

            <Title heading={4}>Model</Title>
            <Paragraph>
              A model is a specific LLM version available through a provider (e.g.,
              <Text code> deepseek-chat</Text>, <Text code> qwen-max</Text>). Admins manage the model
              catalog. Users add provider keys to enable specific models.
            </Paragraph>

            <Divider />

            <Title heading={4}>Circuit Breaker</Title>
            <Paragraph>
              The circuit breaker pattern prevents cascading failures. When a provider returns
              consecutive errors, the breaker "opens" and routes requests to a fallback provider.
              After a cooldown period, a test request probes the provider. If it succeeds, the
              breaker "closes" and normal routing resumes.
            </Paragraph>

            <Divider />

            <Title heading={4}>Usage Log</Title>
            <Paragraph>
              Every request is recorded in the usage log with: model, provider, token counts, latency,
              cost, cache hit status, and user agent. Usage logs power the analytics dashboard and
              billing system.
            </Paragraph>
          </div>
        )}
      </Card>
    </div>
  );
}
