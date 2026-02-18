# Project Overview

## Purpose

AI-powered Shopping Assistant Bot for Facebook Messenger with optional e-commerce integration (Shopify optional).

## Tech Stack

### Backend
- **Language**: Python 3.11.7+
- **Framework**: FastAPI
- **Database**: PostgreSQL (async via asyncpg)
- **ORM**: SQLAlchemy 2.0 (with async support)
- **Migrations**: Alembic
- **Cache**: Redis
- **Validation**: Pydantic v2
- **Logging**: structlog
- **Rate Limiting**: slowapi

### Frontend
- **Language**: TypeScript 5.3+
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Testing**: Vitest (unit), Playwright (E2E)

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Pre-commit**: pre-commit framework

## Architecture

Monorepo structure with separate backend and frontend applications:

```
shop/
├── backend/               # Python/FastAPI backend
│   ├── app/              # Application code
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality (errors, config, database)
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic schemas (API contracts)
│   │   └── services/     # Business logic
│   ├── tests/            # Test suite (co-located pattern)
│   └── alembic/          # Database migrations
├── frontend/             # React/TypeScript frontend
│   └── src/
│       ├── components/   # React components
│       ├── stores/       # Zustand state management
│       ├── services/     # API clients
│       └── lib/types/    # Generated TypeScript types
├── scripts/              # Shared scripts
└── docs/                 # Documentation
```

## Key Features

- Optional E-Commerce (works with or without Shopify)
- FAQ & Business Info automated responses
- Human Handoff for complex queries
- Pluggable Provider Architecture (Shopify, extensible to others)
- Multiple LLM Provider Support (Ollama, OpenAI, Anthropic, Gemini)

## Task Management

- **Beads (bd)**: AI-native issue tracking with git-tracked JSONL files
- **BMad Method**: Structured AI-driven development workflows

See `AGENTS.md` for detailed task management workflow.
