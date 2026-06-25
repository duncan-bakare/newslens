from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.analyse import router as analyse_router
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="NewsLens API",
    description="AI-powered news bias and credibility analyser",
    version="0.1.0"
)

# Build allowed origins from environment
allowed_origins = [
    "http://localhost:3000",
]

# Add production frontend URL if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse_router, prefix="/api", tags=["Analysis"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "NewsLens API"}