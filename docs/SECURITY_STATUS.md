# Security Status Report

## ✅ FIXED: Rate Limiting on Expensive Endpoints

**Problem:** Anonymous users could hammer expensive API endpoints (`/analyze/*`, `/influencer/*`, `/company/trust`, `/product/trust`), burning through paid API quotas (Mistral AI, Serper, Instaloader, TikTok APIs).

**Solution Implemented:**
- **IP-based rate limiting**: 10 requests per day per IP address
- **Fail-closed design**: If rate limiting fails, requests are blocked (no fail-open vulnerability)
- **Cannot be bypassed**: Uses actual request IP from FastAPI, not spoofable headers
- **Protected endpoints**:
  - `POST /analyze/text` - Mistral AI text analysis
  - `POST /analyze/full` - Full analysis with social media scraping
  - `POST /influencer/stats` - Instagram data via Instaloader
  - `POST /influencer/trust` - Influencer trust scoring
  - `POST /company/trust` - Company reputation via Serper
  - `POST /product/trust` - Product reliability via Serper

**Files Modified:**
- `backend/rate_limiter.py` - New rate limiting module
- `backend/rate_limit_schema.sql` - Database schema for rate tracking
- `backend/api/routes.py` - Added rate limiting to all expensive endpoints
- `backend/RATE_LIMITING_SETUP.md` - Setup and configuration guide

**Status:** ✅ Complete (requires SQL schema deployment)

---

## ⚠️ REMAINING CRITICAL ISSUES

### 1. Marketplace Write Operations - No Authentication

**Location:** `backend/api/routes.py` (lines 370-588)

**Problem:**
- `POST /marketplace/add` - Anyone can create marketplace influencer entries
- `POST /marketplace/remove` - Anyone can delete marketplace entries
- No admin check or authentication
- Uses Supabase service-role key (full database access)

**Risk:** Attacker can:
- Create fake influencer listings
- Overwrite existing marketplace data
- Delete all marketplace entries
- Corrupt the marketplace database

**Recommended Fix:**
```python
# Add authentication decorator
from fastapi import Depends, Header
from backend.auth import verify_admin_token

@router.post("/marketplace/add")
async def add_to_marketplace(
    req: AddToMarketplaceRequest,
    request: Request,
    admin_token: str = Header(..., alias="X-Admin-Token")
):
    verify_admin_token(admin_token)  # Raises 401/403 if invalid
    # ... rest of the function
```

**Priority:** 🔴 Critical - Implement before production launch

---

### 2. Admin Notes Leaked in Public Responses

**Location:** `backend/api/routes.py` (lines 421, 474, 565)

**Problem:**
- Marketplace list/detail endpoints return `admin_notes` field to all users
- Sensitive comments, internal flags, and moderation notes are exposed
- No filtering of private fields

**Risk:** Internal moderation data, reasons for blocking/flagging influencers, and sensitive comments are visible to attackers and competitors.

**Recommended Fix:**
```python
# In backend/supabase_client.py - list_marketplace_influencers()
def list_marketplace_influencers(req: MarketplaceListRequest) -> MarketplaceListResponse:
    # ... existing query code ...

    influencers = []
    for row in data:
        # Remove admin_notes from public responses
        influencer_data = {**row}
        if 'admin_notes' in influencer_data:
            del influencer_data['admin_notes']
        influencers.append(MarketplaceInfluencer(**influencer_data))

    return MarketplaceListResponse(influencers=influencers, total=total)
```

**Priority:** 🔴 Critical - Fix immediately

---

### 3. Feedback Rate Limiting Bypass

**Location:**
- `backend/api/routes.py` (lines 599-606)
- `frontend/src/app/api/feedback/route.ts` (lines 10-20)
- `backend/supabase_client.py` (lines 488-512)

**Problems:**
1. **Trusts user-supplied headers**: Backend accepts `X-Forwarded-For` and `X-Session-ID` from client
2. **Next.js proxy forwards attacker headers**: Frontend API route passes through whatever the client sends
3. **Fails open on errors**: If Supabase/RPC errors occur, limiter allows the request through

**Risk:**
- Attacker can spoof new headers per request to bypass rate limits
- Can call backend directly with forged headers
- Can intentionally trigger exceptions to disable rate limiting
- Can spam feedback/newsletter submissions

**Recommended Fix:**

In `backend/api/routes.py`:
```python
@router.post("/feedback")
async def submit_feedback(req: UserFeedbackRequest, request: Request):
    # Use actual IP, not headers
    client_ip = request.client.host if request.client else "unknown"

    # Remove X-Session-ID from trusted sources
    # Or generate server-side session IDs

    try:
        # Check rate limit (fail closed)
        allowed = check_feedback_rate_limit(client_ip)
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many feedback submissions")
    except HTTPException:
        raise  # Re-raise HTTP errors
    except Exception as e:
        # FAIL CLOSED: block on error
        raise HTTPException(status_code=503, detail="Rate limiting unavailable")

    # ... rest of feedback logic
```

**Priority:** 🟠 High - Fix before accepting user feedback

---

### 4. Admin API Key in Query String

**Location:** `backend/api/routes.py` (lines 648-681)

**Problem:**
- Newsletter export endpoint: `GET /admin/newsletter/export?api_key=SECRET`
- API key appears in:
  - Server access logs
  - Browser history
  - Referrer headers
  - Proxy logs
- No rate limiting or brute-force protection

**Risk:**
- Key can be brute-forced
- Key leaks in logs and browser history
- Anyone with logs can access admin endpoints

**Recommended Fix:**
```python
from fastapi import Header

@router.get("/admin/newsletter/export")
async def export_newsletter(
    request: Request,
    authorization: str = Header(..., alias="Authorization")
):
    # Rate limit admin endpoints too
    check_rate_limit(request, endpoint_group="admin")

    # Validate Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization")

    token = authorization.replace("Bearer ", "")
    if not verify_admin_token(token):  # Compare with hashed secret
        raise HTTPException(status_code=403, detail="Invalid admin token")

    # ... rest of export logic
```

**Priority:** 🟠 High - Fix before exposing admin endpoints

---

### 5. SQL Injection in Supabase Search

**Location:** `backend/supabase_client.py` (lines 396-404)

**Problem:**
- User-controlled search term is directly interpolated into `.or_()` filter
- Crafted input with commas/parentheses can rewrite the PostgREST filter
- Can alter query conditions or crash the query

**Example Exploit:**
```python
search_term = "test,handle.eq.admin),admin_notes.is.null"
# Produces: .or_(f"handle.ilike.%{search_term}%,full_name.ilike.%{search_term}%")
# PostgREST interprets this as multiple conditions
```

**Recommended Fix:**
```python
def list_marketplace_influencers(req: MarketplaceListRequest) -> MarketplaceListResponse:
    # ... existing code ...

    if req.search_term:
        # ESCAPE special characters in search term
        import re
        safe_search = re.sub(r'[,().]', '', req.search_term.strip())
        # Or use URL encoding
        from urllib.parse import quote
        safe_search = quote(req.search_term.strip())

        query = query.or_(
            f"handle.ilike.%{safe_search}%,full_name.ilike.%{safe_search}%"
        )
```

**Priority:** 🟠 High - Fix before accepting user search input

---

### 6. Automatic Marketplace Upsert in Full Analysis

**Location:** `backend/api/routes.py` (lines 223-256)

**Problem:**
- `POST /analyze/full` automatically upserts influencer data to marketplace
- No authentication check
- Anyone can pollute the marketplace by analyzing random influencers

**Risk:**
- Marketplace filled with junk data
- Attackers can track which influencers are being analyzed
- Can overwrite existing marketplace entries

**Recommended Fix:**
```python
# In analyze_full() function:
# Remove or make conditional:
if influencer_trust and is_admin(request):  # Only admins can add to marketplace
    add_influencer_to_marketplace(AddToMarketplaceRequest(
        handle=influencer_trust.stats.handle,
        # ...
    ))
```

**Priority:** 🟡 Medium - Review logic, possibly disable auto-upsert

---

## 📋 Priority Action Items

### Before Production Launch:
1. 🔴 **Apply rate limiting SQL schema** (`backend/rate_limit_schema.sql`)
2. 🔴 **Strip `admin_notes` from public API responses**
3. 🔴 **Add authentication to marketplace write endpoints**
4. 🟠 **Fix feedback rate limiting bypass** (use real IP, fail closed)
5. 🟠 **Move admin API key to Authorization header**
6. 🟠 **Sanitize Supabase search filters** (escape special chars)

### Future Improvements (When You Have Time):
- Implement proper authentication (JWT, OAuth, or API keys)
- User-based rate limiting instead of IP-based
- Role-based access control (RBAC) for admin operations
- API key rotation and hashing
- Audit logging for sensitive operations
- Web Application Firewall (WAF) for additional protection

---

## 🛠️ How to Deploy Rate Limiting

1. **Apply SQL Schema:**
   - Open Supabase dashboard → SQL Editor
   - Run `backend/rate_limit_schema.sql`

2. **Verify Setup:**
   ```sql
   SELECT * FROM rate_limits LIMIT 5;
   SELECT routine_name FROM information_schema.routines
   WHERE routine_name LIKE '%rate_limit%';
   ```

3. **Restart Backend:**
   ```bash
   cd backend
   python run_backend.py
   ```

4. **Test:**
   ```bash
   # Make 11 requests to trigger rate limit
   for i in {1..11}; do
     curl -X POST http://localhost:5371/analyze/text \
       -H "Content-Type: application/json" \
       -d '{"text": "test"}';
     echo "Request $i";
   done
   ```

See `backend/RATE_LIMITING_SETUP.md` for detailed instructions.

---

## 📞 Questions?

If you need help implementing any of these fixes or have questions about the security improvements, please reach out!

**Current Status:**
- ✅ Rate limiting implemented and ready to deploy
- ⚠️ 5 critical/high priority issues remain
- ⏳ Proper authentication system needed for production
