"""Code-level guardrails: contact hours, PII redaction, and the outbound message filter.

These run outside the model so a model mistake cannot break a hard rule.
"""

import re
from datetime import datetime

from .config import CONTACT_HOURS_END, CONTACT_HOURS_START
from .ledger import Borrower


class OutsideContactHours(Exception):
    pass


def check_contact_hours(now: datetime, borrower_requested: bool = False) -> None:
    """Refuse to open a session outside 8 AM-7 PM borrower-local time, unless the borrower asked for it."""
    if borrower_requested:
        return
    if not CONTACT_HOURS_START <= now.hour < CONTACT_HOURS_END:
        raise OutsideContactHours(
            f"{now:%H:%M} is outside the {CONTACT_HOURS_START}:00-{CONTACT_HOURS_END}:00 contact window "
            "in the borrower's local time."
        )


# --- PII redaction ----------------------------------------------------------

_PII_PATTERNS = [
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b"), "[PHONE]"),
    (re.compile(r"\bSFL-PL-\d{2}(\d{4})\b"), r"SFL-PL-XX\1"),
]


def redact(text: str, borrower: Borrower | None = None) -> str:
    """Mask phone numbers, PAN, full loan IDs and (when known) the borrower's date of birth."""
    for pattern, repl in _PII_PATTERNS:
        text = pattern.sub(repl, text)
    if borrower is not None:
        text = text.replace(borrower.dob, "[DOB]")
    return text


def redact_obj(obj, borrower: Borrower | None = None):
    """Redact every string inside a JSON-like structure."""
    if isinstance(obj, str):
        return redact(obj, borrower)
    if isinstance(obj, list):
        return [redact_obj(v, borrower) for v in obj]
    if isinstance(obj, dict):
        return {k: redact_obj(v, borrower) for k, v in obj.items()}
    return obj


# --- Outbound message filter ------------------------------------------------

_BANNED = {
    "legal_threat": re.compile(
        r"\b(police|jail|arrest(ed)?|FIR|criminal|legal action|court|lawsuit|sue|summons|warrant)\b", re.I
    ),
    "third_party_contact": re.compile(
        r"\b(contact|call|inform|tell|notify|visit|reach out to|message)\b[^.?!]{0,40}"
        r"\b(family|relatives|parents|spouse|employer|boss|office|workplace|colleagues|neighbou?rs|friends|references?)\b",
        re.I,
    ),
    "home_visit": re.compile(r"\b(agents?|someone|team)\b[^.?!]{0,30}\b(visit|come to|come over)\b", re.I),
    "shaming": re.compile(r"\b(shame(ful)?|irresponsible|cheat(er|ing)?|fraud(ster)?|defaulter|liar|useless)\b", re.I),
    "credit_threat": re.compile(
        r"\b(ruin|destroy|damage|blacklist(ed)?)\b[^.?!]{0,30}\b(credit|CIBIL|score)\b"
        r"|\b(credit|CIBIL)( score)?\b[^.?!]{0,30}\b(ruin|destroy|blacklist)",
        re.I,
    ),
}


def check_outbound(text: str) -> list[str]:
    """Return the banned-language categories found in an agent message (empty list means it may be sent)."""
    return [name for name, pattern in _BANNED.items() if pattern.search(text)]
