"use client";

export default function HeroNetworkPreview() {
  const nodes = [
    { handle: "@WempiF90099",      score: 92, fill: "var(--accent-danger)", r: 22, cx: 240, cy: 140, pulse: true },
    { handle: "@cyber_indojaya99", score: 89, fill: "var(--accent-danger)", r: 20, cx: 160, cy: 200, pulse: false },
    { handle: "@buzzer_senter07",  score: 84, fill: "var(--accent-danger)", r: 18, cx: 320, cy: 210, pulse: false },
    { handle: "@Uniliswara0",      score: 68, fill: "var(--accent-warn)",   r: 16, cx: 200, cy: 280, pulse: false },
    { handle: "@notnamern",        score: 54, fill: "var(--accent-warn)",   r: 14, cx: 350, cy: 140, pulse: false },
    { handle: "@naraeraa",         score: 22, fill: "var(--accent-go)",     r: 12, cx: 120, cy: 100, pulse: false },
    { handle: "@ccaramelh2h",      score: 34, fill: "var(--accent-go)",     r: 12, cx: 380, cy: 290, pulse: false },
    { handle: "@BuchroniK",        score: 28, fill: "var(--accent-go)",     r: 12, cx:  80, cy: 250, pulse: false },
  ];

  // Edges: [from-index, to-index, isHighRisk]
  const edges: [number, number, boolean][] = [
    [0, 1, true],
    [0, 2, true],
    [1, 2, true],
    [1, 3, false],
    [2, 4, false],
    [3, 7, false],
    [5, 7, false],
    [5, 6, false],
    [4, 6, false],
  ];

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
        {edges.map(([a, b, highRisk], i) => (
          <line
            key={i}
            x1={nodes[a].cx}
            y1={nodes[a].cy}
            x2={nodes[b].cx}
            y2={nodes[b].cy}
            stroke={highRisk ? "var(--accent-danger)" : "var(--border)"}
            strokeWidth={highRisk ? 1.5 : 1}
            opacity={highRisk ? 0.5 : 0.4}
          />
        ))}

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
      </svg>
    </div>
  );
}
