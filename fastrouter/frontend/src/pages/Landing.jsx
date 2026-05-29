import { useNavigate } from "react-router-dom";
import { Button, Card, Grid, Typography, Divider } from "@arco-design/web-react";
import {
  IconCloud,
  IconSafe,
  IconThunderbolt,
  IconCode,
  IconDashboard,
  IconSwap,
  IconLock,
  IconBranch,
  IconStorage,
} from "@arco-design/web-react/icon";

const { Title, Paragraph, Text } = Typography;
const { Row, Col } = Grid;

const features = [
  {
    icon: <IconSwap style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "Multi-Provider Routing",
    desc: "One API, every Chinese LLM. DeepSeek, Qwen, GLM, Kimi — auto-routed through a single endpoint with intelligent failover.",
  },
  {
    icon: <IconLock style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "Bring Your Own Key",
    desc: "You own the provider relationship. Add your API keys, we encrypt them and proxy requests. No markup, no reseller margin. Your keys, your data.",
  },
  {
    icon: <IconThunderbolt style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "Smart Caching",
    desc: "Identical prompts served from cache at zero cost. Coding agents save up to 60% on token spend through system prompt deduplication.",
  },
  {
    icon: <IconBranch style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "Automatic Failover",
    desc: "Circuit breakers detect provider outages and reroute to healthy alternatives in milliseconds. No manual intervention needed.",
  },
  {
    icon: <IconDashboard style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "Usage Analytics",
    desc: "Per-model cost tracking, latency percentiles, agent detection, and cache hit rates. Know exactly where your tokens go.",
  },
  {
    icon: <IconCode style={{ fontSize: 28, color: "#165DFF" }} />,
    title: "OpenAI-Compatible",
    desc: "Drop-in replacement for any OpenAI SDK client. No code changes — just swap the base URL and API key.",
  },
];

const tiers = [
  {
    name: "Free",
    price: "0",
    period: "forever",
    requests: "1,000",
    features: [
      "All supported models",
      "Automatic failover",
      "Prompt caching",
      "Basic analytics",
      "Community support",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "29",
    period: "month",
    requests: "100,000",
    features: [
      "Everything in Free",
      "Priority failover routing",
      "Advanced analytics",
      "Agent detection",
      "Email support",
      "SLA guarantee",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    requests: "Unlimited",
    features: [
      "Everything in Pro",
      "Custom rate limits",
      "Multi-tenant teams",
      "SSO / SAML",
      "Dedicated support",
      "On-premise deployment",
    ],
    cta: "Contact Us",
    highlighted: false,
  },
];

const providers = [
  { name: "DeepSeek", models: "deepseek-chat, deepseek-reasoner, deepseek-v4-pro" },
  { name: "Qwen (Alibaba)", models: "qwen-turbo, qwen-plus, qwen-max" },
  { name: "GLM (Zhipu)", models: "glm-4, glm-4-flash, GLM-4.5-Air" },
  { name: "Kimi (Moonshot)", models: "kimi-latest" },
];

export default function Landing() {
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  return (
    <div style={{ minHeight: "100vh", background: "#fff" }}>
      {/* ── Nav ──────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 40px",
          borderBottom: "1px solid #e5e6eb",
          position: "sticky",
          top: 0,
          background: "rgba(255,255,255,0.92)",
          backdropFilter: "blur(8px)",
          zIndex: 100,
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 20, color: "#165DFF", letterSpacing: -0.5 }}>
          FastRouter
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <a href="#features" style={{ color: "#4e5969", fontSize: 14, textDecoration: "none" }}>Features</a>
          <a href="#pricing" style={{ color: "#4e5969", fontSize: 14, textDecoration: "none" }}>Pricing</a>
          <a href="#providers" style={{ color: "#4e5969", fontSize: 14, textDecoration: "none" }}>Providers</a>
          <Button type="primary" onClick={() => navigate(token ? "/" : "/login")}>
            {token ? "Dashboard" : "Sign In"}
          </Button>
        </div>
      </div>

      {/* ── Hero ─────────────────────────────────────────── */}
      <div
        style={{
          padding: "80px 40px 60px",
          textAlign: "center",
          background: "linear-gradient(135deg, #f0f5ff 0%, #e8f4fd 40%, #f5f0ff 100%)",
        }}
      >
        <Title heading={1} style={{ fontSize: 48, fontWeight: 800, marginBottom: 20, letterSpacing: -1 }}>
          One API for Every<br />Chinese LLM
        </Title>
        <Paragraph style={{ fontSize: 18, color: "#4e5969", maxWidth: 620, margin: "0 auto 32px", lineHeight: 1.7 }}>
          Route requests across DeepSeek, Qwen, GLM, and Kimi through a single OpenAI-compatible
          endpoint. Bring your own keys, keep your provider relationships, and never worry about
          outages again.
        </Paragraph>
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          <Button type="primary" size="large" onClick={() => navigate("/login")} style={{ borderRadius: 8, height: 44, padding: "0 28px" }}>
            Start for free
          </Button>
          <Button
            size="large"
            onClick={() => navigate("/docs")}
            style={{ borderRadius: 8, height: 44, padding: "0 28px" }}
          >
            View docs
          </Button>
        </div>
        <div style={{ marginTop: 48, padding: "14px 20px", background: "rgba(22,93,255,0.06)", borderRadius: 8, display: "inline-block" }}>
          <code style={{ fontSize: 13, color: "#1d2129" }}>export FASTROUTER_KEY="sk-your-key"</code>
          <span style={{ margin: "0 10px", color: "#c9cdd4" }}>|</span>
          <code style={{ fontSize: 13, color: "#1d2129" }}>curl https://api.fastrouter.dev/v1/chat/completions</code>
        </div>
      </div>

      {/* ── Features ─────────────────────────────────────── */}
      <div id="features" style={{ padding: "80px 40px", maxWidth: 1100, margin: "0 auto" }}>
        <Title heading={2} style={{ textAlign: "center", fontWeight: 700, marginBottom: 12 }}>
          Why FastRouter?
        </Title>
        <Paragraph style={{ textAlign: "center", color: "#86909c", fontSize: 16, marginBottom: 48 }}>
          Built for teams that need reliable access to Chinese AI models without vendor lock-in.
        </Paragraph>

        <Row gutter={[32, 32]}>
          {features.map((f) => (
            <Col span={8} key={f.title}>
              <div style={{ padding: "8px 0" }}>
                <div style={{ marginBottom: 12 }}>{f.icon}</div>
                <Title heading={5} style={{ fontWeight: 600, marginBottom: 8 }}>{f.title}</Title>
                <Paragraph style={{ color: "#86909c", fontSize: 14, lineHeight: 1.7 }}>{f.desc}</Paragraph>
              </div>
            </Col>
          ))}
        </Row>
      </div>

      {/* ── How it works ─────────────────────────────────── */}
      <div style={{ padding: "80px 40px", background: "#f7f8fa", textAlign: "center" }}>
        <Title heading={2} style={{ fontWeight: 700, marginBottom: 12 }}>How It Works</Title>
        <Paragraph style={{ color: "#86909c", fontSize: 16, marginBottom: 48 }}>
          Three steps from your editor to any Chinese LLM.
        </Paragraph>

        <Row gutter={[24, 24]} style={{ maxWidth: 900, margin: "0 auto" }}>
          {[
            { step: "1", title: "Add your provider keys", desc: "DeepSeek, Qwen, GLM, Kimi — bring your own API keys. Encrypted at rest." },
            { step: "2", title: "Create a FastRouter API key", desc: "One key to route them all. Use it in any OpenAI-compatible client." },
            { step: "3", title: "Make requests as usual", desc: "Same /v1/chat/completions endpoint. We auto-route and failover." },
          ].map((s) => (
            <Col span={8} key={s.step}>
              <Card style={{ textAlign: "center", paddingTop: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: "50%",
                    background: "#165DFF",
                    color: "#fff",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: 18,
                    marginBottom: 16,
                  }}
                >
                  {s.step}
                </div>
                <Title heading={5} style={{ fontWeight: 600 }}>{s.title}</Title>
                <Paragraph style={{ color: "#86909c", fontSize: 14 }}>{s.desc}</Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* ── Providers ────────────────────────────────────── */}
      <div id="providers" style={{ padding: "80px 40px", maxWidth: 900, margin: "0 auto" }}>
        <Title heading={2} style={{ textAlign: "center", fontWeight: 700, marginBottom: 12 }}>
          Supported Providers
        </Title>
        <Paragraph style={{ textAlign: "center", color: "#86909c", fontSize: 16, marginBottom: 48 }}>
          We support every major Chinese LLM provider. More added weekly.
        </Paragraph>

        <Row gutter={[16, 16]}>
          {providers.map((p) => (
            <Col span={12} key={p.name}>
              <Card>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                  <IconCloud style={{ fontSize: 22, color: "#165DFF" }} />
                  <Title heading={5} style={{ fontWeight: 600, margin: 0 }}>{p.name}</Title>
                </div>
                <Paragraph style={{ color: "#86909c", fontSize: 13, fontFamily: "monospace", margin: 0 }}>
                  {p.models}
                </Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* ── Pricing ──────────────────────────────────────── */}
      <div id="pricing" style={{ padding: "80px 40px", background: "#f7f8fa" }}>
        <Title heading={2} style={{ textAlign: "center", fontWeight: 700, marginBottom: 12 }}>
          Simple Pricing
        </Title>
        <Paragraph style={{ textAlign: "center", color: "#86909c", fontSize: 16, marginBottom: 48 }}>
          Pay for what you route. No hidden fees, no provider markup.
        </Paragraph>

        <Row gutter={[24, 24]} style={{ maxWidth: 960, margin: "0 auto" }}>
          {tiers.map((t) => (
            <Col span={8} key={t.name}>
              <Card
                style={{
                  textAlign: "center",
                  borderColor: t.highlighted ? "#165DFF" : undefined,
                  borderWidth: t.highlighted ? 2 : 1,
                  position: "relative",
                }}
              >
                {t.highlighted && (
                  <div
                    style={{
                      position: "absolute",
                      top: -12,
                      left: "50%",
                      transform: "translateX(-50%)",
                      background: "#165DFF",
                      color: "#fff",
                      padding: "2px 16px",
                      borderRadius: 12,
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    Most Popular
                  </div>
                )}
                <Title heading={5} style={{ fontWeight: 600, marginTop: 8 }}>{t.name}</Title>
                <div style={{ margin: "16px 0 8px" }}>
                  <span style={{ fontSize: 36, fontWeight: 800, color: "#1d2129" }}>
                    {t.price === "0" ? "$0" : `$${t.price}`}
                  </span>
                  {t.period && (
                    <span style={{ color: "#86909c", fontSize: 14 }}>/{t.period}</span>
                  )}
                </div>
                <Paragraph style={{ color: "#86909c", fontSize: 13, marginBottom: 16 }}>
                  {t.requests} requests
                </Paragraph>
                <ul style={{ listStyle: "none", padding: 0, textAlign: "left", marginBottom: 24 }}>
                  {t.features.map((f) => (
                    <li key={f} style={{ padding: "6px 0", fontSize: 14, color: "#4e5969" }}>
                      <span style={{ color: "#00b42a", marginRight: 8 }}>&#10003;</span> {f}
                    </li>
                  ))}
                </ul>
                <Button
                  type={t.highlighted ? "primary" : "default"}
                  long
                  onClick={() => navigate(t.name === "Enterprise" ? "mailto:sales@fastrouter.dev" : "/login")}
                  style={{ borderRadius: 8 }}
                >
                  {t.cta}
                </Button>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* ── Footer ───────────────────────────────────────── */}
      <div style={{ borderTop: "1px solid #e5e6eb", padding: "32px 40px", textAlign: "center" }}>
        <Paragraph style={{ color: "#86909c", fontSize: 13, margin: 0 }}>
          FastRouter &mdash; Two-way LLM routing platform. Built for the AI era.
        </Paragraph>
      </div>
    </div>
  );
}
