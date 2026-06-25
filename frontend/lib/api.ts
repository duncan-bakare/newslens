const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface BiasResult {
  label: string;
  confidence: number;
  reasoning?: string;
}

export interface ToneResult {
  label: string;
  score: number;
  reasoning?: string;
}

export interface AnalysisResult {
  url: string;
  headline: string;
  source: string;
  bias: BiasResult;
  tone: ToneResult;
  entity_density: number;
  summary: string;
  analysed_at: string;
  cached: boolean;
}

export interface ApiError {
  detail: string;
}

export async function analyseArticle(url: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/api/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
}