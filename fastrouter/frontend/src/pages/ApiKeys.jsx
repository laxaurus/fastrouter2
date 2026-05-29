import { useState, useEffect, useRef } from "react";
import { Card, Typography, Table, Button, Modal, Input, Message, Popconfirm, Tag, Space, Select, Spin, Descriptions } from "@arco-design/web-react";
import { IconPlus, IconDelete, IconCopy, IconCheck, IconSend, IconEye } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("Default");
  const [createdKey, setCreatedKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef(null);

  // Playground state
  const [models, setModels] = useState([]);
  const [playgroundKey, setPlaygroundKey] = useState("");
  const [playgroundModel, setPlaygroundModel] = useState("");
  const [playgroundPrompt, setPlaygroundPrompt] = useState("");
  const [playgroundSending, setPlaygroundSending] = useState(false);
  const [playgroundResult, setPlaygroundResult] = useState(null);

  // Review state
  const [showReview, setShowReview] = useState(false);
  const [reviewData, setReviewData] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  const load = () => {
    api.listKeys()
      .then((data) => setKeys(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    api.listModels().then((data) => {
      const modelList = (data.data || []).map((m) => ({ value: m.id, label: m.id }));
      setModels(modelList);
      if (modelList.length > 0) setPlaygroundModel(modelList[0].value);
    }).catch(() => {});
  }, []);

  const handleCreate = async () => {
    try {
      const result = await api.createKey(newKeyName);
      setCreatedKey(result.key);
      setPlaygroundKey(result.key);  // auto-fill playground
      setCopied(false);
      // Keep modal open — user must click Done after copying
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(createdKey);
      setCopied(true);
      Message.success("API key copied to clipboard");
    } catch {
      inputRef.current?.select();
      Message.info("Please copy manually (Ctrl+C)");
    }
  };

  const handleCloseCreate = () => {
    setShowCreate(false);
    setCreatedKey(null);
    setCopied(false);
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

  const handleReview = async (id) => {
    setReviewLoading(true);
    setShowReview(true);
    try {
      const data = await api.getKey(id);
      setReviewData(data);
    } catch (e) {
      Message.error(e.message);
      setShowReview(false);
    } finally {
      setReviewLoading(false);
    }
  };

  const handlePlaygroundSend = async () => {
    if (!playgroundKey.trim()) {
      Message.warning("Paste your API key first (create one above)");
      return;
    }
    if (!playgroundPrompt.trim()) {
      Message.warning("Enter a prompt first");
      return;
    }
    setPlaygroundSending(true);
    setPlaygroundResult(null);
    try {
      const resp = await fetch("/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${playgroundKey}`,
        },
        body: JSON.stringify({
          model: playgroundModel,
          messages: [{ role: "user", content: playgroundPrompt }],
          max_tokens: 256,
          stream: false,
        }),
      });
      const data = await resp.json();
      if (resp.ok) {
        const content = data.choices?.[0]?.message?.content || JSON.stringify(data);
        setPlaygroundResult({
          success: true,
          content,
          model: data.model || playgroundModel,
          provider: data.x_provider || "unknown",
          usage: data.usage,
        });
      } else {
        setPlaygroundResult({
          success: false,
          content: data.detail || data.error || resp.statusText,
        });
      }
    } catch (e) {
      setPlaygroundResult({ success: false, content: e.message });
    } finally {
      setPlaygroundSending(false);
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
        <Space>
          <Button type="text" icon={<IconEye />} size="small" onClick={() => handleReview(id)} />
          <Popconfirm title="Revoke this key? This cannot be undone." onOk={() => handleDelete(id)}>
            <Button type="text" status="danger" icon={<IconDelete />} size="small" />
          </Popconfirm>
        </Space>
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

      {/* Playground */}
      <Card title="Test Playground" style={{ marginTop: 24 }}>
        <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
          <Input.Password
            placeholder="Paste your API key here (create one above)"
            value={playgroundKey}
            onChange={setPlaygroundKey}
            style={{ width: 320 }}
          />
          <Select
            value={playgroundModel}
            onChange={setPlaygroundModel}
            options={models}
            style={{ width: 200 }}
          />
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <Input.TextArea
              placeholder="Type a message to test your API key..."
              value={playgroundPrompt}
              onChange={setPlaygroundPrompt}
              rows={3}
            />
          </div>
          <Button
            type="primary"
            icon={playgroundSending ? <Spin size={14} /> : <IconSend />}
            onClick={handlePlaygroundSend}
            loading={playgroundSending}
            style={{ marginTop: 0 }}
          >
            Send
          </Button>
        </div>

        {keys.length === 0 && (
          <div style={{ color: "var(--color-text-3)", fontSize: 13, marginTop: 8 }}>
            Create an API key above — it will auto-fill the playground.
          </div>
        )}

        {playgroundResult && (
          <div style={{
            padding: 12,
            borderRadius: 4,
            background: playgroundResult.success ? "var(--color-success-1)" : "var(--color-danger-1)",
            border: `1px solid ${playgroundResult.success ? "var(--color-success-3)" : "var(--color-danger-3)"}`,
            marginTop: 12,
          }}>
            {playgroundResult.success && (
              <div style={{ marginBottom: 8, fontSize: 12, color: "var(--color-text-3)" }}>
                Model: {playgroundResult.model} | Provider: {playgroundResult.provider}
                {playgroundResult.usage && (
                  <span> | Tokens: {playgroundResult.usage.total_tokens}</span>
                )}
              </div>
            )}
            <pre style={{
              margin: 0,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              fontSize: 13,
              fontFamily: "inherit",
            }}>
              {playgroundResult.content}
            </pre>
          </div>
        )}
      </Card>

      <Modal
        title="Create API Key"
        visible={showCreate}
        onCancel={handleCloseCreate}
        footer={
          createdKey ? (
            <Button type="primary" onClick={handleCloseCreate}>Done</Button>
          ) : (
            <>
              <Button onClick={handleCloseCreate}>Cancel</Button>
              <Button type="primary" onClick={handleCreate}>Create</Button>
            </>
          )
        }
      >
        {createdKey ? (
          <div>
            <div style={{
              background: "var(--color-warning-1)",
              border: "1px solid var(--color-warning-3)",
              borderRadius: 4,
              padding: "8px 12px",
              marginBottom: 12,
              fontSize: 13,
              color: "var(--color-warning-6)",
              fontWeight: 500,
            }}>
              Copy this key now — it won't be shown again.
            </div>
            <Input.TextArea
              ref={inputRef}
              value={createdKey}
              readOnly
              rows={2}
              style={{ fontFamily: "monospace", marginBottom: 12 }}
            />
            <Button
              type="outline"
              icon={copied ? <IconCheck /> : <IconCopy />}
              onClick={handleCopy}
              long
            >
              {copied ? "Copied!" : "Copy to Clipboard"}
            </Button>
          </div>
        ) : (
          <div>
            <p style={{ color: "var(--color-text-3)", marginBottom: 12, fontSize: 13 }}>
              Create an API key to authenticate with the FastRouter proxy endpoint.
            </p>
            <Input
              placeholder="Key name (e.g. 'Production' or 'Development')"
              value={newKeyName}
              onChange={setNewKeyName}
            />
          </div>
        )}
      </Modal>

      <Modal
        title="Key Details"
        visible={showReview}
        onCancel={() => { setShowReview(false); setReviewData(null); }}
        footer={<Button type="primary" onClick={() => { setShowReview(false); setReviewData(null); }}>Close</Button>}
      >
        {reviewLoading ? (
          <div style={{ textAlign: "center", padding: 24 }}><Spin /></div>
        ) : reviewData ? (
          <div>
            <Descriptions
              column={1}
              border
              data={[
                { label: "Name", value: reviewData.name },
                { label: "Prefix", value: <code>{reviewData.key_prefix}...</code> },
                { label: "Status", value: reviewData.is_active ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag> },
                { label: "Created", value: reviewData.created_at ? new Date(reviewData.created_at).toLocaleString() : "-" },
                { label: "Last Used", value: reviewData.last_used_at ? new Date(reviewData.last_used_at).toLocaleString() : "Never" },
              ]}
              style={{ marginBottom: 16 }}
            />
            <Title heading={6} style={{ marginBottom: 8 }}>Provider Keys</Title>
            {reviewData.provider_keys && reviewData.provider_keys.length > 0 ? (
              <Table
                data={reviewData.provider_keys}
                pagination={false}
                size="small"
                rowKey="id"
                columns={[
                  { title: "Provider", dataIndex: "provider", render: (v) => <Tag color="arcoblue">{v}</Tag> },
                  { title: "Prefix", dataIndex: "key_prefix", render: (v) => <code>{v}...</code> },
                  { title: "Synced", dataIndex: "synced", render: (v) => v ? <Tag color="green">Yes</Tag> : <Tag color="orange">Pending</Tag> },
                  { title: "Status", dataIndex: "is_active", render: (v) => v ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag> },
                ]}
              />
            ) : (
              <div style={{ color: "var(--color-text-3)", fontSize: 13, padding: "12px 0" }}>
                No provider keys configured. Add a BYOK key to route requests to external providers.
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
