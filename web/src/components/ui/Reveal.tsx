"use client";

import type { ReactNode } from "react";
import { useInView } from "@/hooks/useInView";

export default function Reveal({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const { ref, isInView } = useInView<HTMLDivElement>();
  return (
    <div ref={ref} className={`reveal ${isInView ? "reveal-visible" : ""} ${className}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}
