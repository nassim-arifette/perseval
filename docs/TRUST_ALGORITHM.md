# Trust Score Algorithm

## Overview

Perseval's trust scoring system uses a multi-factor approach combining content analysis, social metrics, web reputation research, and transparency evaluation. The algorithm leverages AI (Mistral, Perplexity) to provide objective, data-driven trust assessments.

## Trust Score Formula

```
Overall Trust Score =
    30% × Message History Score +
    15% × Followers Score +
    40% × Web Reputation Score +
    15% × Disclosure Score
```

**Trust Levels:**
- **High (≥75%)**: ✓ Green badge - Consistently trustworthy
- **Medium (40-74%)**: ~ Yellow badge - Mixed signals
- **Low (<40%)**: ! Red badge - Multiple red flags

---

## Component Breakdown

### 1. Message History Score (30% weight)

**Purpose**: Evaluate recent content for scam indicators and misleading claims

**Method**:
1. Fetch recent posts (default: 5 most recent)
2. Run each through Mistral AI scam detection
3. Calculate average trustworthiness

**Scoring**:
```python
for each post:
    if classified as "scam": score = 0.0
    elif classified as "not_scam": score = 1.0
    else (uncertain): score = 0.5

message_history_score = average(all_scores)
```

**Example**:
```
Post 1: "Buy now! Limited time! 90% off!" → 0.0 (scam)
Post 2: "Here's my honest review of..." → 1.0 (not scam)
Post 3: "Check out this product..." → 0.5 (uncertain)
Post 4: "My morning routine..." → 1.0 (not scam)
Post 5: "Click link in bio!" → 0.5 (uncertain)

Score = (0.0 + 1.0 + 0.5 + 1.0 + 0.5) / 5 = 0.60
```

**Red Flags Detected**:
- Urgent language ("act now", "limited time")
- Unrealistic promises ("lose 20 lbs in 2 days")
- Pressure tactics ("only 3 left")
- Crypto/investment schemes
- Suspicious links or DM requests

---

### 2. Followers Score (15% weight)

**Purpose**: Assess account credibility through follower metrics

**Method**:
```python
def compute_followers_score(followers, following):
    # Part A: Follower count (logarithmic scale)
    # 100 followers → 0.0
    # 10,000 followers → 0.67
    # 100,000 followers → 1.0
    log_followers = log10(max(followers, 1))
    size_score = max(0.0, min(1.0, (log_followers - 2) / 3))

    # Part B: Follower/Following ratio
    # Following > Followers suggests bot-like behavior
    ratio_score = 1.0
    if following > 0 and followers > 0:
        ratio = following / followers
        if ratio > 1:
            # Penalize accounts following more than followers
            ratio_score = max(0.0, 1.0 - (ratio - 1))

    # Weighted combination
    return 0.7 × size_score + 0.3 × ratio_score
```

**Examples**:
| Followers | Following | Size Score | Ratio Score | Final Score |
|-----------|-----------|------------|-------------|-------------|
| 100,000   | 500       | 1.00       | 1.00        | 1.00        |
| 10,000    | 1,000     | 0.67       | 1.00        | 0.97        |
| 1,000     | 5,000     | 0.33       | 0.00        | 0.23        |
| 500       | 10,000    | 0.17       | 0.00        | 0.12        |

**Red Flags**:
- Very low follower count (<1000)
- Following significantly more than followers
- Sudden follower spikes (bot purchases)
- Low engagement relative to follower count

---

### 3. Web Reputation Score (40% weight) ⭐

**Purpose**: Research public sentiment and controversies

**Method**: **Uses Perplexity AI (preferred) or Serper (fallback)**

```python
def evaluate_web_reputation(handle, full_name):
    # Step 1: Multi-query search via Perplexity/Serper
    queries = [
        f'"{handle}" influencer scam controversy',
        f'"{handle}" sponsored posts disclosure',
        f'"{full_name}" influencer reputation reviews'
    ]

    # Perplexity Sonar provides comprehensive, cited results
    snippets = search_with_perplexity(queries)
    if not snippets:
        snippets = search_with_serper(queries)  # Fallback

    # Step 2: AI analysis of search results
    reputation_data = mistral_analyze_reputation(snippets)

    return reputation_data['influencer_reliability']  # 0.0 to 1.0
```

**Perplexity Sonar Advantages**:
- More comprehensive search results
- Includes citations and source credibility
- Better context understanding
- Real-time web data

**What It Looks For**:
✓ **Positive signals**:
- Positive reviews and testimonials
- Professional collaborations
- Transparent disclosure practices
- Awards or recognition

✗ **Negative signals**:
- Scam accusations or lawsuits
- FTC violations or warnings
- Fake follower accusations
- Undisclosed sponsorships
- Pyramid scheme involvement

**Example Analysis**:

```
Search: "techguru123 influencer scam controversy"

Results via Perplexity:
1. "TechGuru123 praised for honest reviews" - TechNews.com
2. "Creator settles FTC complaint over undisclosed ads" - FTC.gov
3. "TechGuru123 community trust survey: 4.2/5" - ReviewSite.com

AI Analysis:
- Overall sentiment: Mixed
- Issues found: 1 (FTC disclosure violation)
- Positive mentions: 2
- Reliability score: 0.62 (medium trust)
```

---

### 4. Disclosure Score (15% weight)

**Purpose**: Evaluate transparency in sponsored content

**Method**:
```python
def compute_disclosure_score(posts):
    disclosure_markers = [
        "#ad", "#sponsored", "#partner",
        "paid partnership", "sponsored",
        "#gifted", "#collab"
    ]

    disclosed_posts = 0
    total_posts = 0

    for post in posts:
        if post.strip():
            total_posts += 1
            if any(marker in post.lower() for marker in disclosure_markers):
                disclosed_posts += 1

    if total_posts == 0:
        return 0.3  # Insufficient data

    disclosure_rate = disclosed_posts / total_posts

    if disclosure_rate >= 0.6:
        return 1.0    # Excellent disclosure
    elif disclosure_rate > 0:
        return 0.6    # Partial disclosure
    else:
        return 0.3    # Poor/no disclosure
```

**Scoring Guide**:
| Disclosure Rate | Score | Rating      |
|----------------|-------|-------------|
| ≥60%           | 1.0   | Excellent   |
| 1-59%          | 0.6   | Partial     |
| 0%             | 0.3   | Poor        |

**Example**:
```
Post 1: "Loving this new phone! #ad"           → Disclosed ✓
Post 2: "My skincare routine"                  → Not disclosed
Post 3: "Thanks @brand for this! #gifted"      → Disclosed ✓
Post 4: "Check out this amazing product"       → Not disclosed
Post 5: "Paid partnership with @company"       → Disclosed ✓

Disclosure Rate: 3/5 = 60% → Score = 1.0
```

**Why It Matters**:
- FTC requires disclosure of sponsored content
- Transparency builds trust with audience
- Undisclosed ads are deceptive marketing
- Legal requirement in most countries

---

## Complete Example Calculation

**Influencer**: @tech_reviewer
**Platform**: Instagram
**Followers**: 45,000 | Following: 1,200

### Step 1: Fetch Data
```
Recent Posts (5):
1. "Honest review of the new laptop..."
2. "Thanks @TechCo for sending this! #ad"
3. "My top 5 gadgets of 2024..."
4. "MASSIVE GIVEAWAY! Follow and tag 3 friends!"
5. "Unboxing video up now! #partner"
```

### Step 2: Calculate Component Scores

**Message History** (30%):
```
Post 1: Not scam → 1.0
Post 2: Not scam → 1.0
Post 3: Not scam → 1.0
Post 4: Uncertain (giveaway) → 0.5
Post 5: Not scam → 1.0

Score: (1.0 + 1.0 + 1.0 + 0.5 + 1.0) / 5 = 0.90
```

**Followers Score** (15%):
```
log10(45,000) = 4.65
size_score = (4.65 - 2) / 3 = 0.88

ratio = 1,200 / 45,000 = 0.027 (following < followers)
ratio_score = 1.0

Score: 0.7 × 0.88 + 0.3 × 1.0 = 0.92
```

**Web Reputation** (40%):
```
Perplexity Search Results:
- "tech_reviewer praised for honest content"
- "45K subscriber milestone"
- "No major controversies found"

AI Analysis:
Reliability Score: 0.85
```

**Disclosure Score** (15%):
```
Disclosed: Posts 2, 5 (2/5 = 40%)
Score: 0.6 (partial disclosure)
```

### Step 3: Calculate Overall Score

```
Overall Trust =
    0.30 × 0.90 (message) +
    0.15 × 0.92 (followers) +
    0.40 × 0.85 (web rep) +
    0.15 × 0.60 (disclosure)

= 0.27 + 0.138 + 0.34 + 0.09
= 0.838
= 83.8%

Trust Level: HIGH ✓
```

### Step 4: Generate Summary
```
Trust Score: 0.84 (High)

Analysis:
✓ Recent posts look mostly safe
✓ Followers profile looks plausible
✓ Web reputation: Positive reviews, no major controversies
~ Disclosure behavior: Ads are sporadically flagged as sponsored

Recommendation: This influencer shows strong trust signals with
good content quality and positive reputation. Disclosure practices
could be improved.
```

---

## Algorithm Improvements

### Current Implementation
The algorithm currently uses:
- Mistral AI for content classification
- Perplexity Sonar/Serper for web research
- Rule-based scoring for followers and disclosure

### Future Enhancements

#### 1. Machine Learning Models
```python
# Train classifier on labeled influencer dataset
from sklearn.ensemble import RandomForestClassifier

features = [
    'followers', 'following_ratio', 'posts_per_week',
    'avg_likes', 'avg_comments', 'verified_status',
    'account_age_days', 'scam_post_ratio', 'disclosure_rate'
]

# Train on historical data with known trust labels
model = train_trust_classifier(features, labels)
ml_score = model.predict_proba(influencer_features)[1]

# Blend with existing scores
final_score = 0.6 * rule_based_score + 0.4 * ml_score
```

#### 2. Temporal Analysis
```python
# Track trust changes over time
def temporal_trust_score(influencer_id):
    history = get_score_history(influencer_id, days=90)

    # Detect sudden drops (red flag)
    if has_sudden_drop(history, threshold=0.2):
        return apply_penalty(current_score, 0.1)

    # Reward consistent high scores
    if is_consistently_high(history, threshold=0.8):
        return apply_bonus(current_score, 0.05)

    return current_score
```

#### 3. Network Analysis
```python
# Analyze who they associate with
def network_trust_score(influencer):
    # Check mutual followers
    connections = get_connections(influencer)

    # Flag if connected to known scammers
    scammer_connections = [c for c in connections if is_known_scammer(c)]
    if scammer_connections:
        penalty = len(scammer_connections) * 0.05
        return max(0, base_score - penalty)

    # Bonus for verified, high-trust connections
    trusted_connections = [c for c in connections if c.trust_score > 0.8]
    bonus = min(0.1, len(trusted_connections) * 0.01)

    return base_score + bonus
```

#### 4. Engagement Authenticity
```python
# Detect fake engagement
def engagement_authenticity_score(posts):
    for post in posts:
        likes = post.likes
        comments = post.comments
        followers = post.author.followers

        # Expected engagement rate: 3-5% for authentic accounts
        engagement_rate = (likes + comments) / followers

        # Suspicious if too high (bot likes) or too low (bought followers)
        if engagement_rate > 0.20 or engagement_rate < 0.005:
            return 0.4  # Low authenticity

    return 1.0  # Authentic engagement
```

#### 5. Content Quality Metrics
```python
# Analyze content production quality
def content_quality_score(posts):
    metrics = {
        'spelling_errors': count_spelling_errors(posts),
        'grammar_score': analyze_grammar(posts),
        'image_quality': analyze_images(posts),
        'video_quality': analyze_videos(posts),
        'caption_length_variance': calculate_variance(post_lengths)
    }

    # High-quality creators have consistent, polished content
    return aggregate_quality_metrics(metrics)
```

---

## Perplexity vs Serper Comparison

### Perplexity Sonar (Recommended)

**Advantages**:
- More comprehensive results with citations
- Better context and relevance
- Understands complex queries
- Real-time web data
- Fact-checking capabilities

**Example Response**:
```json
{
  "search_results": [
    {
      "title": "TechReviewer settles FTC complaint",
      "snippet": "Influencer TechReviewer agreed to clearly disclose...",
      "url": "https://ftc.gov/...",
      "credibility": "high"
    }
  ],
  "summary": "Mixed reputation with one regulatory issue but generally positive reviews"
}
```

### Serper (Fallback)

**Advantages**:
- Fast and reliable
- Good coverage
- Free tier available
- Simple to use

**Example Response**:
```json
{
  "organic": [
    {
      "title": "TechReviewer - Reviews",
      "snippet": "Check out tech reviews...",
      "link": "https://example.com"
    }
  ]
}
```

**Fallback Logic**:
```python
# Perplexity is tried first
results = search_with_perplexity(query)

if not results or results is None:
    # Automatic fallback to Serper
    results = search_with_serper(query)

if not results:
    # If both fail, use default score
    return default_reputation_score(0.5)
```

---

## Limitations & Considerations

### Current Limitations

1. **Data Freshness**
   - Instagram API limitations
   - Web search may miss very recent events
   - Cache expiration needs tuning

2. **Language Support**
   - Primarily optimized for English content
   - Non-English posts may have lower accuracy

3. **Private Accounts**
   - Cannot analyze private Instagram accounts
   - Requires public profile data

4. **Platform Coverage**
   - Currently focused on Instagram
   - TikTok, YouTube, Twitter support in progress

5. **Sample Size**
   - Only analyzes 5 most recent posts by default
   - May miss patterns in older content

### Bias Mitigation

The algorithm attempts to be objective by:
- Using multiple data sources (not just one)
- Weighting web reputation heavily (40%)
- Not penalizing promotional content (just requires disclosure)
- Separating sponsored vs scam content detection
- Providing transparent score breakdowns

### Privacy & Ethics

- Only analyzes publicly available data
- No personal data collection
- Transparent methodology
- Appeals process for flagged accounts (via admin)
- Regular algorithm audits for fairness

---

## Testing & Validation

### Test Cases

**High Trust Influencer** (Expected: 0.75+):
- Consistent, quality content
- Large, engaged following
- Good disclosure practices
- Positive web reputation
- No scam indicators

**Medium Trust Influencer** (Expected: 0.40-0.74):
- Mixed content quality
- Some promotional posts without disclosure
- Average follower metrics
- Limited web presence

**Low Trust Influencer** (Expected: <0.40):
- Multiple scam indicators in posts
- Suspicious follower patterns
- Negative web reputation
- Poor/no disclosure
- Legal issues or complaints

### Validation Process

1. **Manual Review**: Compare algorithm scores with human expert assessments
2. **A/B Testing**: Test algorithm changes on historical data
3. **User Feedback**: Collect feedback on accuracy
4. **Regular Audits**: Quarterly review of scoring accuracy
5. **Edge Cases**: Test boundary conditions and unusual profiles

---

## API Integration

The trust algorithm is automatically used by:

1. **Full Analysis Endpoint**: `/api/analyze/full`
2. **Influencer Trust Endpoint**: `/api/influencer/trust`
3. **Marketplace Addition**: `/api/marketplace/influencers`

Scores are cached in Supabase for 7 days to reduce API costs and improve response times.

---

## Summary

Perseval's trust scoring provides:
- ✓ **Multi-factor analysis** - Not relying on single metric
- ✓ **AI-powered** - Leverages Mistral and Perplexity
- ✓ **Transparent** - Clear score breakdown
- ✓ **Objective** - Data-driven, not subjective opinions
- ✓ **Scalable** - Works for any public influencer
- ✓ **Continuously improving** - Algorithm updates based on feedback

The 40% weight on web reputation (powered by Perplexity AI) ensures comprehensive research beyond just analyzing social media posts, providing users with trustworthy, well-researched trust assessments.
