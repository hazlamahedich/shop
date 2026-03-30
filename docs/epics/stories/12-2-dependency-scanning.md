# Story 12-2: Dependency Security Scanning

**Epic**: 12 - Security Hardening
**Priority**: P1 (High)
**Status**: backlog
**Estimate**: 6 hours
**Dependencies**: None

## Problem Statement

No automated dependency vulnerability scanning exists. The `pyproject.toml` lists security dependencies but there's no CI/CD integration to detect vulnerable packages.

## Acceptance Criteria

- [ ] GitHub Dependabot configured for Python
- [ ] GitHub Dependabot configured for Node.js
- [ ] `pip-audit` integrated in CI pipeline
- [ ] `npm audit` integrated in CI pipeline
- [ ] Snyk or similar SCA tool evaluated
- [ ] Security alerts configured for team
- [ ] Vulnerability remediation SLA defined
- [ ] Documentation for vulnerability response

## Technical Design

### GitHub Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 10
    labels:
      - "security"
      - "dependencies"
      
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 10
    labels:
      - "security"
      - "dependencies"
```

### CI Integration

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  pip-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit
      - run: pip-audit --requirement backend/requirements.txt
      
  npm-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: cd frontend && npm audit --audit-level=high
```

## Vulnerability Severity Response

| Severity | Response Time | Action |
|----------|---------------|--------|
| Critical | 24 hours | Immediate patch |
| High | 7 days | Prioritized patch |
| Medium | 30 days | Scheduled patch |
| Low | 90 days | Best effort |

## Testing Strategy

1. Test with known vulnerable package
2. Verify CI fails on vulnerability
3. Verify Dependabot PR creation
4. Test alert notifications

## Related Files

- `.github/dependabot.yml` (new)
- `.github/workflows/security.yml` (new)
- `backend/requirements.txt`
- `frontend/package.json`
