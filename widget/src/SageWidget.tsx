"use client";

import { useState } from "react";
import { MODULE_THEME, SAGE_BG, SAGE_BORDER, SAGE_SURFACE, SAGE_TEXT, SAGE_TEXT_MUTED } from "./theme";
import { useSageCompletion } from "./useSageCompletion";
import { NegotiatorPrepSheet, type NegotiatorPrep } from "./NegotiatorPrepSheet";
import { LockerRoomOkrGate, type OkrKillCriteria } from "./LockerRoomOkrGate";
import type { DealmakerMode, ModuleId, SageLanguage } from "./types";

const MODULE_ORDER: ModuleId[] = ["visionary", "storyteller", "dealmaker", "negotiator", "locker_room"];

export interface SageWidgetProps {
  /** Same-origin proxy path, e.g. "/api/sage/completions" or "/api/v1/sage/completions". */
  endpoint: string;
  /** Business context to send with every request -- e.g. QuietNoise's
   * ClientGoals/StrategySummary fields, or Lorito's Account/Opportunity
   * fields. Supplied by the host app since only it knows its own data. */
  initialContext?: Record<string, unknown>;
  dealmakerMode?: DealmakerMode;
  /** Driven by the host app's own current UI language -- see
   * gateway/app/schemas/context.py::ContextPayload for why this isn't a
   * separate in-widget setting. */
  language?: SageLanguage;
}

export function SageWidget({
  endpoint,
  initialContext = {},
  dealmakerMode = "enterprise",
  language = "en",
}: SageWidgetProps) {
  const [open, setOpen] = useState(false);
  const [activeModule, setActiveModule] = useState<ModuleId>("visionary");
  const [userMessage, setUserMessage] = useState("");
  const [negotiatorPrep, setNegotiatorPrep] = useState<NegotiatorPrep | null>(null);
  const [lockerRoomOkr, setLockerRoomOkr] = useState<OkrKillCriteria | null>(null);
  const { run, loading, error, result } = useSageCompletion({ endpoint });

  const theme = MODULE_THEME[activeModule];

  // Section 2.4.3 / 2.5.3: Negotiator and Locker Room each gate the chat
  // input behind a structured form until their module-specific
  // prerequisite exists (Walk-Away Ledger; Kill Criteria) -- once
  // completed, those values ride along in every request's context so the
  // Gateway's own validation (which independently refuses to proceed
  // without them) always has them too.
  const gateBlocking =
    (activeModule === "negotiator" && !negotiatorPrep) || (activeModule === "locker_room" && !lockerRoomOkr);

  const extraContext: Record<string, unknown> =
    activeModule === "negotiator" && negotiatorPrep
      ? {
          counterpart_position: negotiatorPrep.position,
          counterpart_interest: negotiatorPrep.interest,
          walk_away_value: negotiatorPrep.batna,
          plausible_range: negotiatorPrep.range,
        }
      : activeModule === "locker_room" && lockerRoomOkr
        ? {
            kill_criteria_metric: lockerRoomOkr.metric,
            kill_criteria_target: lockerRoomOkr.target,
            kill_criteria_window: lockerRoomOkr.window,
          }
        : {};

  const handleSubmit = async () => {
    if (!userMessage.trim() || loading || gateBlocking) return;
    try {
      await run({
        module: activeModule,
        mode: activeModule === "dealmaker" ? dealmakerMode : null,
        language,
        userMessage,
        context: { ...initialContext, ...extraContext },
      });
    } catch {
      // error state already surfaced via the hook
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Open Quasar Sage"
        style={{
          position: "fixed",
          bottom: 24,
          right: 24,
          zIndex: 1000,
          width: 56,
          height: 56,
          borderRadius: "50%",
          border: `2px solid ${theme.color}`,
          background: SAGE_BG,
          color: theme.color,
          fontSize: 24,
          cursor: "pointer",
          boxShadow: "0 4px 16px rgba(0,0,0,0.35)",
        }}
      >
        ✦
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Quasar Sage"
          style={{
            position: "fixed",
            bottom: 92,
            right: 24,
            zIndex: 1000,
            width: 380,
            maxHeight: "70vh",
            display: "flex",
            flexDirection: "column",
            background: SAGE_BG,
            border: `1px solid ${SAGE_BORDER}`,
            borderRadius: 16,
            boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
            overflow: "hidden",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <div style={{ display: "flex", borderBottom: `1px solid ${SAGE_BORDER}` }}>
            {MODULE_ORDER.map((moduleId) => {
              const moduleTheme = MODULE_THEME[moduleId];
              const isActive = moduleId === activeModule;
              return (
                <button
                  key={moduleId}
                  onClick={() => setActiveModule(moduleId)}
                  title={moduleTheme.live ? moduleTheme.label : `${moduleTheme.label} (coming soon)`}
                  style={{
                    flex: 1,
                    padding: "10px 4px",
                    background: isActive ? SAGE_SURFACE : "transparent",
                    border: "none",
                    borderBottom: isActive ? `2px solid ${moduleTheme.color}` : "2px solid transparent",
                    color: moduleTheme.live ? moduleTheme.color : SAGE_TEXT_MUTED,
                    fontSize: 11,
                    fontWeight: 600,
                    cursor: "pointer",
                    opacity: moduleTheme.live ? 1 : 0.55,
                  }}
                >
                  {moduleTheme.label}
                  {!moduleTheme.live && <div style={{ fontSize: 9, fontWeight: 400 }}>Coming soon</div>}
                </button>
              );
            })}
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: 16, color: SAGE_TEXT }}>
            {!theme.live && (
              <p style={{ color: SAGE_TEXT_MUTED, fontSize: 13 }}>
                The {theme.label} module isn't enabled yet — try Visionary or Storyteller.
              </p>
            )}

            {theme.live && activeModule === "negotiator" && !negotiatorPrep && (
              <NegotiatorPrepSheet onComplete={setNegotiatorPrep} />
            )}
            {theme.live && activeModule === "negotiator" && negotiatorPrep && (
              <div
                style={{
                  fontSize: 11,
                  color: SAGE_TEXT_MUTED,
                  border: `1px solid ${SAGE_BORDER}`,
                  borderRadius: 8,
                  padding: 8,
                  marginBottom: 12,
                }}
              >
                <strong style={{ color: theme.color }}>Walk-Away Ledger:</strong> BATNA{" "}
                {negotiatorPrep.batna}, range {negotiatorPrep.range}
              </div>
            )}

            {theme.live && activeModule === "locker_room" && !lockerRoomOkr && (
              <LockerRoomOkrGate onComplete={setLockerRoomOkr} />
            )}
            {theme.live && activeModule === "locker_room" && lockerRoomOkr && (
              <div
                style={{
                  fontSize: 11,
                  color: SAGE_TEXT_MUTED,
                  border: `1px solid ${SAGE_BORDER}`,
                  borderRadius: 8,
                  padding: 8,
                  marginBottom: 12,
                }}
              >
                <strong style={{ color: theme.color }}>Kill Criteria:</strong> {lockerRoomOkr.target}{" "}
                {lockerRoomOkr.metric} in {lockerRoomOkr.window}
              </div>
            )}

            {result && (
              <div style={{ marginBottom: 16, fontSize: 13, lineHeight: 1.5 }}>
                <div style={{ color: theme.color, fontWeight: 600, marginBottom: 4 }}>Strategic critique</div>
                <p style={{ margin: "0 0 12px" }}>{result.strategic_critique}</p>

                {result.generated_content && (
                  <>
                    <div style={{ color: theme.color, fontWeight: 600, marginBottom: 4 }}>Generated content</div>
                    <p style={{ margin: "0 0 12px", whiteSpace: "pre-wrap" }}>{result.generated_content}</p>
                  </>
                )}

                {result.missing_variables.length > 0 && (
                  <>
                    <div style={{ color: SAGE_TEXT_MUTED, fontWeight: 600, marginBottom: 4 }}>Still needed</div>
                    <ul style={{ margin: "0 0 12px", paddingLeft: 18 }}>
                      {result.missing_variables.map((v) => (
                        <li key={v}>{v}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}

            {error && <p style={{ color: "#F87171", fontSize: 13 }}>{error}</p>}
          </div>

          <div style={{ padding: 12, borderTop: `1px solid ${SAGE_BORDER}`, display: "flex", gap: 8 }}>
            <textarea
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder={
                !theme.live
                  ? "This module isn't live yet"
                  : gateBlocking
                    ? "Complete the form above first"
                    : `Ask the ${theme.label}...`
              }
              disabled={!theme.live || gateBlocking}
              rows={2}
              style={{
                flex: 1,
                resize: "none",
                borderRadius: 8,
                border: `1px solid ${SAGE_BORDER}`,
                background: SAGE_SURFACE,
                color: SAGE_TEXT,
                padding: 8,
                fontSize: 13,
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={!theme.live || gateBlocking || loading || !userMessage.trim()}
              style={{
                borderRadius: 8,
                border: "none",
                background: theme.live && !gateBlocking ? theme.color : SAGE_BORDER,
                color: SAGE_BG,
                fontWeight: 700,
                padding: "0 14px",
                cursor: theme.live && !gateBlocking ? "pointer" : "not-allowed",
              }}
            >
              {loading ? "..." : "Send"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
