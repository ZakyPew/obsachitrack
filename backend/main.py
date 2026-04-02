from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import asyncio
import logging

from database import SessionLocal, engine, Base
from auth.steam import steam_router
from routers.avatar import router as avatar_router
from services.avatar_queue import avatar_queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all database tables
Base.metadata.create_all(bind=engine)

# Background task reference
queue_processor_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    global queue_processor_task
    
    # Startup: Start the avatar queue processor
    logger.info("🎬 Starting avatar queue processor...")
    queue_processor_task = asyncio.create_task(avatar_queue.process_queue())
    logger.info("✅ Avatar queue processor started")
    
    yield
    
    # Shutdown: Clean up
    logger.info("🛑 Shutting down avatar queue processor...")
    avatar_queue.stop()
    if queue_processor_task:
        queue_processor_task.cancel()
        try:
            await queue_processor_task
        except asyncio.CancelledError:
            pass
    logger.info("✅ Avatar queue processor stopped")


app = FastAPI(
    title="StreamTracker Web", 
    version="1.0.0",
    lifespan=lifespan,
    description="StreamTracker API with avatar burst mode support"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(steam_router, prefix="/auth", tags=["auth"])
app.include_router(avatar_router, tags=["avatar"])

@app.get("/")
def root():
    return {
        "message": "StreamTracker Web API", 
        "version": "1.0.0",
        "features": [
            "Steam authentication",
            "Avatar burst mode",
            "WebSocket real-time updates"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "queue_status": avatar_queue.get_queue_status()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
