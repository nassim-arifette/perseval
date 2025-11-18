# Rate Limiting Setup Instructions

## Overview
We've implemented IP-based rate limiting for all expensive API endpoints to protect against abuse and quota exhaustion.

**Rate Limit:** 10 requests per day per IP address

**Protected Endpoints:**
- `/analyze/text` - Text analysis using Mistral AI
- `/analyze/full` - Full analysis with Instagram/TikTok scraping
- `/influencer/stats` - Instagram data via Instaloader
- `/influencer/trust` - Influencer trust scoring
- `/company/trust` - Company reputation via Serper API
- `/product/trust` - Product reliability via Serper API

## Security Features

### ✅ What's Fixed:
1. **IP-Based Rate Limiting**: Uses actual request IP, not spoofable headers
2. **Fail-Closed Design**: If rate limiting system fails, requests are blocked (not allowed)
3. **Separate Quotas**: Different endpoint groups can have different limits
4. **Daily Reset**: Quotas reset at midnight UTC
5. **Race Condition Safe**: Uses database row locking

### 🔒 How It Works:
- Rate limits are tracked in Supabase using PostgreSQL functions
- The system uses `request.client.host` from FastAPI (cannot be spoofed)
- Each IP gets 10 requests per day across all endpoints in a group
- After 10 requests, the API returns HTTP 429 with reset time

## Setup Steps

### 1. Apply the SQL Schema

Open your Supabase dashboard and navigate to the SQL Editor:

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy the entire contents of `backend/rate_limit_schema.sql`
6. Paste into the SQL editor
7. Click "Run" or press `Ctrl+Enter`

### 2. Verify Installation

Run this SQL query to verify the tables and functions were created:

```sql
-- Check if the rate_limits table exists
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'rate_limits';

-- Check if the functions exist
SELECT routine_name
FROM information_schema.routines
WHERE routine_name IN (
    'check_and_increment_rate_limit',
    'get_rate_limit_status',
    'cleanup_old_rate_limits'
);
```

You should see:
- One table: `rate_limits`
- Three functions: `check_and_increment_rate_limit`, `get_rate_limit_status`, `cleanup_old_rate_limits`

### 3. Restart Your Backend

```bash
# Stop the backend if it's running
# Then start it again:
cd backend
python run_backend.py
```

### 4. Test Rate Limiting

```bash
# Test with a simple curl command (run this 11 times):
curl -X POST http://localhost:5371/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

# The 11th request should return HTTP 429 with a message like:
# {
#   "detail": {
#     "error": "Rate limit exceeded",
#     "limit": 10,
#     "remaining": 0,
#     "reset_at": "2025-11-19T00:00:00+00:00",
#     "message": "You have exceeded the daily limit of 10 requests..."
#   }
# }
```

## Configuration

### Adjusting the Daily Limit

To change the rate limit from 10 to a different number:

1. Open `backend/rate_limiter.py`
2. Change the `DAILY_LIMIT` constant:
   ```python
   DAILY_LIMIT = 20  # Change from 10 to 20, for example
   ```
3. Restart the backend

### Different Limits for Different Endpoint Groups

Currently, we have three endpoint groups:
- `"analysis"` - Text and full analysis endpoints
- `"influencer"` - Influencer stats and trust endpoints
- `"trust"` - Company and product trust endpoints

All share the same 10/day limit. To implement different limits:

1. Modify the `check_rate_limit()` calls in `backend/api/routes.py`
2. Pass different limit values based on the endpoint group
3. Update the rate limiter to accept per-group limits

## Maintenance

### Cleaning Up Old Records

The rate limiting system stores records in Supabase. To prevent table bloat, run this cleanup function periodically (e.g., weekly):

```sql
-- Delete rate limit records older than 7 days
SELECT cleanup_old_rate_limits();
```

You can automate this by creating a Supabase cron job or pg_cron task.

## Monitoring

### Check Current Rate Limit Status

```sql
-- See all current rate limits
SELECT
    client_ip,
    endpoint_group,
    request_count,
    window_start,
    last_request_at
FROM rate_limits
WHERE window_start >= CURRENT_DATE
ORDER BY last_request_at DESC;

-- Find IPs hitting the limit
SELECT
    client_ip,
    endpoint_group,
    request_count,
    last_request_at
FROM rate_limits
WHERE window_start >= CURRENT_DATE
  AND request_count >= 10
ORDER BY request_count DESC;
```

### Manually Reset a Rate Limit

If you need to reset the rate limit for a specific IP:

```sql
-- Delete the rate limit record for an IP
DELETE FROM rate_limits
WHERE client_ip = '192.168.1.100'
  AND endpoint_group = 'analysis';

-- Or reset the counter to 0
UPDATE rate_limits
SET request_count = 0,
    window_start = DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
WHERE client_ip = '192.168.1.100'
  AND endpoint_group = 'analysis';
```

## Known Limitations

1. **Local Development**: When testing locally, all requests come from `127.0.0.1`, so you'll hit the limit quickly. Consider increasing the limit for development.

2. **Shared IPs**: Users behind NAT or corporate proxies share the same public IP, so they share the rate limit quota.

3. **No User Authentication**: This is IP-based only. When you implement proper authentication (JWT, OAuth), you should switch to user-based rate limiting.

## Future Improvements

When you have time to implement proper authentication:

1. **User-Based Rate Limiting**: Track limits per authenticated user ID instead of IP
2. **Tiered Plans**: Free users get 10/day, paid users get 1000/day
3. **API Keys**: Issue API keys for programmatic access
4. **Admin Exemptions**: Certain users or API keys bypass rate limits
5. **Geographic Limits**: Different limits based on user location
6. **Endpoint-Specific Limits**: More granular control per individual endpoint

## Troubleshooting

### "Rate limiting system unavailable" (HTTP 503)

This means the Supabase connection or RPC call failed. Check:
- Supabase is accessible
- SQL functions were created correctly
- Supabase credentials in `.env` are correct

### Rate limit not working (no 429 errors)

Check:
- SQL schema was applied successfully
- Backend was restarted after code changes
- No errors in backend console logs

### False positives (legitimate users blocked)

Consider:
- Increasing `DAILY_LIMIT` in `rate_limiter.py`
- Implementing user authentication instead of IP-based limits
- Exempting certain IPs (requires code changes)
