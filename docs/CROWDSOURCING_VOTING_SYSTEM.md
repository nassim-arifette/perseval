# Crowdsourcing Voting System

## Overview

The voting system allows users to vote on influencers in the marketplace, creating a crowdsourced "user trust score" that is weighted into the overall trust calculation. This democratic approach combines AI analysis with community feedback for more accurate trust assessments.

## Trust Score Calculation with User Votes

### Original Algorithm (without user votes)

The original trust score combines 4 components:

```
Overall Trust Score =
  30% × Message History Score    (AI analysis of posts)
+ 15% × Followers Score          (follower metrics)
+ 40% × Web Reputation Score     (Perplexity AI research)
+ 15% × Disclosure Score         (ad transparency)
```

### Updated Algorithm (with user votes - **10% weight**)

When user votes are available, the algorithm adjusts to include crowdsourced feedback:

```
Overall Trust Score =
  27% × Message History Score    (AI analysis)
+ 13.5% × Followers Score        (follower metrics)
+ 36% × Web Reputation Score     (Perplexity AI)
+ 13.5% × Disclosure Score       (ad transparency)
+ 10% × User Trust Score         (crowdsourced votes) ← NEW!
```

**Weight Distribution:**
- The 10% weight for user votes is proportionally redistributed from other components
- AI-driven scores still dominate (77%) while community input contributes meaningfully (10%)
- Neutral baseline (13%) ensures fair starting point for new influencers

### User Trust Score Calculation

The user trust score is calculated using a smoothed ratio formula:

```
User Trust Score = (trust_votes + 2) / (total_votes + 4)
```

**Smoothing Benefits:**
- Prevents extreme scores with few votes
- New influencers start near neutral (0.50)
- Score becomes more accurate as vote count increases

**Examples:**
- 0 votes: 2/4 = 0.50 (neutral)
- 5 trust, 0 distrust: 7/9 = 0.78 (high trust)
- 0 trust, 5 distrust: 2/9 = 0.22 (low trust)
- 10 trust, 10 distrust: 12/24 = 0.50 (controversial/neutral)
- 50 trust, 5 distrust: 52/59 = 0.88 (very high trust)

## Architecture

### Database Schema

**Table: `influencer_votes`**

Located in: `backend/sql/supabase_schema.sql` (run this once), plus incremental updates in `backend/sql/migrations` (apply them sequentially whenever you pull new changes).

```sql
CREATE TABLE influencer_votes (
    id UUID PRIMARY KEY,
    influencer_handle TEXT NOT NULL,
    influencer_platform TEXT NOT NULL,
    vote_type TEXT NOT NULL CHECK (vote_type IN ('trust', 'distrust')),
    vote_weight DECIMAL(3, 2) DEFAULT 1.00,  -- For future weighted voting
    voter_ip_hash TEXT NOT NULL,  -- SHA-256 for privacy
    voter_session_hash TEXT,
    comment TEXT,  -- Optional feedback (max 500 chars)
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    UNIQUE(influencer_handle, influencer_platform, voter_ip_hash)  -- One vote per IP
);
```

**Marketplace Updates:**
```sql
ALTER TABLE marketplace_influencers
ADD COLUMN user_trust_score DECIMAL(3, 2) DEFAULT 0.50,
ADD COLUMN total_votes INTEGER DEFAULT 0;
```

**Database Functions:**
- `check_vote_rate_limit(p_ip_hash)` - Max 20 votes per IP per hour
- `calculate_user_trust_score(p_handle, p_platform)` - Compute smoothed ratio
- `get_user_vote(p_handle, p_platform, p_ip_hash)` - Retrieve user's current vote

**View: `influencer_vote_stats`**
- Aggregates votes by influencer
- Shows trust/distrust counts and calculated score

### Backend API

**Repository: `backend/app/repositories/votes.py`**

Core functions:
- `hash_ip_address(ip)` - Privacy-preserving SHA-256 hashing
- `check_vote_rate_limit(ip_hash)` - Spam prevention
- `submit_vote(...)` - Submit or update vote (upsert)
- `get_user_vote(...)` - Get current user's vote
- `get_vote_stats(...)` - Get aggregated vote statistics
- `update_marketplace_user_score(...)` - Sync votes to marketplace
- `delete_vote(...)` - Remove user's vote

**API Endpoints: `backend/api/routes.py`**

Public endpoints:

1. **POST /votes/influencers** - Submit a vote
   ```json
   {
     "handle": "influencer_username",
     "platform": "instagram",
     "vote_type": "trust",  // or "distrust"
     "comment": "Optional feedback..."
   }
   ```
   Response:
   ```json
   {
     "handle": "influencer_username",
     "platform": "instagram",
     "vote_type": "trust",
     "message": "Thank you for your vote!",
     "vote_stats": {
       "trust_votes": 15,
       "distrust_votes": 3,
       "total_votes": 18,
       "user_trust_score": 0.77
     }
   }
   ```

2. **GET /votes/influencers/{handle}** - Get vote statistics
   Query params: `platform` (default: instagram)

   Response:
   ```json
   {
     "handle": "influencer_username",
     "platform": "instagram",
     "user_vote": "trust",  // User's current vote (or null)
     "vote_stats": {
       "trust_votes": 15,
       "distrust_votes": 3,
       "total_votes": 18,
       "user_trust_score": 0.77
     }
   }
   ```

3. **DELETE /votes/influencers/{handle}** - Remove your vote
   Query params: `platform` (default: instagram)

**Trust Algorithm: `backend/app/services/trust.py`**

Updated `combine_trust_score()` function:
```python
def combine_trust_score(
    message_history_score: float,
    followers_score: float,
    web_reputation_score: float,
    disclosure_score: float,
    user_trust_score: Optional[float] = None,
) -> float:
    if user_trust_score is not None:
        # With user votes (10% weight)
        return (
            0.27 * message_history_score +
            0.135 * followers_score +
            0.36 * web_reputation_score +
            0.135 * disclosure_score +
            0.10 * user_trust_score
        )

    # Original weights without user votes
    return (
        0.3 * message_history_score +
        0.15 * followers_score +
        0.4 * web_reputation_score +
        0.15 * disclosure_score
    )
```

### Frontend (Recommended Implementation)

**Component: Voting Buttons**

Add voting UI to marketplace influencer cards:

```tsx
// Example implementation
import { useState } from 'react';

interface VotingProps {
  handle: string;
  platform: string;
  initialVote?: 'trust' | 'distrust';
  stats: {
    trust_votes: number;
    distrust_votes: number;
    total_votes: number;
    user_trust_score: number;
  };
}

function VotingButtons({ handle, platform, initialVote, stats }: VotingProps) {
  const [userVote, setUserVote] = useState(initialVote);
  const [voteStats, setVoteStats] = useState(stats);

  const handleVote = async (voteType: 'trust' | 'distrust') => {
    try {
      const response = await fetch('/api/votes/influencers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle, platform, vote_type: voteType })
      });

      const data = await response.json();
      setUserVote(voteType);
      setVoteStats(data.vote_stats);
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  return (
    <div>
      <div className="flex gap-2">
        <button
          onClick={() => handleVote('trust')}
          className={userVote === 'trust' ? 'active' : ''}
        >
          👍 Trust ({voteStats.trust_votes})
        </button>
        <button
          onClick={() => handleVote('distrust')}
          className={userVote === 'distrust' ? 'active' : ''}
        >
          👎 Distrust ({voteStats.distrust_votes})
        </button>
      </div>
      <p>
        User Trust Score: {(voteStats.user_trust_score * 100).toFixed(0)}%
        ({voteStats.total_votes} votes)
      </p>
    </div>
  );
}
```

**Display User Trust Score:**

Show the crowdsourced score alongside AI scores:

```tsx
<div className="trust-scores">
  <div>Overall Trust: {(influencer.overall_trust_score * 100).toFixed(0)}%</div>

  <details>
    <summary>Score Breakdown</summary>
    <ul>
      <li>AI Analysis: {(influencer.message_history_score * 100).toFixed(0)}%</li>
      <li>Follower Metrics: {(influencer.followers_score * 100).toFixed(0)}%</li>
      <li>Web Reputation: {(influencer.web_reputation_score * 100).toFixed(0)}%</li>
      <li>Ad Disclosure: {(influencer.disclosure_score * 100).toFixed(0)}%</li>
      <li>Community Votes: {(influencer.user_trust_score * 100).toFixed(0)}%
        ({influencer.total_votes} votes)  ← NEW!
      </li>
    </ul>
  </details>
</div>
```

## Security Features

### Privacy Protection
- IP addresses hashed with SHA-256 before storage
- Never store raw IP addresses
- Session hashing for additional anonymization

### Spam Prevention
- **Rate limiting:** 20 votes per IP per hour
- **One vote per influencer:** Users can update but not duplicate votes
- **Vote validation:** XSS prevention on optional comments

### Vote Manipulation Resistance
- **Smoothing algorithm:** Prevents extreme scores with few votes
- **IP-based tracking:** Harder to manipulate than account-based
- **Transparent statistics:** Vote counts visible to detect anomalies

## Usage Examples

### Submit a Vote

```bash
curl -X POST "http://localhost:8000/votes/influencers" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "johndoe",
    "platform": "instagram",
    "vote_type": "trust",
    "comment": "Consistent transparency and honest reviews"
  }'
```

Response:
```json
{
  "handle": "johndoe",
  "platform": "instagram",
  "vote_type": "trust",
  "message": "Thank you for your vote! Your feedback helps others make informed decisions.",
  "vote_stats": {
    "trust_votes": 24,
    "distrust_votes": 5,
    "total_votes": 29,
    "user_trust_score": 0.79
  }
}
```

### Get Vote Statistics

```bash
curl "http://localhost:8000/votes/influencers/johndoe?platform=instagram"
```

Response:
```json
{
  "handle": "johndoe",
  "platform": "instagram",
  "user_vote": "trust",
  "vote_stats": {
    "trust_votes": 24,
    "distrust_votes": 5,
    "total_votes": 29,
    "user_trust_score": 0.79
  }
}
```

### Update Your Vote

Simply submit a new vote - the system will update your existing vote:

```bash
curl -X POST "http://localhost:8000/votes/influencers" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "johndoe",
    "platform": "instagram",
    "vote_type": "distrust"
  }'
```

### Remove Your Vote

```bash
curl -X DELETE "http://localhost:8000/votes/influencers/johndoe?platform=instagram"
```

## Configuration

### Environment Variables

No new environment variables required - uses existing Supabase configuration.

### Database Setup

Run in Supabase SQL Editor:
```sql
-- Execute the updated schema in backend/sql/supabase_schema.sql
-- This creates:
-- - influencer_votes table
-- - Voting functions (check_vote_rate_limit, calculate_user_trust_score, get_user_vote)
-- - influencer_vote_stats view
-- - Updates marketplace_influencers table with user_trust_score and total_votes columns
```

Then apply each SQL file inside `backend/sql/migrations` in numerical order to pick up incremental changes (for example, the community voting columns). Every migration is idempotent, so you can safely rerun them.

### Adjusting Vote Weight

To change the 10% weight for user votes, edit `backend/app/services/trust.py`:

```python
def combine_trust_score(..., user_trust_score: Optional[float] = None) -> float:
    if user_trust_score is not None:
        # Change 0.10 to your desired weight (e.g., 0.15 for 15%)
        # Adjust other weights proportionally to sum to 1.0
        return (
            0.27 * message_history_score +
            0.135 * followers_score +
            0.36 * web_reputation_score +
            0.135 * disclosure_score +
            0.10 * user_trust_score  # ← Change this weight
        )
```

**Recommended weights:**
- **5%:** Minimal community input, AI-dominated
- **10%:** Balanced (current default)
- **15%:** Stronger community voice
- **20%+:** Community-driven (not recommended without anti-manipulation measures)

## Testing

### Test Voting Flow

1. **Vote on an influencer:**
   ```bash
   curl -X POST "http://localhost:8000/votes/influencers" \
     -H "Content-Type: application/json" \
     -d '{"handle": "test_user", "platform": "instagram", "vote_type": "trust"}'
   ```

2. **Check vote statistics:**
   ```bash
   curl "http://localhost:8000/votes/influencers/test_user"
   ```

3. **Update vote:**
   ```bash
   curl -X POST "http://localhost:8000/votes/influencers" \
     -H "Content-Type: application/json" \
     -d '{"handle": "test_user", "platform": "instagram", "vote_type": "distrust"}'
   ```

4. **Remove vote:**
   ```bash
   curl -X DELETE "http://localhost:8000/votes/influencers/test_user"
   ```

### Test Rate Limiting

Submit 21 votes in quick succession - the 21st should fail with 429 error.

### Verify Trust Score Integration

1. Add influencer to marketplace (without votes)
2. Check overall_trust_score (should use original weights)
3. Submit votes for the influencer
4. Check overall_trust_score again (should now include user_trust_score with 10% weight)

## Analytics & Insights

### Most Voted Influencers

```sql
SELECT * FROM influencer_vote_stats
ORDER BY total_votes DESC
LIMIT 20;
```

### Controversial Influencers

(close to 50/50 trust/distrust split)

```sql
SELECT *,
  ABS(trust_votes - distrust_votes) as vote_difference
FROM influencer_vote_stats
WHERE total_votes > 10
ORDER BY vote_difference ASC
LIMIT 20;
```

### High Trust Consensus

```sql
SELECT * FROM influencer_vote_stats
WHERE user_trust_score > 0.8
AND total_votes > 20
ORDER BY user_trust_score DESC;
```

### Low Trust Warnings

```sql
SELECT * FROM influencer_vote_stats
WHERE user_trust_score < 0.3
AND total_votes > 20
ORDER BY user_trust_score ASC;
```

## Future Enhancements

### Planned Features
- [ ] Weighted voting (verified users get higher weight)
- [ ] Vote history timeline
- [ ] Trending votes (recent activity)
- [ ] Vote reasoning categories (not just free text)
- [ ] Flagging system for spam votes
- [ ] Admin dashboard for vote moderation
- [ ] Email notifications for vote milestones
- [ ] Leaderboards (most active voters, most voted influencers)

### Advanced Anti-Manipulation
- [ ] Machine learning to detect coordinated voting
- [ ] IP geolocation analysis for suspicious patterns
- [ ] Time-decay for older votes
- [ ] User reputation system (trusted voters)
- [ ] Requiring account authentication for voting
- [ ] CAPTCHA for high-volume voters

### UX Improvements
- [ ] Visual voting interface with animations
- [ ] Real-time vote count updates (WebSockets)
- [ ] Vote comments feed
- [ ] Sorting/filtering by community rating
- [ ] "Controversial" badge for mixed votes

## Troubleshooting

### Common Issues

**"Voting system is not available"**
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Verify database schema has been executed
- Test Supabase connection manually

**"Rate limit exceeded"**
- Normal behavior - wait 1 hour
- For testing, use different IPs or clear vote history
- Check influencer_votes table for IP hash records

**Vote not appearing in marketplace**
- Votes update user_trust_score automatically
- Check marketplace_influencers table for user_trust_score column
- Verify influencer exists in marketplace
- Run `update_marketplace_user_score()` manually if needed

**User trust score not affecting overall score**
- Check that `combine_trust_score()` is called with user_trust_score parameter
- Verify marketplace influencer has user_trust_score value
- Re-analyze influencer to recalculate overall score

## Support

For issues or questions:
1. Check backend logs: `tail -f backend.log`
2. Check Supabase logs in dashboard
3. Verify vote records in `influencer_votes` table
4. Check vote statistics in `influencer_vote_stats` view
5. Review API response errors
6. Consult documentation files in `docs/`

## File Reference

### Backend
- `backend/sql/supabase_schema.sql` - Voting schema and functions
- `backend/app/repositories/votes.py` - Vote data access layer
- `backend/app/services/trust.py` - Updated trust algorithm
- `backend/app/models/schemas.py` - Voting request/response models
- `backend/api/routes.py` - Voting API endpoints
- `backend/app/repositories/marketplace.py` - Updated marketplace queries

### Documentation
- `docs/CROWDSOURCING_VOTING_SYSTEM.md` - This file
- `docs/TRUST_ALGORITHM.md` - Original trust algorithm documentation
- `docs/MARKETPLACE_GUIDE.md` - Marketplace overview

## Summary

The crowdsourcing voting system adds democratic validation to AI-driven trust scores:

✅ **10% weight** for community votes in overall trust calculation
✅ **Privacy-preserving** with IP hashing
✅ **Spam-resistant** with rate limiting and smoothing
✅ **Easy to use** - simple thumbs up/down voting
✅ **Transparent** - vote counts and scores visible
✅ **Flexible** - configurable weights and formulas

This creates a hybrid trust system that combines:
- **AI Analysis** (77%): Objective data-driven assessment
- **Community Input** (10%): Real-world user experiences
- **Established Baseline** (13%): Prevents manipulation

The result is a more accurate, democratic, and robust trust scoring system that benefits from both automated analysis and human judgment.
