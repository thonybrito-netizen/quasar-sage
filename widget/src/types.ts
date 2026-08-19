export type ModuleId = "visionary" | "storyteller" | "dealmaker" | "negotiator" | "locker_room";
export type DealmakerMode = "enterprise" | "retail";
/** Driven by the host app's own current UI language, not a separate widget setting. */
export type SageLanguage = "en" | "es" | "pt";

/** Mirrors gateway/app/schemas/context.py::ContextPayload */
export interface SageCompletionRequestBody {
  module: ModuleId;
  mode?: DealmakerMode | null;
  language?: SageLanguage;
  user_message: string;
  context: Record<string, unknown>;
}

/** Mirrors gateway/app/schemas/envelope.py::CompletionResponse */
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

/** Mirrors gateway/app/routers/modules.py::get_modules */
export interface SageModuleInfo {
  module_id: ModuleId;
  live: boolean;
  theme_color: string;
}
