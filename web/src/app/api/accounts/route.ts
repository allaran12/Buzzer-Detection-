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

export async function GET(request: Request) {
  const target = backendUrl();
  if (!target) {
    return NextResponse.json({ error: "Inference backend belum dikonfigurasi" }, { status: 503 });
  }

  const { searchParams } = new URL(request.url);
  const params = new URLSearchParams();
  for (const key of ["risk", "issue", "q"]) {
    const value = searchParams.get(key);
    if (value) params.set(key, value);
  }

  try {
    const response = await fetch(`${target}/api/v1/accounts?${params.toString()}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(30000),
    });
    const data = await readJson(response);
    return NextResponse.json(data, { status: response.ok ? 200 : response.status });
  } catch {
    return NextResponse.json({ error: "Gagal menghubungi inference backend" }, { status: 502 });
  }
}
