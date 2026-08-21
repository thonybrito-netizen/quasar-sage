"use client";

import { useState } from "react";
import Link from "next/link";
import { PulsarMark } from "@/components/PulsarMark";
import { MODULES, type DealmakerMode, type ModuleId, type SageCompletionResponse } from "@/lib/types";
import { BG, BORDER, SURFACE, SURFACE_RAISED, TEXT, TEXT_MUTED, TEXT_DIM } from "@/lib/theme";

/** "key: value" per line -> a real context object, so an instructor can
 * hand Sage known facts without needing to understand JSON. */
function parseFacts(raw: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of raw.split("\n")) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    if (key && value) out[key] = value;
  }
  return out;
}

export default function WorkspacePage() {
  const [activeId, setActiveId] = useState<ModuleId>("visionary");
  const [dealmakerMode, setDealmakerMode] = useState<DealmakerMode>("enterprise");
  const [studentWork, setStudentWork] = useState("");
  const [facts, setFacts] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SageCompletionResponse | null>(null);

  const active = MODULES.find((m) => m.id === activeId)!;

  const handleSubmit = async () => {
    if (!studentWork.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module: activeId,
          mode: activeId === "dealmaker" ? dealmakerMode : null,
          language: "en",
          user_message: studentWork,
          context: parseFacts(facts),
        }),
      });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data: SageCompletionResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: BG, display: "flex" }}>
      {/* Sidebar */}
      <aside style={{ width: 240, borderRight: `1px solid ${BORDER}`, padding: 20, flexShrink: 0 }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", marginBottom: 32 }}>
          <PulsarMark size={28} />
          <span style={{ color: TEXT, fontWeight: 700, fontSize: 15 }}>Quasar Sage</span>
        </Link>

        <div style={{ color: TEXT_DIM, fontSize: 11, fontWeight: 700, letterSpacing: 0.5, marginBottom: 8 }}>
          MODULES
        </div>
        {MODULES.map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setActiveId(m.id);
              setResult(null);
              setError(null);
            }}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              background: activeId === m.id ? SURFACE_RAISED : "transparent",
              border: "none",
              borderLeft: `3px solid ${activeId === m.id ? m.color : "transparent"}`,
              color: activeId === m.id ? m.color : TEXT_MUTED,
              padding: "10px 12px",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              marginBottom: 4,
            }}
          >
            {m.label}
          </button>
        ))}
      </aside>

      {/* Main workspace */}
      <main style={{ flex: 1, padding: "32px 40px", maxWidth: 820 }}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: active.color, fontWeight: 700, fontSize: 22 }}>{active.label}</div>
          <div style={{ color: TEXT_MUTED, fontSize: 13, marginBottom: 12 }}>{active.tagline}</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            {active.frameworks.map((f) => (
              <span
                key={f}
                style={{
                  fontSize: 11,
                  color: active.color,
                  border: `1px solid ${active.color}55`,
                  borderRadius: 999,
                  padding: "3px 10px",
                }}
              >
                {f}
              </span>
            ))}
          </div>
          <div
            style={{
              fontSize: 12,
              color: TEXT_MUTED,
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 8,
              padding: "10px 12px",
              marginTop: 8,
            }}
          >
            <strong style={{ color: TEXT }}>Grading hint:</strong> {active.gradeHint}
          </div>
        </div>

        {activeId === "dealmaker" && (
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {(["enterprise", "retail"] as DealmakerMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setDealmakerMode(mode)}
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  textTransform: "capitalize",
                  padding: "6px 14px",
                  borderRadius: 999,
                  border: `1px solid ${dealmakerMode === mode ? active.color : BORDER}`,
                  background: dealmakerMode === mode ? `${active.color}22` : "transparent",
                  color: dealmakerMode === mode ? active.color : TEXT_MUTED,
                  cursor: "pointer",
                }}
              >
                {mode}
              </button>
            ))}
          </div>
        )}

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: TEXT_MUTED, marginBottom: 6 }}>
          Student work / scenario to evaluate
        </label>
        <textarea
          value={studentWork}
          onChange={(e) => setStudentWork(e.target.value)}
          placeholder="Paste a student's positioning statement, email draft, deal summary, etc."
          rows={4}
          style={{
            width: "100%",
            boxSizing: "border-box",
            background: SURFACE,
            border: `1px solid ${BORDER}`,
            borderRadius: 8,
            color: TEXT,
            padding: 10,
            fontSize: 13,
            resize: "vertical",
            marginBottom: 16,
          }}
        />

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: TEXT_MUTED, marginBottom: 6 }}>
          Known facts (one per line, e.g. <code>enemy: legacy spreadsheets</code>)
        </label>
        <textarea
          value={facts}
          onChange={(e) => setFacts(e.target.value)}
          placeholder={"enemy: legacy spreadsheets\ndeal_value: 85000"}
          rows={3}
          style={{
            width: "100%",
            boxSizing: "border-box",
            background: SURFACE,
            border: `1px solid ${BORDER}`,
            borderRadius: 8,
            color: TEXT,
            padding: 10,
            fontSize: 13,
            fontFamily: "monospace",
            resize: "vertical",
            marginBottom: 20,
          }}
        />

        <button
          onClick={handleSubmit}
          disabled={!studentWork.trim() || loading}
          style={{
            background: studentWork.trim() ? active.color : BORDER,
            color: BG,
            fontWeight: 700,
            fontSize: 14,
            border: "none",
            borderRadius: 8,
            padding: "12px 28px",
            cursor: studentWork.trim() ? "pointer" : "not-allowed",
            marginBottom: 32,
          }}
        >
          {loading ? "Sage is thinking…" : `Run ${active.label}`}
        </button>

        {error && (
          <p style={{ color: "#F87171", fontSize: 13, marginBottom: 24 }}>
            {error}
          </p>
        )}

        {result && (
          <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 24 }}>
            <div style={{ color: active.color, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
              Strategic critique
            </div>
            <p style={{ color: TEXT, fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>
              {result.strategic_critique}
            </p>

            {result.generated_content && (
              <>
                <div style={{ color: active.color, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
                  Generated content
                </div>
                <p
                  style={{
                    color: TEXT,
                    fontSize: 14,
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                    background: SURFACE,
                    border: `1px solid ${BORDER}`,
                    borderRadius: 8,
                    padding: 14,
                    marginBottom: 20,
                  }}
                >
                  {result.generated_content}
                </p>
              </>
            )}

            {result.missing_variables.length > 0 && (
              <>
                <div style={{ color: TEXT_MUTED, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
                  Still missing
                </div>
                <ul style={{ color: TEXT, fontSize: 13, lineHeight: 1.8, marginBottom: 20 }}>
                  {result.missing_variables.map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              </>
            )}

            {Object.keys(result.sourced_fields).length > 0 && (
              <>
                <div style={{ color: TEXT_MUTED, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
                  Grounded claims (claim → fact it's sourced from)
                </div>
                <ul style={{ color: TEXT_DIM, fontSize: 12, lineHeight: 1.8, fontFamily: "monospace" }}>
                  {Object.entries(result.sourced_fields).map(([claim, key]) => (
                    <li key={claim}>
                      "{claim}" ← {key}
                    </li>
                  ))}
                </ul>
              </>
            )}

            <div style={{ color: TEXT_DIM, fontSize: 11, marginTop: 16 }}>
              resolved via: {result.resolved_via}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
