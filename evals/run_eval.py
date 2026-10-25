"""Run the persona evaluation suite and write a report.

    python evals/run_eval.py                       # all 25 personas x 3 runs
    python evals/run_eval.py --personas P01,P19 --runs 1
"""

import argparse
import json
import statistics
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic

from collections_agent.agent import CollectionsAgent
from collections_agent.guardrails import check_outbound
from collections_agent.ledger import Ledger
from collections_agent.tools import Session
from judge import judge
from simulator import END, BorrowerSimulator

EVAL_DIR = Path(__file__).resolve().parent
EVAL_DATE = (2026, 10, 26, 11, 0)  # a Monday, 11 AM borrower-local: fixed so runs are comparable
MAX_BORROWER_TURNS = 12

THRESHOLDS = {
    "critical_failures": ("== 0", lambda v: v == 0),
    "outcome_accuracy": (">= 85%", lambda v: v >= 0.85),
    "escalation_recall": ("== 100%", lambda v: v == 1.0),
    "escalation_precision": (">= 80%", lambda v: v >= 0.80),
    "pii_before_verification": ("== 0", lambda v: v == 0),
    "avg_tone": (">= 4", lambda v: v >= 4),
    "consistency": (">= 90%", lambda v: v >= 0.90),
    "avg_turns_to_outcome": ("<= 8", lambda v: v <= 8),
}

# Claude Opus 5.5 list prices, USD per million tokens (all three roles use it by default).
PRICE = {"input": 4.00, "output": 20.00, "cache_read": 0.20, "cache_write": 5.00}


def cost(usages) -> float:
    total = 0.0
    for u in usages:
        total += u.input_tokens * PRICE["input"] + u.output_tokens * PRICE["output"]
        total += (getattr(u, "cache_read_input_tokens", 0) or 0) * PRICE["cache_read"]
        total += (getattr(u, "cache_creation_input_tokens", 0) or 0) * PRICE["cache_write"]
    return total / 1_000_000


def outcome_labels(outcomes: list[dict]) -> list[str]:
    labels = set()
    for o in outcomes:
        if o["type"] == "handoff":
            labels |= {f"handoff:{reason}" for reason in o["reasons"]}
        else:
            labels.add(o["type"])
    return sorted(labels) or ["none"]


def pii_leaks(transcript: list[dict], borrower) -> list[str]:
    """Agent messages sent before verification that contain the borrower's amounts, loan ID or DOB."""
    secrets = {borrower.loan_id[-4:], borrower.dob}
    for n in (borrower.emi_amount, borrower.total_due):
        secrets |= {f"{n:,}", str(n)}
    return [
        m["text"]
        for m in transcript
        if m["role"] == "agent" and not m["verified"] and any(s in m["text"] for s in secrets)
    ]


def run_one(client, persona: dict, run: int) -> dict:
    borrower = Ledger().get(persona["borrower_id"])
    session = Session(borrower=borrower, now=datetime(*EVAL_DATE, tzinfo=ZoneInfo(borrower.timezone)))
    agent = CollectionsAgent(session, client=client)
    sim = BorrowerSimulator(client, persona, session)

    turns_to_outcome = None
    agent_text = agent.start()
    for _ in range(MAX_BORROWER_TURNS):
        borrower_text = sim.respond(agent_text)
        ended = END in borrower_text
        borrower_text = borrower_text.replace(END, "").strip()
        if not borrower_text:
            break
        agent_text = agent.reply(borrower_text)
        if turns_to_outcome is None and session.outcomes:
            turns_to_outcome = sum(1 for m in agent.transcript if m["role"] == "agent")
        if ended:
            break

    record = agent.record()
    verdict, judge_usage = judge(client, persona, record)
    labels = outcome_labels(session.outcomes)
    escalated = any(o["type"] == "handoff" for o in session.outcomes)
    leaks = pii_leaks(agent.transcript, borrower)
    sent_violations = [m["text"] for m in agent.transcript if m["role"] == "agent" and check_outbound(m["text"])]
    return {
        "persona": persona["id"],
        "group": persona["group"],
        "run": run,
        "labels": labels,
        "outcome_correct": set(labels) <= set(persona["acceptable_outcomes"]),
        "escalation": persona["escalation"],
        "escalated": escalated,
        "turns_to_outcome": turns_to_outcome,
        "pii_leaks": leaks,
        "sent_filter_violations": sent_violations,
        "blocked_drafts": sum(1 for e in agent.guardrail_events if e["type"] == "blocked_draft"),
        "judgement": verdict.model_dump(),
        "critical_failures": len(verdict.critical_violations) + len(leaks) + len(sent_violations),
        "cost_usd": round(cost(agent.usage + sim.usage + [judge_usage]), 4),
        "record": record,
    }


def summarize(results: list[dict]) -> dict:
    required = [r for r in results if r["escalation"] == "required"]
    escalated = [r for r in results if r["escalated"]]
    by_persona = defaultdict(list)
    for r in results:
        by_persona[r["persona"]].append(tuple(r["labels"]))
    multi_run = {p: runs for p, runs in by_persona.items() if len(runs) > 1}
    turns = [r["turns_to_outcome"] for r in results if r["turns_to_outcome"] is not None]
    return {
        "critical_failures": sum(r["critical_failures"] for r in results),
        "outcome_accuracy": sum(r["outcome_correct"] for r in results) / len(results),
        "escalation_recall": sum(r["escalated"] for r in required) / len(required) if required else 1.0,
        "escalation_precision": (
            sum(r["escalation"] != "forbidden" for r in escalated) / len(escalated) if escalated else 1.0
        ),
        "pii_before_verification": sum(len(r["pii_leaks"]) for r in results),
        "avg_tone": statistics.mean(r["judgement"]["tone_score"] for r in results),
        "consistency": (
            sum(len(set(runs)) == 1 for runs in multi_run.values()) / len(multi_run) if multi_run else 1.0
        ),
        "avg_turns_to_outcome": statistics.mean(turns) if turns else 0.0,
    }


def fmt(name: str, value: float) -> str:
    if name in ("outcome_accuracy", "escalation_recall", "escalation_precision", "consistency"):
        return f"{value:.0%}"
    if name in ("avg_tone", "avg_turns_to_outcome"):
        return f"{value:.2f}"
    return str(value)


def write_report(out_dir: Path, results: list[dict], errors: list[dict], summary: dict, runs: int) -> Path:
    passed = all(check(summary[k]) for k, (_, check) in THRESHOLDS.items())
    opening_ok = sum(r["judgement"]["opening_disclosure"] for r in results)
    blocked = sum(r["blocked_drafts"] for r in results)
    lines = [
        f"# Eval report: {out_dir.name}",
        "",
        f"**Verdict: {'PILOT-READY' if passed else 'NOT YET'}**. {len(results)} conversations "
        f"({len({r['persona'] for r in results})} personas x {runs} runs), "
        f"cost ${sum(r['cost_usd'] for r in results):.2f}.",
        "",
        "| Metric | Result | Threshold | Pass |",
        "|---|---|---|---|",
    ]
    for name, (label, check) in THRESHOLDS.items():
        lines.append(f"| {name} | {fmt(name, summary[name])} | {label} | {'yes' if check(summary[name]) else 'NO'} |")
    lines += [
        "",
        f"Opening disclosure present: {opening_ok}/{len(results)}. "
        f"Drafts blocked by the outbound filter (caught before sending): {blocked}.",
        "",
        "## By persona",
        "",
        "| Persona | Group | Correct runs | Outcomes seen | Critical | Tone |",
        "|---|---|---|---|---|---|",
    ]
    by_persona = defaultdict(list)
    for r in results:
        by_persona[r["persona"]].append(r)
    for pid in sorted(by_persona):
        rs = by_persona[pid]
        seen = sorted({", ".join(r["labels"]) for r in rs})
        lines.append(
            f"| {pid} | {rs[0]['group']} | {sum(r['outcome_correct'] for r in rs)}/{len(rs)} | "
            f"{'; '.join(seen)} | {sum(r['critical_failures'] for r in rs)} | "
            f"{statistics.mean(r['judgement']['tone_score'] for r in rs):.1f} |"
        )
    failures = [r for r in results if not r["outcome_correct"] or r["critical_failures"]]
    lines += ["", "## Failures", ""]
    if not failures:
        lines.append("None.")
    for r in sorted(failures, key=lambda r: (r["persona"], r["run"])):
        j = r["judgement"]
        lines.append(f"### {r['persona']} run {r['run']} ({r['group']}): cause `{j['failure_cause']}`")
        if not r["outcome_correct"]:
            lines.append(f"- Outcome {r['labels']} not in the acceptable set.")
        for v in j["critical_violations"]:
            lines.append(f"- **{v['rule']}**: \"{v['quote']}\" ({v['explanation']})")
        for leak in r["pii_leaks"]:
            lines.append(f"- **pii_before_verification**: \"{leak}\"")
        lines.append(f"- Judge notes: {j['notes']}")
        lines.append("")
    if errors:
        lines += ["## Errors", ""] + [f"- {e['persona']} run {e['run']}: {e['error']}" for e in errors]
    path = out_dir / "report.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--personas", help="Comma-separated persona IDs (default: all)")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    personas = json.loads((EVAL_DIR / "personas.json").read_text())
    if args.personas:
        wanted = set(args.personas.split(","))
        personas = [p for p in personas if p["id"] in wanted]

    client = anthropic.Anthropic()
    out_dir = EVAL_DIR / "reports" / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True)
    results, errors = [], []
    jobs = [(p, run) for p in personas for run in range(1, args.runs + 1)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, client, p, run): (p, run) for p, run in jobs}
        for i, future in enumerate(as_completed(futures), 1):
            p, run = futures[future]
            try:
                r = future.result()
                results.append(r)
                status = "ok" if r["outcome_correct"] and not r["critical_failures"] else "FAIL"
                print(f"[{i}/{len(jobs)}] {p['id']} run {run}: {status} {r['labels']} ${r['cost_usd']:.3f}")
            except anthropic.BadRequestError as e:
                if "credit balance" not in str(e):
                    raise
                print(f"\nStopping: API credit balance is too low. Partial report covers {len(results)} runs.")
                pool.shutdown(wait=False, cancel_futures=True)
                errors.append({"persona": p["id"], "run": run, "error": "credit balance too low; suite stopped"})
                break
            except Exception as e:  # keep the suite running; errors are listed in the report
                errors.append({"persona": p["id"], "run": run, "error": repr(e)})
                print(f"[{i}/{len(jobs)}] {p['id']} run {run}: ERROR {e!r}")
                traceback.print_exc()

    with (out_dir / "results.jsonl").open("w") as f:
        for r in sorted(results, key=lambda r: (r["persona"], r["run"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if not results:
        raise SystemExit("No conversations completed.")
    summary = summarize(results)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nReport: {write_report(out_dir, results, errors, summary, args.runs)}")
    for name, (label, check) in THRESHOLDS.items():
        print(f"  {name:24} {fmt(name, summary[name]):>8}  {label:>7}  {'pass' if check(summary[name]) else 'FAIL'}")


if __name__ == "__main__":
    main()
