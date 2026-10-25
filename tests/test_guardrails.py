from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from collections_agent.guardrails import OutsideContactHours, check_contact_hours, check_outbound, redact
from collections_agent.ledger import Ledger

IST = ZoneInfo("Asia/Kolkata")


@pytest.mark.parametrize("hour, allowed", [(7, False), (8, True), (18, True), (19, False), (22, False)])
def test_contact_hours(hour, allowed):
    now = datetime(2026, 10, 26, hour, 30, tzinfo=IST)
    if allowed:
        check_contact_hours(now)
    else:
        with pytest.raises(OutsideContactHours):
            check_contact_hours(now)


def test_borrower_requested_time_overrides_window():
    check_contact_hours(datetime(2026, 10, 26, 21, 0, tzinfo=IST), borrower_requested=True)


def test_redaction():
    b = Ledger().get("B001")
    text = f"Call +91 9876543210 or 9876543210, PAN {b.pan}, loan {b.loan_id}, born {b.dob}."
    out = redact(text, b)
    assert "9876543210" not in out and b.pan not in out and b.dob not in out
    assert b.loan_id not in out and b.loan_id[-4:] in out


@pytest.mark.parametrize(
    "text, category",
    [
        ("If you don't pay we will take legal action.", "legal_threat"),
        ("We may have to inform your employer about this.", "third_party_contact"),
        ("We will call your references today.", "third_party_contact"),
        ("Our agents will visit your home tomorrow.", "home_visit"),
        ("This is irresponsible behaviour.", "shaming"),
        ("Not paying will ruin your CIBIL score.", "credit_threat"),
    ],
)
def test_outbound_filter_blocks(text, category):
    assert category in check_outbound(text)


@pytest.mark.parametrize(
    "text",
    [
        "I'm Sahyog Finance's automated assistant, and this chat is recorded. Am I speaking with Aarav?",
        "I'm so sorry to hear about the loss in your family. I'll ask an officer to call you back.",
        "Your overdue amount is Rs 7,376, due on 2 October. What got in the way of the payment?",
        "I've sent a payment link for Rs 7,376 by SMS. It is valid for 24 hours.",
        "A Sahyog officer will call you within 1 business day, and your reference number is HT-6c8496f4fc.",
    ],
)
def test_outbound_filter_allows_normal_messages(text):
    assert check_outbound(text) == []
