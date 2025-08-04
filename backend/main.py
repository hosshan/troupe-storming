from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import signal
import sys
import asyncio
from dotenv import load_dotenv
from app.database.config import engine
from app.models import models
from app.api import worlds, characters, discussions

# Load environment variables from .env file
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TinyTroupe Brainstorming API",
    description="Backend API for brainstorming application with TinyTroupe integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(worlds.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(discussions.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "TinyTroupe Brainstorming API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("Shutting down application...")
    # Clean up any active discussion streams
    from app.api.discussions import discussion_streams, active_connections
    discussion_streams.clear()
    active_connections.clear()
    print("Cleanup completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting TinyTroupe Brainstorming API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)