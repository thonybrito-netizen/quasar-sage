import { NextRequest, NextResponse } from "next/server";

/**
 * This standalone app is Quasar Sage's own first-party product surface
 * (unlike QuietNoise/Lorito, which are third-party embeddings) -- but the
 * Gateway's tenant key still stays server-side here, same principle as
 * every other integration: the browser never sees it.
 */
export async function POST(req: NextRequest) {
  const gatewayUrl = process.env.SAGE_GATEWAY_URL;
  const apiKey = process.env.SAGE_DEMO_TENANT_KEY;

  if (!gatewayUrl || !apiKey) {
    return NextResponse.json({ error: "Sage is not configured for this environment" }, { status: 503 });
  }

  try {
    const body = await req.json();
    const response = await fetch(`${gatewayUrl}/v1/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    return NextResponse.json(data, { status: response.status });
  } catch (err: unknown) {
    const detail = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: "Sage unreachable", detail }, { status: 503 });
  }
}
