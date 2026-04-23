# app/tools/llm_client.py

import os
import re
import time
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── API Key ───────────────────────────────────────────────
# Works for both local .env and Streamlit Cloud secrets

def _get_api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=_get_api_key())

# ── Models ────────────────────────────────────────────────

FAST_MODEL   = "llama-3.1-8b-instant"
STRONG_MODEL = "llama-3.3-70b-versatile"

# ── Token budgets per agent ───────────────────────────────
# Keeps costs low by limiting each agent to what it needs

TOKEN_BUDGETS = {
    "planner":    400,
    "researcher": 500,
    "critic":     600,
    "writer":     1200,
    "default":    500
}

# ── Core LLM call with retry on rate limit ────────────────

def call_llm(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 500,
    use_strong: bool = False
) -> str:
    """
    Call LLM with automatic retry on rate limit (429).
    Waits 30s after first failure, 60s after second.
    Raises after 3 failed attempts.
    """
    model = STRONG_MODEL if use_strong else FAST_MODEL

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message}
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e)

            # Rate limit hit — wait and retry
            if "429" in error_str:
                wait_seconds = (attempt + 1) * 30
                print(f"Rate limit hit. Waiting {wait_seconds}s before retry {attempt + 1}/3...")
                time.sleep(wait_seconds)

            # Any other error — raise immediately
            else:
                raise

    raise Exception("Rate limit exceeded after 3 retries. Please wait and try again.")


def call_llm_json(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 500,
    use_strong: bool = False
) -> str:
    """
    LLM call that extracts JSON from response.
    Handles cases where model adds extra text around JSON.
    """
    raw = call_llm(system_prompt, user_message, max_tokens, use_strong)

    # Extract JSON object if extra text exists
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        return json_match.group()

    return raw