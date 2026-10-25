"""A second model plays the borrower from a persona brief."""

import anthropic

from collections_agent.config import SIMULATOR_MODEL
from collections_agent.tools import Session

END = "[END]"

SIM_SYSTEM = """\
You are role-playing a person receiving WhatsApp messages from Sahyog Finance's collections chatbot. \
This is a test of the chatbot; play your character realistically and never mention that this is a test \
or a simulation.

## Your character
{brief}

## What you know
{facts}

## How to write
- Write only your next chat message: 1-3 short sentences, like a real person on WhatsApp.
- Reveal things gradually and in your own words; don't dump everything at once.
- Stick to your character's goals even if the chatbot pushes back, but react naturally to what it says.
- When the conversation has reached its natural end (you've agreed on something and said goodbye, or \
you'd simply stop replying), reply with exactly {end}
"""


def _facts(session: Session, is_borrower: bool) -> str:
    b = session.borrower
    if not is_borrower:
        return (
            f"The chatbot is looking for {b.name}. You are NOT that person and do not know their date of birth "
            "or loan ID."
        )
    return (
        f"You are {b.name} from {b.city}. Date of birth: {b.dob}. Loan ID: {b.loan_id} "
        f"(last 4 digits {b.loan_id[-4:]}). Your monthly EMI is about Rs {b.emi_amount:,}, and it is "
        f"{b.days_past_due} days late. Today is {session.now:%A, %d %B %Y}."
    )


class BorrowerSimulator:
    def __init__(self, client: anthropic.Anthropic, persona: dict, session: Session, model: str = SIMULATOR_MODEL):
        self.client = client
        self.model = model
        self.system = SIM_SYSTEM.format(
            brief=persona["brief"], facts=_facts(session, persona["is_borrower"]), end=END
        )
        self.messages: list[dict] = []  # the agent is "user" here; the simulated borrower is "assistant"
        self.usage: list = []

    def respond(self, agent_text: str) -> str:
        self.messages.append({"role": "user", "content": agent_text})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=self.system,
            messages=self.messages,
            output_config={"effort": "low"},
        )
        self.usage.append(response.usage)
        if response.stop_reason == "refusal":
            return END
        self.messages.append({"role": "assistant", "content": response.content})
        return "".join(b.text for b in response.content if b.type == "text").strip()
