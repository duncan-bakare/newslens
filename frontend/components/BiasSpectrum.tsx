"use client";

import { useEffect, useState } from "react";

interface Props {
  label: string;
  confidence: number;
}

// Map bias labels to positions on the spectrum (0 = far left, 100 = far right)
const BIAS_POSITIONS: Record<string, number> = {
  "left-wing": 8,
  "centre-left": 28,
  "centre": 50,
  "centre-right": 72,
  "right-wing": 92,
};

const BIAS_COLOURS: Record<string, string> = {
  "left-wing": "#3B82F6",
  "centre-left": "#60A5FA",
  "centre": "#10B981",
  "centre-right": "#F87171",
  "right-wing": "#EF4444",
};

export default function BiasSpectrum({ label, confidence }: Props) {
  const [animated, setAnimated] = useState(false);
  const position = BIAS_POSITIONS[label] ?? 50;
  const colour = BIAS_COLOURS[label] ?? "#10B981";

  useEffect(() => {
    // Trigger animation after mount
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="w-full">
      {/* Label row */}
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-medium tracking-widest uppercase"
          style={{ color: "var(--lead)" }}>
          Political Lean
        </span>
        <span className="mono text-sm font-medium px-2 py-0.5 rounded"
          style={{
            backgroundColor: `${colour}18`,
            color: colour
          }}>
          {label} · {Math.round(confidence * 100)}%
        </span>
      </div>

      {/* Spectrum bar */}
      <div className="relative h-2 rounded-full overflow-visible"
        style={{
          background: "linear-gradient(to right, #3B82F6, #60A5FA, #10B981, #F87171, #EF4444)"
        }}>

        {/* Needle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 transition-all duration-700 ease-out"
          style={{ left: animated ? `${position}%` : "50%" }}
        >
          <div className="w-4 h-4 rounded-full border-2 border-white shadow-lg"
            style={{ backgroundColor: colour }} />
        </div>
      </div>

      {/* Axis labels */}
      <div className="flex justify-between mt-2">
        <span className="mono text-xs" style={{ color: "var(--lead)" }}>Left</span>
        <span className="mono text-xs" style={{ color: "var(--lead)" }}>Centre</span>
        <span className="mono text-xs" style={{ color: "var(--lead)" }}>Right</span>
      </div>
    </div>
  );
}