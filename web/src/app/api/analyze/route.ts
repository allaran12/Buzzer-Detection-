import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const query = String(body.query || "").trim();
    const datasetPath = String(
      body.datasetPath || process.env.COORDINX_DEFAULT_DATASET_PATH || ""
    ).trim();

    if (!query && !datasetPath) {
      return NextResponse.json({ error: "Dataset atau query analisis wajib diisi" }, { status: 400 });
    }

    const backendUrl =
      process.env.FASTAPI_BACKEND_URL ||
      (process.env.NODE_ENV !== "production" ? "http://127.0.0.1:8000" : "");
    if (!backendUrl) {
      if (process.env.COORDINX_DEMO_MODE === "true") {
        return NextResponse.json({ source: "simulation", query, accounts: [], newAccounts: [], summary: null });
      }
      return NextResponse.json({ error: "Inference backend belum dikonfigurasi" }, { status: 503 });
    }

    const response = await fetch(`${backendUrl.replace(/\/$/, "")}/api/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(120000),
      body: JSON.stringify({
        dataset_path: body.datasetPath || undefined,
        query: body.datasetPath ? undefined : query,
        model_experiment: body.modelExperiment,
        limit: body.limit || 25,
        fetch_replies: body.fetchReplies ?? false,
        days: body.days || 30,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json({ source: "error", error: data.detail || "Inference gagal" }, { status: response.status });
    }
    return NextResponse.json({ ...data, newAccounts: data.accounts || [] });
  } catch (error) {
    const message = error instanceof DOMException && error.name === "TimeoutError"
      ? "Inference timeout: proses scraping melebihi 120 detik"
      : "Gagal menghubungi inference backend";
    return NextResponse.json({ source: "error", error: message }, { status: 502 });
  }
}
