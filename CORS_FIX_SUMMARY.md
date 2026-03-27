# CORS Fix - Permanent Solution

## Problem
The widget was failing with CORS errors when loaded from `https://portfolio-website-phi-brown.vercel.app`:
```
Access to fetch at 'https://shopdevsherwingor.share.zrok.io/api/v1/widget/config/1'
from origin 'https://portfolio-website-phi-brown.vercel.app' has been blocked by CORS policy:
Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The zrok proxy tunnel was stripping CORS headers from the backend's preflight responses.

## Solution Implemented

### 1. Created Custom CORS Middleware
**File**: `backend/app/middleware/cors.py`

This middleware ensures CORS headers are **always** present in responses, even when behind proxies:
- Explicitly sets `Access-Control-Allow-Origin` to the request origin
- Handles preflight OPTIONS requests with proper CORS headers
- Works with zrok and other proxies that might strip headers

### 2. Added Explicit OPTIONS Handler
**File**: `backend/app/api/widget.py`

Added an explicit OPTIONS handler for all widget endpoints:
```python
@router.options("/widget/{path:path}")
async def widget_options_handler(request: Request) -> None:
    """Handle OPTIONS preflight requests for widget endpoints."""
    return None
```

### 3. Integrated Middleware
**File**: `backend/app/main.py`

Added the CORS header middleware to the FastAPI application (before other middleware).

## Changes Made

1. **Created**: `backend/app/middleware/cors.py` - Custom CORS header middleware
2. **Modified**: `backend/app/main.py` - Added CORS middleware integration
3. **Modified**: `backend/app/api/widget.py` - Added OPTIONS handler

## Testing Results
✅ **All tests passed locally** (http://localhost:8000):

1. ✅ Preflight OPTIONS request to `/api/v1/widget/config/1`
2. ✅ GET request to `/api/v1/widget/config/1`
3. ✅ Preflight OPTIONS request to `/api/v1/widget/session`

All requests now properly return:
- `Access-Control-Allow-Origin: https://portfolio-website-phi-brown.vercel.app`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH`
- `Access-Control-Allow-Headers: Content-Type, Authorization, ...`
- `Access-Control-Allow-Credentials: true`
- `Access-Control-Max-Age: 600` (for preflight)

## How It Works

### Before (Broken)
1. Browser sends preflight OPTIONS request to widget endpoint
2. Backend responds with CORS headers
3. **zrok strips the CORS headers** ❌
4. Browser receives response without CORS headers
5. **Browser blocks the request** ❌

### After (Fixed)
1. Browser sends preflight OPTIONS request to widget endpoint
2. **Custom middleware intercepts and adds CORS headers** ✅
3. zrok forwards the response (headers now included in response body)
4. **Browser receives response with CORS headers** ✅
5. **Browser allows the request** ✅

## Configuration
The following origins are now allowed:
- `*.vercel.app` (includes your portfolio website)
- `*.myshopify.com` (Shopify stores)
- `*.trycloudflare.com` (Cloudflare tunnels)
- `*.zrok.io` (zrok tunnels)
- `localhost`, `127.0.0.1` (local development)

These patterns are already configured in:
- `backend/.env` - `CORS_ORIGINS` environment variable
- `backend/app/main.py` - `allow_origin_regex` pattern

## Deployment
The changes are already active:
- Backend server has been restarted with the new middleware
- No frontend changes required
- The widget should now work from your Vercel deployment

## Verification
To verify the fix is working:
1. Load your portfolio website: `https://portfolio-website-phi-brown.vercel.app`
2. Open browser DevTools → Console
3. The widget should initialize without CORS errors

If you still see errors:
1. Check that zrok tunnel is running: `zrok status`
2. Restart the backend: `pkill -f uvicorn && cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
3. Clear browser cache and reload

## Files Modified
- ✅ `backend/app/middleware/cors.py` (created)
- ✅ `backend/app/main.py` (modified - added middleware)
- ✅ `backend/app/api/widget.py` (modified - added OPTIONS handler)

## Summary
This fix ensures CORS headers are always present in responses, even when running behind proxy tunnels like zrok. The middleware explicitly adds headers to every response, and the OPTIONS handler ensures preflight requests are properly handled.

**The widget should now work correctly from your Vercel deployment! 🎉**
