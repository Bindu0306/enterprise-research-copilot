import json
from datetime import datetime
from dotenv import load_dotenv
from app.models.state import ResearchState
from app.prompts.researcher_prompt import (
    RESEARCHER_SYSTEM_PROMPT,
    RESEARCHER_USER_TEMPLATE
)
from app.tools.wikipedia_tool import search_wikipedia
from app.tools.llm_client import call_llm_json

load_dotenv()


def run_researcher(state: ResearchState) -> ResearchState:
    subquestions = state["subquestions"]
    trace = state["trace"]
    retry_count = state["retry_count"]

    trace.append(
        f"[{_timestamp()}] Researcher: starting — "
        f"researching {len(subquestions)} sub-questions "
        f"(attempt {retry_count + 1})"
    )

    all_findings = []
    failed_searches = []

    for subquestion in subquestions:
        trace.append(
            f"[{_timestamp()}] Researcher: "
            f"searching — '{subquestion[:60]}'"
        )

        try:
            wiki_result = search_wikipedia(subquestion)

            if not wiki_result["found"]:
                trace.append(
                    f"[{_timestamp()}] Researcher: "
                    f"no Wikipedia result for '{subquestion[:40]}'"
                )
                failed_searches.append(subquestion)
                all_findings.append({
                    "subquestion": subquestion,
                    "summary": "",
                    "key_facts": [],
                    "source": "Wikipedia",
                    "url": "",
                    "confidence": 0.0
                })
                continue

            user_message = RESEARCHER_USER_TEMPLATE.format(
                subquestion=subquestion,
                title=wiki_result["title"],
                url=wiki_result["url"],
                content=wiki_result["content"]
            )

            raw_output = call_llm_json(
                RESEARCHER_SYSTEM_PROMPT,
                user_message,
                max_tokens=600
            )

            parsed = json.loads(raw_output)

            required = [
                "subquestion", "summary",
                "key_facts", "source", "confidence"
            ]
            for field in required:
                if field not in parsed:
                    raise ValueError(f"Missing field: {field}")

            all_findings.append(parsed)
            trace.append(
                f"[{_timestamp()}] Researcher: found content for "
                f"'{subquestion[:40]}' "
                f"(confidence: {parsed['confidence']})"
            )

        except json.JSONDecodeError as e:
            trace.append(
                f"[{_timestamp()}] Researcher: "
                f"JSON error for '{subquestion[:40]}' — {e}"
            )
            failed_searches.append(subquestion)

        except Exception as e:
            trace.append(
                f"[{_timestamp()}] Researcher: "
                f"error for '{subquestion[:40]}' — {e}"
            )
            failed_searches.append(subquestion)

    trace.append(
        f"[{_timestamp()}] Researcher: complete — "
        f"{len(all_findings)} findings, "
        f"{len(failed_searches)} failed"
    )

    return {
        **state,
        "findings": all_findings,
        "trace": trace,
        "error": None
    }


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")