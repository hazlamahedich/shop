---
# Beads Integration Step
# This step provides automatic BMad → Beads task synchronization
#
# TO DISABLE: Delete this file or set enabled: false in beads-integration-hook.md
# LAST MODIFIED: 2025-02-11
# =====================================================================

# OPTIONAL STEP: Beads Integration
# This step automatically syncs BMad sprint status to Beads tasks

## Check Integration Status

1. **Check if Beads integration hook exists:**
   - File: `{project-root}/_bmad/core/beads-integration-hook.md`
   - If missing: Skip Beads sync (not configured)
   - If exists: Continue to next check

2. **Check if integration is enabled:**
   - Read hook configuration
   - Parse: `enabled` value
   - If `enabled != true`: Skip Beads sync (disabled in config)
   - If `enabled == true`: Continue to next check

3. **Check if current workflow should trigger sync:**
   - Parse `sync_triggers[]` list from hook config
   - Check if current workflow name is in the list
   - If not in list: Skip Beads sync (not configured for this workflow)
   - If in list: Proceed with sync

## Execute Sync (If all checks pass)

1. **Display sync message:**
   - Output: `🔄 Syncing BMad sprint status to Beads tasks...`

2. **Build and execute sync command:**
   - Parse `sync_mode` from hook config (default: "backlog")
   - Parse `sync_command` template from hook config
   - Substitute `{sync_mode}` in command
   - Execute: `./scripts/bmad-to-beads --create --status {sync_mode}`

3. **Handle result:**
   - **If success:** Output `✅ Beads sync complete! Run 'bd ready' to see available tasks`
   - **If failed:** Handle based on `on_error` setting:
     - `warn`: Show warning, continue
     - `fail`: Show error, ask user to continue
     - `silent`: Continue without notification

## Configuration File Format

The hook configuration file (`_bmad/core/beads-integration-hook.md`) should contain:

```yaml
enabled: true
sync_triggers:
  - after: "create-epics-and-stories"
  - after: "sprint-planning"
  - after: "sprint-status"
  - after: "create-story"
sync_mode: "backlog"  # or "ready-for-dev", "all", "none"
sync_command: "./scripts/bmad-to-beads --create --status {sync_mode}"
on_error: "warn"  # or "fail", "silent"
```

## Quick Disable Options

To disable Beads integration without modifying workflow files:

1. **Delete the hook file:** `rm _bmad/core/beads-integration-hook.md`
2. **Set enabled: false** in the hook file
3. **Rename the hook file:** `mv _bmad/core/beads-integration-hook.md _bmad/core/beads-integration-hook.md.disabled`

Any of these options will cause all workflows to skip the Beads sync step.

# =====================================================================
# END BEADS INTEGRATION STEP
# =====================================================================
