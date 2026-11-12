import { NextResponse } from "next/server";

const backend = () => (process.env.FASTAPI_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function GET(request: Request) {
  const token = request.headers.get("x-coordinx-admin-token") || "";
  if (!backend()) return NextResponse.json({ error: "Backend belum dikonfigurasi" }, { status: 503 });
  try {
    const response = await fetch(`${backend()}/api/v1/scraper/accounts`, { headers: { "x-coordinx-admin-token": token }, cache: "no-store" });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: "Inference backend tidak berjalan di port 8000" }, { status: 502 });
  }
}

export async function POST(request: Request) {
  const token = request.headers.get("x-coordinx-admin-token") || "";
  const body = await request.json();
  if (!backend()) return NextResponse.json({ error: "Backend belum dikonfigurasi" }, { status: 503 });
  try {
    const response = await fetch(`${backend()}/api/v1/scraper/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-coordinx-admin-token": token },
      body: JSON.stringify(body),
    });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: "Inference backend tidak berjalan di port 8000" }, { status: 502 });
  }
}
