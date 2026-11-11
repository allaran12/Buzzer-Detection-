"use client";

import React from "react";
import { DashboardSummary } from "@/types/buzzer";
import { Users, AlertTriangle, ShieldCheck, Zap, Network, Flame } from "lucide-react";

interface StatsOverviewProps {
  summary: DashboardSummary;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ summary }) => {
  const highRiskPercent = ((summary.highRiskCount / summary.totalAccounts) * 100).toFixed(1);
  const mediumRiskPercent = ((summary.mediumRiskCount / summary.totalAccounts) * 100).toFixed(1);
  const lowRiskPercent = ((summary.lowRiskCount / summary.totalAccounts) * 100).toFixed(1);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total Accounts */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Total Akun Dianalisis
          </span>
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Users className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {summary.totalAccounts.toLocaleString("id-ID")}
          </span>
          <span className="text-xs text-slate-400">akun unik</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-slate-400 space-x-2">
          <span className="text-indigo-400 font-medium">{summary.totalPosts.toLocaleString("id-ID")}</span>
          <span>total tweet terkumpul</span>
        </div>
      </div>

      {/* High Risk / Buzzer */}
      <div className="p-4 sm:p-5 rounded-2xl bg-rose-950/20 border border-rose-900/30 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
            Terindikasi Buzzer (Risiko Tinggi)
          </span>
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-bold text-rose-400 tracking-tight">
            {summary.highRiskCount}
          </span>
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300">
            {highRiskPercent}%
          </span>
        </div>
        <div className="mt-3 text-xs text-slate-400">
          Skor koordinasi &gt; 70 (anomali teks & burst serentak)
        </div>
      </div>

      {/* Medium Risk / In Review */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-950/20 border border-amber-900/30 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
            Potensi Terkoordinasi (Sedang)
          </span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Flame className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-bold text-amber-400 tracking-tight">
            {summary.mediumRiskCount}
          </span>
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
            {mediumRiskPercent}%
          </span>
        </div>
        <div className="mt-3 text-xs text-slate-400">
          Perlu review manual (skor 40 - 70)
        </div>
      </div>

      {/* Clusters & Burst Events */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Klaster & Lonjakan Terdeteksi
          </span>
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Network className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-bold text-emerald-400 tracking-tight">
            {summary.clustersDetected}
          </span>
          <span className="text-xs text-slate-400">klaster jaringan</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-slate-400 space-x-2">
          <span className="text-emerald-400 font-medium">{summary.burstEventsCount} event</span>
          <span>lonjakan waktu serentak</span>
        </div>
      </div>
    </div>
  );
};

