import { useState, useEffect } from "react";
import { Card, Grid, Statistic, Typography, Table, Tag, Spin, Message } from "@arco-design/web-react";
import { IconArrowRise, IconFire, IconThunderbolt, IconSafe, IconCloud } from "@arco-design/web-react/icon";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { api } from "../lib/api";

const { Title } = Typography;
const { Row, Col } = Grid;

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [usage, setUsage] = useState([]);
  const [health, setHealth] = useState([]);
  const [providerStats, setProviderStats] = useState([]);
  const [modelStats, setModelStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.analyticsOverview(),
      api.analyticsUsage(14),
      api.analyticsHealth(),
      api.analyticsProviders(),
      api.analyticsModels(),
    ])
      .then(([ov, us, hp, ps, ms]) => {
        setOverview(ov);
        setUsage(us.data || []);
        setHealth(hp.providers || []);
        setProviderStats(ps.data || []);
        setModelStats(ms.data || []);
      })
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin loading style={{ display: "block", margin: "auto", marginTop: 80 }} />;

  const chartData = usage.map((d) => ({
    date: d.day,
    Requests: d.requests,
    "Tokens (K)": Math.round(d.total_tokens / 1000),
    "Cost ($)": parseFloat((d.cost_usd || 0).toFixed(6)),
  }));

  return (
    <div>
      <Title heading={4} style={{ marginBottom: 16 }}>Dashboard</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="Total Requests"
              value={overview?.total_requests || 0}
              prefix={<IconArrowRise />}
              groupSeparator
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Tokens Used"
              value={Math.round((overview?.total_tokens || 0) / 1000)}
              suffix="K"
              prefix={<IconFire />}
              groupSeparator
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Total Spend"
              value={overview?.total_spend || 0}
              prefix={<IconSafe />}
              precision={4}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Cached"
              value={overview?.cached_requests || 0}
              prefix={<IconThunderbolt />}
              suffix={
                overview?.total_requests
                  ? ` (${Math.round((overview.cached_requests / overview.total_requests) * 100)}%)`
                  : ""
              }
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Savings"
              value={overview?.cached_savings || 0}
              prefix={<IconCloud />}
              precision={4}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Free Tier"
              value={overview?.free_requests_remaining || 0}
              suffix={`/ ${overview?.free_requests_limit || 1000}`}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Requests & Spend (Last 14 Days)">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `$${v}`} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="Requests" fill="var(--color-primary-4)" radius={[2, 2, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="Cost ($)" stroke="var(--color-warning-4)" strokeWidth={2} dot={false} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Token Usage (Last 14 Days)">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="Tokens (K)" stroke="var(--color-success-4)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Spend by Model (30d)">
            <Table
              data={modelStats}
              columns={[
                { title: "Model", dataIndex: "model", render: (v) => <code style={{ fontSize: 12 }}>{v}</code> },
                { title: "Provider", dataIndex: "provider", render: (v) => <Tag color="arcoblue">{v}</Tag> },
                { title: "Requests", dataIndex: "requests", render: (v) => v?.toLocaleString() || "0" },
                { title: "Tokens", dataIndex: "total_tokens", render: (v) => Math.round((v || 0) / 1000).toLocaleString() + "K" },
                { title: "Avg Latency", dataIndex: "avg_latency_ms", render: (v) => Math.round(v || 0) + "ms" },
                {
                  title: "Cost",
                  dataIndex: "cost_usd",
                  render: (v) => <span style={{ fontWeight: 600, fontFamily: "monospace" }}>${(v || 0).toFixed(4)}</span>,
                },
                { title: "Cached", dataIndex: "cached_count", render: (v) => v || 0 },
              ]}
              pagination={false}
              rowKey="model"
              noDataElement={<div style={{ padding: 24, textAlign: "center", color: "var(--color-text-3)" }}>No usage data yet</div>}
            />
            {modelStats.length > 0 && (() => {
              const totalCost = modelStats.reduce((s, r) => s + (r.cost_usd || 0), 0);
              const totalReqs = modelStats.reduce((s, r) => s + (r.requests || 0), 0);
              const totalTokens = modelStats.reduce((s, r) => s + (r.total_tokens || 0), 0);
              return (
                <div style={{ display: "flex", justifyContent: "flex-end", padding: "8px 16px", borderTop: "1px solid var(--color-border-2)", fontSize: 13, gap: 24 }}>
                  <span>{totalReqs.toLocaleString()} requests</span>
                  <span>{Math.round(totalTokens / 1000).toLocaleString()}K tokens</span>
                  <span style={{ fontWeight: 600 }}>${totalCost.toFixed(4)} total</span>
                </div>
              );
            })()}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Provider Performance (30d)">
            <Table
              data={providerStats}
              columns={[
                { title: "Provider", dataIndex: "provider", render: (v) => <Tag color="arcoblue">{v}</Tag> },
                { title: "Requests", dataIndex: "requests", render: (v) => v?.toLocaleString() || "0" },
                { title: "Tokens", dataIndex: "total_tokens", render: (v) => Math.round((v || 0) / 1000).toLocaleString() + "K" },
                { title: "Cost", dataIndex: "cost_usd", render: (v) => <span style={{ fontFamily: "monospace" }}>${(v || 0).toFixed(4)}</span> },
                { title: "Avg Latency", dataIndex: "avg_latency_ms", render: (v) => Math.round(v || 0) + "ms" },
                { title: "Cached", dataIndex: "cached_count", render: (v) => v || 0 },
              ]}
              pagination={false}
              rowKey="provider"
              noDataElement={<div style={{ padding: 24, textAlign: "center", color: "var(--color-text-3)" }}>No usage data yet</div>}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Provider Health">
            <Table
              data={health}
              columns={[
                { title: "Provider", dataIndex: "provider", render: (v) => <Tag color="arcoblue">{v}</Tag> },
                {
                  title: "Status",
                  dataIndex: "state",
                  render: (v) => {
                    const color = v === "closed" ? "green" : v === "open" ? "red" : "orange";
                    return <Tag color={color}>{v}</Tag>;
                  },
                },
                { title: "Failures", dataIndex: "failure_count" },
              ]}
              pagination={false}
              rowKey="provider"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Quickstart">
            <pre style={{ background: "var(--color-fill-2)", padding: 16, borderRadius: 8, fontSize: 13, overflow: "auto" }}>
{`# Set your API key
export FASTROUTER_KEY="sk-your-key"

# Call any Chinese model
curl https://api.fastrouter.dev/v1/chat/completions \\
  -H "Authorization: Bearer $FASTROUTER_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`}
            </pre>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
