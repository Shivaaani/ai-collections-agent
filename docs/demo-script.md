# Demo script (2–3 minutes)

Record the terminal and the README side by side. The agent's replies vary a little each time, so the borrower lines below are what you type, and the notes say what to point out in the agent's reply.

## Before recording

```bash
cd ai-collections-agent && source venv/bin/activate
export MODEL_BACKEND=claude-cli   # uses your Claude subscription; drop this line if you have API credits
```

`--time` fixes the clock at 11 AM, so the contact-hours check passes whenever you record. Do one dry run of each chat first. Each one uses roughly 40–60k tokens.

---

## 0:00–0:20 · The problem

> "Sahyog Finance, a fictional Indian lender, has 8,000 loans a month falling 1 to 30 days overdue. A 60-person calling team chases them at ₹45 an account, with inconsistent scripts and tone complaints. The question: can an AI agent take the first contact, recover as much, and stay fully compliant with RBI rules?"

## 0:20–1:05 · Happy path: forgot to pay

```bash
python -m collections_agent --borrower B001 --time 2026-10-26T11:00
```

| You type | Point out |
|---|---|
| `Yes, this is Aarav` | It discloses that it's automated and the chat is recorded, and says nothing about a loan yet. |
| `Aarav Sharma, 1983-04-08` | Verified. Only now does it state ₹7,376 (EMI ₹6,876 plus the ₹500 late fee). |
| `Sorry, I totally forgot. I can pay right now` | It sends a payment link for the exact amount. The amounts come from tools, not the model. |
| `/quit` | Outcomes: `pay_now`. The transcript is saved with PII redacted. |

## 1:05–1:50 · Hardship, in Hinglish

```bash
python -m collections_agent --borrower B013 --time 2026-10-26T11:00
```

| You type | Point out |
|---|---|
| `haan main Karan hoon` | It switches to Hinglish. |
| `Karan Malhotra, 1999-03-18` | Verified, dues stated. |
| `dekho meri job chali gayi last month, abhi kuch nahi hai paas mein` | It acknowledges the job loss with care, opens a hardship ticket, and makes **no payment ask**. |
| `pata nahi kab tak hoga, bahut tension hai` | It shares Tele-MANAS 14416, and the same ticket becomes **urgent** with a `distress` secondary tag. |
| `/quit` | One ticket: primary tag `hardship`, secondary tag `distress`. |

## 1:50–2:05 · A hard rule in code

```bash
python -m collections_agent --borrower B020 --time 2026-10-26T21:00
```

> "Ritu lives in Dubai. It's 9 PM her time, so the session never starts. That's the RBI contact-hours rule, enforced in code, before the model is even called."

## 2:05–2:45 · How it was tested

Show the README's **"What the evals found, and what changed"** table.

> "25 simulated borrowers, from cooperative to hostile, play against the agent, and a judge model scores every conversation. Four runs, and each found something. The most important finding: the agent's worst failure, a canned reply to a self-harm hint, came from my own safety filter, not the model. It read a ticket *reference* number as a threat to call the borrower's *references*. I fixed it and turned every draft the filter had ever blocked into a regression test. Another run surfaced a policy question, whether a delayed salary counts as hardship, which I decided as a product call and wrote into both the agent and the judge."

Point at: **0 loan details shared before verification across 66 conversations**, and 100% escalation recall.

## 2:45–3:00 · The value

Show the README's **"Value case"** table.

> "On these assumptions, cost per account drops from ₹45 to ₹28, saving about ₹16 lakh a year, with payback in about 7 months, before counting any recovery uplift. Next step: one full evaluation run on the final code, then a 6-week pilot."
