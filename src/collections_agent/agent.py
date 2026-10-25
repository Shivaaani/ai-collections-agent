"""The collections agent: a manual tool-use loop with code-level guardrails around every turn."""

import json
from datetime import datetime
from pathlib import Path

import anthropic

from .config import AGENT_EFFORT, AGENT_MODEL
from .guardrails import check_outbound, redact_obj
from .prompts import SYSTEM_PROMPT, session_context
from .tools import TOOL_SCHEMAS, Session, run_tool

MAX_TOOL_STEPS = 8
OPENING_NOTE = "[Chat opened by Sahyog Finance. The customer has not written yet. Send your opening message.]"
SAFE_FALLBACK = (
    "Sorry, I'm unable to help with that here. A Sahyog Finance officer can assist you; "
    "would you like me to arrange a callback?"
)


class CollectionsAgent:
    def __init__(
        self,
        session: Session,
        client: anthropic.Anthropic | None = None,
        model: str = AGENT_MODEL,
        effort: str = AGENT_EFFORT,
    ):
        self.session = session
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.messages: list[dict] = []
        self.transcript: list[dict] = []  # what each side actually saw
        self.guardrail_events: list[dict] = []
        self.usage: list = []  # one usage object per API call, for cost reporting
        self._system = [
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": session_context(session)},
        ]

    def start(self) -> str:
        self.messages.append({"role": "user", "content": OPENING_NOTE})
        return self._run_turn()

    def reply(self, borrower_text: str) -> str:
        self.transcript.append({"role": "borrower", "text": borrower_text})
        self.messages.append({"role": "user", "content": borrower_text})
        return self._run_turn()

    def _call(self):
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=self._system,
            tools=TOOL_SCHEMAS,
            messages=self.messages,
            output_config={"effort": self.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

    def _run_turn(self) -> str:
        rewrite_requested = False
        for _ in range(MAX_TOOL_STEPS):
            response = self._call()
            self.usage.append(response.usage)

            if response.stop_reason == "refusal":
                self.guardrail_events.append({"type": "model_refusal"})
                return self._send(SAFE_FALLBACK)
            if response.stop_reason == "max_tokens":
                raise RuntimeError("Agent response hit max_tokens.")

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result, is_error = run_tool(self.session, block.name, block.input)
                        results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result),
                                "is_error": is_error,
                            }
                        )
                self.messages.append({"role": "user", "content": results})
                continue

            text = "".join(b.text for b in response.content if b.type == "text").strip()
            violations = check_outbound(text)
            if not violations and text:
                return self._send(text, already_in_history=True)

            # Blocked or empty draft: drop it, ask for one rewrite, then fall back to a safe line.
            self.messages.pop()
            self.guardrail_events.append({"type": "blocked_draft", "categories": violations, "draft": text})
            if rewrite_requested:
                return self._send(SAFE_FALLBACK)
            rewrite_requested = True
            self.messages.append(
                {
                    "role": "system",
                    "content": (
                        "Your draft reply was blocked by the compliance filter"
                        + (f" ({', '.join(violations)})" if violations else " (empty reply)")
                        + ". Write a new reply to the customer that avoids threats, legal or police references, "
                        "mentions of contacting anyone else, shaming words, and credit-score claims."
                    ),
                }
            )
        raise RuntimeError("Agent exceeded the tool-step limit for one turn.")

    def _send(self, text: str, already_in_history: bool = False) -> str:
        if not already_in_history:
            self.messages.append({"role": "assistant", "content": text})
        self.transcript.append({"role": "agent", "text": text, "verified": self.session.verified})
        return text

    def record(self) -> dict:
        """A redacted record of the conversation, safe to store."""
        s = self.session
        return redact_obj(
            {
                "borrower_id": s.borrower.borrower_id,
                "started_at": s.now.isoformat(),
                "model": self.model,
                "transcript": self.transcript,
                "tool_log": s.tool_log,
                "outcomes": s.outcomes,
                "guardrail_events": self.guardrail_events,
            },
            s.borrower,
        )

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.session.borrower.borrower_id}-{datetime.now():%Y%m%d-%H%M%S}.json"
        path.write_text(json.dumps(self.record(), indent=2, ensure_ascii=False) + "\n")
        return path
