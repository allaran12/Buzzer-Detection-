import { NextResponse } from "next/server";

export const runtime = "nodejs";

const backend = () =>
  (process.env.FASTAPI_BACKEND_URL || (process.env.NODE_ENV !== "production" ? "http://127.0.0.1:8000" : ""))
    .replace(/\/$/, "");

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
  const target = backend();
  if (!target) return NextResponse.json({ error: "Backend belum dikonfigurasi" }, { status: 503 });
  const token = request.headers.get("x-coordinx-admin-token") || "";
  try {
    const response = await fetch(`${target}/api/v1/scraper/accounts`, {
      headers: { "x-coordinx-admin-token": token },
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    return NextResponse.json(await readJson(response), { status: response.status });
  } catch {
    return NextResponse.json({ error: "Inference backend Railway tidak merespons. Periksa status service backend." }, { status: 502 });
  }
}

export async function POST(request: Request) {
  const target = backend();
  if (!target) return NextResponse.json({ error: "Backend belum dikonfigurasi" }, { status: 503 });
  const token = request.headers.get("x-coordinx-admin-token") || "";
  try {
    const response = await fetch(`${target}/api/v1/scraper/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-coordinx-admin-token": token },
      body: JSON.stringify(await request.json()),
      cache: "no-store",
      signal: AbortSignal.timeout(60000),
    });
    return NextResponse.json(await readJson(response), { status: response.status });
  } catch {
    return NextResponse.json({ error: "Inference backend Railway tidak merespons. Periksa status service backend." }, { status: 502 });
  }
}
