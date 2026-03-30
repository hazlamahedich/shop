# Epic 12: Security Hardening

**Status**: Planning
**Priority**: P0 (Critical - Production Blocker)
**Created**: 2026-03-28
**Owner**: Security Team

## Overview

Comprehensive security hardening initiative to address vulnerabilities identified in the security assessment and ensure production readiness for handling personal data (PII).

## Goals

1. Achieve production-ready security posture
2. Ensure GDPR/CCPA compliance for personal data handling
3. Implement defense-in-depth security measures
4. Establish security monitoring and incident response

## Security Assessment Summary

### Strengths (Already Implemented)
- ✅ JWT authentication with httpOnly cookies, Secure + SameSite=Strict
- ✅ bcrypt password hashing (work factor 12)
- ✅ CSRF double-submit cookie protection
- ✅ Rate limiting on auth/widget endpoints
- ✅ Fernet encryption for sensitive data at rest
- ✅ HMAC-SHA256 webhook signature verification
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ GDPR data tier system with retention policies
- ✅ Deletion/export audit logs

### Concerns (To Be Addressed)
- ⚠️ In-memory rate limiting (not distributed)
- ⚠️ Dev key fallbacks in production config
- ⚠️ Verbose debug logging in widget
- ⚠️ Dead code reading from localStorage
- ⚠️ No automated dependency scanning
- ⚠️ Third-party LLM data sharing disclosure

## Stories

### P0 - Critical (Production Blockers)

| Story | Title | Est. Hours |
|-------|-------|------------|
| 12-1 | Rate Limiting Redis Migration | 8h |
| 12-12 | Deployment Blockers Checklist | 4h |

### P1 - High Priority

| Story | Title | Est. Hours |
|-------|-------|------------|
| 12-2 | Dependency Security Scanning | 6h |
| 12-3 | CSRF Delete Endpoints | 4h |
| 12-4 | File Upload Security Hardening | 6h |
| 12-5 | Dev Key Production Check | 3h |
| 12-13 | Dead Code Cleanup | 2h |
| 12-14 | Production Security Checklist | 4h |

### P2 - Medium Priority

| Story | Title | Est. Hours |
|-------|-------|------------|
| 12-6 | Security Incident Response Plan | 6h |
| 12-7 | Error Messages UX Review | 4h |
| 12-8 | Logging Improvements | 6h |
| 12-9 | Security Test Suite | 8h |
| 12-11 | Integration Security Tests | 6h |
| 12-15 | Beads Task Sync | 2h |
| 12-16 | Final Security Validation | 4h |

### P3 - Low Priority

| Story | Title | Est. Hours |
|-------|-------|------------|
| 12-10 | Security Documentation | 4h |
| 12-17 | Sprint Retrospective | 2h |

## Total Estimate

- **P0**: 12 hours
- **P1**: 25 hours
- **P2**: 36 hours
- **P3**: 6 hours
- **Total**: 79 hours (~10 sprint days)

## Dependencies

- Story 12-1 blocks 12-16 (Redis must be working before final validation)
- Story 12-2 blocks 12-16 (Dependency scanning must pass)
- Story 12-9 blocks 12-16 (Security tests must pass)

## Success Criteria

1. All P0 stories completed and validated
2. All P1 stories completed
3. Security test suite passing
4. No critical/high vulnerabilities in dependencies
5. Production security checklist signed off
6. Incident response plan documented

## References

- Security Assessment: `.opencode/plans/security-assessment.md`
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- GDPR Compliance: https://gdpr.eu/
- CCPA Compliance: https://oag.ca.gov/privacy/ccpa
