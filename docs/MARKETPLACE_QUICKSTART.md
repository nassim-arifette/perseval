# Marketplace Quick Start

Get your influencer marketplace up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 16+
- Supabase account (free tier works)
- API keys for Mistral and Perplexity (or Serper)

## Step 1: Get API Keys (5 minutes)

### Required Keys

1. **Mistral API** (for AI analysis)
   - Go to: https://console.mistral.ai/
   - Sign up and create an API key
   - Free tier available

2. **Perplexity API** (recommended) OR **Serper API** (fallback)
   - Perplexity: https://www.perplexity.ai/settings/api
   - Serper: https://serper.dev/
   - Get at least one for web search

3. **Supabase** (for database)
   - Go to: https://supabase.com/
   - Create a new project
   - Get your project URL and service role key

4. **Admin API Key** (for managing marketplace)
   - Generate a secure random key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Step 2: Configure Environment (2 minutes)

```bash
# Navigate to backend
cd backend

# Copy example config
cp .env.example .env

# Edit .env with your keys
nano .env  # or use your preferred editor
```

Your `.env` should look like:
```bash
# Required
MISTRAL_API_KEY=your_mistral_key_here

# Web Search (at least one required)
PERPLEXITY_API_KEY=your_perplexity_key_here  # Recommended
SERPER_API_KEY=your_serper_key_here          # Fallback

# Database (required for marketplace)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key_here

# Admin access
ADMIN_API_KEY=your_secure_random_key_here
```

## Step 3: Set Up Database (3 minutes)

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the sidebar
3. Open the schema file:
   ```bash
   cat backend/sql/supabase_schema.sql
   ```
4. Copy the entire SQL content
5. Paste into Supabase SQL Editor
6. Click "Run" to create all tables
7. Still in the SQL Editor, apply every file inside `backend/sql/migrations` (from lowest number to highest). Each uses safe `IF NOT EXISTS` guards, so you can re-run them whenever new migrations are added.

You should see these tables created:
- `influencer_cache`
- `company_cache`
- `product_cache`
- `marketplace_influencers` ⭐
- `user_feedback`

## Step 4: Install Dependencies (3 minutes)

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Step 5: Start the Application (1 minute)

### Terminal 1 - Backend
```bash
cd backend
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
```

## Step 6: Add Your First Influencer (2 minutes)

### Option A: Via API

```bash
curl -X POST http://localhost:8000/api/marketplace/influencers \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "handle": "mkbhd",
    "platform": "instagram",
    "is_featured": true
  }'
```

### Option B: Via Python Script

Create `quick_add.py`:
```python
import os
import requests

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "your_key_here")

response = requests.post(
    "http://localhost:8000/api/marketplace/influencers",
    headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
    json={
        "handle": "mkbhd",
        "platform": "instagram",
        "is_featured": True
    }
)

if response.ok:
    data = response.json()
    print(f"✓ Added @{data['handle']}")
    print(f"  Trust Score: {data['overall_trust_score']:.2f}")
    print(f"  Trust Level: {data['trust_label']}")
else:
    print(f"✗ Error: {response.text}")
```

Run it:
```bash
python quick_add.py
```

## Step 7: View the Marketplace

Open your browser and go to:
```
http://localhost:3000/marketplace
```

You should see:
- Your newly added influencer
- Trust score with color-coded badge
- Search and filter options
- Detailed profile information

## What Just Happened?

When you added an influencer, Perseval:

1. ✓ Fetched their Instagram profile
2. ✓ Analyzed their 5 most recent posts
3. ✓ Searched the web via Perplexity for reputation data
4. ✓ Calculated 4 trust score components:
   - Message History (30%)
   - Followers Score (15%)
   - Web Reputation (40%) ← Powered by Perplexity
   - Disclosure Score (15%)
5. ✓ Combined scores into overall trust rating
6. ✓ Stored everything in Supabase
7. ✓ Made it available via API and frontend

## Testing the Marketplace

### Search Functionality
- Try searching by handle: "mkbhd"
- Try searching by name
- Filter by trust level: High/Medium/Low

### Sorting Options
- Sort by Trust Score (default)
- Sort by Followers
- Sort by Last Analyzed

### Detailed View
- Click on any influencer card
- See full breakdown of trust scores
- View analysis summary
- Check component scores

## Common Issues

### "Marketplace is not available"
- Check Supabase credentials in `.env`
- Verify database schema was created
- Ensure you're using service role key, not anon key

### "Failed to fetch Instagram stats"
- Influencer might have private account
- Try removing @ symbol from handle
- Instagram might be rate limiting

### "Authorization failed"
- Check `ADMIN_API_KEY` matches in `.env` and your request
- Ensure you're sending: `Authorization: Bearer YOUR_KEY`
- No quotes around the key in `.env`

### Perplexity API errors
- Verify your Perplexity API key is correct
- Check you have API credits remaining
- System will automatically fall back to Serper if available

## Next Steps

### Add More Influencers

Use the seed script to add multiple:
```bash
python scripts/seed_marketplace.py
```

### Customize Trust Weights

Edit `backend/app/services/trust.py`:
```python
def combine_trust_score(...):
    return (
        0.30 * message_history_score +  # Adjust these
        0.15 * followers_score +
        0.40 * web_reputation_score +
        0.15 * disclosure_score
    )
```

### Monitor Performance

Check backend logs for:
- `[WebSearch] Using Perplexity` ← Perplexity working
- `[WebSearch] Falling back to Serper` ← Perplexity unavailable
- `[Supabase] Added/updated marketplace influencer` ← Database working

### Explore API

Full API documentation:
```bash
# Open in browser
http://localhost:8000/docs
```

Interactive Swagger UI with all endpoints.

## Production Deployment

When deploying to production:

1. ✓ Use HTTPS for all API requests
2. ✓ Rotate API keys regularly
3. ✓ Set proper CORS origins in `.env`
4. ✓ Enable rate limiting (already configured)
5. ✓ Use environment-specific configs
6. ✓ Set up monitoring and logging
7. ✓ Regular database backups

See [DEPLOYMENT_READY.md](./DEPLOYMENT_READY.md) for details.

## Learn More

- 📖 [Complete Marketplace Guide](./MARKETPLACE_GUIDE.md)
- ➕ [Adding Influencers Guide](./ADDING_INFLUENCERS.md)
- 🧮 [Trust Algorithm Explained](./TRUST_ALGORITHM.md)
- 🔐 [Admin API Usage](./ADMIN_API_USAGE.md)

## Support

Having trouble? Check:
1. Backend logs for errors
2. Frontend console for API errors
3. Supabase logs for database issues
4. API documentation at `/docs`

## Success!

You now have a fully functional influencer marketplace with:
- ✓ AI-powered trust scores
- ✓ Perplexity integration for web research
- ✓ Real-time search and filtering
- ✓ Admin API for management
- ✓ Responsive, modern UI

Time to add more influencers and explore! 🚀
