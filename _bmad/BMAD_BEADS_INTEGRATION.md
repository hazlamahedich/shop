# BMad + Beads Full Integration

This project has **automatic BMad → Beads task synchronization** enabled.

## What It Does

After these BMad workflows complete, tasks are **automatically created in Beads**:
- `create-epics-and-stories` → Creates epic + story tasks in Beads
- `create-story` → Creates the new story task in Beads
- `sprint-status` → Syncs status changes to Beads
- `sprint-planning` → Syncs planned stories to Beads

## Quick Disable (3 Options)

If the integration causes issues, disable it with any of these:

### Option 1: Edit Config File (Easiest)
```bash
# Open the config
nano _bmad/core/beads-integration-hook.md

# Change first line:
enabled: true
# To:
enabled: false
```

### Option 2: Delete Config File
```bash
rm _bmad/core/beads-integration-hook.md
```

### Option 3: Rename to Disable
```bash
mv _bmad/core/beads-integration-hook.md _bmad/core/beads-integration-hook.md.disabled
```

## Files Modified by Integration

| File | Purpose | How to Remove Integration |
|------|---------|--------------------------|
| `_bmad/bmm/workflows/4-implementation/sprint-status/instructions.md` | Adds Beads sync step | Delete from `<!-- BEADS INTEGRATION -->` to `<!-- END BEADS -->` |
| `_bmad/bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-04-final-validation.md` | Adds Beads sync step | Delete from `<!-- BEADS INTEGRATION -->` to `<!-- END BEADS -->` |
| `_bmad/bmm/workflows/4-implementation/create-story/instructions.xml` | Adds Beads sync step | Delete from `<!-- BEADS INTEGRATION -->` to `<!-- END BEADS -->` |

**Note:** Disabling the config file (Options 1-3) is safer than editing workflow files.

## Configuration Options

The `_bmad/core/beads-integration-hook.md` file controls:

```yaml
enabled: true                    # Master on/off switch
sync_mode: "backlog"             # What to sync: backlog, ready-for-dev, all, none
sync_command: "./scripts/bmad-to-beads --create --status {sync_mode}"
on_error: "warn"                 # On sync failure: warn, fail, or silent
sync_triggers:
  - after: "create-epics-and-stories"
  - after: "create-story"
  - after: "sprint-status"
  - after: "sprint-planning"
```

## Verify Integration Status

```bash
# Check if integration is enabled
grep "enabled" _bmad/core/beads-integration-hook.md

# Test the sync manually
./scripts/bmad-to-beads --dry-run

# Check Beads status
bd ready
bd list
```

## Manual Sync (If Automatic Disabled)

```bash
# Sync backlog items
./scripts/bmad-to-beads --create --status backlog

# Sync ready-for-dev items
./scripts/bmad-to-beads --create --status ready-for-dev

# Sync all items
./scripts/bmad-to-beads --create --status all
```

## Troubleshooting

**"bd command not found"**
- Install Beads: `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash`

**Beads tasks not being created**
- Check if integration is enabled: `grep "enabled" _bmad/core/beads-integration-hook.md`
- Test manually: `./scripts/bmad-to-beads --dry-run`
- Check BMad workflows ran successfully (sprint-status.yaml should be updated)

**Want to use Beads manually only?**
- Set `enabled: false` in beads-integration-hook.md
- Run `./scripts/bmad-to-beads --create` when you want to sync

## Full Documentation

- Beads: https://github.com/steveyegge/beads
- BMad Method: https://github.com/bmad-code-org/BMAD-METHOD
- Script usage: `scripts/README_BMAD_TO_BEADS.md`
