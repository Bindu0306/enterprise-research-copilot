import json
from datetime import datetime
from dotenv import load_dotenv
from app.models.state import ResearchState
from app.prompts.critic_prompt import (
    CRITIC_SYSTEM_PROMPT,
    CRITIC_USER_TEMPLATE
)
from app.tools.llm_client import call_llm_json

load_dotenv()


def run_critic(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    subquestions = state["subquestions"]
    findings = state["findings"]
    trace = state["trace"]

    trace.append(
        f"[{_timestamp()}] Critic: starting evaluation of "
        f"{len(findings)} findings"
    )

    try:
        subquestions_text = "\n".join(
            f"{i+1}. {q}"
            for i, q in enumerate(subquestions)
        )

        findings_text = ""
        for i, finding in enumerate(findings):
            findings_text += f"\nFinding {i+1}:\n"
            findings_text += f"  Sub-question: {finding.get('subquestion', '')}\n"
            findings_text += f"  Summary: {finding.get('summary', '')}\n"
            findings_text += f"  Key Facts: {finding.get('key_facts', [])}\n"
            findings_text += f"  Confidence: {finding.get('confidence', 0)}\n"
            findings_text += f"  URL: {finding.get('url', '')}\n"

        user_message = CRITIC_USER_TEMPLATE.format(
            topic=topic,
            subquestions=subquestions_text,
            findings=findings_text
        )

        raw_output = call_llm_json(
            CRITIC_SYSTEM_PROMPT,
            user_message,
            max_tokens=800
        )

        parsed = json.loads(raw_output)

        required = [
            "approved", "confidence_score",
            "feedback", "coverage_check"
        ]
        for field in required:
            if field not in parsed:
                raise ValueError(
                    f"Missing field in Critic output: {field}"
                )

        confidence = parsed["confidence_score"]
        feedback = parsed["feedback"]
        approved = parsed["approved"]

        trace.append(
            f"[{_timestamp()}] Critic: evaluation complete — "
            f"confidence={confidence} "
            f"approved={approved} "
            f"issues={len(feedback)}"
        )

        if feedback:
            for item in feedback:
                trace.append(
                    f"[{_timestamp()}] Critic flagged: {item}"
                )

        return {
            **state,
            "critic_feedback": feedback,
            "confidence_score": confidence,
            "trace": trace,
            "error": None
        }

    except json.JSONDecodeError as e:
        error_msg = f"Critic failed: invalid JSON — {e}"
        trace.append(f"[{_timestamp()}] Critic: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}

    except ValueError as e:
        error_msg = f"Critic failed: {e}"
        trace.append(f"[{_timestamp()}] Critic: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}

    except Exception as e:
        error_msg = f"Critic unexpected error: {e}"
        trace.append(f"[{_timestamp()}] Critic: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")