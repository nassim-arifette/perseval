import json
import math
import os
from dataclasses import asdict
from typing import List, Literal, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

try:
    from backend.influencer_probe import (
        get_instagram_post_from_url,
        get_instagram_stats,
    )
except ModuleNotFoundError:  # script executed from backend directory
    from influencer_probe import get_instagram_post_from_url, get_instagram_stats

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise RuntimeError("Missing MISTRAL_API_KEY in .env")

app = FastAPI(title="Scam Checker API")


# ---------- Request / response schemas ----------

class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="Raw text to evaluate for scam risk")


class ScamPrediction(BaseModel):
    label: Literal["scam", "not_scam", "uncertain"]
    score: float          # 0-1 confidence
    reason: str           # short explanation
    raw_post_text: str


class InfluencerStatsRequest(BaseModel):
    platform: Literal["instagram"] = Field(
        "instagram",
        description="Target platform (Instagram only while Twitter/X support is paused).",
    )
    handle: str = Field(..., description="Target username / handle (with or without @).")
    max_posts: int = Field(5, ge=1, le=20, description="How many recent posts to inspect.")


class InfluencerStatsResponse(BaseModel):
    platform: Literal["instagram"]
    handle: str
    full_name: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    posts_count: Optional[int] = None
    is_verified: Optional[bool] = None
    bio: Optional[str] = None
    url: Optional[str] = None
    sample_posts: Optional[List[str]] = None


class InstagramPostAnalyzeRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="Instagram post / reel URL whose caption should be analyzed.",
    )


class InfluencerTrustResponse(BaseModel):
    stats: InfluencerStatsResponse
    trust_score: float = Field(..., ge=0.0, le=1.0)
    label: Literal["high", "medium", "low"]
    message_history_score: float = Field(..., ge=0.0, le=1.0)
    followers_score: float = Field(..., ge=0.0, le=1.0)
    notes: str


# ---------- Helpers ----------

def mistral_scam_check(post_text: str) -> ScamPrediction:
    """
    Call Mistral chat API and ask it to classify the post as scam / not_scam / uncertain.
    """
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    SYSTEM_PROMPT = """
You are a risk analysis assistant.
Given the text of a social media post, decide whether it is likely part of a scam,
high-risk misleading promotion, or not.

Be conservative:
- Use "scam" when there are clear red flags: guaranteed returns, crypto doubling,
  suspicious links, pressure to act now, miracle cures, impersonation, etc.
- Use "not_scam" when it is clearly harmless.
- Use "uncertain" only when there is genuinely not enough information.

You MUST respond with a single JSON object with EXACTLY these keys:
- "label": one of "scam", "not_scam", or "uncertain"
- "score": a number between 0 and 1 (float) representing your confidence
- "reason": a short human-readable explanation string

Valid example:
{"label": "scam", "score": 0.97, "reason": "Promises to double your crypto if you send funds first."}

Rules:
- Do NOT include any additional keys.
- Do NOT add explanations outside the JSON.
- Do NOT use Markdown.
"""

    payload = {
        "model": "open-mixtral-8x22b",  # or another model you prefer
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Post text:\n{post_text}"},
        ],
        "temperature": 0.2,
    }

    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error from Mistral API: {resp.text}"
        )

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    # DEBUG: see exactly what Mistral sent
    print("=== MISTRAL RAW CONTENT ===")
    print(repr(content))
    print("=== END RAW CONTENT ===")

    j = None

    # 1) Try direct JSON parse
    try:
        j = json.loads(content)
    except json.JSONDecodeError:
        # 2) Try to clean up (remove ``` fences, keep only {...})
        cleaned = content.strip()

        # Remove ```json ... ``` fences if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = [
                line for line in lines
                if not line.strip().startswith("```")
            ]
            cleaned = "\n".join(lines).strip()

        # Keep only the substring from first '{' to last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]

        try:
            j = json.loads(cleaned)
        except Exception:
            j = None

    # 3) Final fallback if everything fails
    if not isinstance(j, dict):
        j = {
            "label": "uncertain",
            "score": 0.0,
            "reason": content,  # keep full text for debugging
        }

    label = j.get("label", "uncertain")
    score = float(j.get("score", 0.0))
    reason = str(j.get("reason", ""))

    return ScamPrediction(
        label=label,
        score=score,
        reason=reason,
        raw_post_text=post_text
    )


def compute_message_history_score(sample_posts: List[str]) -> float:
    """
    Re-run the scam classifier on recent posts and derive a 0..1 score.
    """
    meaningful_posts = [text for text in sample_posts if text and text.strip()]
    if not meaningful_posts:
        return 0.5  # lack of evidence

    scores: List[float] = []
    for text in meaningful_posts:
        prediction = mistral_scam_check(text)
        if prediction.label == "scam":
            val = 0.0
        elif prediction.label == "not_scam":
            val = 1.0
        else:
            val = 0.5
        scores.append(val)

    return sum(scores) / len(scores)


def compute_followers_score(
    followers: Optional[int],
    following: Optional[int],
) -> float:
    """
    Simple heuristic about follower volume and ratios.
    """
    if not followers or followers <= 0:
        return 0.5

    log_f = math.log10(max(followers, 1))
    followers_size_score = max(0.0, min(1.0, (log_f - 2) / 3))  # 100 -> 100k window

    ratio_score = 1.0
    if following is not None and followers > 0:
        ratio = following / followers
        if ratio > 1:
            ratio_score = max(0.0, 1.0 - (ratio - 1))

    return 0.7 * followers_size_score + 0.3 * ratio_score


def combine_trust_score(message_history_score: float, followers_score: float) -> float:
    return 0.7 * message_history_score + 0.3 * followers_score


def label_from_trust_score(score: float) -> Literal["high", "medium", "low"]:
    if score >= 0.75:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


# ---------- API endpoints ----------

@app.post("/analyze/text", response_model=ScamPrediction)
def analyze_text(req: TextAnalyzeRequest):
    """
    Accept pasted text directly and evaluate whether it looks like a scam or not.
    """
    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Text to analyze cannot be empty.")

    prediction = mistral_scam_check(cleaned_text)
    return prediction


@app.post("/influencer/stats", response_model=InfluencerStatsResponse)
async def influencer_stats(req: InfluencerStatsRequest):
    """
    Fetch influencer metadata + sample posts via Instaloader (Instagram only for now).
    """
    handle = req.handle.strip()
    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty.")

    try:
        stats = get_instagram_stats(handle, max_posts=req.max_posts)
        return InfluencerStatsResponse(**asdict(stats))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch {req.platform} stats: {exc}",
        ) from exc


@app.post("/influencer/trust", response_model=InfluencerTrustResponse)
async def influencer_trust(req: InfluencerStatsRequest):
    """
    Return influencer stats plus a composite trust score.
    """
    handle = req.handle.strip()
    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty.")

    try:
        stats_dc = get_instagram_stats(handle, max_posts=req.max_posts)
        stats = InfluencerStatsResponse(**asdict(stats_dc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch {req.platform} stats: {exc}",
        ) from exc

    mh_score = compute_message_history_score(stats.sample_posts or [])
    followers_score = compute_followers_score(stats.followers, stats.following)
    trust_score = combine_trust_score(mh_score, followers_score)
    label = label_from_trust_score(trust_score)

    recent_note = (
        "mostly safe" if mh_score > 0.7 else "mixed" if mh_score > 0.4 else "often risky"
    )
    follower_note = (
        "plausible" if followers_score > 0.7 else "unusual" if followers_score < 0.4 else "unclear"
    )
    notes = f"Recent posts look {recent_note}. Followers profile looks {follower_note}."

    return InfluencerTrustResponse(
        stats=stats,
        trust_score=trust_score,
        label=label,
        message_history_score=mh_score,
        followers_score=followers_score,
        notes=notes,
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Scam checker API running"}


@app.post("/instagram/post/analyze", response_model=ScamPrediction)
def analyze_instagram_post(req: InstagramPostAnalyzeRequest):
    """
    Given a public Instagram post URL, fetch its caption via Instaloader and run the scam checker.
    """
    try:
        post = get_instagram_post_from_url(str(req.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - instaloader-specific failures
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch Instagram post: {exc}",
        ) from exc

    caption = (post.caption or "").strip()
    if not caption:
        raise HTTPException(
            status_code=400,
            detail="This Instagram post has no caption to analyze.",
        )

    return mistral_scam_check(caption)
