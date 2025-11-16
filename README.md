# Perseval – Scam & Trust Checker

Perseval is a full‑stack tool that helps you quickly assess whether a social media promotion looks like a scam and how much you can trust the people and brands behind it.

The project has:
- a FastAPI backend (`backend/`) that talks to Mistral and Serper.dev, inspects Instagram posts, and computes trust scores
- a Next.js frontend (`frontend/`) that provides a one‑page UI for pasting messages or URLs and visualizing risk

---

## Quick start

### 1. Clone and set up environment

```bash
git clone <your-repo-url> perseval
cd perseval
python -m venv .venv
.venv\Scripts\activate  # on Windows
# source .venv/bin/activate  # on macOS/Linux
```

Create `backend/.env` (or reuse the one in this repo) with:

```bash
MISTRAL_API_KEY=...
SERPER_API_KEY=...
X_BEARER_TOKEN=...        # currently unused
MS_TOKEN=...              # currently unused
```

You need:
- a Mistral API key (for all LLM‑based scoring)
- a Serper.dev API key (for web reputation lookups)

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Run the backend API

From the repo root (with the virtualenv active):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API root should now respond at:

- `GET http://localhost:8000/` → health check

The main endpoints used by the UI:

- `POST /analyze/full` – full pipeline for a message or Instagram/TikTok URL
- `POST /analyze/text` – classify raw text as `scam` / `not_scam` / `uncertain`
- `POST /influencer/stats` – Instagram profile stats and recent captions
- `POST /influencer/trust` – influencer trust score
- `POST /company/trust` – company trust score
- `POST /product/trust` – product trust score
- `POST /instagram/post/analyze` – analyze a single Instagram post URL

### 4. Install and run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and make sure the frontend is configured (via `ANALYZE_ENDPOINT` in `frontend/src/app/lib/constants.ts`) to talk to `http://localhost:8000/analyze/full`.

---

## High‑level flow

1. **User input (frontend)**  
   - Paste free‑form text, or  
   - Paste an Instagram or TikTok URL, and optionally  
   - Provide an influencer handle, company name, and/or product name.

2. **Message analysis (backend)**  
   - Text is sent to Mistral via `mistral_scam_check` and classified as:
     - `scam`
     - `not_scam`
     - `uncertain`
   - Mistral also returns a `score` between 0 and 1 (confidence) and a short textual `reason`.

3. **Optional Instagram/TikTok caption fetch**  
   - For Instagram: the backend uses Instaloader to fetch the post caption and recent posts for the profile.
   - For TikTok: the backend uses `TikTokApi` (if installed) to fetch the video caption.

4. **Influencer / company / product reputation**  
   - The backend calls Serper.dev to fetch search snippets.
   - Mistral is prompted to summarize those snippets into reliability scores and issues.

5. **Aggregation & UI**  
   - The backend returns a `FullAnalysisResponse` with:
     - `message_prediction` (label, score, reason)
     - optional `influencer_trust`, `company_trust`, `product_trust`
     - `final_summary` – a stitched human‑readable narrative
   - The frontend:
     - color‑codes the card based on scam risk
     - highlights risky words
     - shows bullet‑point reasons and a global score percentage

---

## Methodology & formulas

### 1. Message scam risk (`mistral_scam_check`)

For any text (raw input or a post caption) the backend:

1. Sends a structured system prompt to Mistral explaining:
   - when to label something as `scam`, `not_scam`, or `uncertain`
   - how to output JSON with keys: `label`, `score`, `reason`
2. Parses the JSON and exposes:
   - `label ∈ {scam, not_scam, uncertain}`
   - `score ∈ [0, 1]` (LLM confidence)
   - `reason` (short explanation)

The frontend converts `score` into a percentage via:

```text
message_percent = round(clamp(score) * 100)
```

where `clamp(score)` is `score` clipped to `[0, 1]`.

### 2. Influencer trust score

For an Instagram handle, the backend:

1. Uses Instaloader to fetch:
   - follower count (`followers`)
   - following count (`following`)
   - recent posts with captions (`sample_posts`)
2. Calls Serper.dev to get web search snippets about the influencer.
3. Asks Mistral (via `evaluate_influencer_reputation`) to summarize those snippets into:
   - `influencer_reliability ∈ [0, 1]`
   - `issues` (list of notable concerns)
   - `summary` (one‑paragraph explanation)

We then compute four component scores in `[0, 1]`:

#### a. Message history score

Re‑run the scam classifier on each recent caption and map the labels to numeric values:

```text
scam       → 0.0
not_scam   → 1.0
uncertain  → 0.5
```

`message_history_score` is the mean of these values:

```text
message_history_score =
  if no meaningful posts: 0.5
  else: average(mapped_label_values)
```

This captures whether the influencer’s *recent output* looks safe or risky.

#### b. Followers score

We mix audience size and follower/following ratio:

```text
followers_size_score = clamp((log10(followers) - 2) / 3)
                       # 0 around 10² followers, 1 around 10⁵+

ratio = following / followers
ratio_score =
  if ratio <= 1: 1.0
  else: max(0, 1 - (ratio - 1))

followers_score = 0.7 * followers_size_score + 0.3 * ratio_score
```

Interpretation:
- larger, organic‑looking accounts score higher
- extremely lopsided “following >> followers” profiles are penalized

#### c. Web reputation score

`evaluate_influencer_reputation` uses Mistral to read Serper snippets and output:

```text
0.0  → clearly untrustworthy (accusations, fraud, major controversies)
0.5  → unclear, mixed, or insufficient data
1.0  → consistently positive or neutral coverage
```

This becomes:

```text
web_reputation_score = influencer_reliability  (clipped to [0,1])
```

#### d. Disclosure score

We scan recent captions for disclosure markers:

```text
markers = ["#ad", "#sponsored", "paid partnership"]

disclosure_ratio = (posts with any marker) / (posts with captions)

disclosure_score =
  if no posts:          0.3
  elif ratio >= 0.6:    1.0    # disclosures are frequent and consistent
  elif ratio > 0:       0.6    # sometimes disclosed
  else:                 0.3    # promotions rarely flagged as ads
```

This favors transparent disclosure behavior.

#### e. Combined influencer trust score

All four components are combined into a single trust score in `[0, 1]`:

```text
trust_score =
  0.30 * message_history_score +
  0.15 * followers_score +
  0.40 * web_reputation_score +
  0.15 * disclosure_score
```

Web reputation and message history carry the most weight, with followers and disclosure acting as modifiers.

We convert `trust_score` to a qualitative label:

```text
if trust_score >= 0.75 → "high"
elif trust_score >= 0.40 → "medium"
else → "low"
```

The frontend displays this influencer trust as a percentage (`trust_score * 100`) and uses it when computing the overall score.

### 3. Company & product trust

For companies and products, the pipeline is simpler:

1. Use Serper.dev to fetch search snippets:
   - `get_company_snippets(name, max_results)`
   - `get_product_snippets(name, max_results)`
2. Call Mistral with a focused system prompt:
   - `evaluate_company_reputation(name, snippets)` → `company_reliability ∈ [0,1]`
   - `evaluate_product_reputation(name, snippets)` → `product_reliability ∈ [0,1]`
3. Expose those as:

```text
CompanyTrustResponse.trust_score  = company_reliability
ProductTrustResponse.trust_score  = product_reliability
```

The responses also include:
- `summary` – a short explanation
- `issues` – list of notable red flags if any

### 4. Overall score shown in the UI

The frontend derives a single “overall” score when a full analysis is available:

```text
scores = [message_prediction.score]
optionally add: influencer_trust.trust_score, company_trust.trust_score, product_trust.trust_score
overall_score = min(scores)
overall_percent = round(clamp(overall_score) * 100)
```

We use the **minimum** rather than an average so that a single very low‑trust component (e.g., known scammy company) can drag the overall score down, even if other elements look fine.

### 5. Risk tiers and UI language

On the backend:

- `label = "scam"` → treated as **high‑risk**
- `label = "uncertain"` → **caution**
- `label = "not_scam"` → **low risk**

On the frontend (`deriveRiskTier`):

```text
if label === "scam"      → tier "high"
elif label === "uncertain" → tier "caution"
else                       → tier "low"
```

The tier selects:
- background gradient / card color
- short disclaimers and visual emphasis

Reason text from the model is split into up to three bullet points, each assigned a severity (`high`, `medium`, `info`) based on scam keywords and the label.

---

## Limitations & disclaimers

- **LLM‑based**: All classifications and scores use Mistral; they can be wrong or biased.
- **Not legal or financial advice**: Treat outputs as decision‑support, not definitive truth.
- **Data coverage**: Web reputation relies on what Serper surfaces; low coverage leads to neutral (0.5) scores.
- **Platform constraints**: TikTok analysis requires `TikTokApi` and may be brittle if the platform changes.

Always verify important decisions with independent sources. Perseval is a research/prototyping tool, not a compliance or KYC system.

