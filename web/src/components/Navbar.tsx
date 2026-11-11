"use client";

import React from "react";
import { ShieldAlert, Activity, Sparkles, ExternalLink } from "lucide-react";

interface NavbarProps {
  onOpenNewAnalysis: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenNewAnalysis }) => {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-rose-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-tight text-white">
                Coordin<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-rose-400">X</span>
              </span>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0 Beta
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI Coordinated Inauthentic Behavior & Buzzer Detection
            </p>
          </div>
        </div>

        {/* Status Indicators & Actions */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* AI Engine Status */}
          <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>IndoBERTweet + LSTM + GraphSAGE</span>
          </div>

          {/* Vercel Badge */}
          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
            <svg className="w-3.5 h-3.5 fill-current text-white" viewBox="0 0 24 24">
              <path d="M24 22.525H0l12-21.05 12 21.05z" />
            </svg>
            <span>Vercel Ready</span>
          </div>

          {/* New Analysis Button */}
          <button
            onClick={onOpenNewAnalysis}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs sm:text-sm shadow-md shadow-indigo-600/20 transition-all duration-200 active:scale-95 cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Analisis URL Baru</span>
          </button>
        </div>
      </div>
    </header>
  );
};

