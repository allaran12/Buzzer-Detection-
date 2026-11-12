"use client";

import { useMemo } from "react";
import { BuzzerAccount } from "@/types/buzzer";

type NetworkNode = {
  id: string;
  username: string;
  name?: string;
  avatar?: string;
  role?: "account" | "target";
  isHub?: boolean;
  isTargetOnly?: boolean;
  buzzerScore?: number;
  riskLevel?: "high" | "medium" | "low";
  inDegree?: number;
  outDegree?: number;
  degree?: number;
  pagerank?: number;
  componentSize?: number;
};

type NetworkEdge = {
  source: string;
  target: string;
  relationType: string;
  relationTypes?: string[];
  count?: number;
};

type Props = {
  accounts?: BuzzerAccount[];
  nodes?: NetworkNode[];
  edges?: NetworkEdge[];
};

type Position = { x: number; y: number };

type PositionedNode = NetworkNode & Position & { radius: number; labelVisible: boolean };

const WIDTH = 860;
const HEIGHT = 520;
const MAX_VISIBLE_NODES = 72;

function nodeColor(node: NetworkNode): string {
  if (node.isTargetOnly || node.role === "target") return "var(--primary)";
  if (node.riskLevel === "high") return "var(--accent-danger)";
  if (node.riskLevel === "medium") return "var(--accent-warn)";
  return "var(--accent-go)";
}

function edgeColor(relationType: string): string {
  if (relationType === "reply") return "var(--primary)";
  if (relationType === "quote") return "var(--accent-warn)";
  if (relationType === "retweet") return "var(--accent-danger)";
  return "var(--muted-foreground)";
}

function layoutNodes(nodes: NetworkNode[], edges: NetworkEdge[]): PositionedNode[] {
  const selectedNodes = [...nodes]
    .sort((firstNode, secondNode) => {
      const firstRank = Number(firstNode.degree ?? ((firstNode.inDegree ?? 0) + (firstNode.outDegree ?? 0)));
      const secondRank = Number(secondNode.degree ?? ((secondNode.inDegree ?? 0) + (secondNode.outDegree ?? 0)));
      return (secondNode.isHub ? 1 : 0) - (firstNode.isHub ? 1 : 0) || secondRank - firstRank;
    })
    .slice(0, MAX_VISIBLE_NODES);
  const selectedIds = new Set(selectedNodes.map((node) => node.id));
  const visibleEdges = edges.filter((edge) => selectedIds.has(edge.source) && selectedIds.has(edge.target));
  const center = { x: WIDTH / 2, y: HEIGHT / 2 - 4 };
  const positions = new Map<string, Position>();
  const hub = selectedNodes.find((node) => node.isHub) ?? selectedNodes[0];

  selectedNodes.forEach((node, index) => {
    if (hub && node.id === hub.id) {
      positions.set(node.id, center);
      return;
    }
    const angle = (index / Math.max(selectedNodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const ring = 115 + (index % 3) * 40;
    positions.set(node.id, {
      x: center.x + Math.cos(angle) * Math.min(ring, 315),
      y: center.y + Math.sin(angle) * Math.min(ring, 180),
    });
  });

  const adjacency = new Map<string, string[]>();
  visibleEdges.forEach((edge) => {
    adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), edge.target]);
    adjacency.set(edge.target, [...(adjacency.get(edge.target) ?? []), edge.source]);
  });

  for (let iteration = 0; iteration < 56; iteration += 1) {
    const movement = new Map<string, { x: number; y: number }>();
    selectedNodes.forEach((node) => movement.set(node.id, { x: 0, y: 0 }));
    for (let firstIndex = 0; firstIndex < selectedNodes.length; firstIndex += 1) {
      for (let secondIndex = firstIndex + 1; secondIndex < selectedNodes.length; secondIndex += 1) {
        const firstNode = selectedNodes[firstIndex];
        const secondNode = selectedNodes[secondIndex];
        const firstPosition = positions.get(firstNode.id);
        const secondPosition = positions.get(secondNode.id);
        if (!firstPosition || !secondPosition) continue;
        const deltaX = firstPosition.x - secondPosition.x;
        const deltaY = firstPosition.y - secondPosition.y;
        const distance = Math.max(Math.hypot(deltaX, deltaY), 12);
        const force = 1750 / (distance * distance);
        const offsetX = (deltaX / distance) * force;
        const offsetY = (deltaY / distance) * force;
        movement.get(firstNode.id)!.x += offsetX;
        movement.get(firstNode.id)!.y += offsetY;
        movement.get(secondNode.id)!.x -= offsetX;
        movement.get(secondNode.id)!.y -= offsetY;
      }
    }
    visibleEdges.forEach((edge) => {
      const sourcePosition = positions.get(edge.source);
      const targetPosition = positions.get(edge.target);
      if (!sourcePosition || !targetPosition) return;
      const deltaX = targetPosition.x - sourcePosition.x;
      const deltaY = targetPosition.y - sourcePosition.y;
      const distance = Math.max(Math.hypot(deltaX, deltaY), 1);
      const force = (distance - 105) * 0.012;
      const offsetX = (deltaX / distance) * force;
      const offsetY = (deltaY / distance) * force;
      movement.get(edge.source)!.x += offsetX;
      movement.get(edge.source)!.y += offsetY;
      movement.get(edge.target)!.x -= offsetX;
      movement.get(edge.target)!.y -= offsetY;
    });
    selectedNodes.forEach((node) => {
      if (hub && node.id === hub.id) return;
      const position = positions.get(node.id)!;
      const deltaX = center.x - position.x;
      const deltaY = center.y - position.y;
      const adjustment = movement.get(node.id)!;
      const connectedPull = (adjacency.get(node.id)?.length ?? 0) > 0 ? 0.003 : 0.009;
      position.x = Math.max(34, Math.min(WIDTH - 34, position.x + adjustment.x + deltaX * connectedPull));
      position.y = Math.max(46, Math.min(HEIGHT - 54, position.y + adjustment.y + deltaY * connectedPull));
    });
  }

  const labelIds = new Set(
    selectedNodes
      .slice()
      .sort((firstNode, secondNode) => (secondNode.degree ?? 0) - (firstNode.degree ?? 0))
      .slice(0, 9)
      .map((node) => node.id),
  );
  return selectedNodes.map((node) => {
    const position = positions.get(node.id) ?? center;
    const degree = Number(node.degree ?? ((node.inDegree ?? 0) + (node.outDegree ?? 0)));
    const score = Math.max(0, Math.min(100, Number(node.buzzerScore ?? 0)));
    return {
      ...node,
      ...position,
      radius: node.isHub ? 25 : Math.max(7, Math.min(21, 7 + Math.sqrt(degree) * 2 + score / 36)),
      labelVisible: labelIds.has(node.id) || Boolean(node.isHub),
    };
  });
}

function displayHandle(username: string): string {
  const handle = `@${username.replace(/^@/, "")}`;
  return handle.length > 18 ? `${handle.slice(0, 16)}...` : handle;
}

export default function HeroNetworkPreview({ accounts = [], nodes, edges = [] }: Props) {
  const graphNodes = useMemo<NetworkNode[]>(() => nodes?.length ? nodes : accounts.map((account) => ({
    id: account.id,
    username: account.username,
    name: account.name,
    avatar: account.avatar,
    buzzerScore: account.buzzerScore,
    riskLevel: account.riskLevel,
    inDegree: account.inDegree,
    outDegree: account.outDegree,
    degree: account.totalDegree ?? account.outDegree,
    componentSize: account.componentSize,
  })), [accounts, nodes]);
  const positionedNodes = useMemo(() => layoutNodes(graphNodes, edges), [edges, graphNodes]);
  const nodeById = useMemo(() => new Map(positionedNodes.map((node) => [node.id, node])), [positionedNodes]);
  const visibleEdges = edges.filter((edge) => nodeById.has(edge.source) && nodeById.has(edge.target));
  const hub = positionedNodes.find((node) => node.isHub);

  return (
    <div className="relative h-full min-h-[360px] w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[radial-gradient(circle_at_50%_44%,rgba(37,99,235,0.12),transparent_42%),linear-gradient(135deg,var(--card-subtle),var(--card))]">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-full w-full" role="img" aria-label="Graf relasi akun pada sampel live">
        <defs>
          <pattern id="network-dots" width="22" height="22" patternUnits="userSpaceOnUse">
            <circle cx="1.5" cy="1.5" r="1" fill="var(--border)" opacity="0.55" />
          </pattern>
          <marker id="network-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L7,3.5 L0,7 z" fill="var(--muted-foreground)" opacity="0.72" />
          </marker>
          <filter id="network-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width={WIDTH} height={HEIGHT} fill="url(#network-dots)" />
        {hub && <circle cx={hub.x} cy={hub.y} r="46" fill="none" stroke="var(--accent-danger)" strokeDasharray="4 8" opacity="0.45" />}
        {visibleEdges.map((edge) => {
          const source = nodeById.get(edge.source);
          const target = nodeById.get(edge.target);
          if (!source || !target) return null;
          const stroke = edgeColor(edge.relationType);
          const width = Math.min(4, 1 + Number(edge.count ?? 1) * 0.55);
          return (
            <g key={`${edge.source}-${edge.target}-${edge.relationType}`}>
              <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke={stroke} strokeWidth={width} opacity="0.42" markerEnd="url(#network-arrow)" />
              {Number(edge.count ?? 1) > 1 && <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 4} textAnchor="middle" fill="var(--muted-foreground)" fontSize="9">{edge.count}x</text>}
            </g>
          );
        })}
        {positionedNodes.map((node) => {
          const score = Math.round(Number(node.buzzerScore ?? 0));
          return (
            <g key={node.id}>
              <title>{`${displayHandle(node.username)} · ${node.role === "target" ? "target" : `${score}/100`}`}</title>
              {node.isHub && <circle cx={node.x} cy={node.y} r={node.radius + 8} fill="none" stroke="var(--accent-danger)" strokeWidth="2" opacity="0.85" filter="url(#network-glow)" />}
              <circle cx={node.x} cy={node.y} r={node.radius} fill={nodeColor(node)} opacity="0.94" stroke="var(--card)" strokeWidth="2" />
              {node.role !== "target" && <text x={node.x} y={node.y + 4} textAnchor="middle" fill="white" fontSize={node.radius > 14 ? 10 : 8} fontWeight="800">{score}</text>}
              {node.labelVisible && <text x={node.x} y={node.y + node.radius + 15} textAnchor="middle" fill="var(--foreground)" fontSize="10" fontWeight="700">{displayHandle(node.username)}</text>}
            </g>
          );
        })}
        {positionedNodes.length === 0 && <text x={WIDTH / 2} y={HEIGHT / 2} textAnchor="middle" fill="var(--muted-foreground)" fontSize="14">Belum ada relasi pada sampel live</text>}
      </svg>
      <div className="pointer-events-none absolute left-3 top-3 rounded-lg border border-[var(--border)] bg-[var(--card)]/85 px-3 py-2 text-[10px] leading-5 text-[var(--muted-foreground)] backdrop-blur-sm">
        <div className="mb-1 font-bold uppercase tracking-[0.16em] text-[var(--foreground)]">Legenda graf</div>
        <div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[var(--accent-danger)]" />Akun risiko tinggi</div>
        <div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[var(--primary)]" />Target/hub relasi</div>
        <div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[var(--accent-go)]" />Akun risiko rendah</div>
      </div>
      <div className="absolute bottom-3 right-3 rounded-lg border border-[var(--border)] bg-[var(--card)]/85 px-3 py-2 text-right text-[10px] text-[var(--muted-foreground)] backdrop-blur-sm">
        <div>{positionedNodes.length} node terlihat · {visibleEdges.length} edge</div>
        <div className="font-semibold text-[var(--foreground)]">Ukuran node = degree relasi</div>
      </div>
    </div>
  );
}
