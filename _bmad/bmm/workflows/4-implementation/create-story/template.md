# Story {{epic_num}}.{{story_num}}: {{story_title}}

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a {{role}},
I want {{action}},
so that {{benefit}}.

## Acceptance Criteria

1. [Add acceptance criteria from epics/PRD]

## Tasks / Subtasks

- [ ] Task 1 (AC: #)
  - [ ] Subtask 1.1
- [ ] Task 2 (AC: #)
  - [ ] Subtask 2.1

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Pre-Development Checklist

Before starting implementation, verify:
- [ ] **CSRF Token**: If story adds/modifies PATCH/POST/PUT/DELETE endpoints, include `X-CSRF-Token` header in frontend API calls
- [ ] **Python Version**: Use `datetime.timezone.utc` (NOT `datetime.UTC`) for Python 3.9/3.11 compatibility
- [ ] **Message Encryption**: Always use `message.decrypted_content` for display, never raw `message.content`
- [ ] **External Integration**: If story depends on Facebook/Shopify/Email, mark as "needs manual verification" and note mock status

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- Cite all technical details with source paths and sections, e.g. [Source: docs/<file>.md#Section]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
