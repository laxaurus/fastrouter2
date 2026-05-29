import { useState, useEffect } from "react";
import {
  Card, Typography, Table, Button, Modal, Tag, Message, Spin,
} from "@arco-design/web-react";
import { IconEye, IconEyeInvisible } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

export default function AdminProviderKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unmasked, setUnmasked] = useState({});
  const [viewing, setViewing] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const load = () => {
    setLoading(true);
    api.adminListProviderKeys()
      .then((data) => setKeys(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const toggleUnmask = async (id) => {
    if (unmasked[id]) {
      setUnmasked((u) => ({ ...u, [id]: false }));
      return;
    }
    setDetailLoading(true);
    try {
      const detail = await api.adminGetProviderKey(id);
      setUnmasked((u) => ({ ...u, [id]: detail.api_key_decrypted }));
    } catch (e) {
      Message.error(e.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const columns = [
    {
      title: "User",
      dataIndex: "user_email",
      render: (v) => <span style={{ fontSize: 13 }}>{v}</span>,
    },
    { title: "Provider", dataIndex: "provider", render: (v) => <Tag>{v}</Tag> },
    {
      title: "Key Prefix",
      dataIndex: "key_prefix",
      render: (v) => <code style={{ fontSize: 12 }}>{v}...</code>,
    },
    {
      title: "Synced",
      dataIndex: "synced",
      render: (v) => (v ? <Tag color="green">Yes</Tag> : <Tag color="red">No</Tag>),
    },
    {
      title: "Active",
      dataIndex: "is_active",
      render: (v) => (v ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>),
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
        <Button
          type="text"
          icon={unmasked[id] ? <IconEyeInvisible /> : <IconEye />}
          size="small"
          onClick={() => toggleUnmask(id)}
        >
          {unmasked[id] ? "Hide" : "Reveal"}
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>Provider Keys</Title>
      </div>

      <Card>
        <Table
          data={keys.map((k) => ({
            ...k,
            _unmasked: unmasked[k.id],
          }))}
          columns={columns}
          pagination={false}
          loading={loading}
          rowKey="id"
          expandedRowRender={(record) =>
            unmasked[record.id] ? (
              <div style={{ padding: "8px 0" }}>
                <Spin loading={detailLoading}>
                  <code
                    style={{
                      background: "var(--color-fill-2)",
                      padding: "8px 12px",
                      borderRadius: 4,
                      display: "block",
                      wordBreak: "break-all",
                      fontSize: 12,
                      fontFamily: "monospace",
                    }}
                  >
                    {unmasked[record.id]}
                  </code>
                </Spin>
              </div>
            ) : null
          }
        />
      </Card>
    </div>
  );
}
