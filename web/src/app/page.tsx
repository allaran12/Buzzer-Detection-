"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { StatsOverview } from "@/components/StatsOverview";
import { BurstTimelineChart } from "@/components/BurstTimelineChart";
import { NetworkGraphView } from "@/components/NetworkGraphView";
import { AccountTable } from "@/components/AccountTable";
import { AccountDetailModal } from "@/components/AccountDetailModal";
import { NewAnalysisModal } from "@/components/NewAnalysisModal";
import { MOCK_ACCOUNTS, MOCK_SUMMARY, MOCK_ISSUES } from "@/data/mockAccounts";
import { BuzzerAccount } from "@/types/buzzer";
import { ShieldAlert, Sparkles } from "lucide-react";

export default function Home() {
  const [selectedAccount, setSelectedAccount] = useState<BuzzerAccount | null>(null);
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false);
  const [accounts, setAccounts] = useState<BuzzerAccount[]>(MOCK_ACCOUNTS);
  const [summary, setSummary] = useState(MOCK_SUMMARY);
  const [issues, setIssues] = useState(MOCK_ISSUES);

  const handleAnalysisSuccess = (payload: {
    newAccounts: BuzzerAccount[];
    issueName: string;
    analyzedPostsCount: number;
  }) => {
    setIsAnalysisModalOpen(false);
    if (payload.newAccounts.length > 0) {
      setAccounts((prev) => [...payload.newAccounts, ...prev]);
      setIssues((prev) =>
        prev.some((i) => i.id === payload.issueName)
          ? prev
          : [...prev, { id: payload.issueName, label: `Analisis Baru: ${payload.issueName}` }]
      );
      setSelectedAccount(payload.newAccounts[0]);
    }
    setSummary((prev) => ({
      ...prev,
      totalAccounts: prev.totalAccounts + Math.max(payload.newAccounts.length, 1),
      totalPosts: prev.totalPosts + payload.analyzedPostsCount,
      highRiskCount:
        prev.highRiskCount +
        payload.newAccounts.filter((a) => a.riskLevel === "high").length,
      clustersDetected: prev.clustersDetected + 1,
    }));
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar onOpenNewAnalysis={() => setIsAnalysisModalOpen(true)} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section Banner */}
        <div className="relative rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-indigo-950/60 via-slate-900 to-violet-950/50 border border-indigo-900/40 overflow-hidden shadow-2xl">
          <div className="relative z-10 max-w-3xl space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Sistem Deteksi Jaringan Buzzer &amp; Perilaku Terkoordinasi</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Investigasi Akun &amp; Pola Koordinasi Manipulatif di X
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
              CoordinX membedah operasi akun buzzer melalui fusi 3 pilar analitik: representasi semantik pesan (<strong>IndoBERTweet</strong>), analisis sekuens waktu serentak (<strong>LSTM Burst</strong>), dan topologi graf relasi interaksi (<strong>GraphSAGE</strong>).
            </p>
          </div>

          {/* Decorative glowing gradient */}
          <div className="absolute -right-20 -top-20 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="absolute right-40 -bottom-20 w-72 h-72 bg-violet-600/10 rounded-full blur-3xl pointer-events-none"></div>
        </div>

        {/* 1. Dashboard KPI Overview */}
        <section>
          <StatsOverview summary={summary} />
        </section>

        {/* 2. Temporal Burst Activity Chart */}
        <section>
          <BurstTimelineChart />
        </section>

        {/* 3. Network Graph Topology Visualization */}
        <section>
          <NetworkGraphView
            accounts={accounts}
            onSelectAccount={(acc) => setSelectedAccount(acc)}
          />
        </section>

        {/* 4. Account Risk Inspector & Table (Core User Request) */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-indigo-400" />
                <span>Account Risk Inspector &amp; Deteksi Akun Mencurigakan</span>
              </h2>
              <p className="text-xs text-slate-400">
                Pilih akun untuk memeriksa dekomposisi skor kecurigaan dan verifikasi sampel tweet
              </p>
            </div>
          </div>

          <AccountTable
            accounts={accounts}
            issues={issues}
            onSelectAccount={(acc) => setSelectedAccount(acc)}
          />
        </section>
      </main>

      {/* Account Detail Modal Drawer */}
      <AccountDetailModal
        account={selectedAccount}
        onClose={() => setSelectedAccount(null)}
      />

      {/* New Analysis Modal */}
      <NewAnalysisModal
        isOpen={isAnalysisModalOpen}
        onClose={() => setIsAnalysisModalOpen(false)}
        onSuccess={handleAnalysisSuccess}
      />

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-900 bg-slate-950 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-400">CoordinX</span>
            <span>•</span>
            <span>Social Cyber Hackathon Research Project</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="hover:text-slate-400 transition-colors">
              Disclaimer: Prediksi AI merupakan indikasi probabilitas dan bukan putusan definitif.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
