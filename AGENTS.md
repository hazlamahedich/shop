# Agent Instructions

This project uses **bd (Beads)** for AI-native issue tracking and **BMad Method** for agile AI-driven development.

---

## 📊 Task Tracking with Beads

Beads provides persistent, structured memory that lives in your repo as git-tracked JSONL files. Perfect for multi-session work and agent coordination.

### Quick Reference

```bash
bd ready              # Show tasks with no open blockers (ready to work)
bd list               # Show all open issues
bd show <id>          # View issue details and audit trail
bd create "Task" -p 0 # Create P0 (critical) task
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd dep add <child> <parent>  # Link tasks (blocks/parent-child)
bd sync               # Sync with git remote
```

### Priority Levels
| Priority | Flag | Usage |
|----------|------|-------|
| P0 | `-p 0` | Critical, blocks release |
| P1 | `-p 1` | High priority, current sprint |
| P2 | `-p 2` | Medium priority, backlog |
| P3 | `-p 3` | Low priority, nice to have |

### Task Hierarchy Pattern
```bash
# Create epic
bd create "Epic: User Authentication" -p 1 -t epic

# Create sub-tasks (auto-generates hierarchical IDs)
bd create "Design auth schema" -p 1
bd create "Implement JWT endpoints" -p 1
bd create "Add unit tests" -p 2

# Link as dependencies
bd dep add <jwt-task-id> <schema-task-id>  # JWT blocks on schema
bd dep add <test-task-id> <jwt-task-id>    # Tests block on JWT
```

### MANDATORY Workflow

**STARTING WORK:**
```bash
# 1. Find available tasks
bd ready

# 2. Claim a task
bd update <id> --status in_progress

# 3. Work...
```

**COMPLETING WORK:**
```bash
# 1. Run quality gates (if code changed)
npm test && npm run lint && npm run build

# 2. Close completed tasks
bd close <id>

# 3. Sync with git
bd sync
git add .
git commit -m "feat: description"
git pull --rebase
git push

# 4. Verify
git status  # MUST show "up to date with origin"
```

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - stranded work is lost work
- ALWAYS create Beads tasks for follow-up work
- Run `bd ready` before starting new work

---

## 🚀 BMad Method Integration

This project uses [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) for structured AI-driven development.

### BMad + Beads Workflow

The key principle: **BMad workflows → Beads tasks via helper script → Execution**

```mermaid
graph TD
    A[BMad Planning Phase] -->|creates| B[sprint-status.yaml]
    B -->|bmad-to-beads| C[Beads Epic/Story Tasks]
    C -->|bd ready| D[Agent picks task]
    D -->|bd update in_progress| E[Implementation]
    E -->|bd close| F[Complete]
```

### 🔄 BMad to Beads Converter

**Auto-convert BMad sprint status to Beads tasks:**

```bash
# Preview what would be created
./scripts/bmad-to-beads

# Show backlog items ready to start
./scripts/bmad-to-beads --status backlog

# Show specific epic
./scripts/bmad-to-beads --epic epic-3

# Actually create Beads tasks
./scripts/bmad-to-beads --create

# Create only backlog stories for epic-1
./scripts/bmad-to-beads --create --epic epic-1 --status backlog
```

**Status Mapping:**
| BMad Status | Beads Status |
|-------------|--------------|
| backlog | todo |
| ready-for-dev | todo |
| in-progress | in_progress |
| review | in_progress |
| done | done |

**See:** `scripts/README_BMAD_TO_BEADS.md` for full documentation
```

### Quick Path (Bug Fixes, Small Features)
```bash
# 1. BMad generates tech spec with stories
/quick-spec

# 2. Create Beads tasks for each story
bd create "Story: Implement login fix" -p 1

# 3. Work the task
/dev-story

# 4. Validate
/code-review
```

### Full Planning Path (Products, Complex Features)
```bash
# Phase 1: Planning (creates Beads epics)
/product-brief        # → Beads epic for product definition
/create-prd           # → Beads epic for requirements
/create-architecture  # → Beads epic for technical design

# Phase 2: Breakdown (creates Beads stories)
/create-epics-and-stories  # → Hierarchical Beads tasks
/sprint-planning           # → Prioritized Beads tasks for sprint

# Phase 3: Execution (work from Beads)
bd ready              # Find next available story
/dev-story            # Implement the story
/code-review          # Validate quality
bd close <id>         # Mark complete
```

### Integration Pattern

| BMad Phase | Beads Action | Command |
|------------|--------------|---------|
| Product Brief | Create epic task | `bd create "Epic: [feature]" -t epic -p 1` |
| PRD Created | Add requirement tasks | `bd create "Story: [requirement]" -p 1` |
| Architecture | Add technical tasks | `bd create "Task: [component]" -p 1` |
| Story Breakdown | Create implementation tasks | `bd create "Impl: [story]" -p 0/1` |
| Sprint Planning | Prioritize & link | `bd dep add <child> <parent>` |
| Development | Work from `bd ready` | Pick tasks with no blockers |
| Code Review | Validate task completion | Review code, then `bd close` |

### Example Session

```bash
# 1. Start new feature work
/bmad-help "I need to add user notifications"

# 2. BMad guides you through planning
# This creates Beads tasks automatically

# 3. Check what's ready to work on
bd ready
# Output:
#   bd-a3f8.1 - Implement notification service API [P1]
#   bd-a3f8.2 - Design notification preferences schema [P1]

# 4. Pick up a task
bd update bd-a3f8.1 --status in_progress

# 5. Implement using BMad dev story workflow
/dev-story bd-a3f8.1

# 6. Review and complete
/code-review
bd close bd-a3f8.1

# 7. Sync everything
bd sync && git push
```

---

## ✅ Story Start Checklist

**CRITICAL:** Complete this checklist BEFORE writing any code for a new story.

### Pre-Implementation Verification

```markdown
□ **CSRF**: Is this story adding/modifying API endpoints?
   - If YES: Verify CSRF bypass/middleware is configured for new routes
   - Check: `backend/app/middleware/auth.py` for bypass paths
   - Reference: Epic 5 had 6 stories forget CSRF initially

□ **Python venv**: Activated before any Python work?
   - Run: `source backend/venv/bin/activate`
   - Verify: `python --version` (should be 3.11.x)
   - Reference: Epic 5 had 5 stories with datetime.UTC errors

□ **Schema Sync**: Frontend and Backend types aligned?
   - Check: TypeScript interface matches Pydantic schema
   - New fields: Add to BOTH frontend types AND backend schemas
   - Reference: Story 5-5 had 5 backend fields vs 11 frontend fields

□ **Naming Convention**: API fields use correct case?
   - Backend/DB: `snake_case` (e.g., `created_at`)
   - Frontend/API: `camelCase` (e.g., `createdAt`)
   - Use Pydantic `alias_generator` for transformation
   - Reference: Story 5-10 stored `isOpen` but expected `is_open`

□ **API Envelope**: Using correct response access pattern?
   - apiClient returns full envelope: `{ data: T, meta: any }`
   - Use `response.data` to get payload (NOT `response.data.data`)
   - Reference: Stories 8-7, 8-11 had `response.data.data` bugs
   - See: `docs/api-envelope-pattern.md`

□ **Embedding Storage**: Using flexible dimensions?
   - Use JSONB with `embedding_dimension` column (not fixed `Vector(1536)`)
   - Cast at query time: `embedding::jsonb::float[]::vector(dimension)`
   - Reference: Story 8-11 migrated from fixed to flexible dimensions

□ **E2E Tests**: Using correct addInitScript pattern?
   - Template literals don't work in browser context
   - Pass values as 2nd argument: `addInitScript((val) => {...}, value)`
   - Use helpers: `setLocalStorageValue(page, key, value)`
   - Reference: Stories 8-6, 8-7, 8-11 had interpolation bugs
```

### Quick Reference

| Check | Command/File | Common Mistake |
|-------|--------------|----------------|
| CSRF | `backend/app/middleware/auth.py` | Forgetting to add new route to bypass list |
| venv | `source backend/venv/bin/activate` | Using system Python (3.12+) instead of venv (3.11) |
| Schema | Compare `frontend/src/types/*.ts` with `backend/app/schemas/*.py` | Adding field to one side only |
| Naming | Pydantic `Field(alias="...")` | Using wrong case for API field names |
| Envelope | Use `response.data` | Using `response.data.data` (double unwrap) |
| Embedding | Use JSONB + dimension column | Using fixed `Vector(N)` dimension |
| E2E | `addInitScript((v) => {...}, val)` | Using template literal `${val}` in browser context |

---

## 🐍 Python Development Guidelines

### Version Requirement

**Always use Python 3.11 from the virtual environment:**

```bash
# Activate venv before any Python work
source backend/venv/bin/activate  # macOS/Linux
# OR
backend\venv\Scripts\activate     # Windows

# Verify version (should be 3.11.x)
python --version
```

**Why:** System Python may be 3.12+, but the venv is 3.11. Using the wrong version causes datetime compatibility issues.

### Datetime Compatibility (Python 3.9/3.11)

```python
# ✅ CORRECT - Works in Python 3.9+
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# ❌ WRONG - Only works in Python 3.11+
from datetime import datetime, UTC
now = datetime.now(UTC)  # AttributeError in Python 3.9/3.10
```

---

## 🗄️ Database Architecture

### Database Separation

This project uses **3 separate PostgreSQL databases** to prevent data loss:

| Database | Purpose | Data Persistence |
|----------|---------|------------------|
| `shop_prod` | **Production** | Permanent (never reset) |
| `shop_dev` | **Development** | Semi-permanent (manual testing data) |
| `shop_test` | **Testing** | Ephemeral (reset before each test) |

### ⚠️ CRITICAL: Test Database Configuration

**Integration tests use `shop_test` database (separate from `shop_dev`)**

```python
# tests/conftest.py
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://developer:developer@localhost:5432/shop_test"
)
```

**This prevents:**
- ✅ Tests from deleting your manual development data
- ✅ Accidental data loss during test runs
- ✅ Conflicts between manual testing and automated tests

### Database Reset Warning System

**Automatic warning when running tests on `shop_dev`:**

```
================================================================================
⚠️  WARNING: RUNNING TESTS ON DEVELOPMENT DATABASE  ⚠️
================================================================================
Test database URL: shop_dev

This will DELETE ALL DATA in your development database!
Tests should use a separate test database (shop_test).

To fix this:
  export TEST_DATABASE_URL='postgresql+asyncpg://developer:developer@localhost:5432/shop_test'

Waiting 5 seconds before continuing...
================================================================================
```

### Seeding Test Data

**Use the seed script to quickly populate `shop_test` database:**

```bash
# Seed all test data (merchant + conversations + FAQs + tutorials)
cd backend
source venv/bin/activate
python scripts/seed_test_data.py

# Seed only merchants
python scripts/seed_test_data.py --merchants

# Seed conversations for specific merchant
python scripts/seed_test_data.py --conversations --merchant-id 1 --count 5
```

**What gets seeded:**
- ✅ Test merchant with widget configuration
- ✅ Sample conversations (active + handoff)
- ✅ FAQ pages (dynamically updated)
- ✅ Tutorial pages (dynamically updated)
- ✅ LLM and Shopify configuration

### Best Practices

**DO:**
- ✅ Use `shop_test` for automated integration tests
- ✅ Use `shop_dev` for manual development/testing
- ✅ Run seed script after database resets
- ✅ Set `TEST_DATABASE_URL` environment variable in CI/CD

**DON'T:**
- ❌ Run integration tests on `shop_dev` (will delete data)
- ❌ Manually edit `shop_test` database (will be reset)
- ❌ Skip the warning system when it appears

### Database Recovery

**If you accidentally lose `shop_dev` data:**

1. **Re-seed test data:**
   ```bash
   python scripts/seed_test_data.py
   ```

2. **Re-connect Shopify manually:**
   - Go through onboarding flow
   - Connect your Shopify store
   - Configure LLM settings

3. **Update widget configuration:**
   - Update merchant ID in widget config
   - Test with new merchant ID

### Test Commands

```bash
# Run integration tests (uses shop_test)
cd backend
source venv/bin/activate
python -m pytest tests/integration/ -v

# Run unit tests (no database required)
python -m pytest app/services/handoff/test_handoff_resolution_service.py -v

# Run all tests
python -m pytest -v
```

---

## 📁 Project Structure

```
shop/
├── .beads/              # Beads task database (git-tracked)
├── _bmad/               # BMad method workflows & memory
│   ├── bmm/             # BMad Method module workflows
│   ├── core/            # Core framework
│   └── _memory/         # BMad session memory
├── .agent/workflows/    # BMad workflow commands
└── AGENTS.md            # This file
```

---

## 🆘 Getting Help

| Question | Command |
|----------|---------|
| What should I do next? | `/bmad-help` |
| What tasks are ready? | `bd ready` |
| How do I use BMad? | `/bmad-help tutorial` |
| Show all tasks | `bd list` |
| BMad workflow reference | `/bmad-help workflows` |

---

## Sources

- [Beads GitHub Repository](https://github.com/steveyegge/beads)
- [BMad Method Documentation](https://github.com/bmad-code-org/BMAD-METHOD)
