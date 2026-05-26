import { useState, useEffect } from "react";
import { Card, Grid, Statistic, Typography, Table, Tag, Spin, Message } from "@arco-design/web-react";
import { IconArrowRise, IconFire, IconCloud, IconThunderbolt } from "@arco-design/web-react/icon";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { api } from "../lib/api";

const { Title } = Typography;
const { Row, Col } = Grid;

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [usage, setUsage] = useState([]);
  const [health, setHealth] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.analyticsOverview(),
      api.analyticsUsage(14),
      api.analyticsHealth(),
    ])
      .then(([ov, us, hp]) => {
        setOverview(ov);
        setUsage(us.data || []);
        setHealth(hp.providers || []);
      })
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin loading style={{ display: "block", margin: "auto", marginTop: 80 }} />;

  const chartData = usage.map((d) => ({
    date: d.day,
    Requests: d.requests,
    Tokens: Math.round(d.total_tokens / 1000),
  }));

  return (
    <div>
      <Title heading={4} style={{ marginBottom: 16 }}>Dashboard</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Requests"
              value={overview?.total_requests || 0}
              prefix={<IconArrowRise />}
              groupSeparator
            />
          </Card>
        </Col>
        <Col span={6}>
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
        <Col span={6}>
          <Card>
            <Statistic
              title="Cached Requests"
              value={overview?.cached_requests || 0}
              prefix={<IconThunderbolt />}
            />
          </Card>
        </Col>
        <Col span={6}>
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
          <Card title="Requests (Last 14 Days)">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="Requests" fill="var(--color-primary-4)" radius={[2, 2, 0, 0]} />
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
                <Line type="monotone" dataKey="Tokens" stroke="var(--color-success-4)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
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
