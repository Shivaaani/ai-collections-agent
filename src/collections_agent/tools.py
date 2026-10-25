"""Mock collections tools and the per-conversation session they act on.

Hard rules live here, not in the prompt: dues are only readable after identity
verification succeeds, promises to pay must fall within 7 days, and amounts can
never exceed what the borrower owes.
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .config import MAX_VERIFICATION_ATTEMPTS
from .ledger import Borrower

PTP_MAX_DAYS = 7

HANDOFF_REASONS = [
    "dispute",
    "hardship",
    "distress",
    "verification_failed",
    "settlement_or_waiver_request",
    "restructure_request",
    "callback_request",
    "borrower_requested_human",
    "other",
]


class ToolError(Exception):
    """A tool refused the call. The message is returned to the model as an error result."""


@dataclass
class Session:
    borrower: Borrower
    now: datetime  # timezone-aware, in the borrower's local time
    verified: bool = False
    failed_verifications: int = 0
    tool_log: list[dict] = field(default_factory=list)
    outcomes: list[dict] = field(default_factory=list)

    @property
    def today(self) -> date:
        return self.now.date()

    @property
    def verification_locked(self) -> bool:
        return self.failed_verifications >= MAX_VERIFICATION_ATTEMPTS


def _normalize_name(name: str) -> str:
    return " ".join(name.lower().split())


def _token(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:10]


def _require_verified(session: Session) -> None:
    if not session.verified:
        raise ToolError("Identity not verified. Call verify_identity first; do not disclose any loan details.")


def _parse_amount(session: Session, amount: int) -> int:
    if amount < 1 or amount > session.borrower.total_due:
        raise ToolError(f"Amount must be between 1 and the total due ({session.borrower.total_due}).")
    return amount


# --- Tool implementations ---------------------------------------------------


def verify_identity(session: Session, full_name: str, verifier_type: str, verifier_value: str) -> dict:
    if session.verified:
        return {"verified": True, "message": "Already verified."}
    if session.verification_locked:
        raise ToolError("Verification is locked after too many failed attempts. Escalate with create_handoff_ticket.")

    b = session.borrower
    name_ok = _normalize_name(full_name) == _normalize_name(b.name)
    if verifier_type == "date_of_birth":
        secret_ok = verifier_value.strip() == b.dob
    elif verifier_type == "loan_id_last4":
        digits = re.sub(r"\D", "", verifier_value)
        secret_ok = len(digits) >= 4 and digits[-4:] == b.loan_id[-4:]
    else:
        raise ToolError("verifier_type must be 'date_of_birth' or 'loan_id_last4'.")

    if name_ok and secret_ok:
        session.verified = True
        return {"verified": True}

    session.failed_verifications += 1
    remaining = MAX_VERIFICATION_ATTEMPTS - session.failed_verifications
    result = {"verified": False, "attempts_remaining": remaining}
    if remaining == 0:
        result["must_escalate"] = True
        result["message"] = "Verification failed. Do not disclose anything; escalate with reason verification_failed."
    return result


def get_dues(session: Session) -> dict:
    _require_verified(session)
    b = session.borrower
    return {
        "loan_id": b.loan_id,
        "emi_amount": b.emi_amount,
        "late_fee": b.late_fee,
        "total_due": b.total_due,
        "due_date": b.due_date(session.today).isoformat(),
        "days_past_due": b.days_past_due,
        "currency": "INR",
    }


def send_payment_link(session: Session, amount: int) -> dict:
    _require_verified(session)
    amount = _parse_amount(session, amount)
    link = f"https://pay.sahyog.example/l/{_token(session.borrower.borrower_id, amount, session.now)}"
    outcome = {"type": "pay_now", "amount": amount, "link": link}
    session.outcomes.append(outcome)
    return {"sent": True, "link": link, "amount": amount, "channel": "sms_and_chat", "expires_in_hours": 24}


def log_promise_to_pay(session: Session, promised_date: str, amount: int) -> dict:
    _require_verified(session)
    amount = _parse_amount(session, amount)
    try:
        when = date.fromisoformat(promised_date)
    except ValueError:
        raise ToolError("promised_date must be YYYY-MM-DD.") from None
    latest = session.today + timedelta(days=PTP_MAX_DAYS)
    if not session.today <= when <= latest:
        raise ToolError(
            f"Promise date must be between {session.today.isoformat()} and {latest.isoformat()}. "
            "For a later date, offer a callback via create_handoff_ticket (reason restructure_request)."
        )
    ptp_id = f"PTP-{_token(session.borrower.borrower_id, when, amount)}"
    outcome = {
        "type": "promise_to_pay",
        "ptp_id": ptp_id,
        "date": when.isoformat(),
        "amount": amount,
        "partial": amount < session.borrower.total_due,
    }
    session.outcomes.append(outcome)
    reminder = "on the morning of the promised date" if when == session.today else "the day before and on the day"
    return {
        "logged": True,
        "ptp_id": ptp_id,
        "date": when.isoformat(),
        "amount": amount,
        "sms_reminder": f"Sent automatically {reminder}, with a payment link.",
    }


def create_handoff_ticket(session: Session, reason: str, summary: str, priority: str) -> dict:
    """One ticket per conversation. The first reason is the primary tag; reasons from later calls become
    secondary tags, and their summaries are appended."""
    if reason not in HANDOFF_REASONS:
        raise ToolError(f"reason must be one of {HANDOFF_REASONS}.")
    if priority not in ("normal", "urgent"):
        raise ToolError("priority must be 'normal' or 'urgent'.")
    ticket = next((o for o in session.outcomes if o["type"] == "handoff"), None)
    if ticket is None:
        ticket = {
            "type": "handoff",
            "ticket_id": f"HT-{_token(session.borrower.borrower_id, reason, session.now)}",
            "primary_tag": reason,
            "secondary_tags": [],
            "priority": priority,
            "summary": summary,
        }
        session.outcomes.append(ticket)
        status = "created"
    else:
        if reason != ticket["primary_tag"] and reason not in ticket["secondary_tags"]:
            ticket["secondary_tags"].append(reason)
        if priority == "urgent":
            ticket["priority"] = "urgent"
        ticket["summary"] += f"\n[Update] {summary}"
        status = "updated_existing_ticket"
    eta = "within 2 hours" if ticket["priority"] == "urgent" else "within 1 business day"
    return {
        "status": status,
        "ticket_id": ticket["ticket_id"],
        "primary_tag": ticket["primary_tag"],
        "secondary_tags": ticket["secondary_tags"],
        "priority": ticket["priority"],
        "human_follow_up": eta,
    }


# --- Schemas sent to the model ----------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "verify_identity",
        "description": (
            "Check the person's identity against the loan record. Call this before sharing ANY loan detail, "
            "including whether a loan exists. Needs the full name plus either date of birth or the last 4 digits "
            "of the loan ID. Convert spoken dates to YYYY-MM-DD before calling."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "Full name as the person gave it."},
                "verifier_type": {"type": "string", "enum": ["date_of_birth", "loan_id_last4"]},
                "verifier_value": {
                    "type": "string",
                    "description": "Date of birth as YYYY-MM-DD, or the last 4 digits of the loan ID.",
                },
            },
            "required": ["full_name", "verifier_type", "verifier_value"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_dues",
        "description": "Get the overdue amount, late fee, due date and days past due. Works only after verification.",
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
    {
        "name": "send_payment_link",
        "description": "Send a secure payment link by SMS and in chat, when the borrower agrees to pay now.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "description": "Amount in rupees, at most the total due."},
            },
            "required": ["amount"],
            "additionalProperties": False,
        },
    },
    {
        "name": "log_promise_to_pay",
        "description": (
            "Record the borrower's commitment to pay a specific amount on a specific date, at most 7 days from today. "
            "Only log a date and amount the borrower actually agreed to."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "promised_date": {"type": "string", "description": "YYYY-MM-DD"},
                "amount": {"type": "integer", "description": "Amount in rupees, at most the total due."},
            },
            "required": ["promised_date", "amount"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_handoff_ticket",
        "description": (
            "Hand the conversation to a human collections officer. Use for disputes, hardship, distress, failed "
            "verification, settlement or waiver requests, restructure requests, callbacks, or when the borrower asks "
            "for a human. The summary is read by the officer: state the situation and what the borrower wants, "
            "without repeating phone numbers, PAN or full account numbers. A conversation has one ticket: the first "
            "call's reason is its primary tag, and calling again adds the new reason as a secondary tag and appends "
            "the summary. Raise the ticket for the customer's main issue first."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "enum": HANDOFF_REASONS},
                "summary": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["normal", "urgent"],
                    "description": "urgent for distress or any risk of self-harm; normal otherwise.",
                },
            },
            "required": ["reason", "summary", "priority"],
            "additionalProperties": False,
        },
    },
]

_IMPLEMENTATIONS = {
    "verify_identity": verify_identity,
    "get_dues": get_dues,
    "send_payment_link": send_payment_link,
    "log_promise_to_pay": log_promise_to_pay,
    "create_handoff_ticket": create_handoff_ticket,
}


def run_tool(session: Session, name: str, tool_input: dict) -> tuple[dict, bool]:
    """Run one tool call. Returns (result, is_error) and records it in the session's tool log."""
    fn = _IMPLEMENTATIONS.get(name)
    try:
        if fn is None:
            raise ToolError(f"Unknown tool: {name}")
        result, is_error = fn(session, **tool_input), False
    except ToolError as e:
        result, is_error = {"error": str(e)}, True
    except TypeError:
        result, is_error = {"error": f"Invalid arguments for {name}."}, True
    session.tool_log.append({"tool": name, "input": tool_input, "result": result, "is_error": is_error})
    return result, is_error
