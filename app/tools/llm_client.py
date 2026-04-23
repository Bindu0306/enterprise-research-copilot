# app/tools/llm_client.py
# Central LLM client — change model here once,
# affects all agents automatically

import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Model to use
MODEL = "llama-3.3-70b-versatile"


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    Central LLM call function.
    All agents use this instead of calling API directly.
    Returns raw text response.
    """
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content


def call_llm_json(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    LLM call that extracts JSON from response.
    Handles cases where model adds extra text around JSON.
    Returns only the JSON string.
    """
    raw = call_llm(system_prompt, user_message, max_tokens)

    # Try to extract JSON object if extra text exists
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        return json_match.group()

    # Return raw if no JSON found — let caller handle error
    return raw