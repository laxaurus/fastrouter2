import { Tag } from "@arco-design/web-react";

function statusColor(state) {
  if (state === "closed") return "green";
  if (state === "open") return "red";
  return "orange";
}

export default function ProviderHealth({ providers }) {
  if (!providers || providers.length === 0) {
    return <div style={{ color: "var(--color-text-3)" }}>No data</div>;
  }

  return (
    <div>
      {providers.map((p) => (
        <div
          key={p.provider}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 0",
            borderBottom: "1px solid var(--color-border-2)",
          }}
        >
          <span style={{ fontWeight: 500 }}>{p.provider}</span>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <Tag color={statusColor(p.state)}>{p.state}</Tag>
            {p.failure_count > 0 && (
              <span style={{ fontSize: 12, color: "var(--color-text-3)" }}>
                {p.failure_count} failures
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
