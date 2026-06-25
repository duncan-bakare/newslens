import { AnalysisResult } from "@/lib/api";
import BiasSpectrum from "./BiasSpectrum";
import ToneMeter from "./ToneMeter";
import EntityScore from "./EntityScore";

interface Props {
  result: AnalysisResult;
}

export default function Scorecard({ result }: Props) {
  const date = new Date(result.analysed_at).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric"
  });

  return (
    <div className="w-full max-w-2xl mx-auto">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <span className="mono text-xs px-2 py-0.5 rounded font-medium"
            style={{
              backgroundColor: "var(--ink)",
              color: "var(--paper)"
            }}>
            {result.source}
          </span>
          <span className="mono text-xs" style={{ color: "var(--lead)" }}>
            {date}
          </span>
          {result.cached && (
            <span className="mono text-xs" style={{ color: "var(--lead)" }}>
              · cached
            </span>
          )}
        </div>

        <h1 className="text-xl font-semibold leading-snug" style={{ color: "var(--ink)" }}>
          {result.headline}
        </h1>
      </div>

      {/* Scorecard panel */}
      <div className="rounded-2xl p-8 mb-6"
        style={{ backgroundColor: "white", border: "1px solid var(--border)" }}>
        <div className="flex flex-col gap-8">
          <BiasSpectrum
            label={result.bias.label}
            confidence={result.bias.confidence}
            reasoning={result.bias.reasoning}
          />
          <div style={{ borderTop: "1px solid var(--border)" }} />
          <ToneMeter
            label={result.tone.label}
            score={result.tone.score}
            reasoning={result.tone.reasoning}
          />
          <div style={{ borderTop: "1px solid var(--border)" }} />
          <EntityScore score={result.entity_density} />
        </div>
      </div>

      {/* Neutral summary */}
      <div className="rounded-2xl p-8"
        style={{ backgroundColor: "white", border: "1px solid var(--border)" }}>
        <span className="text-xs font-medium tracking-widest uppercase block mb-4"
          style={{ color: "var(--lead)" }}>
          Neutral Summary
        </span>
        <p className="text-base leading-relaxed" style={{ color: "var(--ink)" }}>
          {result.summary}
        </p>
        <p className="text-xs mt-4" style={{ color: "var(--lead)" }}>
          Rewritten by AI to remove framing and emotional language.
        </p>
      </div>

      {/* Source link */}
      <div className="mt-6 text-center">
        <a href={result.url} target="_blank" rel="noopener noreferrer"
          className="mono text-xs underline underline-offset-4"
          style={{ color: "var(--lead)" }}>
          View original article →
        </a>
      </div>
    </div>
  );
}