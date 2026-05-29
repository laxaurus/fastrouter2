import { useState, useEffect } from "react";
import { Card, Typography, Button, Tag, Space, Message, Spin, Descriptions } from "@arco-design/web-react";
import { IconPoweroff, IconSync } from "@arco-design/web-react/icon";
import { api } from "../lib/api";

const { Title } = Typography;

export default function AdminServices() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [restarting, setRestarting] = useState(null);

  const loadStatus = () => {
    setLoading(true);
    api.adminServicesStatus()
      .then((data) => setStatus(data))
      .catch((e) => Message.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadStatus(); }, []);

  const handleRestart = async (service) => {
    setRestarting(service);
    try {
      let result;
      if (service === "litellm") {
        result = await api.adminRestartLitellm();
      } else {
        result = await api.adminRestartBackend();
      }
      if (result.ready !== undefined) {
        if (result.ready) {
          Message.success(`LiteLLM restarted and ready (took ~${result.wait_seconds}s)`);
        } else {
          Message.warning(result.warning || "LiteLLM restarted but may still be starting up");
        }
      } else {
        Message.success(`${service} restarted successfully`);
      }
      setTimeout(loadStatus, 2000);
    } catch (e) {
      Message.error(e.message);
    } finally {
      setRestarting(null);
    }
  };

  const containers = status?.services?.containers || {};
  const litellm = status?.services?.litellm || {};

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title heading={4} style={{ margin: 0 }}>Service Control</Title>
        <Button icon={<IconSync />} loading={loading} onClick={loadStatus}>
          Refresh
        </Button>
      </div>

      <Spin loading={loading} style={{ width: "100%" }}>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          <Card title="LiteLLM Proxy">
            <Descriptions
              column={1}
              data={[
                { label: "Status", value: litellm.reachable ? <Tag color="green">Reachable</Tag> : <Tag color="red">Unreachable</Tag> },
                { label: "Error", value: litellm.error || "-" },
              ]}
            />
            <Button
              type="primary"
              status="warning"
              icon={<IconPoweroff />}
              loading={restarting === "litellm"}
              onClick={() => handleRestart("litellm")}
              style={{ marginTop: 12 }}
            >
              Restart LiteLLM
            </Button>
          </Card>

          <Card title="FastRouter Backend">
            <Button
              type="primary"
              status="warning"
              icon={<IconPoweroff />}
              loading={restarting === "backend"}
              onClick={() => handleRestart("backend")}
            >
              Restart Backend
            </Button>
          </Card>

          <Card title="Docker Containers">
            {Object.keys(containers).length === 0 ? (
              <span style={{ color: "var(--color-text-3)" }}>No container info available</span>
            ) : (
              Object.entries(containers).map(([name, status]) => (
                <div key={name} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                  <code>{name}</code>
                  <Tag color={status.includes("Up") ? "green" : "red"}>{status}</Tag>
                </div>
              ))
            )}
          </Card>
        </Space>
      </Spin>
    </div>
  );
}
