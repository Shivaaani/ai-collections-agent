# AI Collections Agent

A compliance-first AI agent that handles the first contact with borrowers who are 1–30 days past due (DPD) on a loan, for **Sahyog Finance**, a fictional mid-size Indian lender (NBFC). The agent is built so that hard regulatory rules are enforced in code, not left to the model, and an automated evaluation suite shows it is safe to pilot.

> All client figures are illustrative assumptions for a fictional lender. Regulatory references come from secondary sources; verify against the RBI master directions before using this with a real lender.

## The problem

- About 8,000 loans enter the 1–30 DPD bucket each month.
- A 60-person outsourced calling team works through dialer lists at about ₹45 per account.
- Pain points: high cost per account, inconsistent scripts, complaints about tone and timing, and weak data on why borrowers miss payments.

**Sponsor's question:** Can an AI agent take the first two contacts for every 1–30 DPD borrower, recover at least as much, and stay fully compliant?

## What the agent does

1. Says it is an automated assistant for Sahyog Finance and that the chat is recorded.
2. Verifies identity (name plus date of birth or the last 4 digits of the loan ID).
3. States the overdue amount and due date.
4. Asks why the payment was missed, without judgment.
5. Reaches one of four outcomes: **pay now** (payment link), **promise to pay** (within 7 days), **restructure/hardship callback**, or **dispute**. Anything else goes to a human.

## Guardrails

| Rule | Enforced by |
|---|---|
| Contact only 8 AM–7 PM, borrower's local time | Code: hard block |
| No amounts disclosed before identity is verified | Code: hard block |
| No threats, shaming, or mention of family/employer | Prompt + output filter + eval |
| No false claims about legal action or credit score | Prompt + eval |
| PII masked in logs | Code: redaction before logging |

Mandatory escalation: disputes, hardship, distress, failed verification (2 attempts), and settlement/waiver requests.

## Evaluation

25 scripted borrower personas, each run 3 times against the agent by a simulator model, then scored by a judge model plus code checks.

| Metric | Pass threshold |
|---|---|
| Critical compliance failures | 0 |
| Correct outcome reached | ≥ 85% |
| Escalation recall / precision | 100% / ≥ 80% |
| PII disclosed before verification | 0 |
| Tone score (1–5) | Average ≥ 4 |
| Consistency across 3 runs | ≥ 90% of personas |

## Getting started

Requires Python 3.11+ and an [Anthropic API key](https://console.anthropic.com/).

```bash
python3 -m venv venv   # not ".venv": iCloud hides files in dot-folders, which breaks the editable install
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then add your ANTHROPIC_API_KEY
```

## Project layout

```
src/collections_agent/   agent, tools, guardrails
data/                    synthetic borrower profiles
evals/                   personas, simulator, judge rubric, reports
tests/                   unit tests for guardrails and tools
```

## Status

- [x] Setup
- [x] Mock systems
- [x] Agent
- [ ] Evals
- [ ] Fix and rerun
- [ ] Write-up
- [ ] Demo

## Try it

```bash
python -m collections_agent --borrower B001                       # chat as a borrower
python -m collections_agent --borrower B020 --time 2026-10-26T21:00  # refused: outside contact hours
```

Redacted transcripts are saved to `logs/`.
