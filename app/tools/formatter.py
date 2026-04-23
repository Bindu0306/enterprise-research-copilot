# app/tools/formatter.py

import re
from datetime import datetime


def format_report(raw_report: str) -> str:
    """
    Clean and format the Writer's Markdown report
    before displaying to the user.
    """
    if not raw_report or not raw_report.strip():
        return _empty_report()

    report = raw_report.strip()

    # Remove any JSON that accidentally slipped through
    report = _remove_json_blocks(report)

    # Remove any system-level text
    report = _remove_system_text(report)

    # Clean up extra blank lines
    report = _clean_whitespace(report)

    return report


def format_trace(trace: list) -> list:
    """
    Format the agent trace list for display in UI.
    Returns cleaned list of trace strings.
    """
    if not trace:
        return ["No trace available"]

    cleaned = []
    for entry in trace:
        if entry and entry.strip():
            cleaned.append(entry.strip())

    return cleaned


def _remove_json_blocks(text: str) -> str:
    """Remove any JSON code blocks that slipped into report."""
    # Remove ```json ... ``` blocks
    text = re.sub(
        r'```json.*?```',
        '',
        text,
        flags=re.DOTALL
    )
    # Remove ``` ... ``` blocks
    text = re.sub(
        r'```.*?```',
        '',
        text,
        flags=re.DOTALL
    )
    return text


def _remove_system_text(text: str) -> str:
    """Remove any system-level phrases from report."""
    SYSTEM_PHRASES = [
        "As an AI language model",
        "As an AI assistant",
        "I cannot",
        "I am unable",
        "I don't have access",
    ]
    for phrase in SYSTEM_PHRASES:
        text = text.replace(phrase, "")
    return text


def _clean_whitespace(text: str) -> str:
    """Replace 3 or more blank lines with 2 blank lines."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _empty_report() -> str:
    """Return a fallback report if Writer produced nothing."""
    return f"""# Research Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Notice
The report could not be generated at this time.
Please try again with a different research topic.

*Enterprise Research Copilot*
"""