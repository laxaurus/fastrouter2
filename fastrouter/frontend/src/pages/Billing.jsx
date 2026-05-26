import { useState } from "react";
import { Card, Typography, Button, Statistic, Descriptions, Message, Tag, Grid } from "@arco-design/web-react";
import { api } from "../lib/api";

const { Title } = Typography;
const { Row, Col } = Grid;

const PRICE_PER_MONTH = 19;

export default function Billing({ user }) {
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const base = window.location.origin;
      const { checkout_url } = await api.createCheckout(
        `${base}/billing?success=true`,
        `${base}/billing?canceled=true`
      );
      window.location.href = checkout_url;
    } catch (e) {
      Message.error(e.message);
      setLoading(false);
    }
  };

  const handlePortal = async () => {
    setLoading(true);
    try {
      const { portal_url } = await api.createPortal(window.location.origin + "/billing");
      window.location.href = portal_url;
    } catch (e) {
      Message.error(e.message);
      setLoading(false);
    }
  };

  const isActive = user?.subscription_status === "active";
  const isPastDue = user?.subscription_status === "past_due";

  return (
    <div>
      <Title heading={4} style={{ marginBottom: 16 }}>Billing</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Status"
              value={isActive ? "Active" : isPastDue ? "Past Due" : "Inactive"}
              prefix={
                <Tag color={isActive ? "green" : isPastDue ? "red" : "gray"} style={{ marginRight: 0 }}>
                  {user?.subscription_status || "inactive"}
                </Tag>
              }
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Plan" value={isActive ? `$${PRICE_PER_MONTH}/mo` : "Free Tier"} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Free Requests Remaining" value={Math.max(0, (user?.free_requests_limit || 1000) - (user?.free_requests_used || 0))} suffix={`/ ${user?.free_requests_limit || 1000}`} />
          </Card>
        </Col>
      </Row>

      <Card title="Subscription" style={{ marginBottom: 24 }}>
        {isActive ? (
          <div>
            <Descriptions
              column={1}
              data={[
                { label: "Plan", value: `FastRouter Pro — $${PRICE_PER_MONTH}/month` },
                { label: "Status", value: <Tag color="green">Active</Tag> },
                { label: "Features", value: "Unlimited requests, all providers, priority failover, prompt caching" },
              ]}
              style={{ marginBottom: 16 }}
            />
            <Button type="outline" onClick={handlePortal} loading={loading}>
              Manage Subscription
            </Button>
          </div>
        ) : (
          <div>
            <p style={{ marginBottom: 16, color: "var(--color-text-2)" }}>
              You're on the free tier. Upgrade for unlimited requests across all providers.
            </p>
            <Descriptions
              column={1}
              data={[
                { label: "Free Tier", value: "1,000 lifetime requests, basic routing" },
                { label: "Pro Plan", value: `$${PRICE_PER_MONTH}/month — unlimited requests, all providers, prompt caching, priority support` },
              ]}
              style={{ marginBottom: 16 }}
            />
            <Button type="primary" onClick={handleSubscribe} loading={loading}>
              Subscribe for ${PRICE_PER_MONTH}/month
            </Button>
            {isPastDue && (
              <p style={{ color: "var(--color-danger-4)", marginTop: 12 }}>
                Your payment is past due. Please update your payment method.
              </p>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
