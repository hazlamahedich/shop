# Security Runbook

This runbook provides procedures for handling security incidents, vulnerability management, and security best practices for the Shopping Assistant Bot project.

## Table of Contents

1. [Security Incident Response](#security-incident-response)
2. [Vulnerability Management](#vulnerability-management)
3. [Security Scanning Procedures](#security-scanning-procedures)
4. [Secret Management](#secret-management)
5. [Deployment Security](#deployment-security)
6. [Emergency Contacts](#emergency-contacts)

---

## Security Incident Response

### Incident Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **CRITICAL** | Active exploit, data breach, production compromise | Immediate (1 hour) |
| **HIGH** | Unauthorized access, sensitive data exposure | 4 hours |
| **MEDIUM** | Potential vulnerability, non-critical exposure | 24 hours |
| **LOW** | Best practice violation, informational finding | 1 week |

### Incident Response Procedure

#### Phase 1: Identification (0-1 hour)

1. **Verify the Incident**
   ```bash
   # Check recent security scan results
   gh api repos/:owner/:repo/code-scanning/alerts

   # Review GitHub Security tab
   # Check Dependabot alerts
   # Review secret scanning alerts
   ```

2. **Containment Actions**
   ```bash
   # If credentials are leaked, rotate immediately
   # If production is compromised, initiate hotfix deployment
   # If data breach detected, activate incident response team
   ```

#### Phase 2: Analysis (1-4 hours)

1. **Root Cause Analysis**
   ```bash
   # Pull security scan reports
   ./scripts/security-scan.sh all

   # Review git history for when vulnerability was introduced
   git log --all --source --full-history -S "vulnerable_pattern"

   # Check which environments are affected
   ```

2. **Impact Assessment**
   - Determine data exposure scope
   - Identify affected user accounts
   - Assess service availability impact

#### Phase 3: Remediation (4-24 hours)

1. **Fix Implementation**
   ```bash
   # Create security hotfix branch
   git checkout -b security/hotfix-$(date +%Y%m%d)

   # Apply security patches
   # Update dependencies
   pip install -U --upgrade-strategy eager -e ".[security]"
   npm audit fix

   # Run full security validation
   ./scripts/security-scan.sh all
   ```

2. **Deployment**
   ```bash
   # Deploy to staging first
   # Run security tests on staging
   # Deploy to production with monitoring
   ```

#### Phase 4: Post-Incident (24-72 hours)

1. **Documentation**
   - Create incident report
   - Document root cause
   - Update prevention measures

2. **Prevention**
   - Add new security tests
   - Update pre-commit hooks
   - Schedule additional scans

---

## Vulnerability Management

### Dependency Vulnerability Response

#### HIGH/CRITICAL Vulnerabilities

**Action Required**: Fix before next deployment

```bash
# Check for vulnerabilities
npm audit --audit-level=high
pip-audit

# Update affected packages
npm update <package>
pip install -U <package>

# Verify fix
npm audit
pip-audit
```

#### MEDIUM Vulnerabilities

**Action Required**: Fix within 7 days

1. Create tracking issue
2. Schedule maintenance window
3. Update dependencies
4. Run full test suite

#### LOW Vulnerabilities

**Action Required**: Fix in next dependency update cycle

- Add to backlog
- Update during regular maintenance

### Zero-Day Vulnerability Response

```bash
# Immediate containment
1. Check if vulnerable dependency is used:
   grep -r "vulnerable-package" package.json pyproject.toml

2. If used, assess exposure:
   - Is the vulnerable code path reachable?
   - Is user input processed?
   - Is data exposed?

3. Apply vendor patches or temporary mitigations

4. Update to patched version immediately
```

---

## Security Scanning Procedures

### Local Development Scans

**Before Every Push**

```bash
# Quick security check
./scripts/security-scan.sh secrets

# Full security scan (before major commits)
./scripts/security-scan.sh all
```

### CI/CD Security Pipeline

**Every PR/Commit**

- Secret scanning (Gitleaks)
- Backend security (Bandit, Safety, Semgrep)
- Frontend security (npm audit, Snyk)
- Infrastructure security (Trivy, Hadolint)
- CodeQL analysis

**Daily Scheduled Scans** (2 AM UTC)

- Full security suite
- Dependency vulnerability check
- API contract security testing

**Weekly Scans** (Sunday 3 AM UTC)

- Docker image vulnerability scanning
- Dependency update recommendations

### Manual Security Scans

```bash
# Backend security
cd backend
pip install -e ".[security]"
bandit -r app/
safety check
pip-audit

# Frontend security
cd frontend
npm audit --audit-level=high
snyk test  # Requires Snyk token

# Infrastructure security
trivy config .
hadolint Dockerfile

# Full scan
./scripts/security-scan.sh all
```

---

## Secret Management

### Secret Types

| Secret Type | Storage Method | Rotation Policy |
|-------------|----------------|-----------------|
| Database passwords | Environment variables | Quarterly |
| API keys (external) | Secrets manager (GitHub/AWS) | Monthly |
| JWT signing keys | Secrets manager | Annually |
| OAuth tokens | Secrets manager | On compromise |

### Secret Detection

**Pre-Commit Detection**
```bash
# Pre-commit hooks automatically check for:
# - Private keys
# - API keys
# - Passwords in code
# - JWT tokens
```

**Manual Secret Scan**
```bash
# Scan entire repository
./scripts/security-scan.sh secrets

# Scan specific patterns
git grep -iE "(password|secret|api[_-]?key|token)\s*=" -- '*.py' '*.ts' '*.tsx'
```

### Secret Rotation Procedure

1. **Generate new secret**
   ```bash
   # Generate new JWT secret
   openssl rand -base64 32

   # Generate new database password
   # Use password manager or secure generator
   ```

2. **Update in production**
   ```bash
   # Update environment variables
   # Deploy with new credentials
   # Verify service functionality
   ```

3. **Invalidate old secret**
   - Remove from secrets manager
   - Revoke any API keys
   - Update documentation

---

## Deployment Security

### Pre-Deployment Checklist

- [ ] All security scans passing
- [ ] No HIGH/CRITICAL vulnerabilities
- [ ] MEDIUM vulnerabilities reviewed and accepted
- [ ] Secrets not in code
- [ ] Environment variables configured
- [ ] TLS/SSL certificates valid
- [ ] Database backups tested
- [ ] Rollback plan documented

### Deployment Security Steps

```bash
# 1. Run full security scan
./scripts/security-scan.sh all

# 2. Check for new vulnerabilities
npm audit
pip-audit

# 3. Verify environment variables
# Ensure all secrets are set via environment, not hardcoded

# 4. Deploy with monitoring
# Enable enhanced logging during deployment

# 5. Post-deployment verification
# Check application logs for security events
# Monitor error rates
# Verify authentication flow
```

### Rollback Procedure

```bash
# If security issue detected in production:

# 1. Immediately revert to previous version
git revert HEAD
# or
git checkout <previous-stable-tag>

# 2. Deploy previous version
# Follow standard deployment procedure

# 3. Post-mortem analysis
# Determine root cause
# Update prevention measures
```

---

## Emergency Contacts

### Security Team

| Role | Contact | Availability |
|------|---------|---------------|
| Security Lead | security@example.com | 24/7 |
| DevOps Engineer | devops@example.com | Business hours |
| Engineering Lead | engineering@example.com | Business hours |

### External Resources

- **GitHub Security Advisory**: https://github.com/advisories
- **NVD (National Vulnerability Database)**: https://nvd.nist.gov/
- **Snyk Vulnerability Database**: https://snyk.io/vuln
- **Python Security**: https://python.org/security/
- **npm Security**: https://www.npmjs.com/advisories

---

## Security Metrics

### Key Performance Indicators

1. **Mean Time to Detect (MTTD)**: Target < 1 hour
2. **Mean Time to Respond (MTTR)**: Target < 4 hours
3. **Vulnerability Remediation SLA**:
   - CRITICAL: 24 hours
   - HIGH: 7 days
   - MEDIUM: 30 days
4. **Security Scan Coverage**: 100% of codebase
5. **Zero False Negatives**: Continuous improvement

### Reporting

**Weekly Security Summary**
- New vulnerabilities detected
- Vulnerabilities remediated
- Outstanding security issues
- Upcoming security tasks

**Monthly Security Review**
- Security posture assessment
- Trend analysis
- Tool effectiveness review
- Process improvements

---

## Appendix: Quick Reference

### Common Security Commands

```bash
# Scan for secrets
./scripts/security-scan.sh secrets

# Full security scan
./scripts/security-scan.sh all

# Check Python dependencies
cd backend && pip-audit

# Check npm dependencies
cd frontend && npm audit

# Scan Docker images
trivy image <image-name>

# Run Schemathesis API security tests
cd backend
pytest tests/contract/ --schemathesis-io
```

### Security Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/security.yml` | Main security scanning workflow |
| `.github/workflows/docker-security.yml` | Container security scanning |
| `.github/codeql-config.yml` | CodeQL advanced analysis |
| `.pre-commit-config.yaml` | Pre-commit security hooks |
| `scripts/security-scan.sh` | Local security scanning |
| `backend/pyproject.toml` | Python security dependencies |
| `frontend/package.json` | npm security scripts |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-04 | Initial security runbook creation | DevOps Team |
