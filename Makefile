.PHONY: test pytest pytest-v coverage backend-shell frontend-shell shell

# Default target
all: test

# Run all tests
test:
	@echo "Running all tests..."
	./backend/venv/bin/python -m pytest backend/tests/

# Run pytest with optional args
pytest:
	@echo "Running pytest..."
	./backend/venv/bin/python -m pytest backend/tests/ $(ARGS)

# Run pytest with verbose output
pytest-v:
	@echo "Running pytest with verbose output..."
	./backend/venv/bin/python -m pytest backend/tests/ -v $(ARGS)

# Run coverage report
coverage:
	@echo "Running tests with coverage..."
	./backend/venv/bin/python -m pytest --cov=app --cov-report=html backend/tests/
	@echo "Coverage report generated: htmlcov/index.html"

# Drop into backend shell with venv activated
backend-shell:
	@echo "Activating backend venv and starting shell..."
	cd backend && source venv/bin/activate && exec $$SHELL

# Run frontend tests
frontend-test:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Run frontend lint
frontend-lint:
	@echo "Running frontend lint..."
	cd frontend && npm run lint

# Run backend lint
backend-lint:
	@echo "Running backend lint..."
	./backend/venv/bin/ruff check backend/
	./backend/venv/bin/mypy backend/

# Run all linters
lint: backend-lint frontend-lint

# Format code
format:
	@echo "Formatting code..."
	./backend/venv/bin/black backend/
	./backend/venv/bin/ruff check --fix backend/
	cd frontend && npm run format

# Install dependencies
install:
	@echo "Installing dependencies..."
	./backend/venv/bin/python -m pip install -e backend/
	cd frontend && npm install

# Database migration
migrate:
	@echo "Running database migrations..."
	cd backend && ./venv/bin/alembic upgrade head

# Rollback database migration
rollback:
	@echo "Rolling back last migration..."
	cd backend && ./venv/bin/alembic downgrade -1

# Development server
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && ./venv/bin/python -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
