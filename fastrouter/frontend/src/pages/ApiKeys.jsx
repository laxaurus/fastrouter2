import { useState, useEffect } from "react";
import { Card, Typography, Table, Button, Modal, Input, Message, Popconfirm, Tag } from "@arco-design/web-react";
import { IconPlus, IconDelete } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("Default");
  const [createdKey, setCreatedKey] = useState(null);

  const load = () => {
    api.listKeys()
      .then((data) => setKeys(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    try {
      const result = await api.createKey(newKeyName);
      setCreatedKey(result.key);
      setShowCreate(false);
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteKey(id);
      Message.success("Key revoked");
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const columns = [
    { title: "Name", dataIndex: "name" },
    { title: "Prefix", dataIndex: "key_prefix", render: (v) => <code>{v}...</code> },
    {
      title: "Status",
      dataIndex: "is_active",
      render: (v) => (v ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>),
    },
    {
      title: "Last Used",
      dataIndex: "last_used_at",
      render: (v) => (v ? new Date(v).toLocaleDateString() : "Never"),
    },
    {
      title: "Created",
      dataIndex: "created_at",
      render: (v) => (v ? new Date(v).toLocaleDateString() : ""),
    },
    {
      title: "",
      dataIndex: "id",
      render: (id) => (
        <Popconfirm title="Revoke this key? This cannot be undone." onOk={() => handleDelete(id)}>
          <Button type="text" status="danger" icon={<IconDelete />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>API Keys</Title>
        <Button type="primary" icon={<IconPlus />} onClick={() => setShowCreate(true)}>
          New Key
        </Button>
      </div>

      <Card>
        <Table data={keys} columns={columns} pagination={false} loading={loading} rowKey="id" />
      </Card>

      <Modal
        title="Create API Key"
        visible={showCreate}
        onCancel={() => { setShowCreate(false); setCreatedKey(null); }}
        onOk={createdKey ? () => { setShowCreate(false); setCreatedKey(null); } : handleCreate}
        okText={createdKey ? "Done" : "Create"}
      >
        {createdKey ? (
          <div>
            <p style={{ color: "var(--color-danger-4)", fontWeight: 600, marginBottom: 8 }}>
              Copy this key now — it won't be shown again.
            </p>
            <Input.TextArea value={createdKey} readOnly rows={2} style={{ fontFamily: "monospace" }} />
          </div>
        ) : (
          <Input
            placeholder="Key name"
            value={newKeyName}
            onChange={setNewKeyName}
          />
        )}
      </Modal>
    </div>
  );
}
