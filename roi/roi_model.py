"""One-page ROI model for the early-collections agent. All inputs are illustrative assumptions.

    python roi/roi_model.py
    python roi/roi_model.py --ai-share 0.5 --ai-cost 12
"""

import argparse


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--accounts", type=int, default=8_000, help="Accounts entering 1-30 DPD per month")
    p.add_argument("--human-cost", type=float, default=45, help="Human cost per account contacted (Rs)")
    p.add_argument("--ai-cost", type=float, default=10, help="AI cost per account: model, messaging, platform (Rs)")
    p.add_argument("--ai-share", type=float, default=0.60, help="Share resolved by AI without a human")
    p.add_argument("--deploy-cost", type=float, default=10_00_000, help="One-time deployment cost (Rs)")
    p.add_argument("--avg-overdue", type=float, default=6_000, help="Average overdue amount per account (Rs)")
    p.add_argument("--ptp-before", type=float, default=0.28, help="Promise-to-pay rate today")
    p.add_argument("--ptp-after", type=float, default=0.30, help="Promise-to-pay rate with the agent")
    p.add_argument("--kept-rate", type=float, default=0.60, help="Share of promises kept")
    a = p.parse_args()

    today = a.accounts * a.human_cost
    ai = a.accounts * a.ai_cost  # the agent makes first contact on every account
    human = a.accounts * (1 - a.ai_share) * a.human_cost
    with_agent = ai + human
    saving = today - with_agent
    extra_payers = a.accounts * (a.ptp_after - a.ptp_before) * a.kept_rate

    lakh = lambda x: f"Rs {x / 1e5:.2f}L"
    print("Monthly early-collections cost")
    print(f"  Today (all human):        {lakh(today)}  (Rs {today / a.accounts:.0f} per account)")
    print(f"  With agent:               {lakh(with_agent)}  (Rs {with_agent / a.accounts:.0f} per account)")
    print(f"    AI on every account:    {lakh(ai)}")
    print(f"    Humans on {1 - a.ai_share:.0%} handed off: {lakh(human)}")
    print(f"  Saving:                   {lakh(saving)} a month ({saving / today:.0%}), {lakh(saving * 12)} a year")
    if saving > 0:
        print(f"  Payback on {lakh(a.deploy_cost)}:      {a.deploy_cost / saving:.1f} months (cost alone)")
    print("\nRecovery upside (not in payback)")
    print(
        f"  PTP {a.ptp_before:.0%} -> {a.ptp_after:.0%} at {a.kept_rate:.0%} kept: about {extra_payers:.0f} more "
        f"accounts pay early each month, about {lakh(extra_payers * a.avg_overdue)} sooner."
    )


if __name__ == "__main__":
    main()
