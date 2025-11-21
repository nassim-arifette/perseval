# Marketplace Guide

## Overview

The Perseval Marketplace is a curated directory of influencers with verified trust scores and comprehensive reputation analysis. It allows users to discover trustworthy influencers and understand their credibility through AI-powered analysis.

## Features

### 🔍 Trust Score Calculation

The marketplace uses a sophisticated multi-factor trust scoring system:

1. **Message History Score (30%)** - Analyzes recent posts for scam indicators
2. **Followers Score (15%)** - Evaluates follower count and follower/following ratio
3. **Web Reputation Score (40%)** - Web research via Perplexity AI or Serper
4. **Disclosure Score (15%)** - Checks for proper ad disclosure (#ad, #sponsored, etc.)

### 🤖 AI-Powered Reputation Analysis

**Perplexity AI Integration (Primary)**
- Uses Perplexity Sonar model for comprehensive web research
- Provides citations and factual information
- Searches for controversies, lawsuits, and reputation issues
- Analyzes disclosure practices and sponsored content

**Serper API (Fallback)**
- Automatic fallback if Perplexity is unavailable
- Ensures continuous service availability

### 📊 Trust Levels

- **High Trust (≥75%)**: Green badge - Consistently trustworthy content
- **Medium Trust (40-74%)**: Yellow badge - Mixed signals, proceed with caution
- **Low Trust (<40%)**: Red badge - Multiple red flags detected

## Architecture

### Backend Components

#### 1. Database Schema (`backend/sql/supabase_schema.sql`)

> After provisioning the base schema above, apply the incremental scripts in `backend/sql/migrations` in order. Each migration is idempotent, so you can re-run them whenever new files appear without worrying about existing data.

```sql
-- Marketplace influencers table
CREATE TABLE marketplace_influencers (
    id UUID PRIMARY KEY,
    handle TEXT NOT NULL,
    platform TEXT (instagram, tiktok, youtube, etc.),

    -- Profile data
    display_name TEXT,
    bio TEXT,
    followers_count INTEGER,
    is_verified BOOLEAN,

    -- Trust scores
    overall_trust_score DECIMAL(3, 2),
    trust_label TEXT,
    message_history_score DECIMAL(3, 2),
    followers_score DECIMAL(3, 2),
    web_reputation_score DECIMAL(3, 2),
    disclosure_score DECIMAL(3, 2),

    -- Metadata
    analysis_summary TEXT,
    issues JSONB,
    last_analyzed_at TIMESTAMPTZ,
    is_featured BOOLEAN
);
```

#### 2. Repository Layer (`backend/app/repositories/marketplace.py`)

Functions:
- `add_influencer_to_marketplace()` - Add/update influencer
- `list_marketplace_influencers()` - List with filters and pagination
- `get_marketplace_influencer()` - Get single influencer details
- `remove_from_marketplace()` - Remove influencer

#### 3. Trust Calculation (`backend/app/services/trust.py`)

- `compute_message_history_score()` - Scam detection on posts
- `compute_followers_score()` - Follower metrics analysis
- `compute_disclosure_score()` - Ad disclosure compliance
- `combine_trust_score()` - Weighted combination
- `build_influencer_trust_response()` - Complete analysis pipeline

#### 4. Web Search (`backend/app/services/web_search.py`)

- `search_with_perplexity()` - Perplexity Sonar API integration
- `search_with_serper()` - Serper API fallback
- `web_search()` - Unified interface with automatic fallback
- `multi_query_search()` - Execute multiple searches and deduplicate

#### 5. API Endpoints (`backend/api/routes.py`)

**Public Endpoints:**
- `GET /marketplace/influencers` - List influencers with filters
- `GET /marketplace/influencers/{handle}` - Get influencer details

**Admin Endpoints (Require Authentication):**
- `POST /marketplace/influencers` - Add influencer to marketplace
- `DELETE /marketplace/influencers/{handle}` - Remove influencer

### Frontend Components

#### Marketplace Page (`frontend/src/app/marketplace/page.tsx`)

Features:
- Real-time search by handle or name
- Filter by trust level (high/medium/low)
- Sort by trust score, followers, or last analyzed date
- Responsive card-based layout
- Detailed influencer profiles with expandable modals
- Trust score visualization with color coding

## API Usage

### 1. List Marketplace Influencers

```bash
GET /api/marketplace/influencers

Query Parameters:
- search: string (optional) - Search by handle or display name
- trust_level: 'high' | 'medium' | 'low' (optional)
- sort_by: 'trust_score' | 'followers' | 'last_analyzed'
- sort_order: 'asc' | 'desc'
- limit: number (default: 20, max: 100)
- offset: number (default: 0)

Response:
{
  "influencers": [
    {
      "id": "uuid",
      "handle": "example",
      "platform": "instagram",
      "display_name": "Example User",
      "followers_count": 100000,
      "overall_trust_score": 0.85,
      "trust_label": "high",
      "analysis_summary": "...",
      "last_analyzed_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 2. Get Influencer Details

```bash
GET /api/marketplace/influencers/{handle}?platform=instagram

Response:
{
  "id": "uuid",
  "handle": "example",
  "platform": "instagram",
  "display_name": "Example User",
  "bio": "Content creator...",
  "followers_count": 100000,
  "following_count": 500,
  "is_verified": true,
  "overall_trust_score": 0.85,
  "trust_label": "high",
  "message_history_score": 0.90,
  "followers_score": 0.80,
  "web_reputation_score": 0.85,
  "disclosure_score": 0.75,
  "analysis_summary": "...",
  "issues": [],
  "last_analyzed_at": "2025-01-15T10:30:00Z",
  "is_featured": false
}
```

### 3. Add Influencer (Admin Only)

```bash
POST /api/marketplace/influencers
Authorization: Bearer YOUR_ADMIN_API_KEY

Request Body:
{
  "handle": "example",
  "platform": "instagram",
  "admin_notes": "Featured creator",
  "is_featured": true
}

Response:
{
  // Full influencer object with calculated trust scores
}
```

### 4. Remove Influencer (Admin Only)

```bash
DELETE /api/marketplace/influencers/{handle}?platform=instagram
Authorization: Bearer YOUR_ADMIN_API_KEY

Response:
{
  "message": "Influencer @example removed from marketplace successfully."
}
```

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required
MISTRAL_API_KEY=your_mistral_api_key

# Web Search (at least one required, Perplexity preferred)
PERPLEXITY_API_KEY=your_perplexity_key  # Recommended
SERPER_API_KEY=your_serper_key          # Fallback

# Database (required for marketplace)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key

# Admin access (required for adding/removing influencers)
ADMIN_API_KEY=your_secure_random_key
```

### 2. Database Setup

Run the schema in your Supabase SQL editor:

```bash
# Execute the schema file
cat backend/sql/supabase_schema.sql
# Copy and paste into Supabase SQL editor
```

Then apply each file in `backend/sql/migrations` in numeric order. These scripts only add/alter objects with `IF NOT EXISTS`, so re-running them later is safe when new migrations are added.
```

### 3. Generate Admin API Key

```bash
# Generate a secure random key
openssl rand -base64 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000/marketplace` to see the marketplace.

## How Trust Scores Are Calculated

### 1. Message History Analysis

The system analyzes the influencer's recent posts using Mistral AI:

```python
def compute_message_history_score(sample_posts: List[str]) -> float:
    scores = []
    for post in sample_posts:
        prediction = mistral_scam_check(post)
        if prediction.label == "scam":
            scores.append(0.0)
        elif prediction.label == "not_scam":
            scores.append(1.0)
        else:
            scores.append(0.5)
    return average(scores)
```

### 2. Follower Metrics

Evaluates account size and follower/following ratio:

```python
def compute_followers_score(followers: int, following: int) -> float:
    # Logarithmic scale for follower count
    size_score = (log10(followers) - 2) / 3  # 100 to 100k range

    # Penalize if following > followers (bot-like behavior)
    ratio_score = 1.0
    if following > followers:
        ratio_score = max(0, 1.0 - (following/followers - 1))

    return 0.7 * size_score + 0.3 * ratio_score
```

### 3. Web Reputation (Perplexity/Serper)

Searches the web for controversies and reputation issues:

```python
def evaluate_influencer_reputation(handle: str) -> dict:
    # Search queries via Perplexity or Serper
    queries = [
        f'"{handle}" influencer scam controversy',
        f'"{handle}" sponsored posts disclosure',
        f'"{full_name}" influencer reputation reviews'
    ]

    snippets = multi_query_search(queries)
    # Mistral analyzes snippets for reputation signals
    return mistral_analyze_reputation(snippets)
```

### 4. Disclosure Compliance

Checks for ad disclosure markers:

```python
def compute_disclosure_score(posts: List[str]) -> float:
    markers = ("#ad", "#sponsored", "paid partnership")
    disclosed = count_posts_with_markers(posts, markers)
    ratio = disclosed / total_posts

    if ratio >= 0.6: return 1.0    # Good disclosure
    if ratio > 0: return 0.6        # Partial disclosure
    return 0.3                       # Poor disclosure
```

### 5. Combined Score

```python
overall_trust_score = (
    0.30 * message_history_score +
    0.15 * followers_score +
    0.40 * web_reputation_score +    # Highest weight
    0.15 * disclosure_score
)
```

## Automatic Marketplace Addition

When users analyze an influencer via `/analyze/full` endpoint, the influencer is automatically added to the marketplace with their trust scores. This keeps the marketplace up-to-date with recently analyzed profiles.

## Future Enhancements

### Planned Features

1. **Enhanced AI Analysis**
   - GPT-4 integration option for deeper analysis
   - Sentiment analysis on influencer content
   - Trend detection in posting patterns

2. **More Platforms**
   - TikTok influencer support
   - YouTube creator analysis
   - Twitter/X personality evaluation
   - Twitch streamer metrics

3. **Advanced Filtering**
   - Category/niche filtering
   - Location-based search
   - Engagement rate analysis
   - Content type classification

4. **Community Features**
   - User reviews and ratings
   - Report suspicious behavior
   - Community trust votes
   - Influencer response system

5. **Analytics Dashboard**
   - Trust score trends over time
   - Platform-wide statistics
   - Category breakdowns
   - Top trusted influencers

## Security Considerations

### Admin Authentication

- Admin endpoints require `Authorization: Bearer YOUR_ADMIN_API_KEY`
- API key must be stored securely (never in frontend code)
- Use HTTPS in production
- Rotate API keys regularly

### Rate Limiting

All endpoints are rate-limited:
- Public analysis: 10 requests/day per IP
- Marketplace read: Unlimited
- Admin actions: 100 requests/day per IP

### Data Privacy

- User IP addresses are hashed before storage
- No personally identifiable information is stored
- Influencer data is public information only
- GDPR-compliant data handling

## Troubleshooting

### Marketplace Not Available

**Error**: "Marketplace is not available. Supabase configuration required."

**Solution**: Configure Supabase credentials in `.env`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
```

### Perplexity API Errors

If Perplexity API fails, the system automatically falls back to Serper. Check logs:

```
[WebSearch] Using Perplexity for query: example
# or
[WebSearch] Falling back to Serper for query: example
```

### Trust Scores Not Updating

Trust scores are cached for performance. To force refresh:
1. Remove influencer from marketplace
2. Re-analyze the influencer
3. They'll be re-added with updated scores

### Admin Endpoints Return 401

Ensure you're sending the correct header:
```bash
Authorization: Bearer YOUR_ADMIN_API_KEY
```

The API key must match the `ADMIN_API_KEY` in your `.env` file.

## API Examples

### Python

```python
import requests

# List influencers
response = requests.get(
    "http://localhost:8000/api/marketplace/influencers",
    params={
        "trust_level": "high",
        "sort_by": "followers",
        "limit": 10
    }
)
influencers = response.json()

# Add influencer (admin)
response = requests.post(
    "http://localhost:8000/api/marketplace/influencers",
    headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
    json={
        "handle": "example",
        "platform": "instagram",
        "is_featured": True
    }
)
```

### JavaScript/TypeScript

```typescript
// List influencers
const response = await fetch(
  '/api/marketplace/influencers?trust_level=high&limit=10'
);
const data = await response.json();

// Add influencer (admin)
const response = await fetch('/api/marketplace/influencers', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${ADMIN_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    handle: 'example',
    platform: 'instagram',
    is_featured: true
  })
});
```

### cURL

```bash
# List high-trust influencers
curl "http://localhost:8000/api/marketplace/influencers?trust_level=high"

# Add influencer (admin)
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"handle": "example", "platform": "instagram"}'
```

## Support

For issues or questions:
- Check the troubleshooting section above
- Review logs for error messages
- Ensure all API keys are configured correctly
- Verify Supabase schema is properly set up

## Contributing

To add new features or improve trust scoring:

1. Update trust calculation in `backend/app/services/trust.py`
2. Modify database schema if needed
3. Update API endpoints in `backend/api/routes.py`
4. Test thoroughly with sample influencers
5. Document changes in this guide
