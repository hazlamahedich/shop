# Story 12-9: Security Test Suite

**Epic**: 12 - Security Hardening
**Priority**: P2 (Medium)
**Status**: backlog
**Estimate**: 8 hours
**Dependencies**: None

## Problem Statement

No dedicated security test suite exists. Security tests are scattered across the codebase.

## Acceptance Criteria

- [ ] Dedicated security test directory structure
- [ ] Authentication security tests
- [ ] Authorization/security tests
- [ ] Input validation security tests
- [ ] Rate limiting tests
- [ ] CSRF protection tests
- [ ] Encryption tests
- [ ] SQL injection tests (parameterized queries verified)
- [ ] XSS prevention tests
- [ ] Test fixtures for security scenarios

## Technical Design

### Test Structure

```
backend/tests/security/
├── __init__.py
├── conftest.py
├── test_authentication.py
├── test_authorization.py
├── test_csrf.py
├── test_encryption.py
├── test_input_validation.py
├── test_rate_limiting.py
├── test_sql_injection.py
└── test_xss.py
```

### Example Tests

```python
# backend/tests/security/test_authentication.py
import pytest

class TestAuthenticationSecurity:
    async def test_brute_force_protection(self, client):
        """Test account lockout after failed attempts"""
        for _ in range(6):
            response = await client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrong"
            })
        
        assert response.status_code == 429
        
    async def test_timing_attack_resistance(self, client):
        """Test constant-time comparison for passwords"""
        import time
        
        times = []
        for password in ["a", "aaaaaaaaaaaaaaaa"]:
            start = time.time()
            await client.post("/auth/login", json={
                "email": "test@example.com",
                "password": password
            })
            times.append(time.time() - start)
        
        # Times should be similar (within 50ms)
        assert abs(times[0] - times[1]) < 0.05
```

```python
# backend/tests/security/test_sql_injection.py
class TestSQLInjection:
    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1; SELECT * FROM users",
    ])
    async def test_sql_injection_blocked(self, client, payload, auth_header):
        """Verify SQL injection payloads are blocked"""
        response = await client.get(
            f"/api/users?search={payload}",
            headers=auth_header
        )
        
        # Should not return error with SQL details
        assert "sql" not in response.text.lower()
        assert "error" not in response.text.lower() or response.status_code == 400
```

## Testing Strategy

1. Run all security tests
2. Add to CI pipeline
3. Regular security test reviews
4. Penetration testing validation

## Related Files

- `backend/tests/security/` (new)
- `backend/tests/security/conftest.py` (new)
- `.github/workflows/security.yml`
