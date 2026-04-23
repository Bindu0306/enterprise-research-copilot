from app.models.state import ResearchState

MAX_RETRIES = 1
MIN_CONFIDENCE = 0.65
MAX_FEEDBACK_ITEMS = 2


def should_retry(state: ResearchState) -> bool:
    # Safety rule — never retry more than once
    if state["retry_count"] >= MAX_RETRIES:
        return False

    # Check 1 — any sub-question has zero findings
    subquestions = state["subquestions"]
    findings = state["findings"]

    answered = set()
    for finding in findings:
        answered.add(finding["subquestion"])

    for question in subquestions:
        if question not in answered:
            return True

    # Check 2 — confidence score too low
    if state["confidence_score"] < MIN_CONFIDENCE:
        return True

    # Check 3 — too many critic feedback items
    if len(state["critic_feedback"]) > MAX_FEEDBACK_ITEMS:
        return True

    return False