"use client";

import React, { useState, useMemo } from "react";
import { BuzzerAccount } from "@/types/buzzer";
import { Network, ZoomIn, Info, Sparkles } from "lucide-react";

interface NetworkGraphViewProps {
  accounts: BuzzerAccount[];
  onSelectAccount: (account: BuzzerAccount) => void;
}

interface NodePosition {
  account: BuzzerAccount;
  x: number;
  y: number;
  radius: number;
}

export const NetworkGraphView: React.FC<NetworkGraphViewProps> = ({
  accounts,
  onSelectAccount,
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string>("all");

  // Fixed canvas dimensions for SVG viewBox
  const width = 800;
  const height = 380;

  const clusters = useMemo(() => {
    const unique = Array.from(
      new Set(accounts.map((a) => a.clusterId).filter(Boolean))
    ) as string[];
    return unique;
  }, [accounts]);

  // Compute deterministic node coordinates grouped by cluster
  const nodes: NodePosition[] = useMemo(() => {
    const clusterCenters: Record<string, { x: number; y: number }> = {
      "cluster-alpha": { x: 220, y: 150 },
      "cluster-beta": { x: 460, y: 240 },
      "cluster-gamma": { x: 630, y: 130 },
      "cluster-live": { x: 400, y: 100 },
      organic: { x: 140, y: 290 },
    };

    const counts: Record<string, number> = {};

    return accounts
      .filter((a) => selectedCluster === "all" || a.clusterId === selectedCluster)
      .map((acc) => {
        const key = acc.clusterId || "organic";
        const idx = counts[key] || 0;
        counts[key] = idx + 1;

        const center = clusterCenters[key] || { x: 400, y: 200 };
        const angle = idx * 1.45 + (key.length * 0.5);
        const dist = acc.isClusterLeader ? 0 : 48 + (idx % 3) * 28;

        const x = Math.max(40, Math.min(width - 40, center.x + Math.cos(angle) * dist));
        const y = Math.max(40, Math.min(height - 40, center.y + Math.sin(angle) * dist));
        const radius = acc.isClusterLeader ? 22 : acc.buzzerScore >= 70 ? 16 : 13;

        return { account: acc, x, y, radius };
      });
  }, [accounts, selectedCluster]);

  // Build edges between accounts in the same cluster or targetUsername match
  const edges = useMemo(() => {
    const list: { source: NodePosition; target: NodePosition; type: string }[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        if (
          a.account.clusterId &&
          a.account.clusterId === b.account.clusterId
        ) {
          list.push({ source: a, target: b, type: "coordinated" });
        } else if (
          a.account.campaignIssue === b.account.campaignIssue &&
          (a.account.isClusterLeader || b.account.isClusterLeader)
        ) {
          list.push({ source: a, target: b, type: "mention" });
        }
      }
    }
    return list;
  }, [nodes]);

  const getNodeColor = (acc: BuzzerAccount) => {
    if (acc.buzzerScore >= 70) return { fill: "#f43f5e", stroke: "#fda4af" }; // rose-500
    if (acc.buzzerScore >= 40) return { fill: "#f59e0b", stroke: "#fcd34d" }; // amber-500
    return { fill: "#10b981", stroke: "#6ee7b7" }; // emerald-500
  };

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/60 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-white text-base">
              Topologi Jejaring &amp; Klaster Koordinasi (GraphSAGE Preview)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Klik simpul (node) akun untuk memeriksa detail skor koordinasi dan sampel tweet
          </p>
        </div>

        {/* Cluster Filter */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <button
            onClick={() => setSelectedCluster("all")}
            className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
              selectedCluster === "all"
                ? "bg-indigo-600 text-white font-semibold"
                : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            Semua Klaster
          </button>
          {clusters.map((c) => (
            <button
              key={c}
              onClick={() => setSelectedCluster(c)}
              className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-colors cursor-pointer ${
                selectedCluster === c
                  ? "bg-indigo-600 text-white font-semibold"
                  : "bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              #{c}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Network Canvas */}
      <div className="mt-4 relative rounded-xl bg-slate-950/80 border border-slate-800/70 overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-[300px] sm:h-[360px] select-none"
        >
          {/* Subtle grid pattern */}
          <defs>
            <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
              <path
                d="M 32 0 L 0 0 0 32"
                fill="none"
                stroke="#1e293b"
                strokeWidth="0.5"
                opacity="0.4"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Edges */}
          {edges.map((edge, idx) => {
            const isHighlighted =
              hoveredId === edge.source.account.id ||
              hoveredId === edge.target.account.id;
            return (
              <line
                key={idx}
                x1={edge.source.x}
                y1={edge.source.y}
                x2={edge.target.x}
                y2={edge.target.y}
                stroke={
                  edge.type === "coordinated"
                    ? isHighlighted
                      ? "#f43f5e"
                      : "#9f1239"
                    : "#4f46e5"
                }
                strokeWidth={isHighlighted ? 2.2 : 1.1}
                strokeDasharray={edge.type === "mention" ? "4 4" : undefined}
                opacity={isHighlighted ? 0.95 : 0.45}
                className="transition-all duration-200"
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const colors = getNodeColor(node.account);
            const isHovered = hoveredId === node.account.id;

            return (
              <g
                key={node.account.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseEnter={() => setHoveredId(node.account.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => onSelectAccount(node.account)}
                className="cursor-pointer group"
              >
                {/* Glow ring */}
                {(node.account.buzzerScore >= 70 || isHovered) && (
                  <circle
                    r={node.radius + 7}
                    fill={colors.fill}
                    opacity={isHovered ? 0.3 : 0.14}
                    className={node.account.buzzerScore >= 85 ? "animate-ping" : ""}
                  />
                )}

                {/* Main Circle */}
                <circle
                  r={isHovered ? node.radius + 3 : node.radius}
                  fill={colors.fill}
                  stroke={colors.stroke}
                  strokeWidth={isHovered ? 3 : 1.8}
                  className="transition-all duration-200"
                />

                {/* Score inside circle */}
                <text
                  textAnchor="middle"
                  dy="0.35em"
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="bold"
                  className="pointer-events-none font-mono"
                >
                  {node.account.buzzerScore}
                </text>

                {/* Username label */}
                <text
                  y={node.radius + 14}
                  textAnchor="middle"
                  fill={isHovered ? "#ffffff" : "#94a3b8"}
                  fontSize={isHovered ? "11" : "10"}
                  fontWeight={isHovered ? "bold" : "normal"}
                  className="pointer-events-none font-mono transition-all"
                >
                  @{node.account.username}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend overlay */}
        <div className="absolute bottom-3 left-3 flex flex-wrap items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] backdrop-blur-sm">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span className="text-slate-300">Buzzer (&ge;70)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span className="text-slate-300">Suspicious (40-69)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span className="text-slate-300">Organik (&lt;40)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
