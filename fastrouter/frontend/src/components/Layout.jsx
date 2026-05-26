import { Layout as ArcoLayout } from "@arco-design/web-react";
import Sidebar from "./Sidebar";

const { Sider, Content, Header } = ArcoLayout;

export default function Layout({ children, user }) {
  return (
    <ArcoLayout style={{ minHeight: "100vh" }}>
      <Sider width={220} style={{ background: "#f7f8fa", boxShadow: "1px 0 0 0 #e5e6eb" }}>
        <div style={{ padding: "16px 16px 0", fontWeight: 700, fontSize: 16, color: "#1d2129" }}>
          Menu
        </div>
        <Sidebar user={user} />
      </Sider>
      <ArcoLayout>
        <Header
          style={{
            height: 56,
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid var(--color-border-2)",
            background: "var(--color-bg-2)",
          }}
        >
          <span style={{ fontWeight: 600, fontSize: 16 }}>FastRouter</span>
          <span style={{ color: "var(--color-text-3)", fontSize: 14 }}>
            {user?.email}
          </span>
        </Header>
        <Content style={{ padding: 24, background: "var(--color-bg-1)" }}>
          {children}
        </Content>
      </ArcoLayout>
    </ArcoLayout>
  );
}
