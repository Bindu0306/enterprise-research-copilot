# app/tools/wikipedia_tool.py

import time
import wikipedia
from dotenv import load_dotenv

load_dotenv()

wikipedia.set_lang("en")
MAX_SENTENCES = 5
SEARCH_RESULTS = 3


def search_wikipedia(query: str) -> dict:
    """
    Search Wikipedia for a query.
    Returns a dict with title, summary, url, and found status.
    Never crashes — all errors caught and returned as structured response.
    """
    try:
        # Respect Wikipedia rate limits
        time.sleep(1)

        # Step 1 — search for matching page titles
        search_results = wikipedia.search(query, results=SEARCH_RESULTS)

        if not search_results:
            return {
                "subquestion": query,
                "source": "Wikipedia",
                "title": "No results found",
                "content": "",
                "url": "",
                "found": False
            }

        # Step 2 — open the first page
        page_title = search_results[0]

        summary = wikipedia.summary(
            page_title,
            sentences=MAX_SENTENCES,
            auto_suggest=False
        )

        page = wikipedia.page(page_title, auto_suggest=False)

        return {
            "subquestion": query,
            "source": "Wikipedia",
            "title": page_title,
            "content": summary,
            "url": page.url,
            "found": True
        }

    except wikipedia.exceptions.DisambiguationError as e:
        # Wikipedia found multiple matches
        # Ask LLM to pick the most relevant one
        try:
            time.sleep(1)

            best_option = _pick_best_option(query, e.options)

            summary = wikipedia.summary(
                best_option,
                sentences=MAX_SENTENCES,
                auto_suggest=False
            )

            page = wikipedia.page(best_option, auto_suggest=False)

            return {
                "subquestion": query,
                "source": "Wikipedia",
                "title": best_option,
                "content": summary,
                "url": page.url,
                "found": True
            }

        except Exception:
            return {
                "subquestion": query,
                "source": "Wikipedia",
                "title": "Disambiguation error",
                "content": "",
                "url": "",
                "found": False
            }

    except wikipedia.exceptions.PageError:
        return {
            "subquestion": query,
            "source": "Wikipedia",
            "title": "Page not found",
            "content": "",
            "url": "",
            "found": False
        }

    except Exception as e:
        return {
            "subquestion": query,
            "source": "Wikipedia",
            "title": "Error",
            "content": f"Search failed: {e}",
            "url": "",
            "found": False
        }


def _pick_best_option(query: str, options: list) -> str:
    """
    When Wikipedia returns multiple options (DisambiguationError),
    ask LLM to pick the most relevant one for the research query.
    Falls back to first option if LLM fails.
    """
    try:
        from app.tools.llm_client import call_llm

        top_options = options[:5]
        options_text = "\n".join(
            f"{i+1}. {opt}"
            for i, opt in enumerate(top_options)
        )

        response = call_llm(
            system_prompt="""You are a search assistant.
Given a research query and Wikipedia page options,
return ONLY the single most relevant page title.
No explanation. No punctuation. Just the exact title.""",
            user_message=f"""Research query:
\"\"\"{query}\"\"\"

Wikipedia options:
\"\"\"{options_text}\"\"\"

Return only the best matching title.""",
            max_tokens=50
        )

        best = response.strip()

        # Safety check — make sure LLM picked a valid option
        if best in top_options:
            return best

        # Fallback to first option
        return options[0]

    except Exception:
        # If LLM call fails — use first option
        return options[0]