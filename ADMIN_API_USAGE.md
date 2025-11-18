# Admin API Usage Guide

Quick reference for using authenticated admin endpoints.

## Setup

### 1. Generate Admin API Key

```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Add to Environment

```bash
# Add to your .env file
echo "ADMIN_API_KEY=your-generated-key-here" >> backend/.env
```

### 3. Restart Backend

```bash
cd backend
python run_backend.py
```

---

## Admin Endpoints

All admin endpoints require the `Authorization` header:

```
Authorization: Bearer YOUR_ADMIN_API_KEY
```

### 1. Get Newsletter Subscribers

**Endpoint:** `GET /admin/newsletter/subscribers`

**Example:**
```bash
curl http://localhost:5371/admin/newsletter/subscribers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

**Response:**
```json
{
  "subscribers": [
    {
      "id": "123",
      "email": "user@example.com",
      "subscribed_at": "2025-11-18T10:30:00Z",
      "analysis_type": "full",
      "experience_rating": "good"
    }
  ],
  "total": 42
}
```

---

### 2. Add Influencer to Marketplace

**Endpoint:** `POST /marketplace/influencers`

**Example:**
```bash
curl -X POST http://localhost:5371/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "example_influencer",
    "platform": "instagram",
    "is_featured": false,
    "category": "fashion",
    "admin_notes": "Verified manually, high quality content"
  }'
```

**Response:**
```json
{
  "id": 456,
  "handle": "example_influencer",
  "display_name": "Example Influencer",
  "platform": "instagram",
  "followers_count": 125000,
  "is_verified": true,
  "overall_trust_score": 0.85,
  "trust_label": "highly_trusted",
  "is_featured": false,
  "category": "fashion",
  "last_analyzed_at": "2025-11-18T12:00:00Z"
}
```

---

### 3. Remove Influencer from Marketplace

**Endpoint:** `DELETE /marketplace/influencers/{handle}`

**Example:**
```bash
curl -X DELETE http://localhost:5371/marketplace/influencers/example_influencer \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

**Response:**
```json
{
  "message": "Influencer @example_influencer removed from marketplace successfully."
}
```

---

## Error Responses

### Missing Authorization Header (401)

```bash
# Request without Authorization header
curl -X POST http://localhost:5371/marketplace/influencers \
  -H "Content-Type: application/json" \
  -d '{"handle": "test"}'
```

**Response:**
```json
{
  "detail": "Unauthorized. Authorization header required. Use: 'Authorization: Bearer YOUR_API_KEY'"
}
```

---

### Invalid API Key (401)

```bash
# Request with wrong API key
curl -X POST http://localhost:5371/marketplace/influencers \
  -H "Authorization: Bearer wrong-key-here" \
  -H "Content-Type: application/json" \
  -d '{"handle": "test"}'
```

**Response:**
```json
{
  "detail": "Unauthorized. Invalid API key."
}
```

---

### Rate Limit Exceeded (429)

Admin endpoints are rate limited to 10 requests per day per IP.

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "limit": 10,
    "remaining": 0,
    "reset_at": "2025-11-19T00:00:00+00:00",
    "message": "You have exceeded the daily limit of 10 requests. Please try again after 2025-11-19T00:00:00+00:00."
  }
}
```

---

## Python Example

```python
import os
import requests

# Load API key from environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
BASE_URL = "http://localhost:5371"

# Set up headers
headers = {
    "Authorization": f"Bearer {ADMIN_API_KEY}",
    "Content-Type": "application/json"
}

# Get newsletter subscribers
response = requests.get(
    f"{BASE_URL}/admin/newsletter/subscribers",
    headers=headers
)
print(response.json())

# Add influencer to marketplace
data = {
    "handle": "new_influencer",
    "platform": "instagram",
    "is_featured": True,
    "category": "tech",
    "admin_notes": "High-quality tech reviewer"
}
response = requests.post(
    f"{BASE_URL}/marketplace/influencers",
    headers=headers,
    json=data
)
print(response.json())

# Remove influencer from marketplace
response = requests.delete(
    f"{BASE_URL}/marketplace/influencers/old_influencer",
    headers=headers
)
print(response.json())
```

---

## JavaScript/TypeScript Example

```typescript
const ADMIN_API_KEY = process.env.ADMIN_API_KEY;
const BASE_URL = "http://localhost:5371";

const headers = {
  "Authorization": `Bearer ${ADMIN_API_KEY}`,
  "Content-Type": "application/json"
};

// Get newsletter subscribers
const subscribers = await fetch(`${BASE_URL}/admin/newsletter/subscribers`, {
  headers
}).then(res => res.json());

console.log(subscribers);

// Add influencer to marketplace
const newInfluencer = await fetch(`${BASE_URL}/marketplace/influencers`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    handle: "new_influencer",
    platform: "instagram",
    is_featured: true,
    category: "tech",
    admin_notes: "High-quality tech reviewer"
  })
}).then(res => res.json());

console.log(newInfluencer);

// Remove influencer from marketplace
const removed = await fetch(
  `${BASE_URL}/marketplace/influencers/old_influencer`,
  {
    method: "DELETE",
    headers
  }
).then(res => res.json());

console.log(removed);
```

---

## Security Best Practices

### ✅ Do's

- **Store API key in environment variables** - Never hardcode in source code
- **Use HTTPS in production** - Protect key in transit
- **Rotate keys periodically** - Generate new keys every 90 days
- **Use different keys per environment** - Separate keys for dev/staging/production
- **Monitor API usage** - Check rate limits and access logs

### ❌ Don'ts

- **Never commit API keys to git** - Add .env to .gitignore
- **Never share keys in chat/email** - Use secure secret management
- **Never log API keys** - Redact from application logs
- **Never use in frontend code** - Backend only!
- **Never use same key for multiple services** - Each service should have unique keys

---

## Troubleshooting

### "Admin API key not configured" (501)

**Problem:** `ADMIN_API_KEY` not set in environment.

**Solution:**
```bash
# Make sure .env file has the key
cat backend/.env | grep ADMIN_API_KEY

# If missing, add it:
echo "ADMIN_API_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> backend/.env

# Restart backend
```

---

### "Invalid authorization format" (401)

**Problem:** Authorization header not using `Bearer` format.

**Wrong:**
```bash
-H "Authorization: YOUR_API_KEY"  # Missing "Bearer "
```

**Correct:**
```bash
-H "Authorization: Bearer YOUR_API_KEY"  # Correct format
```

---

### "Rate limiting system unavailable" (503)

**Problem:** Supabase not configured or SQL schema not applied.

**Solution:**
1. Check Supabase connection in `.env`
2. Apply `backend/rate_limit_schema.sql` in Supabase SQL Editor
3. Restart backend

---

## Key Rotation

When rotating admin API keys:

1. **Generate new key:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update environment:**
   ```bash
   # Update .env file
   ADMIN_API_KEY=new-key-here
   ```

3. **Restart backend:**
   ```bash
   cd backend
   python run_backend.py
   ```

4. **Update all clients:**
   - Update any scripts or tools using the old key
   - Test with new key before fully migrating

5. **Verify old key is revoked:**
   ```bash
   # Test with old key - should fail
   curl http://localhost:5371/admin/newsletter/subscribers \
     -H "Authorization: Bearer old-key-here"
   ```

---

## Rate Limits

All admin endpoints share the **admin** rate limit group:

- **Limit:** 10 requests per day per IP
- **Reset:** Midnight UTC
- **Scope:** All `/admin/*` and marketplace write endpoints

To check your current usage:

```sql
-- In Supabase SQL Editor
SELECT client_ip, request_count, window_start, last_request_at
FROM rate_limits
WHERE endpoint_group = 'admin'
  AND window_start >= CURRENT_DATE;
```

---

## Quick Reference

| Endpoint | Method | Auth Required | Rate Limit |
|----------|--------|---------------|------------|
| `/admin/newsletter/subscribers` | GET | ✅ Yes | 10/day |
| `/marketplace/influencers` | POST | ✅ Yes | 10/day |
| `/marketplace/influencers/{handle}` | DELETE | ✅ Yes | 10/day |
| `/marketplace/influencers` | GET | ❌ No | None |
| `/marketplace/influencers/{handle}` | GET | ❌ No | None |

---

For more details, see:
- `SECURITY_FIXES_COMPLETE.md` - Complete security overview
- `backend/RATE_LIMITING_SETUP.md` - Rate limiting setup guide
- `SECURITY_STATUS.md` - Original security audit
