# Story: Merchant Registration

**Status:** ✅ Complete
**Date Completed:** 2026-03-10
**Sprint:** Auth & Onboarding

---

## Overview

A public registration endpoint and page allowing new merchants to create accounts. The feature provides a simple registration form with email and password, automatic login upon successful registration, and redirects new users to the onboarding flow.

---

## Requirements

### User Stories
- As a new merchant, I want to create an account so I can access the dashboard
- As a new merchant, I want to be automatically logged in after registration so I can start onboarding immediately
- As a new merchant, I want clear feedback if my email is already registered or password doesn't meet requirements

### Acceptance Criteria
- [x] Registration page accessible at `/register`
- [x] Email input with format validation
- [x] Password input with requirements display (8+ chars, uppercase, lowercase)
- [x] Confirm password input with matching validation
- [x] "Sign up" link on login page directing to registration
- [x] "Sign in" link on registration page directing to login
- [x] Auto-login upon successful registration (session cookie set)
- [x] Redirect to `/onboarding` after successful registration
- [x] Error handling for email already registered (code 2010)
- [x] Error handling for password requirements not met (code 2012)
- [x] Rate limiting on registration endpoint (5 per 15 min per IP/email)
- [x] CSRF bypass for registration endpoint

---

## Implementation

### Frontend Components

| Component | File | Description |
|-----------|------|-------------|
| Register Page | `frontend/src/pages/Register.tsx` | Registration form with email/password/confirm |
| Login Page | `frontend/src/pages/Login.tsx` | Modified to include "Sign up" link |
| Auth Service | `frontend/src/services/auth.ts` | Added `register()` API function |
| Auth Store | `frontend/src/stores/authStore.ts` | Added `register()` action |
| Auth Types | `frontend/src/types/auth.ts` | Added `RegisterRequest` interface |
| App Router | `frontend/src/components/App.tsx` | Added `/register` route |

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Create new merchant account with auto-login |

### Request/Response

```typescript
// Request
interface RegisterRequest {
  email: string;
  password: string;
}

// Response (201 Created)
{
  "data": {
    "merchant": {
      "id": number;
      "email": string;
      "merchant_key": string;
      "store_provider": string;
      "has_store_connected": boolean;
    },
    "session": {
      "expiresAt": string; // ISO-8601
    }
  },
  "meta": {
    "request_id": string;
    "timestamp": string;
  }
}
```

### Data Models

**Backend Schema (`backend/app/schemas/auth.py`):**
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min 8 chars
```

---

## Security Considerations

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter

### Protections
- Password hashed with bcrypt before storage
- Rate limiting (5 attempts per 15 minutes per IP/email)
- HttpOnly, Secure, SameSite=Strict cookie for session
- Generic error messages (don't reveal if email exists until after validation)
- CSRF bypass only for public registration endpoint

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 2010 | Email already registered | Email address already in database |
| 2012 | Password requirements not met | Password doesn't meet complexity rules |

---

## User Flow

```
/register → Fill form → Submit →
  ↓
Validation (client + server) →
  ↓
Create merchant + session →
  ↓
Set httpOnly cookie →
  ↓
Redirect to /onboarding
```

---

## Files Changed

### New Files
| File | Description |
|------|-------------|
| `backend/app/schemas/auth.py` | Pydantic schema for registration |
| `frontend/src/pages/Register.tsx` | Registration page component |

### Modified Files
| File | Changes |
|------|---------|
| `backend/app/api/auth.py` | Added `POST /register` endpoint |
| `backend/app/middleware/auth.py` | Added `/api/v1/auth/register` to CSRF bypass |
| `backend/app/core/errors.py` | Added `PASSWORD_REQUIREMENTS_NOT_MET = 2012` |
| `frontend/src/types/auth.ts` | Added `RegisterRequest` interface |
| `frontend/src/services/auth.ts` | Added `register()` API function |
| `frontend/src/stores/authStore.ts` | Added `register()` action |
| `frontend/src/pages/Login.tsx` | Added "Sign up" link |
| `frontend/src/components/App.tsx` | Added `/register` route |

---

## Definition of Done

- [x] All acceptance criteria met
- [x] Frontend registration page implemented
- [x] Backend registration endpoint functional
- [x] Auto-login after registration
- [x] Redirect to onboarding flow
- [x] Error handling implemented
- [x] Rate limiting applied
- [x] CSRF bypass configured
- [x] Code follows existing patterns

---

## Future Enhancements

1. **Email verification** - Require email confirmation before account access
2. **Password strength meter** - Visual indicator of password strength
3. **OAuth registration** - Sign up with Google, GitHub, etc.
4. **Invitation system** - Require invitation code for registration
5. **Terms of service** - Require acceptance of terms during registration
6. **CAPTCHA** - Bot protection for registration form

---

## Related Documentation

- [AGENTS.md](../AGENTS.md) - Story start checklist
- [Error Code Governance](./error-code-governance.md)
