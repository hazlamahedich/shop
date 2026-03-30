# Story 12-4: File Upload Security Hardening

**Epic**: 12 - Security Hardening
**Priority**: P1 (High)
**Status**: backlog
**Estimate**: 6 hours
**Dependencies**: None

## Problem Statement

File upload security needs enhancement to prevent:
- Malicious file uploads
- Path traversal attacks
- MIME type spoofing
- ZIP bomb attacks
- Virus/malware uploads

## Acceptance Criteria

- [ ] File type validation by content (magic bytes), not just extension
- [ ] Maximum file size enforced at multiple layers
- [ ] Filename sanitization (no path traversal)
- [ ] Virus scanning integration (ClamAV or similar)
- [ ] Image re-encoding to strip metadata
- [ ] Separate storage domain for uploads
- [ ] Rate limiting on upload endpoints
- [ ] Audit logging for uploads

## Technical Design

### File Validation

```python
# backend/app/core/file_validation.py
import magic

ALLOWED_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'application/pdf': ['.pdf'],
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(content: bytes, filename: str) -> bool:
    # Check magic bytes
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Invalid file type: {mime_type}")
    
    # Check size
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError("File too large")
    
    # Sanitize filename
    safe_filename = secure_filename(filename)
    
    return True
```

### Virus Scanning

```python
# backend/app/core/virus_scan.py
import clamd

async def scan_file(content: bytes) -> bool:
    try:
        cd = clamd.ClamdUnixSocket()
        result = cd.instream(BytesIO(content))
        return result['stream'][0] == 'OK'
    except Exception:
        # Fail closed - reject if scanner unavailable
        return False
```

## Testing Strategy

1. Test allowed file types
2. Test blocked file types (executables, scripts)
3. Test MIME type spoofing detection
4. Test file size limits
5. Test path traversal attempts
6. Test virus scanning (EICAR test file)

## Related Files

- `backend/app/core/file_validation.py` (new)
- `backend/app/core/virus_scan.py` (new)
- `backend/app/api/upload.py`
- `backend/tests/unit/test_file_validation.py`
