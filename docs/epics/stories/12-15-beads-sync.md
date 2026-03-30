# Story 12-15: Beads Task Sync

**Epic**: 12 - Security Hardening
**Priority**: P2 (Medium)
**Status**: backlog
**Estimate**: 2 hours
**Dependencies**: All other Epic 12 stories

## Problem Statement

Epic 12 stories need to be created as Beads tasks for proper tracking and workflow management.

## Acceptance Criteria

- [ ] Epic created in Beads for Epic 12
- [ ] All 17 stories created as Beads tasks
- [ ] Dependencies linked in Beads
- [ ] Priorities match story priorities
- [ ] Estimates added to tasks
- [ ] Sprint status file updated

## Technical Design

### Beads Commands

```bash
# Create epic
bd create "Epic 12: Security Hardening" -t epic -p 0

# Create P0 stories
bd create "12-1: Rate Limiting Redis Migration" -p 0
bd create "12-12: Deployment Blockers Checklist" -p 0

# Create P1 stories
bd create "12-2: Dependency Security Scanning" -p 1
bd create "12-3: CSRF Delete Endpoints" -p 1
bd create "12-4: File Upload Security Hardening" -p 1
bd create "12-5: Dev Key Production Check" -p 1
bd create "12-13: Dead Code Cleanup" -p 1
bd create "12-14: Production Security Checklist" -p 1

# Create P2 stories
bd create "12-6: Security Incident Response Plan" -p 2
bd create "12-7: Error Messages UX Review" -p 2
bd create "12-8: Logging Improvements" -p 2
bd create "12-9: Security Test Suite" -p 2
bd create "12-11: Integration Security Tests" -p 2
bd create "12-15: Beads Task Sync" -p 2
bd create "12-16: Final Security Validation" -p 2

# Create P3 stories
bd create "12-10: Security Documentation" -p 3
bd create "12-17: Sprint Retrospective" -p 3

# Add dependencies
bd dep add 12-12 12-1  # 12-12 depends on 12-1
bd dep add 12-12 12-2  # 12-12 depends on 12-2
bd dep add 12-14 12-1  # 12-14 depends on 12-1
bd dep add 12-16 12-9  # 12-16 depends on 12-9
```

## Related Files

- `.beads/` (Beads database)
- `_bmad/_memory/sprint-status.yaml`
