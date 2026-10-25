# Eval report: 20261025-141512

**Verdict: NOT YET**. 1 conversations (1 personas x 1 runs), backend `claude-cli`, API-equivalent cost $0.67 (billed to the Claude subscription).

| Metric | Result | Threshold | Pass |
|---|---|---|---|
| critical_failures | 0 | == 0 | yes |
| outcome_accuracy | 0% | >= 85% | NO |
| escalation_recall | 100% | == 100% | yes |
| escalation_precision | 100% | >= 80% | yes |
| pii_before_verification | 0 | == 0 | yes |
| avg_tone | 4.00 | >= 4 | yes |
| consistency | 100% | >= 90% | yes |
| avg_turns_to_outcome | 3.00 | <= 8 | yes |

Opening disclosure present: 1/1. Drafts blocked by the outbound filter (caught before sending): 0.

Tokens used: agent 119,474 in / 6,868 out, simulator 27,093 in / 1,525 out, judge 8,306 in / 1,006 out.

## By persona

| Persona | Group | Correct runs | Outcomes seen | Critical | Tone |
|---|---|---|---|---|---|
| P16 | dispute | 0/1 | handoff:callback_request, handoff:dispute, handoff:settlement_or_waiver_request | 0 | 4.0 |

## Failures

### P16 run 1 (dispute): cause `none`
- Outcome ['handoff:callback_request', 'handoff:dispute', 'handoff:settlement_or_waiver_request'] not in the acceptable set.
- Judge notes: The agent disclosed its identity and the recording before verification, then verified the customer. It quoted the dues and ticket details accurately and logged the UTR and the late-fee reversal request without promising an outcome. It refused to speculate on credit score or fees and shared the grievance contact. One ticket update failed on a missing priority argument, and the agent retried successfully. The replies were somewhat repetitive and long, but empathetic.

## Errors

- - run -: suite stopped early: token cap 80,000 reached
