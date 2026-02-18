# Task Completion Checklist

## After Code Changes

### 1. Run Quality Gates

```bash
# Backend
cd backend
./venv/bin/python -m pytest --cov=app
./venv/bin/ruff check .
./venv/bin/mypy .

# Frontend (if applicable)
cd frontend
npm test
npm run lint
npm run type-check
npm run build
```

Or use Makefile shortcuts:
```bash
make test
make lint
make format
```

### 2. Verify Coverage
- Backend: Coverage must be ≥80%
- Check `htmlcov/index.html` for detailed coverage report

### 3. Run Pre-commit (Optional)
```bash
pre-commit run --all-files
```

## After Tests Pass

### 1. Update Beads Task
```bash
bd close <task-id>
```

### 2. Sync and Push
```bash
bd sync
git add .
git commit -m "type: description"
git pull --rebase
git push
```

### 3. Verify Push
```bash
git status  # Must show "up to date with origin"
```

## Critical Rules

- **Work is NOT complete until `git push` succeeds**
- **NEVER stop before pushing** - stranded work is lost work
- **ALWAYS create Beads tasks for follow-up work**
- **Run `bd ready` before starting new work**

## Type Generation (When Schemas Change)

```bash
python scripts/generate_types.py
```

## Database Migrations (When Models Change)

```bash
cd backend
./venv/bin/alembic revision --autogenerate -m "description"
./venv/bin/alembic upgrade head
```
