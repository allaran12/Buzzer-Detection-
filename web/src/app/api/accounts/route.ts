import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const backendUrl = process.env.FASTAPI_BACKEND_URL;
  const datasetPath = process.env.COORDINX_DEFAULT_DATASET_PATH || "data/features/batch2_account_features_with_scores.csv";
  if (!backendUrl || !datasetPath) {
    return NextResponse.json({ error: "Inference backend atau dataset belum dikonfigurasi" }, { status: 503 });
  }

  const { searchParams } = new URL(request.url);
  const risk = searchParams.get("risk");
  const issue = searchParams.get("issue");
  const q = searchParams.get("q")?.toLowerCase();

  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, "")}/api/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_path: datasetPath }),
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok) return NextResponse.json({ error: data.detail || "Inference gagal" }, { status: response.status });

    let accounts = data.accounts || [];
    if (q) accounts = accounts.filter((account: { username?: string; name?: string; bio?: string }) => `${account.username || ""} ${account.name || ""} ${account.bio || ""}`.toLowerCase().includes(q));
    if (risk && risk !== "all") accounts = accounts.filter((account: { riskLevel: string }) => account.riskLevel === risk);
    if (issue && issue !== "all") accounts = accounts.filter((account: { campaignIssue: string }) => account.campaignIssue === issue);

    return NextResponse.json({ ...data, accounts, total: accounts.length });
  } catch {
    return NextResponse.json({ error: "Gagal menghubungi inference backend" }, { status: 502 });
  }
}
