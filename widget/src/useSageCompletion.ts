import { useCallback, useState } from "react";
import type { DealmakerMode, ModuleId, SageCompletionResponse, SageLanguage } from "./types";

interface UseSageCompletionOptions {
  /** Same-origin proxy path in the host app, e.g. "/api/sage/completions"
   * (QuietNoise) or "/api/v1/sage/completions" (Lorito). The host app's
   * own backend attaches the tenant API key server-side -- the browser
   * never sees it. */
  endpoint: string;
}

interface RunArgs {
  module: ModuleId;
  mode?: DealmakerMode | null;
  language?: SageLanguage;
  userMessage: string;
  context: Record<string, unknown>;
}

export function useSageCompletion({ endpoint }: UseSageCompletionOptions) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SageCompletionResponse | null>(null);

  const run = useCallback(
    async ({ module, mode, language, userMessage, context }: RunArgs) => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            module,
            mode: mode ?? null,
            language: language ?? "en",
            user_message: userMessage,
            context,
          }),
        });
        if (!response.ok) {
          throw new Error(`Sage request failed (${response.status})`);
        }
        const data: SageCompletionResponse = await response.json();
        setResult(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Sage request failed";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [endpoint],
  );

  return { run, loading, error, result };
}
