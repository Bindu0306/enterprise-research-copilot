import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


def get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key

    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    raise ValueError("GROQ_API_KEY not found in .env or Streamlit secrets")


client = Groq(api_key=get_groq_api_key())


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content


def call_llm_json(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    raw = call_llm(system_prompt, user_message, max_tokens)

    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        return json_match.group()

    return raw