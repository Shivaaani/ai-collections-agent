"""Mock loan ledger backed by data/borrowers.json."""

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "borrowers.json"


@dataclass(frozen=True)
class Borrower:
    borrower_id: str
    name: str
    dob: str
    phone: str
    pan: str
    loan_id: str
    city: str
    timezone: str
    preferred_language: str
    loan_amount: int
    tenure_months: int
    emi_amount: int
    days_past_due: int
    late_fee: int
    broken_promises_last_6m: int
    restructure_eligible: bool

    @property
    def total_due(self) -> int:
        return self.emi_amount + self.late_fee

    def due_date(self, today: date) -> date:
        return today - timedelta(days=self.days_past_due)


class Ledger:
    def __init__(self, path: Path = DATA_FILE):
        records = json.loads(path.read_text())
        self._by_id = {r["borrower_id"]: Borrower(**r) for r in records}

    def get(self, borrower_id: str) -> Borrower:
        return self._by_id[borrower_id]

    def all(self) -> list[Borrower]:
        return list(self._by_id.values())
