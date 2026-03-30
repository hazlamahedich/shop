# Story 12-12: Deployment Blockers Checklist

**Epic**: 12 - Security Hardening
**Priority**: P0 (Critical)
**Status**: backlog
**Estimate**: 4 hours
**Dependencies**: 12-1, 12-2, 12-5

## Problem Statement

No clear checklist of security requirements that must be met before production deployment.

## Acceptance Criteria

- [ ] Pre-deployment security checklist created
- [ ] Automated checks where possible
- [ ] Manual verification steps defined
- [ ] Sign-off process documented
- [ ] Rollback criteria defined
- [ ] Security monitoring verified
- [ ] Incident response contacts confirmed

## Technical Design

### Pre-Deployment Security Checklist

```markdown
## Production Deployment Security Checklist

### Critical (Must Pass)
- [ ] All P0 security stories completed
- [ ] No critical/high vulnerabilities in dependencies
- [ ] Production secrets configured (not dev keys)
- [ ] Redis rate limiting operational
- [ ] HTTPS enforced
- [ ] Security headers verified
- [ ] Database encryption enabled
- [ ] Backup encryption verified

### High Priority (Should Pass)
- [ ] P1 security stories completed
- [ ] Dependency scanning in CI
- [ ] File upload security validated
- [ ] Error messages reviewed
- [ ] Logging configured (no PII)

### Verification
- [ ] Security test suite passing
- [ ] Penetration test completed (if required)
- [ ] Security team sign-off
- [ ] Operations team sign-off

### Post-Deployment
- [ ] Security monitoring alerts active
- [ ] Incident response team notified
- [ ] On-call rotation confirmed
```

### Automated Checks Script

```bash
#!/bin/bash
# scripts/check-production-security.sh

set -e

echo "Checking production security requirements..."

# Check for dev keys
if grep -r "dev-" .env.production 2>/dev/null; then
    echo "ERROR: Dev keys found in production config"
    exit 1
fi

# Check dependency vulnerabilities
cd backend && pip-audit --requirement requirements.txt
cd ../frontend && npm audit --audit-level=high

# Check security headers
curl -s -I https://api.example.com | grep -i "x-frame-options\|x-content-type-options\|strict-transport-security"

echo "All security checks passed!"
```

## Rollback Criteria

- Any critical security incident
- Data breach detected
- Authentication system failure
- Encryption key compromise

## Related Files

- `docs/deployment/security-checklist.md` (new)
- `scripts/check-production-security.sh` (new)
- `.github/workflows/deploy.yml`
