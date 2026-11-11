"use client";

import React, { useState, useMemo } from "react";
import { BuzzerAccount, FilterState } from "@/types/buzzer";
import {
  Search,
  SlidersHorizontal,
  ChevronUp,
  ChevronDown,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Eye,
  Filter,
  Download,
} from "lucide-react";

interface AccountTableProps {
  accounts: BuzzerAccount[];
  issues: { id: string; label: string }[];
  onSelectAccount: (account: BuzzerAccount) => void;
}

export const AccountTable: React.FC<AccountTableProps> = ({
  accounts,
  issues,
  onSelectAccount,
}) => {
  const [filterState, setFilterState] = useState<FilterState>({
    searchQuery: "",
    riskFilter: "all",
    issueFilter: "all",
    sortBy: "buzzerScore",
    sortOrder: "desc",
  });

  const filteredAccounts = useMemo(() => {
    return accounts
      .filter((acc) => {
        // Search filter
        if (filterState.searchQuery.trim()) {
          const q = filterState.searchQuery.toLowerCase();
          const matchUsername = acc.username.toLowerCase().includes(q);
          const matchName = acc.name.toLowerCase().includes(q);
          const matchBio = acc.bio.toLowerCase().includes(q);
          if (!matchUsername && !matchName && !matchBio) return false;
        }

        // Risk filter
        if (filterState.riskFilter !== "all" && acc.riskLevel !== filterState.riskFilter) {
          return false;
        }

        // Issue filter
        if (filterState.issueFilter !== "all" && acc.campaignIssue !== filterState.issueFilter) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        const factor = filterState.sortOrder === "asc" ? 1 : -1;
        if (filterState.sortBy === "buzzerScore") {
          return (a.buzzerScore - b.buzzerScore) * factor;
        }
        if (filterState.sortBy === "nPostsInDataset") {
          return (a.nPostsInDataset - b.nPostsInDataset) * factor;
        }
        if (filterState.sortBy === "postRatePerHour") {
          return (a.postRatePerHour - b.postRatePerHour) * factor;
        }
        if (filterState.sortBy === "followerRatio") {
          return (a.followerRatio - b.followerRatio) * factor;
        }
        if (filterState.sortBy === "accountAgeDays") {
          return (a.accountAgeDays - b.accountAgeDays) * factor;
        }
        return 0;
      });
  }, [accounts, filterState]);

  const handleExportCSV = () => {
    const headers = [
      "username",
      "name",
      "buzzer_score",
      "risk_level",
      "campaign_issue",
      "followers",
      "following",
      "follower_ratio",
      "n_posts",
      "post_rate_per_hour",
      "duplicate_ratio",
      "burst_ratio",
      "account_age_days",
    ];
    const rows = filteredAccounts.map((a) => [
      a.username,
      `"${a.name.replace(/"/g, '""')}"`,
      a.buzzerScore,
      a.riskLevel,
      `"${a.campaignIssue}"`,
      a.followers,
      a.following,
      a.followerRatio.toFixed(2),
      a.nPostsInDataset,
      a.postRatePerHour.toFixed(2),
      a.duplicateTextRatio.toFixed(2),
      a.burstRatio.toFixed(2),
      a.accountAgeDays,
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `coordinx_accounts_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSort = (field: FilterState["sortBy"]) => {
    if (filterState.sortBy === field) {
      setFilterState((prev) => ({
        ...prev,
        sortOrder: prev.sortOrder === "asc" ? "desc" : "asc",
      }));
    } else {
      setFilterState((prev) => ({
        ...prev,
        sortBy: field,
        sortOrder: "desc",
      }));
    }
  };

  const getRiskBadge = (score: number) => {
    if (score >= 70) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
          <span>Buzzer ({score})</span>
        </span>
      );
    }
    if (score >= 40) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
          <span>Suspicious ({score})</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
        <span>Organik ({score})</span>
      </span>
    );
  };

  return (
    <div className="rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md overflow-hidden">
      {/* Top Filter & Search Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-800/80 space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Cari username, nama akun, atau bio..."
              value={filterState.searchQuery}
              onChange={(e) =>
                setFilterState((prev) => ({ ...prev, searchQuery: e.target.value }))
              }
              className="w-full pl-10 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
            />
          </div>

          {/* Issue Selector & Export */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-slate-400 shrink-0" />
              <select
                value={filterState.issueFilter}
                onChange={(e) =>
                  setFilterState((prev) => ({ ...prev, issueFilter: e.target.value }))
                }
                className="px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
              >
                {issues.map((iss) => (
                  <option key={iss.id} value={iss.id}>
                    {iss.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleExportCSV}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors cursor-pointer active:scale-95"
              title="Unduh tabel hasil sebagai CSV"
            >
              <Download className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Ekspor CSV</span>
            </button>
          </div>
        </div>

        {/* Risk Level Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-slate-400 mr-1 font-medium">Filter Kategori:</span>
          {(
            [
              { id: "all", label: "Semua Akun" },
              { id: "high", label: "🔴 Risiko Tinggi (Buzzer)" },
              { id: "medium", label: "🟡 Potensi Terkoordinasi" },
              { id: "low", label: "🟢 Akun Organik" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() =>
                setFilterState((prev) => ({ ...prev, riskFilter: tab.id }))
              }
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                filterState.riskFilter === tab.id
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                  : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
          <span className="ml-auto text-xs text-slate-500 font-mono">
            Menampilkan {filteredAccounts.length} dari {accounts.length} akun
          </span>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-semibold text-[11px] tracking-wider">
            <tr>
              <th className="py-3.5 px-4 sm:px-6">Akun / Profil X</th>
              <th
                onClick={() => handleSort("buzzerScore")}
                className="py-3.5 px-4 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Skor Buzzer</span>
                  {filterState.sortBy === "buzzerScore" &&
                    (filterState.sortOrder === "desc" ? (
                      <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />
                    ) : (
                      <ChevronUp className="w-3.5 h-3.5 text-indigo-400" />
                    ))}
                </div>
              </th>
              <th
                onClick={() => handleSort("followerRatio")}
                className="py-3.5 px-4 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Follower / Following</span>
                  {filterState.sortBy === "followerRatio" &&
                    (filterState.sortOrder === "desc" ? (
                      <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />
                    ) : (
                      <ChevronUp className="w-3.5 h-3.5 text-indigo-400" />
                    ))}
                </div>
              </th>
              <th
                onClick={() => handleSort("nPostsInDataset")}
                className="py-3.5 px-4 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Aktivitas &amp; Burst</span>
                  {filterState.sortBy === "nPostsInDataset" &&
                    (filterState.sortOrder === "desc" ? (
                      <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />
                    ) : (
                      <ChevronUp className="w-3.5 h-3.5 text-indigo-400" />
                    ))}
                </div>
              </th>
              <th className="py-3.5 px-4">Indikator Terdeteksi</th>
              <th className="py-3.5 px-4 sm:px-6 text-right">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredAccounts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <Search className="w-8 h-8 text-slate-600" />
                    <p className="text-sm font-medium">Tidak ada akun yang sesuai dengan filter.</p>
                    <p className="text-xs text-slate-500">Coba ubah kata kunci atau pilihan kategori risiko.</p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredAccounts.map((account) => (
                <tr
                  key={account.id}
                  className="hover:bg-slate-800/40 transition-colors group"
                >
                  {/* Account Column */}
                  <td className="py-4 px-4 sm:px-6">
                    <div className="flex items-center space-x-3">
                      <img
                        src={account.avatar || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"}
                        alt={account.username}
                        className="w-10 h-10 rounded-xl object-cover border border-slate-700 shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-bold text-white truncate text-xs sm:text-sm">
                            {account.name}
                          </span>
                          {account.isClusterLeader && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                              Amplifier
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] font-mono">
                          <span>@{account.username}</span>
                          <span>•</span>
                          <span>{account.accountAgeDays} hr</span>
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Buzzer Score */}
                  <td className="py-4 px-4">
                    <div className="space-y-1.5 max-w-[120px]">
                      {getRiskBadge(account.buzzerScore)}
                      {/* Mini Score Bar */}
                      <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            account.buzzerScore >= 70
                              ? "bg-rose-500"
                              : account.buzzerScore >= 40
                              ? "bg-amber-400"
                              : "bg-emerald-400"
                          }`}
                          style={{ width: `${account.buzzerScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>

                  {/* Followers / Following */}
                  <td className="py-4 px-4">
                    <div className="space-y-0.5">
                      <div className="text-slate-200 font-medium">
                        {account.followers.toLocaleString()} flw
                      </div>
                      <div className="text-slate-400 text-[11px]">
                        Following: {account.following.toLocaleString()}
                      </div>
                      <div className={`text-[10px] font-mono ${account.followerRatio > 10 ? "text-rose-400 font-semibold" : "text-slate-500"}`}>
                        Rasio: {account.followerRatio.toFixed(1)}x
                      </div>
                    </div>
                  </td>

                  {/* Activity & Burst */}
                  <td className="py-4 px-4">
                    <div className="space-y-0.5">
                      <div className="text-slate-200 font-medium">
                        {account.nPostsInDataset} post
                      </div>
                      <div className="text-slate-400 text-[11px]">
                        {account.postRatePerHour.toFixed(1)} tweet/jam
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {account.outDegree} reply/quote
                      </div>
                    </div>
                  </td>

                  {/* Key Indicators */}
                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1.5 max-w-xs">
                      {account.duplicateTextRatio > 0.7 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                          Copypasta {(account.duplicateTextRatio * 100).toFixed(0)}%
                        </span>
                      )}
                      {account.burstRatio > 0.8 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          Burst Serentak
                        </span>
                      )}
                      {account.accountAgeDays < 90 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          Akun Baru
                        </span>
                      )}
                      {account.followerRatio > 15 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          Rasio Ekstrem
                        </span>
                      )}
                      {account.duplicateTextRatio <= 0.3 && account.burstRatio <= 0.3 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                          Pola Normal
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Action */}
                  <td className="py-4 px-4 sm:px-6 text-right">
                    <button
                      onClick={() => onSelectAccount(account)}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-indigo-600/10 hover:bg-indigo-600 text-indigo-400 hover:text-white border border-indigo-500/30 transition-all text-xs font-semibold cursor-pointer active:scale-95"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspeksi</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

