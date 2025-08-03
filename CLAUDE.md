# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)
- **Start backend server**: `cd backend && python main.py` or `uvicorn main:app --reload --port 8000`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`
- **API documentation**: http://localhost:8000/docs (FastAPI auto-generated)
- **Health check**: http://localhost:8000/health

### Frontend (React/TypeScript)
- **Start development server**: `cd frontend && npm start`
- **Install dependencies**: `cd frontend && npm install`
- **Build for production**: `cd frontend && npm run build`
- **Run tests**: `cd frontend && npm test`

## Architecture Overview

This is a full-stack brainstorming application that integrates with Microsoft's TinyTroupe library for AI-powered character discussions.

### Core Components

**Backend (FastAPI + SQLAlchemy)**
- `backend/main.py`: FastAPI app with CORS middleware, router registration
- `backend/app/models/models.py`: SQLAlchemy models (World, Character, Discussion)
- `backend/app/services/tinytroupe_service.py`: Core TinyTroupe integration service
- `backend/app/api/`: REST API endpoints for worlds, characters, discussions
- Database: SQLite (`troupe_storming.db`)

**Frontend (React + Material-UI)**
- `frontend/src/pages/`: Main page components (WorldsPage, CharactersPage, DiscussionsPage)
- `frontend/src/services/api.ts`: Axios-based API client
- `frontend/src/types/index.ts`: TypeScript type definitions

### Key Architecture Patterns

**TinyTroupe Integration Flow**:
1. `TinyTroupeService` handles all AI agent creation and simulation
2. Fallback hierarchy: TinyTroupe → OpenAI Direct → Mock data
3. Characters converted to `TinyPerson` agents with defined personas
4. `TinyWorld` environments created for discussion contexts
5. Agent `.think()` and `.act()` methods drive conversations

**API Error Handling**:
- OpenAI quota/rate limit detection with graceful fallback
- Comprehensive logging throughout TinyTroupe operations
- Mock data generation when AI services unavailable

**Database Relationships**:
- World → Characters (one-to-many)
- World → Discussions (one-to-many)
- Discussion results stored as JSON in database

## Environment Setup

**Required Environment Variables**:
- `OPENAI_API_KEY`: Required for TinyTroupe functionality (create `backend/.env` file)

**TinyTroupe Dependencies**:
- Installed via Git: `git+https://github.com/microsoft/tinytroupe.git`
- Uses GPT-4o-mini model by default
- Requires OpenAI API access for AI-powered discussions

## Development Notes

- Backend runs on port 8000, frontend on port 3000
- CORS configured for localhost:3000 in FastAPI
- SQLAlchemy auto-creates tables on startup
- TinyTroupe service includes extensive logging for debugging AI interactions
- Frontend uses Material-UI components consistently
- React Router handles client-side routing