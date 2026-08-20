import type { ModuleId } from "./types";

/** Spec Section 6 (Visual Identity) / Section 1.5 (Dynamic Theming). */
export const MODULE_THEME: Record<ModuleId, { label: string; color: string; live: boolean }> = {
  visionary: { label: "Visionary", color: "#22D3EE", live: true },
  storyteller: { label: "Storyteller", color: "#F59E0B", live: true },
  dealmaker: { label: "Dealmaker", color: "#22C55E", live: true },
  negotiator: { label: "Negotiator", color: "#8B5CF6", live: true },
  locker_room: { label: "Locker Room", color: "#EF4444", live: true },
};

export const SAGE_BG = "#0B1120"; // dark navy, spec Section 6.1
export const SAGE_SURFACE = "#111827";
export const SAGE_BORDER = "#1F2937";
export const SAGE_TEXT = "#E5E7EB";
export const SAGE_TEXT_MUTED = "#9CA3AF";
