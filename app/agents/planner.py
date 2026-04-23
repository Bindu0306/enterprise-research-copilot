import json
from datetime import datetime
from dotenv import load_dotenv
from app.models.state import ResearchState
from app.prompts.planner_prompt import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_TEMPLATE
)
from app.tools.llm_client import call_llm_json

load_dotenv()


def run_planner(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    trace = state["trace"]

    trace.append(
        f"[{_timestamp()}] Planner: starting for topic: '{topic[:50]}'"
    )

    try:
        user_message = PLANNER_USER_TEMPLATE.format(topic=topic)
        raw_output = call_llm_json(
            PLANNER_SYSTEM_PROMPT,
            user_message,
            max_tokens=500
        )
        parsed = json.loads(raw_output)

        if "subquestions" not in parsed or "outline" not in parsed:
            raise ValueError("Missing required fields in Planner output")

        if len(parsed["subquestions"]) != 3:
            raise ValueError(
                f"Expected 3 subquestions, got {len(parsed['subquestions'])}"
            )

        trace.append(
            f"[{_timestamp()}] Planner: created {len(parsed['subquestions'])} sub-questions ✓"
        )

        return {
            **state,
            "subquestions": parsed["subquestions"],
            "trace": trace,
            "error": None
        }

    except json.JSONDecodeError as e:
        error_msg = f"Planner failed: invalid JSON — {e}"
        trace.append(f"[{_timestamp()}] Planner: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}

    except ValueError as e:
        error_msg = f"Planner failed: {e}"
        trace.append(f"[{_timestamp()}] Planner: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}

    except Exception as e:
        error_msg = f"Planner unexpected error: {e}"
        trace.append(f"[{_timestamp()}] Planner: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")