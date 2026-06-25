"use client";

import { useEffect, useState } from "react";

interface Props {
  label: string;
  score: number;
  reasoning?: string;
}

const TONE_COLOURS: Record<string, string> = {
  "neutral": "#10B981",
  "positive": "#3B82F6",
  "moderately charged": "#F59E0B",
  "highly charged": "#EF4444",
};

export default function ToneMeter({ label, score, reasoning }: Props) {
  const [animated, setAnimated] = useState(false);
  const colour = TONE_COLOURS[label] ?? "#10B981";
  const percentage = Math.round(score * 100);

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-medium tracking-widest uppercase"
          style={{ color: "var(--lead)" }}>
          Emotional Tone
        </span>
        <span className="mono text-sm font-medium px-2 py-0.5 rounded"
          style={{ backgroundColor: `${colour}18`, color: colour }}>
          {label} · {percentage}%
        </span>
      </div>

      {/* Bar */}
      <div className="h-2 rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--border)" }}>
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: animated ? `${percentage}%` : "0%",
            backgroundColor: colour
          }}
        />
      </div>

      <div className="flex justify-between mt-2">
        <span className="mono text-xs" style={{ color: "var(--lead)" }}>Neutral</span>
        <span className="mono text-xs" style={{ color: "var(--lead)" }}>Highly charged</span>
      </div>

      {reasoning && (
        <p className="text-xs mt-3 italic" style={{ color: "var(--lead)" }}>
          {reasoning}
        </p>
      )}
    </div>
  );
}