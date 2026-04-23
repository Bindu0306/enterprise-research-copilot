from typing import Tuple


MAX_LENGTH = 300

BLOCKED_PHRASES = [
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "act as",
    "jailbreak",
    "system prompt",
    "forget everything",
    "disregard",
    "override",
]


def validate_input(topic: str) -> Tuple[bool, str]:
    # Check 1 — empty input
    if not topic or not topic.strip():
        return False, "Topic cannot be empty."

    # Check 2 — too long
    if len(topic.strip()) > MAX_LENGTH:
        return False, f"Topic too long. Maximum {MAX_LENGTH} characters allowed."

    # Check 3 — prompt injection detection
    topic_lower = topic.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in topic_lower:
            return False, "Input contains disallowed content. Please enter a valid research topic."

    # All checks passed
    clean_topic = topic.strip()
    return True, clean_topic