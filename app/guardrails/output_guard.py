# app/guardrails/output_guard.py

import re
from typing import Tuple


# Phrases that should never appear in final output
DANGEROUS_PHRASES = [
    "ignore previous instructions",
    "system prompt",
    "jailbreak",
    "as an ai language model",
    "i cannot and will not",
    "i am not able to",
]

# Minimum acceptable report length
MIN_REPORT_LENGTH = 200

# Maximum acceptable report length
MAX_REPORT_LENGTH = 10000


def validate_output(report: str) -> Tuple[bool, str]:
    """
    Validate the final report before showing to user.
    Returns (is_valid, report_or_error_message).
    """

    # Check 1 — empty report
    if not report or not report.strip():
        return False, "Report is empty."

    # Check 2 — too short
    if len(report.strip()) < MIN_REPORT_LENGTH:
        return False, "Report is too short to be valid."

    # Check 3 — too long
    if len(report.strip()) > MAX_REPORT_LENGTH:
        report = report[:MAX_REPORT_LENGTH] + "\n\n*Report truncated.*"

    # Check 4 — dangerous phrases
    report_lower = report.lower()
    for phrase in DANGEROUS_PHRASES:
        if phrase in report_lower:
            report = report.replace(phrase, "[removed]")

    # Check 5 — must have minimum structure
    if "##" not in report:
        return False, "Report is missing required sections."

    return True, report.strip()