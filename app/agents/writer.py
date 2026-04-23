from datetime import datetime
from dotenv import load_dotenv
from app.models.state import ResearchState
from app.prompts.writer_prompt import (
    WRITER_SYSTEM_PROMPT,
    WRITER_USER_TEMPLATE
)
from app.tools.llm_client import call_llm

load_dotenv()


def run_writer(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    subquestions = state["subquestions"]
    findings = state["findings"]
    critic_feedback = state["critic_feedback"]
    confidence_score = state["confidence_score"]
    retry_count = state["retry_count"]
    trace = state["trace"]

    trace.append(
        f"[{_timestamp()}] Writer: starting — "
        f"generating report for topic: '{topic[:50]}'"
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
            findings_text += f"  URL: {finding.get('url', 'No source available')}\n"
            findings_text += f"  Confidence: {finding.get('confidence', 0)}\n"

        if critic_feedback:
            feedback_text = "\n".join(
                f"- {item}" for item in critic_feedback
            )
        else:
            feedback_text = "No issues flagged — research quality approved"

        retry_triggered = "Yes" if retry_count > 0 else "No"
        timestamp = _timestamp()

        user_message = WRITER_USER_TEMPLATE.format(
            topic=topic,
            subquestions=subquestions_text,
            findings=findings_text,
            confidence_score=f"{confidence_score:.0%}",
            critic_feedback=feedback_text,
            retry_triggered=retry_triggered,
            timestamp=timestamp
        )

        raw_report = call_llm(
            WRITER_SYSTEM_PROMPT,
            user_message,
            max_tokens=1500
        )

        if not raw_report or not raw_report.strip():
            raise ValueError("Writer returned empty report")

        if len(raw_report.strip()) < 200:
            raise ValueError(
                f"Report too short: {len(raw_report)} characters"
            )

        trace.append(
            f"[{_timestamp()}] Writer: report generated — "
            f"{len(raw_report)} characters"
        )

        return {
            **state,
            "final_report": raw_report,
            "trace": trace,
            "error": None
        }

    except ValueError as e:
        error_msg = f"Writer failed: {e}"
        trace.append(f"[{_timestamp()}] Writer: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}

    except Exception as e:
        error_msg = f"Writer unexpected error: {e}"
        trace.append(f"[{_timestamp()}] Writer: ERROR — {error_msg}")
        return {**state, "error": error_msg, "trace": trace}


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")