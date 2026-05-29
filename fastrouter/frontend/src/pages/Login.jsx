import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, Message, Tabs } from "@arco-design/web-react";
import { api } from "../lib/api";

const { Title } = Typography;

export default function Login({ onLogin }) {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values, isRegister) => {
    setLoading(true);
    try {
      const method = isRegister ? api.register : api.login;
      const data = await method(values.email, values.password);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      onLogin(data.user);
      Message.success(isRegister ? "Account created!" : "Welcome back!");
      navigate("/");
    } catch (err) {
      Message.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "var(--color-bg-1)" }}>
      <Card style={{ width: 420 }} title={<Title heading={4}>FastRouter</Title>}>
        <Tabs defaultActiveTab="login">
          <Tabs.TabPane key="login" title="Login">
            <Form onSubmit={(v) => handleSubmit(v, false)} layout="vertical">
              <Form.Item field="email" label="Email" rules={[{ required: true, type: "email" }]}>
                <Input placeholder="you@company.com" />
              </Form.Item>
              <Form.Item field="password" label="Password" rules={[{ required: true, minLength: 8 }]}>
                <Input.Password placeholder="Password" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} long>
                  Login
                </Button>
              </Form.Item>
            </Form>
          </Tabs.TabPane>
          <Tabs.TabPane key="register" title="Register">
            <Form onSubmit={(v) => handleSubmit(v, true)} layout="vertical">
              <Form.Item field="email" label="Email" rules={[{ required: true, type: "email" }]}>
                <Input placeholder="you@company.com" />
              </Form.Item>
              <Form.Item field="password" label="Password" rules={[{ required: true, minLength: 8 }]}>
                <Input.Password placeholder="Password" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} long>
                  Create Account
                </Button>
              </Form.Item>
            </Form>
          </Tabs.TabPane>
        </Tabs>
        <div style={{ textAlign: "center", color: "var(--color-text-3)", fontSize: 13, marginTop: 8 }}>
          1,000 free requests included
        </div>
      </Card>
    </div>
  );
}
