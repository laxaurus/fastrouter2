import { useState, useEffect } from "react";
import { Card, Typography, Table, Button, Modal, Input, Select, Message, Popconfirm, Tag, Space, Spin, Alert } from "@arco-design/web-react";
import { IconPlus, IconDelete, IconSend } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

export default function ProviderKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [provider, setProvider] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [testing, setTesting] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [providers, setProviders] = useState([]);
  const [providerModels, setProviderModels] = useState({});
  const [testModalKey, setTestModalKey] = useState(null);
  const [testModel, setTestModel] = useState("");

  useEffect(() => {
    loadKeys();
    loadProviders();
  }, []);

  const loadKeys = () => {
    api.listProviderKeys()
      .then((data) => setKeys(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  const loadProviders = () => {
    api.listModels().then((data) => {
      const modelList = data.data || [];
      const provSet = new Map();
      const modelsByProvider = {};
      for (const m of modelList) {
        if (!modelsByProvider[m.owned_by]) modelsByProvider[m.owned_by] = [];
        modelsByProvider[m.owned_by].push(m.id);
        if (!provSet.has(m.owned_by)) {
          provSet.set(m.owned_by, m.owned_by);
        }
      }
      const provList = Array.from(provSet.values()).map((p) => ({
        value: p,
        label: p.charAt(0).toUpperCase() + p.slice(1),
      }));
      setProviders(provList);
      setProviderModels(modelsByProvider);
    }).catch(() => {}); // Silently fail — providers may be empty if DB not seeded
  };

  const handleAdd = async () => {
    try {
      await api.addProviderKey(provider, apiKey);
      Message.success("Provider key added");
      setShowAdd(false);
      setApiKey("");
      loadKeys();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteProviderKey(id);
      Message.success("Provider key removed");
      loadKeys();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const openTestModal = (record) => {
    setTestModalKey(record);
    const models = providerModels[record.provider] || [];
    setTestModel(models[0] || "");
  };

  const handleTest = async () => {
    if (!testModalKey) return;
    const id = testModalKey.id;
    setTesting(id);
    setTestModalKey(null);
    setTestResult(null);
    try {
      const result = await api.testProviderKey(id, testModel);
      setTestResult(result);
      if (result.authenticated) {
        Message.success(`Connected in ${result.latency_ms}ms`);
      } else if (result.reachable) {
        Message.warning(`Provider reached but key rejected (${result.latency_ms}ms)`);
      } else {
        Message.error(result.detail || "Connection failed");
      }
    } catch (e) {
      Message.error(e.message);
    } finally {
      setTesting(null);
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
      title: "Synced",
      dataIndex: "synced",
      width: 80,
      render: (v) => v ? <Tag color="green">Ready</Tag> : <Tag color="orange">Pending</Tag>,
    },
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
      render: (id, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={testing === id ? <Spin size={14} /> : <IconSend />}
            onClick={() => openTestModal(record)}
            loading={testing === id}
          >
            Test
          </Button>
          <Popconfirm title="Remove this key?" onOk={() => handleDelete(id)}>
            <Button type="text" status="danger" icon={<IconDelete />} size="small" />
          </Popconfirm>
        </Space>
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

      {testResult && (
        <Alert
          type={testResult.authenticated ? "success" : testResult.reachable ? "warning" : "error"}
          title={
            testResult.authenticated
              ? `Connection successful — ${testResult.latency_ms}ms latency (model: ${testResult.model_used})`
              : testResult.reachable
                ? `Provider reached but key was rejected (model: ${testResult.model_used})`
                : "Connection failed"
          }
          content={testResult.detail}
          closable
          onClose={() => setTestResult(null)}
          style={{ marginBottom: 16 }}
        />
      )}

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
            options={providers}
            placeholder="Select a provider"
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

      <Modal
        title="Test Provider Key"
        visible={!!testModalKey}
        onCancel={() => setTestModalKey(null)}
        onOk={handleTest}
        okText="Test"
      >
        {testModalKey && (
          <div>
            <p style={{ color: "var(--color-text-3)", marginBottom: 16, fontSize: 13 }}>
              Select a model to test connectivity for{" "}
              <Tag color="arcoblue">{testModalKey.provider}</Tag>
            </p>
            <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>Model</label>
            <Select
              value={testModel}
              onChange={setTestModel}
              options={(providerModels[testModalKey.provider] || []).map((m) => ({ value: m, label: m }))}
              placeholder="Select a model"
              style={{ width: "100%" }}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}
