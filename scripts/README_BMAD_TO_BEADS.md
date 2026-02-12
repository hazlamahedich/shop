# BMad to Beads Converter

Helper script that converts BMad Method sprint status into Beads tasks.

## Quick Start

```bash
# Preview what would be created (dry-run)
python scripts/bmad_to_beads.py

# Or use the wrapper
./scripts/bmad-to-beads

# Show backlog items ready to start
./scripts/bmad-to-beads --status backlog

# Show specific epic
./scripts/bmad-to-beads --epic epic-3
```

## Creating Beads Tasks

```bash
# Create tasks for all stories
./scripts/bmad-to-beads --create

# Create only backlog stories
./scripts/bmad-to-beads --create --status backlog

# Create only epic-3 stories
./scripts/bmad-to-beads --create --epic epic-3
```

## Status Mapping

| BMad Status | Beads Status |
|-------------|--------------|
| backlog | todo |
| ready-for-dev | todo |
| in-progress | in_progress |
| review | in_progress |
| done | done |

## Priority Mapping

The script automatically assigns priorities based on story descriptions:

| Priority | Patterns |
|----------|----------|
| P0 (Critical) | prerequisite, critical, security, auth |
| P1 (High) | deployment, connection, core, essential |
| P2 (Medium) | feature, integration, configuration |
| P3 (Low) | optional, enhancement, nice-to-have |

## Usage Examples

### Find next tasks to work on
```bash
./scripts/bmad-to-beads --status backlog
./scripts/bmad-to-beads --status ready-for-dev
```

### Convert current sprint work
```bash
# Preview epic-1 backlog stories
./scripts/bmad-to-beads --dry-run --epic epic-1 --status backlog

# Create Beads tasks for them
./scripts/bmad-to-beads --create --epic epic-1 --status backlog
```

### After creating tasks
```bash
# Work from Beads
bd ready              # Show tasks with no blockers
bd show <id>          # View task details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
```

## Integration with BMad Workflows

The typical workflow:

1. **Run BMad planning** → Creates/updates sprint-status.yaml
2. **Convert to Beads** → `./scripts/bmad-to-beads --create`
3. **Work from Beads** → `bd ready` → pick task → implement
4. **Update BMad status** → Mark story complete in sprint-status.yaml
5. **Sync Beads** → `bd close <id>` (optional, or just track in Beads)

## Project Structure

```
shop/
├── _bmad-output/
│   └── implementation-artifacts/
│       └── sprint-status.yaml    # ← Read by script
├── .beads/                        # ← Beads database
├── scripts/
│   ├── bmad_to_beads.py           # Main converter
│   └── bmad-to-beads              # Shell wrapper
└── AGENTS.md                      # Workflow documentation
```

## Troubleshooting

**"sprint-status.yaml not found"**
- Make sure you're in the project root directory
- Run BMad workflows first to generate the output

**"bd command not found"**
- Install Beads CLI: `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash`

**Beads tasks not linking properly**
- Make sure `bd` is working: `bd ready`
- Check epic hierarchy in sprint-status.yaml
