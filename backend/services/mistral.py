"""Mistral API helpers used across the backend."""

import json
from typing import List, Optional, Tuple

import requests
from fastapi import HTTPException

from config import MISTRAL_API_KEY
from schemas import ScamPrediction


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
        "model": "mistral-small-latest",
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
        detail_text = resp.text
        parsed_error = None
        try:
            parsed_error = resp.json()
        except ValueError:
            parsed_error = None

        if isinstance(parsed_error, dict):
            error_type = parsed_error.get("type")
            error_message = parsed_error.get("message") or detail_text

            if error_type == "service_tier_capacity_exceeded":
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Mistral API capacity for your service tier is temporarily exceeded. "
                        "Wait a minute and retry, or use a higher tier."
                    ),
                )
            detail_text = error_message

        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error from Mistral API: {detail_text}",
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
    system_prompt = """
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
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Post text:\n{post_text}"},
    ]
    response_data = call_mistral_json(messages, debug=debug)

    label = response_data.get("label", "uncertain")
    score = float(response_data.get("score", 0.0))
    reason = str(response_data.get("reason", ""))

    return ScamPrediction(
        label=label,
        score=score,
        reason=reason,
        raw_post_text=post_text,
    )


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


def _select_best_candidate(candidates: List[dict]) -> Optional[str]:
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


def detect_company_and_product_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Use the LLM to infer both the company/brand and the product/service being promoted.
    """
    system_prompt = """
You identify any company/brand and product/service referenced in a message.

Distinguish the organization (company) from the item being offered (product).
If the same string refers to both but context makes it primarily a product, leave the company list empty.

Respond ONLY as JSON:
{
  "company_candidates": [
    {"name": "Company or brand", "confidence": 0-1 float}
  ],
  "product_candidates": [
    {"name": "Product or service", "confidence": 0-1 float}
  ]
}

Return empty lists when unsure.
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    data = call_mistral_json(messages)
    company = _select_best_candidate(data.get("company_candidates") or [])
    product = _select_best_candidate(data.get("product_candidates") or [])
    if company and product and company.lower() == product.lower():
        product = None
    return company, product
