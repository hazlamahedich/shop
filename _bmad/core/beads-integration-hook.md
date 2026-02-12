# =====================================================================
# BEADS INTEGRATION HOOK
# =====================================================================
# This file enables automatic conversion of BMad sprint status to Beads tasks.
#
# TO DISABLE THIS INTEGRATION:
#   Option 1: Delete this entire file (safe, will just skip the hook)
#   Option 2: Rename to .disabled (e.g., beads-integration-hook.md.disabled)
#   Option 3: Set enabled: false below
#
# LAST MODIFIED: 2025-02-11
# =====================================================================

enabled: true

# When to run the Beads sync
sync_triggers:
  - after: "create-epics-and-stories"    # After epics/stories are created
  - after: "sprint-planning"             # After sprint planning
  - after: "sprint-status"               # After status updates
  - after: "create-story"                # After individual story creation
  - after: "dev-story"                   # After story implementation (closes Beads task)
  - after: "code-review"                 # After code review (marks done if approved)
  - after: "testarch-automate"           # After test automation (optional)

# What to sync
sync_mode: "backlog"  # Options: "backlog", "ready-for-dev", "all", "none"

# Command to run (relative to project root)
sync_command: "./scripts/bmad-to-beads --create --status {sync_mode}"

# Error handling
on_error: "warn"  # Options: "warn" (show warning, continue), "fail" (stop workflow), "silent" (ignore)

# =====================================================================
# END OF BEADS INTEGRATION HOOK
# To remove integration: Delete from this line upward to the top
# =====================================================================
