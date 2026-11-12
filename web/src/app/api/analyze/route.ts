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
          limit: body.limit || 25,
          fetch_replies: body.fetchReplies ?? true,
          days: body.days || 30,
        }
      : {
          dataset_path: datasetPath,
          model_experiment: body.modelExperiment,
        };

    const response = await fetch(`${target}/api/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(120000),
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const data = await readJson(response);
    if (!response.ok) {
      return NextResponse.json(
        { source: "error", error: data.detail || data.error || "Inference gagal" },
        { status: response.status },
      );
    }
    return NextResponse.json({ ...data, newAccounts: data.accounts || [] });
  } catch (error) {
    const message = error instanceof DOMException && error.name === "TimeoutError"
      ? "Inference timeout: proses scraping melebihi 120 detik"
      : "Gagal menghubungi inference backend";
    return NextResponse.json({ source: "error", error: message }, { status: 502 });
  }
}
