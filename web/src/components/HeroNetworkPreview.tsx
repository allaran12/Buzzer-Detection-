"use client";

import { BuzzerAccount } from "@/types/buzzer";

type NetworkEdge = { source: string; target: string; relationType: string };

type Props = {
  accounts?: BuzzerAccount[];
  edges?: NetworkEdge[];
};

function nodeColor(account: BuzzerAccount): string {
  if (account.riskLevel === "high") return "var(--accent-danger)";
  if (account.riskLevel === "medium") return "var(--accent-warn)";
  return "var(--accent-go)";
}

function layoutNodes(accounts: BuzzerAccount[]) {
  const centerX = 240;
  const centerY = 185;
  const radius = Math.min(145, Math.max(72, accounts.length * 17));
  return accounts.map((account, index) => {
    const angle = accounts.length === 1 ? -Math.PI / 2 : (index / accounts.length) * Math.PI * 2 - Math.PI / 2;
    const score = Math.max(0, Math.min(100, Number(account.buzzerScore) || 0));
    return {
      account,
      handle: `@${account.username.replace(/^@/, "")}`,
      score: Math.round(score),
      fill: nodeColor(account),
      r: Math.max(12, Math.min(23, 11 + score / 10)),
      cx: centerX + Math.cos(angle) * radius,
      cy: centerY + Math.sin(angle) * radius,
      pulse: index === 0 && account.riskLevel === "high",
    };
  });
}

export default function HeroNetworkPreview({ accounts = [], edges = [] }: Props) {
  const nodes = layoutNodes(accounts.slice(0, 20));
  const nodeById = new Map(nodes.map((node) => [node.account.id, node]));

  return (
    <div className="relative w-full h-full flex items-center justify-center select-none">
      <svg
        viewBox="0 0 480 380"
        className="w-full h-full"
        aria-label="Network graph preview of coordinated accounts"
        role="img"
      >
        <defs>
          {/* Subtle dot grid pattern */}
          <pattern id="grid-dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.8" fill="var(--border)" opacity="0.5" />
          </pattern>

          {/* Pulse animation keyframes */}
          <style>{`
            @keyframes svgPulse {
              0%   { r: 28; opacity: 0.6; }
              70%  { r: 42; opacity: 0;   }
              100% { r: 42; opacity: 0;   }
            }
            .pulse-ring {
              animation: svgPulse 2.2s ease-out infinite;
            }
          `}</style>
        </defs>

        {/* Background grid */}
        <rect width="480" height="380" fill="url(#grid-dots)" />

        {/* Edges */}
        {edges.map((edge, index) => {
          const source = nodeById.get(edge.source);
          const target = nodeById.get(edge.target);
          if (!source || !target) return null;
          const highRisk = source.account.riskLevel === "high" || target.account.riskLevel === "high";
          return (
            <line
              key={`${edge.source}-${edge.target}-${edge.relationType}-${index}`}
              x1={source.cx}
              y1={source.cy}
              x2={target.cx}
              y2={target.cy}
              stroke={highRisk ? "var(--accent-danger)" : "var(--border)"}
              strokeWidth={highRisk ? 1.5 : 1}
              opacity={highRisk ? 0.5 : 0.4}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g key={node.handle}>
            {/* Pulsing ring for the highest-score node */}
            {node.pulse && (
              <circle
                cx={node.cx}
                cy={node.cy}
                r={node.r + 6}
                fill="none"
                stroke="var(--accent-danger)"
                strokeWidth="1.5"
                className="pulse-ring"
              />
            )}

            {/* Main circle */}
            <circle
              cx={node.cx}
              cy={node.cy}
              r={node.r}
              fill={node.fill}
            />

            {/* Score inside node */}
            <text
              x={node.cx}
              y={node.cy + 4}
              textAnchor="middle"
              fill="white"
              fontWeight="bold"
              fontSize={node.r >= 18 ? 11 : 9}
              fontFamily="'Plus Jakarta Sans', sans-serif"
            >
              {node.score}
            </text>

            {/* Handle below node */}
            <text
              x={node.cx}
              y={node.cy + node.r + 13}
              textAnchor="middle"
              fill="var(--muted-foreground)"
              fontSize="9"
              fontFamily="'Inter', sans-serif"
            >
              {node.handle}
            </text>
          </g>
        ))}

        {nodes.length === 0 && (
          <text x="240" y="190" textAnchor="middle" fill="var(--muted-foreground)" fontSize="13">
            Belum ada relasi pada sampel live
          </text>
        )}
      </svg>
    </div>
  );
}
