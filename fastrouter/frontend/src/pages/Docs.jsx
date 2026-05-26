import { Card, Typography, Tabs } from "@arco-design/web-react";

const { Title, Paragraph } = Typography;

export default function Docs() {
  return (
    <div>
      <Title heading={4} style={{ marginBottom: 16 }}>Documentation</Title>

      <Card>
        <Tabs>
          <Tabs.TabPane key="quickstart" title="Quickstart">
            <Title heading={5}>1. Get your API key</Title>
            <Paragraph>
              Go to <strong>API Keys</strong> and create a new key. You'll get a key starting with <code>sk-</code>.
            </Paragraph>

            <Title heading={5}>2. Add your provider keys</Title>
            <Paragraph>
              Go to <strong>Provider Keys</strong> and add your DeepSeek or Qwen API key.
              Your keys are encrypted at rest and only used to proxy your requests.
            </Paragraph>

            <Title heading={5}>3. Make your first API call</Title>
            <Paragraph>
              Use the same OpenAI-compatible endpoint you already know:
            </Paragraph>

            <Tabs>
              <Tabs.TabPane key="curl" title="cURL">
                <pre style={{ background: "var(--color-fill-2)", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`curl http://localhost:8000/v1/chat/completions \\
  -H "Authorization: Bearer sk-your-fastrouter-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Write a Python function to sort a list"}]
  }'`}
                </pre>
              </Tabs.TabPane>
              <Tabs.TabPane key="python" title="Python">
                <pre style={{ background: "var(--color-fill-2)", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`import requests

headers = {
    "Authorization": "Bearer sk-your-fastrouter-key",
    "Content-Type": "application/json",
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
    headers=headers,
)

print(response.json()["choices"][0]["message"]["content"])`}
                </pre>
              </Tabs.TabPane>
              <Tabs.TabPane key="js" title="JavaScript">
                <pre style={{ background: "var(--color-fill-2)", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer sk-your-fastrouter-key",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "deepseek-chat",
    messages: [{ role: "user", content: "Hello!" }],
  }),
});

const data = await response.json();
console.log(data.choices[0].message.content);`}
                </pre>
              </Tabs.TabPane>
            </Tabs>
          </Tabs.TabPane>

          <Tabs.TabPane key="models" title="Models">
            <div style={{ marginBottom: 16 }}>
              <Title heading={5}>DeepSeek</Title>
              <ul>
                <li><code>deepseek-chat</code> — DeepSeek-V3, best overall value</li>
                <li><code>deepseek-reasoner</code> — DeepSeek-R1, reasoning tasks</li>
              </ul>
            </div>
            <div>
              <Title heading={5}>Qwen (Alibaba)</Title>
              <ul>
                <li><code>qwen-plus</code> — Balanced performance/cost</li>
                <li><code>qwen-max</code> — Maximum capability</li>
                <li><code>qwen-turbo</code> — Fast, cost-effective</li>
              </ul>
            </div>
            <Paragraph type="secondary" style={{ marginTop: 16 }}>
              More providers (Kimi, GLM) coming soon. Failover happens automatically between providers.
            </Paragraph>
          </Tabs.TabPane>

          <Tabs.TabPane key="failover" title="Failover">
            <Title heading={5}>Automatic Provider Failover</Title>
            <Paragraph>
              FastRouter detects provider failures and automatically routes to a healthy alternative:
            </Paragraph>
            <ul>
              <li><strong>DeepSeek down?</strong> → Requests auto-route to Qwen</li>
              <li><strong>Qwen down?</strong> → Requests auto-route to DeepSeek</li>
            </ul>
            <Paragraph>
              The circuit breaker opens after 5 consecutive failures and tries the provider
              again after 60 seconds. You can monitor provider health on the Dashboard.
            </Paragraph>

            <Title heading={5}>Prompt Caching</Title>
            <Paragraph>
              Repeated prompts are cached for 1 hour, saving you money on provider API costs.
              Coding agents benefit most — system prompts and instructions are often identical
              across requests.
            </Paragraph>
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
