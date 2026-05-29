import { useNavigate, useLocation } from "react-router-dom";
import { Menu } from "@arco-design/web-react";
import {
  IconApps,
  IconCode,
  IconCloud,
  IconSafe,
  IconSettings,
  IconBook,
  IconUserGroup,
  IconStorage,
  IconTool,
} from "@arco-design/web-react/icon";

const menuItems = [
  { key: "/", icon: <IconApps />, label: "Dashboard" },
  { key: "/keys", icon: <IconCode />, label: "API Keys" },
  { key: "/providers", icon: <IconCloud />, label: "Provider Keys" },
  { key: "/billing", icon: <IconSafe />, label: "Billing" },
  { key: "/settings", icon: <IconSettings />, label: "Settings" },
  { key: "/docs", icon: <IconBook />, label: "Docs" },
];

const adminItems = [
  { key: "/admin/models", icon: <IconStorage />, label: "Models" },
  { key: "/admin/keys", icon: <IconCloud />, label: "Provider Keys" },
  { key: "/admin/users", icon: <IconUserGroup />, label: "Users" },
  { key: "/admin/services", icon: <IconTool />, label: "Services" },
];

export default function Sidebar({ user }) {
  const navigate = useNavigate();
  const location = useLocation();

  const isAdmin = user?.role === "admin";

  return (
    <Menu
      selectedKeys={[location.pathname]}
      onClickMenuItem={(key) => navigate(key)}
      style={{ height: "100%", paddingTop: 12 }}
    >
      {menuItems.map((item) => (
        <Menu.Item key={item.key}>
          {item.icon} {item.label}
        </Menu.Item>
      ))}
      {isAdmin && (
        <>
          <div
            style={{
              padding: "8px 16px 4px",
              fontSize: 11,
              fontWeight: 600,
              color: "var(--color-text-3)",
              textTransform: "uppercase",
              letterSpacing: 1,
            }}
          >
            Admin
          </div>
          {adminItems.map((item) => (
            <Menu.Item key={item.key}>
              {item.icon} {item.label}
            </Menu.Item>
          ))}
        </>
      )}
    </Menu>
  );
}
