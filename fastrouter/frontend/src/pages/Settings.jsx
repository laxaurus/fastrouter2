import { Card, Typography, Descriptions, Divider } from "@arco-design/web-react";

const { Title } = Typography;

export default function Settings({ user }) {
  return (
    <div>
      <Title heading={4} style={{ marginBottom: 16 }}>Settings</Title>

      <Card title="Account" style={{ marginBottom: 24 }}>
        <Descriptions
          column={1}
          data={[
            { label: "Email", value: user?.email || "—" },
            { label: "Account ID", value: user?.id || "—" },
            { label: "Member since", value: user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—" },
          ]}
        />
      </Card>

      <Card title="Free Tier">
        <Descriptions
          column={1}
          data={[
            { label: "Requests used", value: `${user?.free_requests_used || 0} / ${user?.free_requests_limit || 1000}` },
            { label: "Subscription", value: user?.subscription_status === "active" ? "Active (tier disabled)" : "Inactive" },
          ]}
        />
      </Card>
    </div>
  );
}
