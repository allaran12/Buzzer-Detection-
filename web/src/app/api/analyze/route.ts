import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backendUrl = () => {
  const configured = process.env.FASTAPI_BACKEND_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");
  return process.env.NODE_ENV !== "production" ? "http://127.0.0.1:8000" : "";
};

async function readJson(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { error: text.slice(0, 500) };
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const query = typeof body.query === "string" ? body.query.trim() : "";
    const requestedDatasetPath = typeof body.datasetPath === "string"
      ? body.datasetPath.trim()
      : (process.env.COORDINX_DEFAULT_DATASET_PATH || "").trim();
    const datasetPath = query ? "" : requestedDatasetPath;

    if (!query && !datasetPath) {
      return NextResponse.json({ error: "URL/query atau dataset wajib diisi" }, { status: 400 });
    }

    const target = backendUrl();
    if (!target) {
      if (process.env.COORDINX_DEMO_MODE === "true") {
        return NextResponse.json({ source: "simulation", query, accounts: [], newAccounts: [], summary: null });
      }
      return NextResponse.json({ error: "Inference backend belum dikonfigurasi" }, { status: 503 });
    }

    const payload = query
      ? {
          query,
          model_experiment: body.modelExperiment,
          limit: body.limit || 500,
          fetch_replies: body.fetchReplies === true,
          days: typeof body.days === "number" ? body.days : null,
        }
      : {
          dataset_path: datasetPath,
          model_experiment: body.modelExperiment,
        };

    const response = await fetch(`${target}/api/v1/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-coordinx-admin-token": process.env.COORDINX_ADMIN_TOKEN || (process.env.NODE_ENV !== "production" ? "local-admin" : ""),
      },
      signal: AbortSignal.timeout(query ? 135000 : 30000),
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const data = await readJson(response);
    if (!response.ok) {
      const backendMessage = data.detail || data.error || data.message;
      const requestId = typeof data.request_id === "string" ? ` (request: ${data.request_id})` : "";
      return NextResponse.json(
        {
          source: "error",
          error: backendMessage ? `${String(backendMessage)}${requestId}` : `Inference gagal (HTTP ${response.status})`,
          backendStatus: response.status,
        },
        { status: response.status },
      );
    }
    return NextResponse.json({ ...data, newAccounts: data.accounts || [] });
  } catch (error) {
    const message = error instanceof DOMException && error.name === "TimeoutError"
      ? "Analisis live melewati batas waktu. Pastikan akun scraper aktif di backend Railway atau gunakan dataset analisis yang tersedia."
      : "Gagal menghubungi inference backend Railway. Periksa status service backend dan konfigurasi FASTAPI_BACKEND_URL.";
    return NextResponse.json({ source: "error", error: message }, { status: 502 });
  }
}
