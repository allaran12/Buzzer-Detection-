import { NextResponse } from "next/server";
import { BuzzerAccount } from "@/types/buzzer";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const query = String(body.query || "").trim();

    if (!query) {
      return NextResponse.json(
        { error: "Query atau URL postingan tidak boleh kosong" },
        { status: 400 }
      );
    }

    // If FastAPI backend is configured, proxy to it
    const fastapiUrl = process.env.FASTAPI_BACKEND_URL || body.apiUrl;
    if (fastapiUrl) {
      try {
        const res = await fetch(`${fastapiUrl.replace(/\/$/, "")}/api/v1/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        });
        if (res.ok) {
          const data = await res.json();
          return NextResponse.json({ source: "fastapi", ...data });
        }
      } catch (err) {
        console.warn("FastAPI fallback to simulation:", err);
      }
    }

    // Extract hashtag or status ID for realistic contextual simulation
    const cleanIssue = query
      .replace(/https?:\/\/(www\.)?(x|twitter)\.com\/[^/]+\/status\//i, "Post_")
      .replace(/^#/, "")
      .slice(0, 24) || "CustomQuery";

    const randomScore = Math.floor(Math.random() * 20) + 76; // 76 - 95
    const timestamp = new Date().toISOString();

    const simulatedAccount: BuzzerAccount = {
      id: `acc_live_${Date.now()}`,
      username: `bot_radar_${Math.floor(Math.random() * 900 + 100)}`,
      name: `Terdeteksi (${cleanIssue})`,
      avatar: "https://images.unsplash.com/photo-1511367461989-f85a21fda167?w=150&auto=format&fit=crop&q=80",
      bio: `Akun terdeteksi otomatis saat pemindaian isu ${query}`,
      created: "2024-09-20T05:00:00Z",
      accountAgeDays: 52,
      followers: 19,
      following: 740,
      followerRatio: 38.9,
      statuses: 2150,
      statusesPerDay: 41.3,
      buzzerScore: randomScore,
      riskLevel: "high",
      campaignIssue: cleanIssue,
      nPostsInDataset: 24,
      postRatePerHour: 16.2,
      duplicateTextRatio: 0.89,
      burstRatio: 0.92,
      outDegree: 15,
      clusterId: "cluster-live",
      indicators: [
        {
          name: "Kemiripan Teks Semantik (NLP)",
          score: 89,
          weight: 0.35,
          description: `Pola narasi identik ditemukan berulang pada topik "${query}".`,
          status: "danger",
        },
        {
          name: "Lonjakan Waktu Serentak (Temporal Burst)",
          score: 92,
          weight: 0.30,
          description: "Lonjakan posting serentak dalam interval 60 detik.",
          status: "danger",
        },
        {
          name: "Topologi Graf Relasi (Out-Degree)",
          score: 79,
          weight: 0.20,
          description: "Terhubung langsung ke node penggerak isu target.",
          status: "danger",
        },
        {
          name: "Anomali Profil Akun",
          score: 88,
          weight: 0.15,
          description: "Akun baru (< 60 hari) dengan rasio following:follower ekstrem.",
          status: "danger",
        },
      ],
      tweets: [
        {
          id: `tw_live_${Date.now()}`,
          date: timestamp,
          text: `Ayo kawal terus narasi ${query}! Jangan biarkan opini publik dibelokkan oleh pihak tertentu. Sebarkan ke semua grup!`,
          relationType: "original",
          duplicateSimilarity: 0.91,
          burstEvent: true,
        },
      ],
    };

    return NextResponse.json({
      source: "simulation",
      query,
      issueName: cleanIssue,
      newAccounts: [simulatedAccount],
      analyzedPostsCount: 48,
      timestamp,
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Gagal memproses permintaan analisis" },
      { status: 500 }
    );
  }
}
