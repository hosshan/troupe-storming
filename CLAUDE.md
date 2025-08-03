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

## Documentation

Detailed technical documentation is available in the `docs/` directory:

- **docs/ARCHITECTURE.md**: Complete code structure analysis, including discussion implementation approaches (REST API, Server-Sent Events, WebSocket) and component responsibilities
- **docs/REFACTOR_PLAN.md**: Refactoring strategy for eliminating code duplication, with specific examples of redundant implementations and integration recommendations

**Note**: The codebase currently has some duplicate implementations for discussion functionality that should be consolidated according to the refactoring plan.

## Git Commit Guidelines

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

### Commit Message Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: A new feature for the user
- **fix**: A bug fix for the user
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries

### Scopes (optional)
- **backend**: Backend/API changes
- **frontend**: Frontend/UI changes
- **docs**: Documentation changes
- **config**: Configuration changes
- **deps**: Dependency changes

### Examples
```bash
feat(backend): add WebSocket support for real-time discussion updates
fix(frontend): resolve infinite loading issue in discussion results page
docs: add code architecture documentation
refactor(backend): consolidate duplicate discussion generation methods
chore(deps): update TinyTroupe to latest version
```

### Commit Strategy
- Commit meaningful units of work frequently
- Each commit should represent a complete, working change
- Use descriptive commit messages that explain the "why" not just the "what"
- Break large changes into smaller, logical commits