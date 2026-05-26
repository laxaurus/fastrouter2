import { useNavigate, useLocation } from "react-router-dom";
import { Menu } from "@arco-design/web-react";
import {
  IconApps,
  IconCode,
  IconCloud,
  IconSafe,
  IconSettings,
  IconBook,
} from "@arco-design/web-react/icon";

const menuItems = [
  { key: "/", icon: <IconApps />, label: "Dashboard" },
  { key: "/keys", icon: <IconCode />, label: "API Keys" },
  { key: "/providers", icon: <IconCloud />, label: "Provider Keys" },
  { key: "/billing", icon: <IconSafe />, label: "Billing" },
  { key: "/settings", icon: <IconSettings />, label: "Settings" },
  { key: "/docs", icon: <IconBook />, label: "Docs" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

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
    </Menu>
  );
}
