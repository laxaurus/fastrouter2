import { Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import ApiKeys from "./pages/ApiKeys";
import ProviderKeys from "./pages/ProviderKeys";
import Billing from "./pages/Billing";
import Settings from "./pages/Settings";
import Docs from "./pages/Docs";
import Login from "./pages/Login";
import Landing from "./pages/Landing";
import AdminModels from "./pages/AdminModels";
import AdminProviderKeys from "./pages/AdminProviderKeys";
import AdminUsers from "./pages/AdminUsers";
import AdminServices from "./pages/AdminServices";
import { api } from "./lib/api";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token");
  if (!token) return <Navigate to="/login" />;
  return children;
}

function AdminRoute({ user, children }) {
  if (user?.role !== "admin") return <Navigate to="/" />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      api.me()
        .then((u) => setUser(u))
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = () => {
    setUser(null);
  };

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={setUser} />} />
      <Route path="/docs" element={<Docs />} />
      <Route path="/" element={user ? (
        <Layout user={user} onLogout={handleLogout}><Dashboard /></Layout>
      ) : (
        <Landing />
      )} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout user={user} onLogout={handleLogout}>
              <Routes>
                <Route path="/keys" element={<ApiKeys />} />
                <Route path="/providers" element={<ProviderKeys />} />
                <Route path="/billing" element={<Billing user={user} />} />
                <Route path="/settings" element={<Settings user={user} />} />
                <Route path="/admin/models" element={<AdminRoute user={user}><AdminModels /></AdminRoute>} />
                <Route path="/admin/keys" element={<AdminRoute user={user}><AdminProviderKeys /></AdminRoute>} />
                <Route path="/admin/users" element={<AdminRoute user={user}><AdminUsers /></AdminRoute>} />
                <Route path="/admin/services" element={<AdminRoute user={user}><AdminServices /></AdminRoute>} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
