"use client";

import React, { useState } from "react";
import {
  X,
  Sparkles,
  Link2,
  Hash,
  Search,
  CheckCircle2,
  Loader2,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";

import { BuzzerAccount } from "@/types/buzzer";

interface NewAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (payload: {
    newAccounts: BuzzerAccount[];
    issueName: string;
    analyzedPostsCount: number;
  }) => void;
}

export const NewAnalysisModal: React.FC<NewAnalysisModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [query, setQuery] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  if (!isOpen) return null;

  const steps = [
    "1. Mengumpulkan data tweet & riwayat balasan via twscrape...",
    "2. Membersihkan dan menormalisasi token teks untuk IndoBERTweet...",
    "3. Membentuk graf interaksi terpusat & mengidentifikasi edge reply/quote...",
    "4. Menggabungkan fitur temporal & menghitung Buzzer Risk Score...",
  ];

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsAnalyzing(true);
    setCurrentStep(0);

    try {
      const apiPromise = fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      }).then((r) => r.json());

      for (let i = 0; i < steps.length - 1; i++) {
        await new Promise((res) => setTimeout(res, 650));
        setCurrentStep(i + 1);
      }

      const data = await apiPromise;
      await new Promise((res) => setTimeout(res, 400));
      setIsAnalyzing(false);
      setQuery("");
      onSuccess({
        newAccounts: data.newAccounts || [],
        issueName: data.issueName || query,
        analyzedPostsCount: data.analyzedPostsCount || 40,
      });
    } catch {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-6 sm:p-7 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={isAnalyzing}
          className="absolute top-5 right-5 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors disabled:opacity-50"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Mulai Analisis Koordinasi Baru
            </h3>
            <p className="text-xs text-slate-400">
              Masukkan tautan status X, kata kunci isu, atau #tagar
            </p>
          </div>
        </div>

        {/* Form */}
        {!isAnalyzing ? (
          <form onSubmit={handleStartAnalysis} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                URL Postingan X atau Tagar Isu
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Link2 className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  placeholder="e.g. https://x.com/username/status/18451299901 atau #PrayForKalimantan"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-mono"
                />
              </div>
            </div>

            {/* Quick Suggestion Pills */}
            <div className="space-y-1.5">
              <span className="text-[11px] text-slate-400 font-medium">Contoh isu cepat:</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "#PrayForKalimantan",
                  "https://x.com/status/wowo2_debate",
                  "#RoySuryoDebatPanci",
                ].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setQuery(s)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 font-mono transition-colors cursor-pointer"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-3">
              <button
                type="submit"
                className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all cursor-pointer active:scale-98"
              >
                <span>Jalankan Pipeline Analisis AI</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        ) : (
          /* Analysis In-Progress Animation */
          <div className="py-6 space-y-6">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto animate-bounce">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
              <h4 className="font-bold text-white text-base">
                Sedang Menganalisis Pola Koordinasi...
              </h4>
              <p className="text-xs text-slate-400 font-mono">
                Query: {query}
              </p>
            </div>

            {/* Steps list */}
            <div className="space-y-2.5 bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
              {steps.map((st, i) => (
                <div key={i} className="flex items-center space-x-3 text-xs">
                  {i < currentStep ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : i === currentStep ? (
                    <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0"></div>
                  )}
                  <span
                    className={`${
                      i <= currentStep ? "text-slate-200 font-medium" : "text-slate-600"
                    }`}
                  >
                    {st}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

