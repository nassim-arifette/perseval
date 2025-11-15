import json
import os
from typing import Literal

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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


@app.get("/")
def root():
    return {"status": "ok", "message": "Scam checker API running"}
