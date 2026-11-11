"use client";

import React, { useState } from "react";
import { BarChart3, Clock, AlertCircle, Info } from "lucide-react";

export const BurstTimelineChart: React.FC = () => {
  const [selectedInterval, setSelectedInterval] = useState<"hourly" | "minute">("hourly");

  // Mock hourly distribution
  const hourlyData = [
    { time: "06:00", organic: 12, buzzer: 2, isSpike: false },
    { time: "07:00", organic: 34, buzzer: 8, isSpike: false },
    { time: "08:00", organic: 62, buzzer: 21, isSpike: false },
    { time: "09:00", organic: 88, buzzer: 185, isSpike: true }, // Spike!
    { time: "10:00", organic: 75, buzzer: 142, isSpike: true }, // Spike!
    { time: "11:00", organic: 58, buzzer: 45, isSpike: false },
    { time: "12:00", organic: 64, buzzer: 32, isSpike: false },
    { time: "13:00", organic: 70, buzzer: 28, isSpike: false },
    { time: "14:00", organic: 82, buzzer: 210, isSpike: true }, // Spike!
    { time: "15:00", organic: 69, buzzer: 65, isSpike: false },
    { time: "16:00", organic: 52, buzzer: 31, isSpike: false },
    { time: "17:00", organic: 60, buzzer: 24, isSpike: false },
  ];

  const maxVal = Math.max(...hourlyData.map((d) => d.organic + d.buzzer));

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 mb-6 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/60 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-white text-base">
              Aktivitas Temporal &amp; Deteksi Lonjakan Serentak (Burst)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Perbandingan volume postingan akun organik vs akun terindikasi buzzer dalam 12 jam terakhir
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-rose-500"></span>
            <span className="text-slate-300">Aktivitas Buzzer (Burst)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-indigo-500/60"></span>
            <span className="text-slate-300">Postingan Organik</span>
          </div>
        </div>
      </div>

      {/* Bar Chart Visualization */}
      <div className="mt-6 pt-4">
        <div className="h-48 flex items-end justify-between gap-1.5 sm:gap-3 px-2">
          {hourlyData.map((item, idx) => {
            const total = item.organic + item.buzzer;
            const heightPercent = (total / maxVal) * 100;
            const buzzerPercent = (item.buzzer / total) * 100;
            const organicPercent = 100 - buzzerPercent;

            return (
              <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                {/* Tooltip */}
                <div className="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20 bg-slate-800 text-slate-100 text-[11px] px-2.5 py-1.5 rounded-lg border border-slate-700 shadow-xl whitespace-nowrap">
                  <div className="font-semibold text-white">{item.time} WIB</div>
                  <div className="text-rose-400">Buzzer: {item.buzzer} tweet</div>
                  <div className="text-indigo-300">Organik: {item.organic} tweet</div>
                </div>

                {/* Burst badge */}
                {item.isSpike && (
                  <span className="mb-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
                    Spike!
                  </span>
                )}

                {/* Stacked bar */}
                <div
                  className="w-full max-w-[36px] rounded-t-md overflow-hidden flex flex-col justify-end transition-all duration-300 group-hover:brightness-110"
                  style={{ height: `${Math.max(heightPercent, 8)}%` }}
                >
                  <div
                    className="w-full bg-rose-500 transition-all"
                    style={{ height: `${buzzerPercent}%` }}
                  ></div>
                  <div
                    className="w-full bg-indigo-500/60 transition-all"
                    style={{ height: `${organicPercent}%` }}
                  ></div>
                </div>

                {/* X axis label */}
                <span className="text-[10px] text-slate-400 mt-2 font-mono">{item.time}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/40 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <Info className="w-4 h-4 text-slate-400" />
          <span>
            Puncak koordinasi tertinggi tercatat pada pukul <strong>09:00 WIB</strong> dan <strong>14:00 WIB</strong> (selisih postingan &lt; 30 detik).
          </span>
        </div>
      </div>
    </div>
  );
};

