from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.analyse import router as analyse_router
import logging

# Configure logging so we can see what's happening in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="NewsLens API",
    description="AI-powered news bias and credibility analyser",
    version="0.1.0"
)

# CORS — Cross Origin Resource Sharing
# This allows your frontend (running on localhost:3000)
# to talk to your backend (running on localhost:8000)
# Without this, browsers block the requests as a security measure
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",         # Local development
        "https://newslens.vercel.app",   # Production (update when deployed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analyse_router, prefix="/api", tags=["Analysis"])


@app.get("/health")
async def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "ok", "service": "NewsLens API"} 
