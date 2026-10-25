"""Chat with the agent in the terminal, playing the borrower.

    python -m collections_agent --borrower B001
    python -m collections_agent --borrower B020 --time 2026-10-26T10:30
"""

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .agent import CollectionsAgent
from .guardrails import OutsideContactHours, check_contact_hours
from .ledger import Ledger
from .tools import Session

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--borrower", default="B001", help="Borrower ID, B001-B020")
    parser.add_argument("--time", help="Borrower-local time to simulate, YYYY-MM-DDTHH:MM (default: now)")
    parser.add_argument("--borrower-requested", action="store_true", help="Borrower asked to be contacted now")
    args = parser.parse_args()

    borrower = Ledger().get(args.borrower)
    tz = ZoneInfo(borrower.timezone)
    now = datetime.fromisoformat(args.time).replace(tzinfo=tz) if args.time else datetime.now(tz)
    try:
        check_contact_hours(now, args.borrower_requested)
    except OutsideContactHours as e:
        raise SystemExit(f"Not starting: {e}")

    agent = CollectionsAgent(Session(borrower=borrower, now=now))
    print(f"Chatting as {borrower.name} ({borrower.borrower_id}). Your DOB is {borrower.dob}, "
          f"loan ID ends {borrower.loan_id[-4:]}. Type /quit to end.\n")
    print(f"Agent: {agent.start()}\n")
    try:
        while (text := input("You: ").strip()) != "/quit":
            if text:
                print(f"\nAgent: {agent.reply(text)}\n")
    except (EOFError, KeyboardInterrupt):
        print()
    print(f"Outcomes: {agent.session.outcomes or 'none'}")
    print(f"Saved redacted transcript to {agent.save(LOG_DIR)}")


if __name__ == "__main__":
    main()
