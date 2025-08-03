from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
from app.database.config import engine
from app.models import models
from app.api import worlds, characters, discussions, websocket_discussions

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
app.include_router(websocket_discussions.router)

@app.get("/")
async def root():
    return {"message": "TinyTroupe Brainstorming API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)