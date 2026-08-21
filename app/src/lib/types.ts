export type ModuleId = "visionary" | "storyteller" | "dealmaker" | "negotiator" | "locker_room";
export type DealmakerMode = "enterprise" | "retail";
export type SageLanguage = "en" | "es" | "pt";

export interface SageCompletionResponse {
  missing_variables: string[];
  strategic_critique: string;
  generated_content: string;
  suggested_next_action: string | null;
  sourced_fields: Record<string, string>;
  resolved_via: "first_attempt" | "invisible_retry" | "graceful_fallback";
  module: ModuleId;
  mode: DealmakerMode | null;
}

export interface ModuleInfo {
  id: ModuleId;
  label: string;
  color: string;
  live: boolean;
  tagline: string;
  frameworks: string[];
  gradeHint: string;
}

export const MODULES: ModuleInfo[] = [
  {
    id: "visionary",
    label: "The Visionary",
    color: "#22D3EE",
    live: true,
    tagline: "Identity & Positioning",
    frameworks: ["Core Belief Method", "Adversary Framework", "Market Fit Lens"],
    gradeHint: "Check for: a real Why (not a feature), a named Enemy, and zero invented market pain.",
  },
  {
    id: "storyteller",
    label: "The Storyteller",
    color: "#F59E0B",
    live: true,
    tagline: "Narrative & Content Creation",
    frameworks: ["Guide Model", "Buyer's Arc", "Inference Method", "Human Truth Check"],
    gradeHint: "Check for: the customer as hero (not the brand), inference over spoon-feeding, a real human truth.",
  },
  {
    id: "dealmaker",
    label: "The Dealmaker",
    color: "#22C55E",
    live: true,
    tagline: "Strategic Sales — Enterprise & Retail",
    frameworks: ["Stakeholder Map", "Win-Result Translator", "Trigger Stack", "Path-to-Cart"],
    gradeHint: "Check for: a named Economic Buyer (Enterprise) or a real inventory-backed trigger (Retail).",
  },
  {
    id: "negotiator",
    label: "The Negotiator",
    color: "#8B5CF6",
    live: true,
    tagline: "Live Deal Strategy",
    frameworks: ["Interest Map", "Walk-Away Ledger", "Anchor Point", "Good-Faith Guardrail"],
    gradeHint: "Check for: interests (not just positions), a defined BATNA, and no deceptive tactics.",
  },
  {
    id: "locker_room",
    label: "The Locker Room",
    color: "#EF4444",
    live: true,
    tagline: "Ruthless Execution & Analytics",
    frameworks: ["Limiting Step Method", "Readiness Protocol", "Keeper Standard"],
    gradeHint: "Check for: real Kill Criteria (metric + value + window), not vanity metrics.",
  },
];
