# CSRF Token Implementation

## Problem
Django was rejecting POST/PUT/DELETE requests with error: `{"detail":"CSRF Failed: CSRF token missing."}`

## Root Cause
Django's CSRF protection requires a CSRF token to be sent with all non-GET requests when using session-based authentication. The frontend wasn't configured to:
1. Obtain the CSRF token from Django
2. Send it back in subsequent requests

## Solution Implemented

### 1. Backend Changes (Django)

#### Settings Configuration (`erp/settings.py`)
Added CSRF cookie settings to allow JavaScript to read the token:

```python
# CSRF Cookie Settings - For cross-origin requests
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read the cookie
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
```

#### New CSRF Endpoint (`finance/api.py`)
Created a dedicated endpoint to set the CSRF cookie:

```python
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    """
    Get CSRF token for subsequent requests.
    Call this endpoint first to get the CSRF cookie.
    """
    permission_classes = []  # Allow anyone to get CSRF token
    
    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})
```

#### URL Configuration (`erp/urls.py`)
Added the CSRF endpoint to URLs:

```python
path("api/csrf/", GetCSRFToken.as_view(), name="csrf"),
```

### 2. Frontend Changes (Next.js)

#### API Client (`frontend/src/lib/api.ts`)

**Added CSRF token extraction function:**
```typescript
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith(name + '=')) {
      return cookie.substring(name.length + 1);
    }
  }
  return null;
}
```

**Added CSRF token to request headers:**
```typescript
api.interceptors.request.use(
  (config) => {
    // Add CSRF token to headers for non-GET requests
    if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  ...
);
```

**Added initialization function:**
```typescript
export async function initCsrfToken(): Promise<void> {
  try {
    await axios.get('http://localhost:8000/api/csrf/', {
      withCredentials: true,
    });
    console.log('CSRF token initialized');
  } catch (error) {
    console.error('Failed to initialize CSRF token:', error);
  }
}
```

#### CSRF Initializer Component (`frontend/src/components/CSRFInitializer.tsx`)
Created a component that calls the CSRF endpoint on app load:

```typescript
'use client';

import { useEffect } from 'react';
import { initCsrfToken } from '@/lib/api';

export default function CSRFInitializer() {
  useEffect(() => {
    initCsrfToken();
  }, []);

  return null;
}
```

#### Root Layout (`frontend/src/app/layout.tsx`)
Added the initializer to the root layout:

```typescript
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CSRFInitializer />
        {children}
      </body>
    </html>
  );
}
```

## How It Works

1. **App Loads**: When the Next.js app loads, `CSRFInitializer` component runs
2. **Get Token**: It calls `GET /api/csrf/` which sets a `csrftoken` cookie
3. **Store Cookie**: Browser stores the cookie (httpOnly=false allows JS access)
4. **Make Request**: User performs action (create account, invoice, etc.)
5. **Extract Token**: Axios interceptor reads `csrftoken` from cookies
6. **Send Token**: Adds `X-CSRFToken` header to POST/PUT/DELETE requests
7. **Verify**: Django verifies the token matches the cookie
8. **Success**: Request proceeds normally

## Testing

After these changes:

1. Open http://localhost:3000
2. Open browser DevTools (F12) → Console
3. You should see: "CSRF token initialized"
4. Go to Application tab → Cookies → http://localhost:3000
5. You should see a `csrftoken` cookie
6. Try creating an account or other entity
7. Request should succeed without CSRF errors

## Verification in Logs

Django logs now show successful CSRF initialization:
```
[12/Oct/2025 20:00:58] "GET /api/csrf/ HTTP/1.1" 200 28
```

## Production Considerations

For production deployment:

1. **Enable HTTPS**: 
   ```python
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   ```

2. **Update trusted origins** to your production domain:
   ```python
   CSRF_TRUSTED_ORIGINS = [
       "https://yourdomain.com",
   ]
   ```

3. **Consider SameSite=Strict** for stricter security:
   ```python
   CSRF_COOKIE_SAMESITE = 'Strict'
   ```

## Alternative: Token-Based Authentication

For a more modern approach, consider implementing JWT authentication which doesn't require CSRF tokens. This current implementation is suitable for session-based authentication.
