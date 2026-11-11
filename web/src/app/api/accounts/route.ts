import { NextResponse } from "next/server";
import { MOCK_ACCOUNTS, MOCK_SUMMARY, MOCK_ISSUES } from "@/data/mockAccounts";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q")?.toLowerCase();
  const risk = searchParams.get("risk");
  const issue = searchParams.get("issue");

  let result = [...MOCK_ACCOUNTS];

  if (q) {
    result = result.filter(
      (acc) =>
        acc.username.toLowerCase().includes(q) ||
        acc.name.toLowerCase().includes(q) ||
        acc.bio.toLowerCase().includes(q)
    );
  }

  if (risk && risk !== "all") {
    result = result.filter((acc) => acc.riskLevel === risk);
  }

  if (issue && issue !== "all") {
    result = result.filter((acc) => acc.campaignIssue === issue);
  }

  return NextResponse.json({
    summary: MOCK_SUMMARY,
    issues: MOCK_ISSUES,
    accounts: result,
    total: result.length,
  });
}

