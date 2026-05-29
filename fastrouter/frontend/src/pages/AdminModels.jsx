import { useState, useEffect, useRef } from "react";
import {
  Card, Typography, Table, Button, Modal, Input, Select,
  Message, Popconfirm, Tag, Space, Switch, Alert,
} from "@arco-design/web-react";
import { IconPlus, IconEdit, IconDelete, IconSync, IconExport, IconImport } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

const emptyModel = {
  model_name: "",
  provider: "",
  api_base: "",
  description: "",
  is_active: true,
};

export default function AdminModels() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...emptyModel });

  // Import state
  const fileInputRef = useRef(null);
  const [showImport, setShowImport] = useState(false);
  const [importPreview, setImportPreview] = useState(null);
  const [importing, setImporting] = useState(false);

  const load = () => {
    setLoading(true);
    api.adminListModels()
      .then((data) => setModels(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyModel });
    setShowModal(true);
  };

  const openEdit = (model) => {
    setEditing(model.id);
    setForm({
      model_name: model.model_name,
      provider: model.provider,
      api_base: model.api_base,
      description: model.description || "",
      is_active: model.is_active,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (editing) {
        await api.adminUpdateModel(editing, form);
        Message.success("Model updated");
      } else {
        await api.adminCreateModel(form);
        Message.success("Model created");
      }
      setShowModal(false);
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      const result = await api.adminDeleteModel(id);
      if (result.warning) Message.warning(result.warning);
      else Message.success("Model deleted");
      load();
    } catch (e) {
      Message.error(e.message);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await api.adminSyncModels();
      Message.success(`Synced ${result.models_synced} models to ${result.path}`);
    } catch (e) {
      Message.error(e.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleExport = () => {
    const exportData = models.map(({ id, created_at, updated_at, ...rest }) => rest);
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fastrouter-models-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    Message.success(`Exported ${exportData.length} models`);
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target.result);
        const rows = Array.isArray(data) ? data : data.models;
        if (!rows || !Array.isArray(rows) || rows.length === 0) {
          Message.error("Invalid file: expected a JSON array of models");
          return;
        }
        // Diff against existing models
        const existingNames = new Map(models.map((m) => [m.model_name, m]));
        const newModels = [];
        const conflicts = [];
        for (const row of rows) {
          if (existingNames.has(row.model_name)) {
            const existing = existingNames.get(row.model_name);
            conflicts.push({ import: row, existing: { model_name: existing.model_name, provider: existing.provider, api_base: existing.api_base } });
          } else {
            newModels.push(row);
          }
        }
        setImportPreview({ rows, newModels, conflicts });
        setShowImport(true);
      } catch (err) {
        Message.error("Failed to parse JSON file: " + err.message);
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-selected
    e.target.value = "";
  };

  const handleImportApply = async (strategy) => {
    setImporting(true);
    try {
      const result = await api.adminImportModels(importPreview.rows, strategy);
      const parts = [];
      if (result.created.length) parts.push(`${result.created.length} created`);
      if (result.updated.length) parts.push(`${result.updated.length} updated`);
      if (result.skipped.length) parts.push(`${result.skipped.length} skipped`);
      Message.success(`Import complete: ${parts.join(", ")}`);
      setShowImport(false);
      setImportPreview(null);
      load();
    } catch (e) {
      Message.error(e.message);
    } finally {
      setImporting(false);
    }
  };

  const updateForm = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const columns = [
    { title: "Model Name", dataIndex: "model_name", render: (v) => <code>{v}</code> },
    { title: "Provider", dataIndex: "provider", render: (v) => <Tag>{v}</Tag> },
    { title: "API Base", dataIndex: "api_base", render: (v) => <span style={{ fontSize: 12 }}>{v}</span> },
    {
      title: "Active",
      dataIndex: "is_active",
      render: (v) => (v ? <Tag color="green">Yes</Tag> : <Tag color="red">No</Tag>),
    },
    { title: "Description", dataIndex: "description", render: (v) => v || "-" },
    {
      title: "",
      dataIndex: "id",
      render: (id, record) => (
        <Space>
          <Button type="text" icon={<IconEdit />} size="small" onClick={() => openEdit(record)} />
          <Popconfirm title="Delete this model?" onOk={() => handleDelete(id)}>
            <Button type="text" status="danger" icon={<IconDelete />} size="small" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>Model Management</Title>
        <Space>
          <Button icon={<IconExport />} onClick={handleExport}>Export</Button>
          <Button icon={<IconImport />} onClick={handleImportClick}>Import</Button>
          <Button icon={<IconSync />} loading={syncing} onClick={handleSync}>
            Sync to LiteLLM
          </Button>
          <Button type="primary" icon={<IconPlus />} onClick={openCreate}>
            Add Model
          </Button>
          <input ref={fileInputRef} type="file" accept=".json" style={{ display: "none" }} onChange={handleFileChange} />
        </Space>
      </div>

      <Card>
        <Table data={models} columns={columns} pagination={false} loading={loading} rowKey="id" />
      </Card>

      <Modal
        title={editing ? "Edit Model" : "Add Model"}
        visible={showModal}
        onCancel={() => setShowModal(false)}
        onOk={handleSave}
        okText={editing ? "Save" : "Create"}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Input
            placeholder="Model name (e.g. deepseek-chat)"
            value={form.model_name}
            onChange={(v) => updateForm("model_name", v)}
          />
          <Input
            placeholder="Provider (e.g. deepseek)"
            value={form.provider}
            onChange={(v) => updateForm("provider", v)}
          />
          <Input
            placeholder="API Base URL"
            value={form.api_base}
            onChange={(v) => updateForm("api_base", v)}
          />
          <Input
            placeholder="Description (optional)"
            value={form.description}
            onChange={(v) => updateForm("description", v)}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Switch checked={form.is_active} onChange={(v) => updateForm("is_active", v)} />
            <span>Active</span>
          </div>
        </div>
      </Modal>

      <Modal
        title="Import Models"
        visible={showImport}
        onCancel={() => { setShowImport(false); setImportPreview(null); }}
        footer={
          <Space>
            <Button onClick={() => { setShowImport(false); setImportPreview(null); }}>Cancel</Button>
            <Button type="primary" loading={importing} onClick={() => handleImportApply("skip")}>
              Import (Skip Duplicates)
            </Button>
            {importPreview?.conflicts.length > 0 && (
              <Button type="primary" status="warning" loading={importing} onClick={() => handleImportApply("overwrite")}>
                Import (Overwrite All)
              </Button>
            )}
          </Space>
        }
      >
        {importPreview && (
          <div>
            <Alert
              type="warning"
              title={`Found ${importPreview.conflicts.length} conflict(s) and ${importPreview.newModels.length} new model(s)`}
              content={
                importPreview.conflicts.length > 0
                  ? "Conflicting models (same name, different details) are listed below. Choose 'Skip Duplicates' to keep existing or 'Overwrite All' to replace them."
                  : "All models are new. No conflicts detected."
              }
              style={{ marginBottom: 16 }}
            />

            {importPreview.conflicts.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Title heading={6} style={{ color: "var(--color-warning-6)", marginBottom: 8 }}>
                  Conflicts ({importPreview.conflicts.length})
                </Title>
                <Table
                  data={importPreview.conflicts}
                  pagination={false}
                  size="small"
                  rowKey={(_, i) => i}
                  columns={[
                    { title: "Model Name", dataIndex: "import.model_name", render: (_, r) => <code>{r.import.model_name}</code> },
                    {
                      title: "Current Provider",
                      render: (_, r) => <Tag>{r.existing.provider}</Tag>,
                    },
                    {
                      title: "Import Provider",
                      render: (_, r) => <Tag color={r.import.provider !== r.existing.provider ? "orangered" : "green"}>{r.import.provider}</Tag>,
                    },
                    {
                      title: "Current API Base",
                      render: (_, r) => <span style={{ fontSize: 11 }}>{r.existing.api_base}</span>,
                    },
                    {
                      title: "Import API Base",
                      render: (_, r) => {
                        const changed = r.import.api_base !== r.existing.api_base;
                        return <span style={{ fontSize: 11, color: changed ? "var(--color-warning-6)" : undefined }}>{r.import.api_base}{changed ? " (changed)" : ""}</span>;
                      },
                    },
                  ]}
                />
              </div>
            )}

            <Title heading={6} style={{ marginBottom: 8 }}>New Models ({importPreview.newModels.length})</Title>
            {importPreview.newModels.length > 0 ? (
              <Table
                data={importPreview.newModels}
                pagination={false}
                size="small"
                rowKey="model_name"
                columns={[
                  { title: "Model Name", dataIndex: "model_name", render: (v) => <code>{v}</code> },
                  { title: "Provider", dataIndex: "provider", render: (v) => <Tag color="arcoblue">{v}</Tag> },
                  { title: "API Base", dataIndex: "api_base", render: (v) => <span style={{ fontSize: 11 }}>{v}</span> },
                ]}
              />
            ) : (
              <div style={{ color: "var(--color-text-3)", fontSize: 13, padding: "12px 0" }}>
                No new models to import — all models in the file already exist.
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
