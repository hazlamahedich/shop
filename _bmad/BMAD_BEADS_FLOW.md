# BMad + Beads Full Integration Flow

## Complete Workflow Diagram (Your Actual Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PLANNING PHASE                                      │
└─────────────────────────────────────────────────────────────────────────────┘

1. /create-epics-and-stories
   ├─> Creates epics.md with stories
   ├─> Updates sprint-status.yaml
   └─> 🔄 AUTO: Beads tasks created (epics + stories)

2. /sprint-planning
   ├─> Updates sprint-status.yaml
   └─> 🔄 AUTO: Beads synced with planned stories

3. /create-story (for next story)
   ├─> Creates story file (status: ready-for-dev)
   ├─> Updates sprint-status.yaml
   └─> 🔄 AUTO: Beads task created for the story

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT PHASE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

4. bd ready
   └─> Shows all available tasks (no blockers)

5. bd update <id> --status in_progress
   └─> Claim the story task in Beads

6. /dev-story (implements the story)
   ├─> Step 4: Marks story "in-progress" in sprint-status.yaml
   │         🔄 AUTO: Updates Beads task to in-progress
   │
   ├─> Steps 5-8: Red-Green-Refactor cycle
   │         - Write failing tests
   │         - Implement code
   │         - Run all tests
   │         - Mark tasks complete
   │
   └─> Step 9: Story complete → status "review"
            🔄 AUTO: Closes Beads task

┌─────────────────────────────────────────────────────────────────────────────┐
│                        QUALITY ASSURANCE PHASE                             │
└─────────────────────────────────────────────────────────────────────────────┘

7. /bmad:tea:testarch:automate
   ├─> Expands test automation coverage
   ├─> Generates E2E, API, Component, Unit tests
   └─> Creates supporting fixtures and helpers

8. /bmad:bmm:code-review
   ├─> Adversarial code review
   ├─> Validates ACs and tasks
   ├─> Finds issues (3-10 minimum)
   ├─> Fixes issues or creates action items
   ├─> Updates sprint-status.yaml
   └─> 🔄 AUTO: Closes Beads task if approved, keeps in-progress if action items

9. /bmad:bmm:qa (or /bmad:bmm:qa-automate)
   ├─> QA test automation
   ├─> Integration + E2E test coverage
   └─> Validates quality gates

┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETION                                          │
└─────────────────────────────────────────────────────────────────────────────┘

10. Story marked "done" in sprint-status.yaml
    └─> All workflows complete, ready for next story

┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATUS SYNCS                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Any time: /sprint-status
   └─> 🔄 AUTO: Syncs all status changes to Beads
```

## Your Complete Workflow (Per Story)

| Step | Command | Beads Action |
|------|---------|--------------|
| 1 | `bd ready` | Shows available tasks |
| 2 | `bd update <id> --status in_progress` | Claims task |
| 3 | `/dev-story` | Updates to in-progress → closes on complete |
| 4 | `/bmad:tea:testarch:automate` | Optional: no Beads action |
| 5 | `/bmad:bmm:code-review` | Closes task if approved |
| 6 | `/bmad:bmm:qa` or `/bmad:bmm:qa-automate` | Optional: no Beads action |

## Key Integration Points

| BMad Workflow | Beads Action | Trigger |
|---------------|--------------|---------|
| **create-epics-and-stories** | Creates epic + story tasks | After epics/stories created |
| **sprint-planning** | Syncs planned stories | After sprint planning |
| **create-story** | Creates new story task | After story file created |
| **dev-story** (Step 4) | Updates task to in-progress | When story starts |
| **dev-story** (Step 9) | Closes task | When story complete |
| **code-review** | Closes task (if approved) | When review approves |
| **sprint-status** | Syncs all status changes | After status check |
| **testarch-automate** | No action | Tests only |

## Status Mapping

| BMad Status | Beads Status | When |
|-------------|--------------|------|
| backlog | todo | Created but not started |
| ready-for-dev | todo | Story ready to implement |
| in-progress (dev) | in-progress | dev-story started |
| review | in-progress | Implementation complete |
| done | done | Code review approved |

## Command Reference

### User Commands
```bash
# See available tasks
bd ready

# Claim a task
bd update <id> --status in_progress

# Check task details
bd show <id>

# Complete a task (usually auto-done by dev-story + code-review)
bd close <id>

# List all tasks
bd list

# Manual sync (if auto disabled)
./scripts/bmad-to-beads --create
```

### BMad Workflows (Your Full Flow)
```bash
# Planning
/create-epics-and-stories        # Creates epics and stories
/sprint-planning                 # Plans sprint
/create-story                    # Creates next story

# Development
/dev-story                       # Implements story

# Quality Assurance
/bmad:tea:testarch:automate     # Test automation expansion
/bmad:bmm:code-review            # Adversarial code review
/bmad:bmm:qa                     # QA workflow
/bmad:bmm:qa-automate            # QA test automation (if available)

# Status
/sprint-status                   # Shows sprint status
```

## How Beads Tracks Your Story

```
[Story Created]
  ├─> sprint-status.yaml: 1-13-bot-preview-mode: backlog
  └─> Beads: shop-xxx [todo] 1-13: Bot Preview Mode

[Story Ready]
  ├─> sprint-status.yaml: 1-13-bot-preview-mode: ready-for-dev
  └─> Beads: shop-xxx [todo] 1-13: Bot Preview Mode

[You Claim Task]
  └─> Beads: shop-xxx [in-progress] 1-13: Bot Preview Mode

[dev-story Starts]
  ├─> sprint-status.yaml: 1-13-bot-preview-mode: in-progress
  └─> Beads: shop-xxx [in-progress] 1-13: Bot Preview Mode (synced)

[dev-story Complete]
  ├─> sprint-status.yaml: 1-13-bot-preview-mode: review
  └─> Beads: shop-xxx [closed] 1-13: Bot Preview Mode

[testarch-automate Runs]
  └─> Beads: No change (task already closed)

[code-review Runs]
  ├─> sprint-status.yaml: 1-13-bot-preview-mode: done (if approved)
  └─> Beads: Task already closed (or re-opened if action items)

[qa Runs]
  └─> Beads: No change (story is done)
```

## Troubleshooting

**Beads task not closed after code-review?**
- Check if review was approved (status should be "done")
- If review created action items, task stays in-progress
- Manually close: `bd close <id>`

**Beads task shows wrong status?**
- Check sprint-status.yaml for actual story status
- Manual sync: `./scripts/bmad-to-beads --create`

**Want to disable auto-sync?**
```bash
# Edit config
nano _bmad/core/beads-integration-hook.md
# Change: enabled: true
# To:     enabled: false
```

## File Locations

| File | Purpose |
|------|---------|
| `_bmad/core/beads-integration-hook.md` | Master on/off switch |
| `_bmad/bmm/workflows/*/instructions.xml` | Workflow integration points |
| `_bmad/bmm/workflows/*/steps/*.md` | Step integration points |
| `scripts/bmad_to_beads.py` | Converter script |
| `.beads/` | Beads database (git-tracked) |

All integration points are marked with clear `<!-- BEADS INTEGRATION -->` tags for easy removal.
