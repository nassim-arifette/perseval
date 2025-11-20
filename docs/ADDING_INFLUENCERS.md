# Quick Guide: Adding Influencers to Marketplace

## Overview

This guide explains how to add influencers to the Perseval marketplace. Trust scores are calculated automatically using AI-powered analysis with Perplexity or Serper.

## Prerequisites

1. **Admin API Key**: Set `ADMIN_API_KEY` in your `.env` file
2. **Supabase**: Configure `SUPABASE_URL` and `SUPABASE_KEY`
3. **Web Search API**: Set `PERPLEXITY_API_KEY` (recommended) or `SERPER_API_KEY`
4. **Mistral API**: Set `MISTRAL_API_KEY` for content analysis

## Trust Score Calculation

Trust scores are calculated automatically and based on:

### 1. Message History (30% weight)
- Analyzes recent posts for scam indicators
- Uses Mistral AI to detect suspicious content
- Checks for misleading claims or red flags

### 2. Followers Score (15% weight)
- Evaluates follower count on logarithmic scale
- Checks follower/following ratio
- Flags unusual patterns (e.g., following more than followers)

### 3. Web Reputation (40% weight) ⭐ **Uses Perplexity AI**
- Searches web for controversies, lawsuits, complaints
- Analyzes disclosure practices and sponsored content
- Reviews influencer reputation across sources
- **Perplexity Sonar** provides comprehensive, cited research
- Falls back to Serper if Perplexity unavailable

### 4. Disclosure Score (15% weight)
- Checks for ad disclosure markers (#ad, #sponsored, etc.)
- Evaluates transparency in sponsored content
- Calculates disclosure rate across recent posts

### Trust Levels
- **High Trust (≥75%)**: Consistently trustworthy, good disclosure practices
- **Medium Trust (40-74%)**: Mixed signals, some concerns
- **Low Trust (<40%)**: Multiple red flags or poor practices

## Methods to Add Influencers

### Method 1: Via API (Recommended)

```bash
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "influencer_handle",
    "platform": "instagram",
    "admin_notes": "Popular tech reviewer",
    "is_featured": false
  }'
```

**What happens:**
1. System fetches influencer profile from Instagram
2. Analyzes recent posts (default: 5 posts)
3. Performs web search via **Perplexity** for reputation data
4. Calculates all trust scores
5. Stores in marketplace database

### Method 2: Automatic Addition

Influencers are automatically added when users analyze them via the full analysis endpoint:

```bash
curl -X POST http://localhost:8000/api/analyze/full \
  -H "Content-Type: application/json" \
  -d '{
    "influencer_handle": "example",
    "text": "Check this amazing product!",
    "max_posts": 5
  }'
```

### Method 3: Using Python Script

Create a script `scripts/add_influencer.py`:

```python
import os
import requests

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
API_BASE = "http://localhost:8000/api"

def add_influencer(handle, is_featured=False, admin_notes=None):
    """Add an influencer to the marketplace."""
    response = requests.post(
        f"{API_BASE}/marketplace/influencers",
        headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
        json={
            "handle": handle,
            "platform": "instagram",
            "is_featured": is_featured,
            "admin_notes": admin_notes
        }
    )

    if response.ok:
        data = response.json()
        print(f"✓ Added @{handle} with trust score: {data['overall_trust_score']:.2f}")
        print(f"  Trust level: {data['trust_label']}")
        return data
    else:
        print(f"✗ Failed to add @{handle}: {response.text}")
        return None

# Usage
if __name__ == "__main__":
    influencers = [
        {"handle": "example1", "is_featured": True},
        {"handle": "example2", "is_featured": False},
        {"handle": "example3", "is_featured": False},
    ]

    for inf in influencers:
        add_influencer(inf["handle"], inf["is_featured"])
```

Run it:
```bash
python scripts/add_influencer.py
```

## Bulk Adding Influencers

For adding multiple influencers, use the seed script:

```bash
python scripts/seed_marketplace.py
```

Or create your own batch script:

```python
import asyncio
import requests
import time

ADMIN_API_KEY = "your_admin_key"
API_BASE = "http://localhost:8000/api"

influencers_to_add = [
    "influencer1",
    "influencer2",
    "influencer3",
    # ... more handles
]

def add_influencer(handle):
    response = requests.post(
        f"{API_BASE}/marketplace/influencers",
        headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
        json={"handle": handle, "platform": "instagram"}
    )
    return response.json() if response.ok else None

for handle in influencers_to_add:
    print(f"Adding @{handle}...")
    result = add_influencer(handle)
    if result:
        print(f"  ✓ Trust: {result['overall_trust_score']:.2f} ({result['trust_label']})")
    time.sleep(1)  # Rate limiting
```

## Understanding the Analysis Process

When you add an influencer, here's what happens behind the scenes:

### Step 1: Profile Fetching
```python
# Fetches from Instagram via Instaloader
stats = get_instagram_stats(handle, max_posts=5)
# Returns: followers, following, bio, verified status, recent posts
```

### Step 2: Message History Analysis
```python
# Analyzes each post for scam indicators
for post in recent_posts:
    prediction = mistral_scam_check(post)
    # Returns: 'scam', 'not_scam', or 'uncertain'
```

### Step 3: Web Reputation Search (Perplexity)
```python
# Searches web using Perplexity Sonar or Serper fallback
queries = [
    f'"{handle}" influencer scam controversy',
    f'"{handle}" sponsored posts disclosure',
    f'"{full_name}" influencer reputation reviews'
]
snippets = multi_query_search(queries)  # Uses Perplexity first
```

### Step 4: Trust Score Calculation
```python
overall_trust = (
    0.30 * message_history_score +
    0.15 * followers_score +
    0.40 * web_reputation_score +    # Perplexity data
    0.15 * disclosure_score
)
```

### Step 5: Database Storage
```python
# Stores in Supabase marketplace_influencers table
add_influencer_to_marketplace(
    handle=handle,
    platform="instagram",
    profile_data={...},
    trust_data={...}
)
```

## Perplexity vs Serper

### Perplexity Sonar (Recommended)
- **Pros**: More comprehensive, includes citations, better context
- **Cons**: Requires separate API key
- **Setup**: `PERPLEXITY_API_KEY` in `.env`
- **Cost**: Pay per request

### Serper (Fallback)
- **Pros**: Reliable, fast, good coverage
- **Cons**: Less contextual than Perplexity
- **Setup**: `SERPER_API_KEY` in `.env`
- **Cost**: Free tier available

The system automatically uses Perplexity if available, falls back to Serper if not.

## Managing Marketplace Influencers

### View Influencer
```bash
curl http://localhost:8000/api/marketplace/influencers/example_handle
```

### Update Influencer
Re-add with the same handle to update scores:
```bash
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"handle": "example_handle", "platform": "instagram"}'
```

### Remove Influencer
```bash
curl -X DELETE http://localhost:8000/api/marketplace/influencers/example_handle \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

### Feature Influencer
```bash
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "example",
    "is_featured": true,
    "admin_notes": "Top creator in tech niche"
  }'
```

## Troubleshooting

### "Failed to fetch Instagram stats"
- Influencer might have private account
- Handle might be incorrect (try without @)
- Instagram rate limiting (wait and retry)

### "Marketplace is not available"
- Check Supabase configuration in `.env`
- Verify database schema is set up
- Ensure service role key is used (not anon key)

### Low Trust Scores
- Review the `analysis_summary` field for details
- Check `message_history_score` - might have scam-like posts
- Review `web_reputation_score` - negative press?
- Check `disclosure_score` - poor ad transparency?

### Perplexity API Errors
- Verify `PERPLEXITY_API_KEY` is correct
- Check API quota/usage limits
- System will automatically fall back to Serper
- Look for log: `[WebSearch] Falling back to Serper`

## Best Practices

1. **Verify Handles**: Double-check spelling before adding
2. **Use Featured Sparingly**: Only for truly exceptional influencers
3. **Add Notes**: Use `admin_notes` to document why added
4. **Regular Updates**: Re-analyze influencers periodically
5. **Monitor Scores**: Watch for score changes over time
6. **Use Perplexity**: Better trust scores with Perplexity API

## Example Workflow

```bash
# 1. Set up environment
export ADMIN_API_KEY="your_key"

# 2. Add high-profile influencer
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "mkbhd",
    "platform": "instagram",
    "is_featured": true,
    "admin_notes": "Tech reviewer, high quality content"
  }'

# 3. Verify it was added
curl http://localhost:8000/api/marketplace/influencers/mkbhd

# 4. Check in frontend
# Visit: http://localhost:3000/marketplace
# Search for "mkbhd"
```

## Rate Limits

- **Analysis Endpoint**: 10 per day per IP (for public)
- **Admin Endpoints**: 100 per day per IP
- **Marketplace Read**: Unlimited

Add delays between bulk additions to respect rate limits.

## Future Algorithm Improvements

The trust scoring algorithm can be enhanced by:

1. **Machine Learning Models**
   - Train on labeled dataset of trustworthy/untrustworthy influencers
   - Use engagement patterns, comment sentiment, posting frequency

2. **Advanced Perplexity Features**
   - Use Perplexity's citation system more deeply
   - Analyze source credibility (high-quality sites vs blogs)
   - Temporal analysis (recent vs old controversies)

3. **Social Graph Analysis**
   - Check who they follow and who follows them
   - Identify association with known scammers
   - Network trust propagation

4. **Content Analysis**
   - Image/video analysis for visual scam indicators
   - Link analysis (suspicious URLs, redirects)
   - Engagement authenticity (bot detection)

5. **Historical Tracking**
   - Trust score trends over time
   - Behavioral changes detection
   - Seasonal pattern analysis

## Support

Need help? Check:
- [MARKETPLACE_GUIDE.md](./MARKETPLACE_GUIDE.md) - Complete guide
- [ADMIN_API_USAGE.md](./ADMIN_API_USAGE.md) - API reference
- Backend logs for detailed error messages

## Contributing

To improve the trust scoring algorithm:
1. Modify `backend/app/services/trust.py`
2. Update weight distribution in `combine_trust_score()`
3. Add new scoring factors if needed
4. Test with diverse influencer profiles
5. Document changes
