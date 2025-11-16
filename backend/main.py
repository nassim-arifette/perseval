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
    from backend.serper_client import serper_search
except ModuleNotFoundError:  # script executed from backend directory
    from influencer_probe import get_instagram_post_from_url, get_instagram_stats
    from serper_client import serper_search

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
    web_reputation_score: float = Field(..., ge=0.0, le=1.0)
    notes: str


class CompanyTrustRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Company / brand name to investigate.")
    max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper search snippets to consider.",
    )


class CompanyTrustResponse(BaseModel):
    name: str
    trust_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    issues: List[str] = Field(default_factory=list)


class ProductTrustRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Product name to investigate.")
    max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper search snippets to consider.",
    )


class ProductTrustResponse(BaseModel):
    name: str
    trust_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    issues: List[str] = Field(default_factory=list)


class FullAnalysisSource(BaseModel):
    text_origin: Literal["input", "instagram"]
    instagram_url: Optional[str] = None
    instagram_owner: Optional[str] = None
    inferred_company_name: Optional[str] = None
    inferred_product_name: Optional[str] = None


class FullAnalysisRequest(BaseModel):
    text: Optional[str] = Field(
        None,
        description="Raw message text provided by the user.",
    )
    instagram_url: Optional[HttpUrl] = Field(
        None,
        description="Instagram post / reel URL to fetch caption from.",
    )
    influencer_handle: Optional[str] = Field(
        None,
        description="Preferred influencer handle (defaults to the Instagram owner if URL is given).",
    )
    company_name: Optional[str] = Field(
        None,
        description="Company name to check via web reputation search.",
    )
    product_name: Optional[str] = Field(
        None,
        description="Product name to check via web reputation search.",
    )
    max_posts: int = Field(
        5,
        ge=1,
        le=20,
        description="Recent posts to inspect for influencer trust scoring.",
    )
    company_max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper snippets to consider for company reputation.",
    )
    product_max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper snippets to consider for product reliability.",
    )


class FullAnalysisResponse(BaseModel):
    message_prediction: ScamPrediction
    influencer_trust: Optional[InfluencerTrustResponse] = None
    company_trust: Optional[CompanyTrustResponse] = None
    product_trust: Optional[ProductTrustResponse] = None
    source_details: FullAnalysisSource
    final_summary: str


# ---------- Helpers ----------

def _parse_mistral_content(raw_content: str) -> dict:
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            lines = [
                line for line in cleaned.splitlines()
                if not line.strip().startswith("```")
            ]
            cleaned = "\n".join(lines).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        try:
            return json.loads(cleaned)
        except Exception:
            return {}


def call_mistral_json(messages: List[dict], *, debug: bool = False) -> dict:
    """
    Shared helper to send chat prompts expecting a JSON object back.
    """
    payload = {
        "model": "open-mixtral-8x22b",
        "response_format": {"type": "json_object"},
        "messages": messages,
        "temperature": 0.2,
    }
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        json=payload,
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error from Mistral API: {resp.text}",
        )

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if debug:
        print("=== MISTRAL RAW CONTENT ===")
        print(repr(content))
        print("=== END RAW CONTENT ===")

    parsed = _parse_mistral_content(content)
    if not isinstance(parsed, dict):
        parsed = {}
    return parsed


def mistral_scam_check(post_text: str, *, debug: bool = True) -> ScamPrediction:
    """
    Call Mistral chat API and ask it to classify the post as scam / not_scam / uncertain.
    """
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

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Post text:\n{post_text}"},
    ]
    j = call_mistral_json(messages, debug=debug)

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
        prediction = mistral_scam_check(text, debug=False)
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


def combine_trust_score(
    message_history_score: float,
    followers_score: float,
    web_reputation_score: float,
) -> float:
    return (
        0.35 * message_history_score
        + 0.15 * followers_score
        + 0.5 * web_reputation_score
    )


def label_from_trust_score(score: float) -> Literal["high", "medium", "low"]:
    if score >= 0.75:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def fetch_snippets_from_queries(queries: List[str], max_results: int = 8) -> List[dict]:
    """
    Query Serper for each query, collect organic snippets, deduplicate, and trim.
    """
    snippets: List[dict] = []
    for query in queries:
        try:
            data = serper_search(query, num=5, search_type="search")
        except Exception as exc:
            print(f"[serper] query failed for {query!r}: {exc}")
            continue
        for item in data.get("organic", []):
            link = item.get("link")
            if not link:
                continue
            snippet = {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": link,
            }
            snippets.append(snippet)

    uniq = {}
    for snip in snippets:
        uniq[snip["link"]] = snip
    return list(uniq.values())[:max_results]


def get_company_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" reviews',
        f'"{name}" scam',
        f'"{name}" lawsuit',
        f'"{name}" complaints',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_product_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" product reviews',
        f'"{name}" complaints',
        f'"{name}" scam',
        f'"{name}" safety issues',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_influencer_snippets(
    handle: str,
    full_name: Optional[str],
    max_results: int = 8,
) -> List[dict]:
    normalized_handle = handle.lstrip("@")
    queries = [
        f'"{normalized_handle}" scam',
        f'"{normalized_handle}" controversy',
        f'"{normalized_handle}" lawsuit',
    ]
    if full_name:
        queries += [
            f'"{full_name}" scam',
            f'"{full_name}" controversy',
        ]
    return fetch_snippets_from_queries(queries, max_results)


def evaluate_company_reputation(name: str, snippets: List[dict]) -> dict:
    if not snippets:
        return {
            "company_reliability": 0.5,
            "issues": ["Insufficient public data"],
            "summary": "No meaningful search results to evaluate reputation.",
        }

    system_prompt = """
You review public web snippets about a company.

Given titles/snippets from search results, answer:
- Are there credible accusations of scams, fraud, lawsuits, or regulatory actions?
- Rate reliability between 0 and 1 (1 = very reliable, 0 = clearly untrustworthy).

Be conservative: some negative reviews are normal, but repeated mentions of scams,
lawsuits, or investigations indicate low reliability.

Respond ONLY as JSON:
{
  "company_reliability": 0-1 float,
  "issues": [list of notable problems or an empty list],
  "summary": "short explanation"
}
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(
                {"company": name, "snippets": snippets},
                ensure_ascii=False,
            ),
        },
    ]
    return call_mistral_json(messages)


def evaluate_product_reputation(name: str, snippets: List[dict]) -> dict:
    if not snippets:
        return {
            "product_reliability": 0.5,
            "issues": ["Insufficient public data"],
            "summary": "No meaningful search results to evaluate reputation.",
        }

    system_prompt = """
You review public web snippets about a consumer product or offer.

Given titles/snippets from search results, answer:
- Are there credible reports of defects, scams, unsafe ingredients, or lawsuits?
- Rate reliability between 0 and 1 (1 = very reliable, 0 = clearly untrustworthy).

Respond ONLY as JSON:
{
  "product_reliability": 0-1 float,
  "issues": [list of notable problems or an empty list],
  "summary": "short explanation"
}
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(
                {"product": name, "snippets": snippets},
                ensure_ascii=False,
            ),
        },
    ]
    return call_mistral_json(messages)


def evaluate_influencer_reputation(handle: str, snippets: List[dict]) -> dict:
    if not snippets:
        return {
            "influencer_reliability": 0.5,
            "issues": ["Insufficient public data"],
            "summary": "No meaningful search results to evaluate reputation.",
        }

    system_prompt = """
You assess public information about a social media influencer.

Given titles/snippets from search results, answer:
- Are there credible accusations of scams, misleading promotions, fraud, or major controversies?
- Rate trustworthiness between 0 and 1 (1 = very trustworthy, 0 = clearly untrustworthy).

Focus on credible reports (news outlets, regulators, well-documented investigations) and ignore gossip.

Respond ONLY as JSON:
{
  "influencer_reliability": 0-1 float,
  "issues": [list of notable problems or an empty list],
  "summary": "short explanation"
}
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(
                {"handle": handle, "snippets": snippets},
                ensure_ascii=False,
            ),
        },
    ]
    return call_mistral_json(messages)


def detect_company_from_text(text: str) -> Optional[str]:
    """
    Use the LLM to guess which company/product is referenced in the message.
    """
    system_prompt = """
You identify the most relevant company or product mentioned in a message.

Respond ONLY as JSON:
{
  "company_candidates": [
    {"name": "Company or product name", "confidence": 0-1 float, "reason": "short string"}
  ]
}

Return an empty list if no credible company is mentioned.
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    data = call_mistral_json(messages)
    candidates = data.get("company_candidates") or []
    best_name = None
    best_conf = 0.0
    for item in candidates:
        try:
            conf = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        name = str(item.get("name") or "").strip()
        if name and conf > best_conf:
            best_conf = conf
            best_name = name
    if best_name and best_conf >= 0.55:
        return best_name
    return None


async def build_influencer_trust_response(
    handle: str,
    max_posts: int,
) -> InfluencerTrustResponse:
    stats_dc = get_instagram_stats(handle, max_posts=max_posts)
    stats = InfluencerStatsResponse(**asdict(stats_dc))

    mh_score = compute_message_history_score(stats.sample_posts or [])
    followers_score = compute_followers_score(stats.followers, stats.following)
    web_snippets = get_influencer_snippets(handle, stats.full_name)
    web_reputation = evaluate_influencer_reputation(handle, web_snippets)
    web_score = float(web_reputation.get("influencer_reliability", 0.5))

    trust_score = combine_trust_score(mh_score, followers_score, web_score)
    label = label_from_trust_score(trust_score)

    recent_note = (
        "mostly safe" if mh_score > 0.7 else "mixed" if mh_score > 0.4 else "often risky"
    )
    follower_note = (
        "plausible" if followers_score > 0.7 else "unusual" if followers_score < 0.4 else "unclear"
    )
    web_note = web_reputation.get("summary") or "Little public information available."
    notes = (
        f"Recent posts look {recent_note}. "
        f"Followers profile looks {follower_note}. "
        f"Web reputation: {web_note}"
    )

    return InfluencerTrustResponse(
        stats=stats,
        trust_score=trust_score,
        label=label,
        message_history_score=mh_score,
        followers_score=followers_score,
        web_reputation_score=web_score,
        notes=notes,
    )


def build_company_trust_response(
    name: str,
    max_results: int,
) -> CompanyTrustResponse:
    snippets = get_company_snippets(name, max_results=max_results)
    reputation = evaluate_company_reputation(name, snippets)
    trust_score = float(reputation.get("company_reliability", 0.5))
    summary = reputation.get("summary") or "Insufficient public data."
    issues = reputation.get("issues") or []

    return CompanyTrustResponse(
        name=name,
        trust_score=trust_score,
        summary=summary,
        issues=issues,
    )


def build_product_trust_response(
    name: str,
    max_results: int,
) -> ProductTrustResponse:
    snippets = get_product_snippets(name, max_results=max_results)
    reputation = evaluate_product_reputation(name, snippets)
    trust_score = float(reputation.get("product_reliability", 0.5))
    summary = reputation.get("summary") or "Insufficient public data."
    issues = reputation.get("issues") or []

    return ProductTrustResponse(
        name=name,
        trust_score=trust_score,
        summary=summary,
        issues=issues,
    )


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
        return await build_influencer_trust_response(handle, max_posts=req.max_posts)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch {req.platform} stats: {exc}",
        ) from exc


@app.post("/company/trust", response_model=CompanyTrustResponse)
def company_trust(req: CompanyTrustRequest):
    """
    Use Serper + Mistral to estimate overall company reputation.
    """
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    return build_company_trust_response(name, max_results=req.max_results)


@app.post("/product/trust", response_model=ProductTrustResponse)
def product_trust(req: ProductTrustRequest):
    """
    Use Serper + Mistral to estimate product-level reliability.
    """
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name cannot be empty.")

    return build_product_trust_response(name, max_results=req.max_results)


@app.get("/")
def root():
    return {"status": "ok", "message": "Scam checker API running"}


@app.post("/analyze/full", response_model=FullAnalysisResponse)
async def analyze_full(req: FullAnalysisRequest):
    """
    Unified endpoint: accept raw text and/or Instagram URL, optionally enrich with influencer + company trust.
    """
    text = (req.text or "").strip()
    influencer_handle = (req.influencer_handle or "").strip() or None
    source_details: FullAnalysisSource = FullAnalysisSource(text_origin="input")

    if req.instagram_url:
        try:
            post = get_instagram_post_from_url(str(req.instagram_url))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch Instagram post: {exc}",
            ) from exc

        caption = (post.caption or "").strip()
        source_details = FullAnalysisSource(
            text_origin="instagram",
            instagram_url=str(req.instagram_url),
            instagram_owner=post.owner_username,
        )
        if caption:
            text = caption
        elif not text:
            raise HTTPException(
                status_code=400,
                detail="Instagram post has no caption and no fallback text was provided.",
            )
        if not influencer_handle:
            influencer_handle = post.owner_username

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Provide either message text or an Instagram URL.",
        )

    prediction = mistral_scam_check(text, debug=False)

    influencer_trust = None
    if influencer_handle:
        try:
            influencer_trust = await build_influencer_trust_response(
                influencer_handle,
                max_posts=req.max_posts,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build influencer trust: {exc}",
            ) from exc

    inferred_company = None
    inferred_product = None
    company_name = (req.company_name or "").strip() or None
    product_name = (req.product_name or "").strip() or None
    detected_candidate = None
    if not company_name or not product_name:
        detected_candidate = detect_company_from_text(text)
    if not company_name and detected_candidate:
        inferred_company = detected_candidate
        company_name = detected_candidate
    if not product_name and detected_candidate:
        inferred_product = detected_candidate
        product_name = detected_candidate
    company_trust = None
    if company_name:
        try:
            company_trust = build_company_trust_response(
                company_name,
                max_results=req.company_max_results,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build company trust: {exc}",
            ) from exc
    product_trust = None
    if product_name:
        try:
            product_trust = build_product_trust_response(
                product_name,
                max_results=req.product_max_results,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build product trust: {exc}",
            ) from exc
    source_details.inferred_company_name = inferred_company
    source_details.inferred_product_name = inferred_product

    summary_parts: List[str] = []
    summary_parts.append(
        f"Message assessment: {prediction.label.replace('_', ' ')} — {prediction.reason or 'no additional context'}."
    )
    if influencer_trust:
        summary_parts.append(
            f"Influencer trust: {influencer_trust.label} ({int(influencer_trust.trust_score * 100)}%). {influencer_trust.notes}"
        )
    if company_trust:
        summary_parts.append(
            f"Company reputation ({company_name}): {int(company_trust.trust_score * 100)}%. {company_trust.summary}"
        )
    elif company_name:
        summary_parts.append(f"Company mentioned ({company_name}) but reputation lookup failed.")
    if product_trust:
        summary_parts.append(
            f"Product reliability ({product_name}): {int(product_trust.trust_score * 100)}%. {product_trust.summary}"
        )
    elif product_name:
        summary_parts.append(f"Product mentioned ({product_name}) but reliability lookup failed.")
    if not company_name and not product_name:
        summary_parts.append("No clear company or product was detected in the content.")
    final_summary = " ".join(summary_parts).strip()

    return FullAnalysisResponse(
        message_prediction=prediction,
        influencer_trust=influencer_trust,
        company_trust=company_trust,
        product_trust=product_trust,
        source_details=source_details,
        final_summary=final_summary,
    )


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
