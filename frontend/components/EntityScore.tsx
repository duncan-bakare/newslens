interface Props {
  score: number;
}

export default function EntityScore({ score }: Props) {
  const percentage = Math.round(score * 100);

  // Interpret the density score for the user
  const interpretation =
    percentage > 15 ? "Fact-dense" :
    percentage > 8  ? "Mixed" :
                      "Opinion-heavy";

  const colour =
    percentage > 15 ? "#10B981" :
    percentage > 8  ? "#F59E0B" :
                      "#EF4444";

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium tracking-widest uppercase"
        style={{ color: "var(--lead)" }}>
        Factual Density
      </span>
      <div className="flex items-baseline gap-2">
        <span className="mono text-3xl font-medium"
          style={{ color: colour }}>
          {percentage}%
        </span>
        <span className="text-sm" style={{ color: "var(--lead)" }}>
          {interpretation}
        </span>
      </div>
    </div>
  );
}