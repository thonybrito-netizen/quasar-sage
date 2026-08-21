"use client";

import { useState } from "react";
import { SAGE_BORDER, SAGE_SURFACE, SAGE_TEXT, SAGE_TEXT_MUTED } from "./theme";

export interface OkrKillCriteria {
  metric: string;
  target: string;
  window: string;
}

const FIELD_STYLE: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  borderRadius: 8,
  border: `1px solid ${SAGE_BORDER}`,
  background: SAGE_SURFACE,
  color: SAGE_TEXT,
  padding: 8,
  fontSize: 12,
  marginBottom: 8,
};

const LABEL_STYLE: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: SAGE_TEXT_MUTED,
  marginBottom: 4,
  display: "block",
};

/**
 * Spec Section 2.5.3: "the standard chat input is temporarily replaced by
 * a strict, structured form field" until the Limiting Step Method's OKR
 * and Kill Criteria are satisfied. This is that structured form -- the
 * "Launch Campaign" button this is meant to gate lives inside each host
 * app's own campaign flow, which this widget has no visibility into, so
 * the enforcement point here is the Locker Room chat itself: no free-text
 * input until real Kill Criteria exist.
 */
export function LockerRoomOkrGate({ onComplete }: { onComplete: (okr: OkrKillCriteria) => void }) {
  const [metric, setMetric] = useState("");
  const [target, setTarget] = useState("");
  const [windowValue, setWindowValue] = useState("");

  const canConfirm = metric.trim() && target.trim() && windowValue.trim();

  return (
    <div style={{ padding: "0 16px 16px" }}>
      <p style={{ fontSize: 12, color: SAGE_TEXT_MUTED, marginTop: 0 }}>
        I won't sign off on a launch without real Kill Criteria. Define the target metric, value,
        and time window this campaign is judged against.
      </p>

      <label style={LABEL_STYLE}>Target metric type</label>
      <input
        style={FIELD_STYLE}
        value={metric}
        onChange={(e) => setMetric(e.target.value)}
        placeholder='e.g. "new orders", "new leads"'
      />

      <label style={LABEL_STYLE}>Target value</label>
      <input
        style={FIELD_STYLE}
        value={target}
        onChange={(e) => setTarget(e.target.value)}
        placeholder="e.g. 20"
      />

      <label style={LABEL_STYLE}>Time window</label>
      <input
        style={FIELD_STYLE}
        value={windowValue}
        onChange={(e) => setWindowValue(e.target.value)}
        placeholder="e.g. 30 days"
      />

      <button
        onClick={() => canConfirm && onComplete({ metric, target, window: windowValue })}
        disabled={!canConfirm}
        style={{
          width: "100%",
          borderRadius: 8,
          border: "none",
          background: canConfirm ? "#EF4444" : SAGE_BORDER,
          color: "#0B1120",
          fontWeight: 700,
          padding: "10px 0",
          cursor: canConfirm ? "pointer" : "not-allowed",
          fontSize: 13,
        }}
      >
        Confirm Kill Criteria
      </button>
    </div>
  );
}
