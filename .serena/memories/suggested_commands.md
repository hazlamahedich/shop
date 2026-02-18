# Suggested Commands

## Infrastructure

```bash
# Start Docker containers (PostgreSQL on port 5433, Redis on 6379)
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f
```

## Backend Development

```bash
# Setup (first time)
cd backend
pip install -e ".[dev,test]"

# Run development server
./venv/bin/python -m uvicorn app.main:app --reload --port 8000
# OR via Makefile:
make dev-backend

# Run tests
./venv/bin/python -m pytest
# OR:
make pytest

# Run tests with coverage
./venv/bin/python -m pytest --cov=app --cov-report=html
# OR:
make coverage

# Run linting
./venv/bin/ruff check backend/
./venv/bin/mypy backend/
# OR:
make backend-lint

# Format code
./venv/bin/black backend/
./venv/bin/ruff check --fix backend/
# OR:
make format

# Database migrations
./venv/bin/alembic upgrade head      # Apply migrations
./venv/bin/alembic downgrade -1      # Rollback one migration
./venv/bin/alembic revision -m "description"  # Create new migration
# OR via Makefile:
make migrate
make rollback
```

## Frontend Development

```bash
# Setup (first time)
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Run tests
npm test
npm run test:coverage

# Linting
npm run lint
npm run lint:fix

# Format code
npm run format
```

## Makefile Shortcuts (from root)

```bash
make test          # Run all backend tests
make pytest        # Run pytest
make pytest-v      # Verbose pytest
make coverage      # Tests with coverage report
make lint          # Run all linters (backend + frontend)
make format        # Format all code
make dev           # Start both backend and frontend
make migrate       # Run database migrations
make install       # Install all dependencies
```

## Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Type Generation

```bash
# Generate TypeScript types from Pydantic schemas
python scripts/generate_types.py
```

## Test Colocation Validation

```bash
python scripts/validate_test_colocation.py
```

## Beads Task Management

```bash
bd ready              # Show tasks ready to work
bd list               # Show all open issues
bd show <id>          # View issue details
bd create "Task" -p 0 # Create P0 task
bd update <id> --status in_progress  # Claim task
bd close <id>         # Complete task
bd sync               # Sync with git remote
```

## Darwin (macOS) System Commands

Standard Unix commands available:
- `git`, `ls`, `cd`, `grep`, `find`, `cat`
- Note: Use `gsed` instead of `sed` for GNU sed behavior, or use `sed -i ''` for BSD sed
