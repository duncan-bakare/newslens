 # NewsLens — AI-Powered News Bias & Credibility Analyser

Understand the bias, tone, and credibility of any news article in seconds.

**Live demo:** [https://newslens-tawny.vercel.app](https://newslens-tawny.vercel.app)

## Demo

![NewsLens Demo](newslensdemo.gif)

## The Problem

Every day, millions of people read news articles and unconsciously absorb the framing, tone, and bias baked into them. Most readers can't tell the difference between a factually dense report and an emotionally charged opinion piece dressed up as news.

NewsLens solves this by providing instant, visual credibility analysis.

## What It Does

Paste any news article URL. Get:

- **Political Lean Spectrum** — left-wing to right-wing with confidence scoring
- **Emotional Tone Analysis** — neutral to highly charged, with reasoning
- **Factual Density Score** — ratio of facts to opinion language
- **Neutral Summary** — AI-rewritten summary stripped of framing and bias

## How It Works

User pastes URL
↓
Backend scrapes article (newspaper3k)
↓
Three parallel Claude analyses:
• Zero-shot bias classification
• Sentiment + tone detection
• Neutral summarisation (BART-style)
↓
Results cached in Supabase
↓
Frontend renders interactive scorecard

## Architecture

┌─────────────────────────────────┐
│   Frontend (Next.js + React)    │
│   • TypeScript + Tailwind CSS   │
│   • Animated bias spectrum      │
│   • Deployed on Vercel          │
└────────────┬────────────────────┘
│ HTTP
┌────────────▼────────────────────┐
│   Backend (FastAPI + Python)    │
│   • Article scraping            │
│   • Claude AI pipeline          │
│   • Deployed on Railway         │
└────────────┬────────────────────┘
│
┌────────┴────────┐
▼                 ▼
┌─────────┐    ┌──────────────┐
│Supabase │    │ Anthropic    │
│ Cache   │    │ Claude Haiku  │
└─────────┘    └──────────────┘

## Tech Stack

**Frontend**
- Next.js 16 with TypeScript
- Tailwind CSS for styling
- Animated React components (Framer Motion via CSS)
- Deployed on Vercel

**Backend**
- FastAPI with Python 3.11
- newspaper3k for article extraction
- Anthropic Claude Haiku for AI analysis
- Supabase (PostgreSQL) for caching
- Deployed on Railway

**AI Models**
- Claude Haiku 4.5 (bias, tone, summarisation)
- Custom zero-shot prompts for political lean
- Entity density heuristic for factual scoring

## Getting Started

### Local Development

**Prerequisites**
- Node.js 18+
- Python 3.11+
- Git

**1. Clone and setup**
```bash
git clone https://github.com/yourusername/newslens.git
cd newslens
```

**2. Backend setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `.env` in the project root:


# Supabase
SUPABASE_URL=https://vemxkcvzlaxasbptdxbt.supabase.co
SUPABASE_KEY=sb_publishable_TYJCsBlQwlumPfVcawTEYg_OshMREd0

Run the backend:
```bash
uvicorn backend.main:app --reload
# Runs on http://localhost:8000
```

**3. Frontend setup**
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

**4. Test it**
Open http://localhost:3000 and paste a news article URL.

### Production Deployment

**Backend (Railway)**
- Connected to GitHub, auto-deploys on push
- Environment variables set in Railway dashboard
- Health check: `GET /health`

**Frontend (Vercel)**
- Connected to GitHub, auto-deploys on push
- `NEXT_PUBLIC_API_URL` points to Railway backend
- Automatic HTTPS, global CDN

## Key Engineering Decisions

### Why Claude Haiku instead of open-source models?
- Network constraints made HuggingFace inference API inaccessible
- Claude Haiku is 10x cheaper than Sonnet for classification tasks
- Prompt engineering gives more control than fixed zero-shot models
- Better reasoning for detecting subtle bias and framing

### Why Supabase caching?
- Dramatically improves UX for repeated articles (instant results)
- Reduces API costs by ~90% on cache hits
- Simple PostgreSQL schema with URL as unique key
- Free tier sufficient for portfolio use

### Why separate frontend/backend?
- Decoupled architecture enables:
  - Swapping UI without touching ML logic
  - Scaling backend independently
  - Clear separation of concerns
- Production-ready pattern used in all real companies

## Limitations & Future Work

**Current limitations**
- Paywalled sites cannot be scraped
- JavaScript-rendered pages not supported (static scraping only)
- Bias scoring is heuristic-based, not trained on labelled data

**Potential improvements**
- Browser extension for one-click analysis
- Article comparison (side-by-side bias analysis)
- Historical tracking (how does outlet bias change over time?)
- Fine-tuned bias classifier on journalistic dataset
- Fact-check integration with external fact-checkers

## Learning Outcomes

This project demonstrates:
- Full-stack AI application architecture
- LLM prompt engineering and structured outputs
- Production Python web development (FastAPI, async)
- Modern frontend with TypeScript and React
- Cloud deployment (Vercel, Railway, Supabase)
- Git workflows and collaborative development practices

## License

MIT — feel free to fork and build on this.

## Questions?

Feel free to reach out on LinkedIn, Github or wherever you can get a hold of me!