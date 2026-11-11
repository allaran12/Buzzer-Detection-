"use client";

import React, { useState } from "react";
import { BuzzerAccount, TweetSample } from "@/types/buzzer";
import {
  X,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  MessageSquare,
  Users,
  Repeat,
  Share2,
  Calendar,
  Sparkles,
} from "lucide-react";

interface AccountDetailModalProps {
  account: BuzzerAccount | null;
  onClose: () => void;
}

export const AccountDetailModal: React.FC<AccountDetailModalProps> = ({
  account,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<"tweets" | "indicators">("tweets");

  if (!account) return null;

  const getRiskBadge = (score: number) => {
    if (score >= 70) {
      return {
        bg: "bg-rose-500/10 border-rose-500/20 text-rose-400",
        label: "Buzzer / Risiko Tinggi",
        icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
      };
    }
    if (score >= 40) {
      return {
        bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
        label: "Potensi Terkoordinasi",
        icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
      };
    }
    return {
      bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
      label: "Akun Organik",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
    };
  };

  const risk = getRiskBadge(account.buzzerScore);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 sm:p-6 border-b border-slate-800/80 bg-slate-900/90 flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <img
              src={account.avatar || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"}
              alt={account.username}
              className="w-14 h-14 rounded-2xl object-cover border-2 border-slate-700 shadow-md"
            />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  {account.name}
                </h2>
                <a
                  href={`https://x.com/${account.username}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-mono transition-colors"
                >
                  <span>@{account.username}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              {account.bio ? (
                <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                  {account.bio}
                </p>
              ) : (
                <p className="text-xs italic text-slate-500 mt-1">
                  (Tidak ada bio profil)
                </p>
              )}

              {/* Badges line */}
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <div
                  className={`flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${risk.bg}`}
                >
                  {risk.icon}
                  <span>{risk.label}</span>
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  Isu: {account.campaignIssue}
                </span>
                {account.clusterId && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    Klaster #{account.clusterId}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Buzzer Score</span>
              <div className="mt-1 flex items-baseline space-x-1">
                <span className={`text-2xl font-black ${account.buzzerScore >= 70 ? "text-rose-400" : account.buzzerScore >= 40 ? "text-amber-400" : "text-emerald-400"}`}>
                  {account.buzzerScore}
                </span>
                <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Follower / Following</span>
              <div className="mt-1 flex items-baseline space-x-1">
                <span className="text-lg font-bold text-white">
                  {account.followers.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400">/ {account.following.toLocaleString()}</span>
              </div>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                Rasio: {account.followerRatio.toFixed(1)}x
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Post Rate</span>
              <div className="mt-1 flex items-baseline space-x-1">
                <span className="text-lg font-bold text-white">
                  {account.postRatePerHour.toFixed(1)}
                </span>
                <span className="text-xs text-slate-400">tweet / jam</span>
              </div>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                Total {account.nPostsInDataset} di dataset
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 uppercase font-medium">Umur Akun</span>
              <div className="mt-1 flex items-baseline space-x-1">
                <span className="text-lg font-bold text-white">
                  {account.accountAgeDays}
                </span>
                <span className="text-xs text-slate-400">hari</span>
              </div>
              <span className="text-[10px] text-slate-500 block mt-0.5 font-mono">
                Dibuat: {account.created ? new Date(account.created).toLocaleDateString("id-ID") : "-"}
              </span>
            </div>
          </div>

          {/* 4 Pillars Breakdown Accordion / Progress */}
          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/90">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Dekomposisi 4 Pilar Koordinasi AI</span>
            </h4>

            <div className="space-y-3">
              {account.indicators.map((ind, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-medium text-slate-200">{ind.name}</span>
                    <span className={`font-mono font-bold ${ind.status === "danger" ? "text-rose-400" : ind.status === "warning" ? "text-amber-400" : "text-emerald-400"}`}>
                      {ind.score}%
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${ind.status === "danger" ? "bg-rose-500" : ind.status === "warning" ? "bg-amber-400" : "bg-emerald-500"}`}
                      style={{ width: `${ind.score}%` }}
                    ></div>
                  </div>

                  <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                    {ind.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Tabs: Sample Tweets vs Indicators */}
          <div>
            <div className="flex border-b border-slate-800 mb-4">
              <button
                onClick={() => setActiveTab("tweets")}
                className={`pb-2 px-3 text-xs font-semibold transition-colors border-b-2 ${
                  activeTab === "tweets"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Sampel Postingan Tweet ({account.tweets.length})
              </button>
            </div>

            {/* Tweets list */}
            {activeTab === "tweets" && (
              <div className="space-y-3">
                {account.tweets.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-4 text-center">
                    Tidak ada sampel tweet yang tersedia untuk akun ini.
                  </p>
                ) : (
                  account.tweets.map((tw) => (
                    <div
                      key={tw.id}
                      className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-center justify-between text-xs mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase bg-slate-800 text-slate-300 border border-slate-700">
                            {tw.relationType}
                          </span>
                          {tw.targetUsername && (
                            <span className="text-indigo-400 text-[11px]">
                              → kepada @{tw.targetUsername}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-1.5 text-slate-500 text-[11px]">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(tw.date).toLocaleString("id-ID")}</span>
                        </div>
                      </div>

                      <p className="text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-line">
                        {tw.text}
                      </p>

                      {/* Tweet indicators */}
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        {tw.duplicateSimilarity && tw.duplicateSimilarity > 0.7 && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                            Kemiripan Teks {(tw.duplicateSimilarity * 100).toFixed(0)}%
                          </span>
                        )}
                        {tw.burstEvent && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                            Terkoordinasi Dalam Menit Sama
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/90 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            ID Akun: {account.id} • CoordinX Intelligence Engine
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition-colors cursor-pointer"
          >
            Tutup Inspeksi
          </button>
        </div>
      </div>
    </div>
  );
};

