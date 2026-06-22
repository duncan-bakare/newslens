"use client";

import { useState } from "react";
import { analyseArticle, AnalysisResult } from "@/lib/api";
import Scorecard from "@/components/Scorecard";

type State = "idle" | "loading" | "result" | "error";

export default function Home() {
  const [url, setUrl] = useState("");
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>("");

  async function handleAnalyse() {
    if (!url.trim()) return;

    setState("loading");
    setError("");
    setResult(null);

    try {
      const data = await analyseArticle(url.trim());
      setResult(data);
      setState("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setState("error");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleAnalyse();
  }

  function handleReset() {
    setState("idle");
    setResult(null);
    setUrl("");
    setError("");
  }

  return (
    <main className="min-h-screen px-4 py-16"
      style={{ backgroundColor: "var(--paper)" }}>

      {/* Logo / wordmark */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: "var(--signal)" }}>
            <span className="text-white font-bold text-sm">N</span>
          </div>
          <span className="font-semibold text-lg tracking-tight"
            style={{ color: "var(--ink)" }}>
            NewsLens
          </span>
        </div>

        {state === "idle" || state === "error" ? (
          <>
            <h2 className="text-3xl font-bold tracking-tight mb-3"
              style={{ color: "var(--ink)" }}>
              Understand what you read.
            </h2>
            <p className="text-base max-w-md mx-auto"
              style={{ color: "var(--lead)" }}>
              Paste any news article URL. Get an instant bias score,
              tone analysis, and neutral summary.
            </p>
          </>
        ) : state === "loading" ? (
          <p className="text-base" style={{ color: "var(--lead)" }}>
            Analysing article...
          </p>
        ) : null}
      </div>

      {/* Input */}
      {(state === "idle" || state === "loading" || state === "error") && (
        <div className="max-w-2xl mx-auto mb-8">
          <div className="flex gap-3">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="https://www.bbc.com/news/..."
              disabled={state === "loading"}
              className="flex-1 px-4 py-3 rounded-xl text-sm outline-none transition-all"
              style={{
                backgroundColor: "white",
                border: "1px solid var(--border)",
                color: "var(--ink)",
                fontFamily: "inherit",
              }}
            />
            <button
              onClick={handleAnalyse}
              disabled={state === "loading" || !url.trim()}
              className="px-6 py-3 rounded-xl text-sm font-medium transition-all"
              style={{
                backgroundColor: state === "loading" ? "var(--border)" : "var(--signal)",
                color: state === "loading" ? "var(--lead)" : "white",
                cursor: state === "loading" ? "not-allowed" : "pointer",
                border: "none",
              }}
            >
              {state === "loading" ? "Analysing..." : "Analyse"}
            </button>
          </div>

          {/* Error message */}
          {state === "error" && (
            <p className="mt-3 text-sm px-4 py-3 rounded-xl"
              style={{
                backgroundColor: "#FEF2F2",
                color: "#EF4444",
                border: "1px solid #FECACA"
              }}>
              {error}. Check the URL and try again.
            </p>
          )}
        </div>
      )}

      {/* Results */}
      {state === "result" && result && (
        <div className="max-w-2xl mx-auto">
          {/* Analyse another */}
          <div className="flex gap-3 mb-8">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="https://www.bbc.com/news/..."
              className="flex-1 px-4 py-3 rounded-xl text-sm outline-none"
              style={{
                backgroundColor: "white",
                border: "1px solid var(--border)",
                color: "var(--ink)",
                fontFamily: "inherit",
              }}
            />
            <button
              onClick={handleAnalyse}
              className="px-6 py-3 rounded-xl text-sm font-medium"
              style={{
                backgroundColor: "var(--signal)",
                color: "white",
                border: "none",
                cursor: "pointer"
              }}
            >
              Analyse
            </button>
          </div>

          <Scorecard result={result} />

          <div className="text-center mt-8">
            <button onClick={handleReset}
              className="mono text-xs underline underline-offset-4"
              style={{ color: "var(--lead)", background: "none", border: "none", cursor: "pointer" }}>
              ← Start over
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {state === "loading" && (
        <div className="max-w-2xl mx-auto">
          <div className="rounded-2xl p-8 animate-pulse"
            style={{ backgroundColor: "white", border: "1px solid var(--border)" }}>
            <div className="h-4 rounded mb-4 w-3/4"
              style={{ backgroundColor: "var(--border)" }} />
            <div className="h-4 rounded mb-8 w-1/2"
              style={{ backgroundColor: "var(--border)" }} />
            <div className="h-2 rounded mb-8"
              style={{ backgroundColor: "var(--border)" }} />
            <div className="h-2 rounded mb-8"
              style={{ backgroundColor: "var(--border)" }} />
            <div className="h-16 rounded"
              style={{ backgroundColor: "var(--border)" }} />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center mt-16">
        <p className="mono text-xs" style={{ color: "var(--border)" }}>
          NewsLens · AI-powered · Built with FastAPI + Next.js
        </p>
      </div>
    </main>
  );
}