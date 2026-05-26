import { useState, useEffect } from "react";
import { Card, Typography, Table, Button, Modal, Input, Select, Message, Popconfirm, Tag } from "@arco-design/web-react";
import { IconPlus, IconDelete } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

const PROVIDERS = [
  { value: "deepseek", label: "DeepSeek" },
  { value: "qwen", label: "Qwen (Alibaba)" },
];

export default function ProviderKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [provider, setProvider] = useState("deepseek");
  const [apiKey, setApiKey] = useState("");

  const load = () => {
    api.listProviderKeys()
      .then((data) => setKeys(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async () => {
    try {
      await api.addProviderKey(provider, apiKey);
      Message.success("Provider key added");
      setShowAdd(false);
      setApiKey("");
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteProviderKey(id);
      Message.success("Provider key removed");
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const columns = [
    {
      title: "Provider",
      dataIndex: "provider",
      render: (v) => <Tag color="arcoblue">{v}</Tag>,
    },
    { title: "Key Prefix", dataIndex: "key_prefix", render: (v) => <code>{v}...</code> },
    {
      title: "Status",
      dataIndex: "is_active",
      render: (v) => (v ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>),
    },
    {
      title: "Added",
      dataIndex: "created_at",
      render: (v) => (v ? new Date(v).toLocaleDateString() : ""),
    },
    {
      title: "",
      dataIndex: "id",
      render: (id) => (
        <Popconfirm title="Remove this key?" onOk={() => handleDelete(id)}>
          <Button type="text" status="danger" icon={<IconDelete />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>Provider Keys (BYOK)</Title>
        <Button type="primary" icon={<IconPlus />} onClick={() => setShowAdd(true)}>
          Add Key
        </Button>
      </div>

      <Card>
        <Table
          data={keys}
          columns={columns}
          pagination={false}
          loading={loading}
          rowKey="id"
          noDataElement={<div style={{ padding: 40, textAlign: "center", color: "var(--color-text-3)" }}>No provider keys yet. Add your DeepSeek or Qwen API key to start routing.</div>}
        />
      </Card>

      <Modal
        title="Add Provider Key"
        visible={showAdd}
        onCancel={() => setShowAdd(false)}
        onOk={handleAdd}
        okText="Add"
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>Provider</label>
          <Select
            value={provider}
            onChange={setProvider}
            options={PROVIDERS}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>API Key</label>
          <Input.Password
            value={apiKey}
            onChange={setApiKey}
            placeholder="Paste your provider API key"
          />
        </div>
        <p style={{ color: "var(--color-text-3)", fontSize: 12, marginTop: 12 }}>
          Your key is encrypted at rest with AES-256. We never store it in plaintext.
        </p>
      </Modal>
    </div>
  );
}
