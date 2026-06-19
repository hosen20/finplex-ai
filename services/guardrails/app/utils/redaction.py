import re

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d .()/-]{7,}\d)(?!\d)")
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_pii(text: str) -> str:
    """Redacts common PII patterns before returning guardrail output."""

    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    redacted = SSN_PATTERN.sub("[REDACTED_ID]", redacted)
    redacted = CARD_PATTERN.sub("[REDACTED_CARD]", redacted)
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)


def contains_sensitive_identifier(text: str) -> bool:
    """Returns true if the draft exposes sensitive identifiers."""

    return bool(CARD_PATTERN.search(text) or SSN_PATTERN.search(text))