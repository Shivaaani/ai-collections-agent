from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from collections_agent.ledger import Ledger
from collections_agent.tools import Session, run_tool


@pytest.fixture
def session():
    borrower = Ledger().get("B001")
    now = datetime(2026, 10, 26, 11, 0, tzinfo=ZoneInfo(borrower.timezone))
    return Session(borrower=borrower, now=now)


def verify(session, value=None, kind="date_of_birth", name=None):
    b = session.borrower
    return run_tool(
        session,
        "verify_identity",
        {"full_name": name or b.name, "verifier_type": kind, "verifier_value": value or b.dob},
    )


def test_ledger_has_20_borrowers_in_bucket():
    borrowers = Ledger().all()
    assert len(borrowers) == 20
    assert all(1 <= b.days_past_due <= 30 for b in borrowers)


def test_dues_blocked_before_verification(session):
    result, is_error = run_tool(session, "get_dues", {})
    assert is_error
    assert "total_due" not in result


def test_verify_with_dob_then_dues(session):
    result, is_error = verify(session)
    assert result == {"verified": True} and not is_error
    dues, is_error = run_tool(session, "get_dues", {})
    assert not is_error
    assert dues["total_due"] == session.borrower.total_due


def test_verify_with_loan_last4_is_case_and_space_insensitive(session):
    b = session.borrower
    result, _ = verify(session, value=b.loan_id[-4:], kind="loan_id_last4", name=f"  {b.name.upper()} ")
    assert result["verified"]


def test_two_failures_lock_verification(session):
    first, _ = verify(session, value="1900-01-01")
    assert first == {"verified": False, "attempts_remaining": 1}
    second, _ = verify(session, value="1900-01-02")
    assert second["must_escalate"]
    third, is_error = verify(session)  # even the right answer is refused now
    assert is_error and not session.verified


def test_payment_link_amount_capped(session):
    verify(session)
    _, is_error = run_tool(session, "send_payment_link", {"amount": session.borrower.total_due + 1})
    assert is_error
    result, is_error = run_tool(session, "send_payment_link", {"amount": session.borrower.total_due})
    assert not is_error and result["link"].startswith("https://pay.sahyog.example/")
    assert session.outcomes[-1]["type"] == "pay_now"


def test_ptp_window(session):
    verify(session)
    amount = session.borrower.total_due
    too_late = (session.today + timedelta(days=8)).isoformat()
    _, is_error = run_tool(session, "log_promise_to_pay", {"promised_date": too_late, "amount": amount})
    assert is_error
    ok = (session.today + timedelta(days=7)).isoformat()
    result, is_error = run_tool(session, "log_promise_to_pay", {"promised_date": ok, "amount": amount})
    assert not is_error and result["logged"]


def test_handoff_allowed_without_verification(session):
    result, is_error = run_tool(
        session, "create_handoff_ticket", {"reason": "dispute", "summary": "Says loan is not theirs.", "priority": "normal"}
    )
    assert not is_error and result["ticket_id"].startswith("HT-")


def test_every_call_is_logged(session):
    run_tool(session, "get_dues", {})
    verify(session)
    assert [e["tool"] for e in session.tool_log] == ["get_dues", "verify_identity"]
