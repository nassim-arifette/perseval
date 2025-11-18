# Railway Deployment Guide

## ✅ Files Updated for Deployment

All Python imports have been converted from absolute (`backend.xyz`) to relative (`xyz`) imports.

This allows Railway to run the application correctly.

## 🚀 Deploy to Railway

### Step 1: Push Your Code

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### Step 2: Go to Railway

1. Visit https://railway.app
2. Sign up/login (use GitHub)
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Connect your repository

### Step 3: Configure Railway

**In Railway Dashboard:**

1. **Settings → General:**
   - Root Directory: `/backend`

2. **Settings → Deploy:**
   - Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
   - (This should be auto-detected from Procfile)

3. **Variables → Add Variables:**
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key  
   MISTRAL_API_KEY=your_mistral_key
   SERPER_API_KEY=your_serper_key
   ADMIN_API_KEY=your_admin_key
   ```

4. **Click "Deploy"**

### Step 4: Get Your URL

After deployment completes, Railway will provide a URL like:
```
https://your-app.up.railway.app
```

Copy this URL - you'll need it for the frontend!

## 🌐 Deploy Frontend to Vercel

### Step 1: Update Frontend Environment

Create `frontend/.env.production`:
```bash
NEXT_PUBLIC_BACKEND_URL=https://your-app.up.railway.app
```

### Step 2: Deploy

1. Visit https://vercel.com
2. Click "Add New Project"
3. Import your GitHub repo
4. Set **Root Directory**: `frontend`
5. Add environment variable: `NEXT_PUBLIC_BACKEND_URL`
6. Click "Deploy"

## ✅ Verify Deployment

Test your backend:
```bash
curl https://your-app.up.railway.app/
# Should return: {"status":"ok","message":"Scam checker API running"}
```

Test rate limiting:
```bash
# Make 11 requests - the 11th should be rate limited
for i in {1..11}; do
  curl -X POST https://your-app.up.railway.app/analyze/text \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}';
done
```

## 🐛 Troubleshooting

### "No module named 'backend'"

**Solution:** Make sure Railway's **Root Directory** is set to `/backend`

### Module import errors

**Solution:** All imports should be relative (no `backend.` prefix)
- ✅ `from supabase_client import ...`
- ❌ `from backend.supabase_client import ...`

### Environment variables not working

**Solution:** Add them in Railway dashboard under **Variables**

## 📊 Free Tier Limits

- **Railway:** 500 hours/month (about 16 hours/day)
- **Vercel:** Unlimited for frontend
- **Supabase:** 500MB database, 2GB bandwidth

Perfect for hackathon demos!
