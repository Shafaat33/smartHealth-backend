import re

EMERGENCY_PATTERNS = re.compile(
    r"\b("
    r"chest pain|heart attack|can't breathe|cannot breathe|trouble breathing|"
    r"severe bleeding|uncontrolled bleeding|"
    r"sudden weakness|facial droop|stroke|"
    r"suicid|kill myself|self[- ]harm|"
    r"overdose|unconscious|seizure"
    r")\b",
    re.IGNORECASE,
)

EMERGENCY_REPLY = (
    "This sounds like it could be an emergency. Do not wait for a routine appointment. "
    "Call your local emergency number or go to the nearest emergency department now."
)


def is_emergency(question: str) -> bool:
    return bool(EMERGENCY_PATTERNS.search(question))
