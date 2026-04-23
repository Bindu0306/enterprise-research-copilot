from typing import TypedDict, Optional


class ResearchState(TypedDict):
    topic:            str
    subquestions:     list[str]
    findings:         list[dict]
    critic_feedback:  list[str]
    confidence_score: float
    retry_count:      int
    final_report:     str
    trace:            list[str]
    error:            Optional[str]