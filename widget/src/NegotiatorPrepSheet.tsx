"use client";

import { useState } from "react";
import { SAGE_BORDER, SAGE_SURFACE, SAGE_TEXT, SAGE_TEXT_MUTED } from "./theme";

export interface NegotiatorPrep {
  position: string;
  interest: string;
  batna: string;
  range: string;
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
 * Spec Section 2.4.3: "Before a negotiation opens, the interface shows a
 * split prep sheet with the Interest Map and Walk-Away Ledger side by
 * side." This is that prep sheet -- the Negotiator's chat input stays
 * disabled until it's completed, matching the module's own hard rule
 * (validation.py won't draft a counter-offer without a Walk-Away Ledger
 * either; this is the UI enforcing the same discipline before the first
 * message is even sent, not just the model catching it after the fact).
 */
export function NegotiatorPrepSheet({ onComplete }: { onComplete: (prep: NegotiatorPrep) => void }) {
  const [position, setPosition] = useState("");
  const [interest, setInterest] = useState("");
  const [batna, setBatna] = useState("");
  const [range, setRange] = useState("");

  const canStart = position.trim() && interest.trim() && batna.trim() && range.trim();

  return (
    <div style={{ padding: "0 16px 16px" }}>
      <p style={{ fontSize: 12, color: SAGE_TEXT_MUTED, marginTop: 0 }}>
        Before we talk strategy, define your Interest Map and Walk-Away Ledger. I won't draft a
        counter-offer without both.
      </p>

      <label style={LABEL_STYLE}>Their stated position</label>
      <input
        style={FIELD_STYLE}
        value={position}
        onChange={(e) => setPosition(e.target.value)}
        placeholder='e.g. "15% discount on renewal"'
      />

      <label style={LABEL_STYLE}>Their underlying interest (why, if known)</label>
      <input
        style={FIELD_STYLE}
        value={interest}
        onChange={(e) => setInterest(e.target.value)}
        placeholder='e.g. "budget cut this fiscal year" -- or "unknown yet"'
      />

      <label style={LABEL_STYLE}>Your walk-away value (BATNA)</label>
      <input
        style={FIELD_STYLE}
        value={batna}
        onChange={(e) => setBatna(e.target.value)}
        placeholder="e.g. 50000"
      />

      <label style={LABEL_STYLE}>Plausible deal range (both sides)</label>
      <input
        style={FIELD_STYLE}
        value={range}
        onChange={(e) => setRange(e.target.value)}
        placeholder="e.g. 50000-65000"
      />

      <button
        onClick={() => canStart && onComplete({ position, interest, batna, range })}
        disabled={!canStart}
        style={{
          width: "100%",
          borderRadius: 8,
          border: "none",
          background: canStart ? "#8B5CF6" : SAGE_BORDER,
          color: "#0B1120",
          fontWeight: 700,
          padding: "10px 0",
          cursor: canStart ? "pointer" : "not-allowed",
          fontSize: 13,
        }}
      >
        Start negotiation prep
      </button>
    </div>
  );
}
