import Link from "next/link";
import { PulsarMark } from "@/components/PulsarMark";
import { MODULES } from "@/lib/types";
import { BG, BORDER, SURFACE, TEXT, TEXT_MUTED } from "@/lib/theme";

export default function HomePage() {
  return (
    <main style={{ minHeight: "100vh", background: BG }}>
      <section
        style={{
          maxWidth: 960,
          margin: "0 auto",
          padding: "96px 24px 64px",
          textAlign: "center",
        }}
      >
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 24 }}>
          <PulsarMark size={72} />
        </div>
        <h1 style={{ fontSize: 40, fontWeight: 800, color: TEXT, margin: "0 0 16px", letterSpacing: -0.5 }}>
          Quasar Sage
        </h1>
        <p style={{ fontSize: 18, color: TEXT_MUTED, maxWidth: 620, margin: "0 auto 8px", lineHeight: 1.6 }}>
          An elite, embedded AI Chief Revenue Officer — not a generic chatbot, but a strict system of five
          consultative modules that force rigorous strategic thinking instead of feature-dumping and vanity
          metrics.
        </p>
        <p style={{ fontSize: 14, color: TEXT_MUTED, maxWidth: 560, margin: "0 auto 40px", lineHeight: 1.6 }}>
          Built as a real-world sales &amp; marketing methodology engine, and equally suited as a teaching tool:
          every framework below is a named, gradable heuristic, not a black box.
        </p>
        <Link
          href="/workspace"
          style={{
            display: "inline-block",
            background: "#22D3EE",
            color: "#0B1120",
            fontWeight: 700,
            fontSize: 15,
            padding: "14px 32px",
            borderRadius: 10,
            textDecoration: "none",
          }}
        >
          Enter the Workspace →
        </Link>
      </section>

      <section style={{ maxWidth: 1040, margin: "0 auto", padding: "0 24px 96px" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 20,
          }}
        >
          {MODULES.map((m) => (
            <div
              key={m.id}
              style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderTop: `3px solid ${m.color}`,
                borderRadius: 12,
                padding: 24,
              }}
            >
              <div style={{ color: m.color, fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{m.label}</div>
              <div style={{ color: TEXT_MUTED, fontSize: 12, marginBottom: 16 }}>{m.tagline}</div>
              <ul style={{ margin: 0, paddingLeft: 18, color: TEXT, fontSize: 13, lineHeight: 1.9 }}>
                {m.frameworks.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <footer
        style={{
          borderTop: `1px solid ${BORDER}`,
          padding: "24px",
          textAlign: "center",
          color: TEXT_MUTED,
          fontSize: 12,
        }}
      >
        Quasar Sage — a Quasar product
      </footer>
    </main>
  );
}
