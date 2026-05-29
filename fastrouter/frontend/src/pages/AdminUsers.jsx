import { useState, useEffect } from "react";
import {
  Card, Typography, Table, Select, Message, Tag,
} from "@arco-design/web-react";
import { api } from "../lib/api";

const { Title } = Typography;

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.adminListUsers()
      .then((data) => setUsers(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.adminUpdateUserRole(userId, newRole);
      Message.success(`Role updated to ${newRole}`);
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const columns = [
    {
      title: "Email",
      dataIndex: "email",
      render: (v) => <span style={{ fontSize: 13 }}>{v}</span>,
    },
    {
      title: "Role",
      dataIndex: "role",
      render: (role, record) => (
        <Select
          value={role}
          style={{ width: 100 }}
          onChange={(v) => handleRoleChange(record.id, v)}
          options={[
            { label: "Admin", value: "admin" },
            { label: "User", value: "user" },
          ]}
        />
      ),
    },
    {
      title: "Subscription",
      dataIndex: "subscription_status",
      render: (v) =>
        v === "active" ? <Tag color="green">Active</Tag> : <Tag color="gray">Inactive</Tag>,
    },
    {
      title: "Free Used",
      render: (_, record) =>
        `${record.free_requests_used} / ${record.free_requests_limit}`,
    },
    {
      title: "Joined",
      dataIndex: "created_at",
      render: (v) => (v ? new Date(v).toLocaleDateString() : ""),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>User Management</Title>
      </div>

      <Card>
        <Table data={users} columns={columns} pagination={false} loading={loading} rowKey="id" />
      </Card>
    </div>
  );
}
