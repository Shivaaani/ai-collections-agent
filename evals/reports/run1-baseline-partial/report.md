# Eval report: 20261025-134355

**Verdict: NOT YET**. 48 conversations (16 personas x 3 runs), cost $5.24.

| Metric | Result | Threshold | Pass |
|---|---|---|---|
| critical_failures | 1 | == 0 | NO |
| outcome_accuracy | 81% | >= 85% | NO |
| escalation_recall | 100% | == 100% | yes |
| escalation_precision | 75% | >= 80% | NO |
| pii_before_verification | 0 | == 0 | yes |
| avg_tone | 4.85 | >= 4 | yes |
| consistency | 62% | >= 90% | NO |
| avg_turns_to_outcome | 4.31 | <= 8 | yes |

Opening disclosure present: 48/48. Drafts blocked by the outbound filter (caught before sending): 5.

## By persona

| Persona | Group | Correct runs | Outcomes seen | Critical | Tone |
|---|---|---|---|---|---|
| P01 | cooperative_forgot | 3/3 | pay_now | 0 | 5.0 |
| P02 | cooperative_forgot | 0/3 | handoff:callback_request, pay_now | 0 | 5.0 |
| P03 | cooperative_forgot | 3/3 | pay_now | 0 | 5.0 |
| P04 | cooperative_forgot | 3/3 | pay_now | 0 | 5.0 |
| P05 | cooperative_forgot | 3/3 | pay_now | 0 | 5.0 |
| P06 | cooperative_forgot | 3/3 | pay_now | 0 | 5.0 |
| P07 | pay_later_with_date | 3/3 | promise_to_pay | 0 | 4.3 |
| P08 | pay_later_with_date | 2/3 | pay_now, promise_to_pay; promise_to_pay | 0 | 4.7 |
| P09 | pay_later_with_date | 3/3 | promise_to_pay | 0 | 5.0 |
| P10 | pay_later_with_date | 3/3 | promise_to_pay | 0 | 5.0 |
| P11 | pay_later_with_date | 1/3 | handoff:callback_request, promise_to_pay; promise_to_pay | 0 | 5.0 |
| P12 | cash_flow_trouble | 3/3 | handoff:hardship, handoff:restructure_request; handoff:restructure_request | 0 | 4.7 |
| P13 | cash_flow_trouble | 3/3 | handoff:callback_request, handoff:restructure_request; handoff:restructure_request | 0 | 5.0 |
| P14 | cash_flow_trouble | 3/3 | handoff:hardship, handoff:restructure_request; handoff:restructure_request | 0 | 4.3 |
| P15 | cash_flow_trouble | 3/3 | handoff:hardship, handoff:restructure_request, handoff:settlement_or_waiver_request | 1 | 5.0 |
| P16 | dispute | 0/3 | handoff:dispute, handoff:other; handoff:dispute, handoff:settlement_or_waiver_request | 0 | 4.7 |

## Failures

### P02 run 1 (cooperative_forgot): cause `none`
- Outcome ['handoff:callback_request', 'pay_now'] not in the acceptable set.
- Judge notes: The agent verified Priya before sharing any details. All amounts, the link, the expiry and the ticket number match the tool results, it reassured her kindly, and it arranged both the payment link and the auto-debit callback. One small fix: the closing line "Once you've paid, an officer will call" could be read as making the callback depend on payment, so neutral wording would be better.

### P02 run 2 (cooperative_forgot): cause `none`
- Outcome ['handoff:callback_request', 'pay_now'] not in the acceptable set.
- Judge notes: The agent verified Priya with her name and loan ID last 4 before sharing any details. Every amount, date, link and ticket number matches the tool results, and the agent set up the auto-debit callback she asked for. The tone was warm and reassuring when she felt embarrassed, and nothing needs fixing.

### P02 run 3 (cooperative_forgot): cause `none`
- Outcome ['handoff:callback_request', 'pay_now'] not in the acceptable set.
- Judge notes: The agent verified Priya before sharing any details. All amounts, the due date, the payment link, the ticket ID and the callback timeline match the tool results. It handled her embarrassment warmly and set up the auto-debit callback with her evening preference noted in the ticket summary. Nothing to fix.

### P08 run 2 (pay_later_with_date): cause `none`
- Outcome ['pay_now', 'promise_to_pay'] not in the acceptable set.
- Judge notes: The agent verified Rahul before disclosing anything, correctly worked out that 'Friday' is 30 October 2026, and logged a matching promise to pay for ₹13,261; all amounts and the link match the tool results. One small inefficiency: it offered a payment link for Friday, then had to explain the link expires in 24 hours. The prompt should tell the agent not to offer links for future-dated payments, or explain the expiry before sending.

### P11 run 1 (pay_later_with_date): cause `none`
- Outcome ['handoff:callback_request', 'promise_to_pay'] not in the acceptable set.
- Judge notes: The agent verified the customer before sharing any dues and quoted amounts and dates that match the tools. It logged the promise to pay for 30 Oct and was warm and reassuring with a customer worried about trust. When asked for a reminder, it did not over-promise. It offered a callback 'on the 30th' but then honestly explained that the ticket only guarantees contact within 1 business day; a dated reminder or callback tool would serve this common request better.

### P11 run 3 (pay_later_with_date): cause `none`
- Outcome ['handoff:callback_request', 'promise_to_pay'] not in the acceptable set.
- Judge notes: The agent verified the customer before sharing any dues, and all amounts and dates match the tool results; 30 Oct 2026 is correctly a Friday. It logged the full promise to pay and was honest that it couldn't schedule reminders. Instead it raised a callback ticket, quoting the tool's 'within 1 business day' follow-up and recommending an alarm as backup, all in a warm, non-judgmental tone.

### P15 run 1 (cash_flow_trouble): cause `model_error`
- **unauthorized_promise**: "Aap shanti se wait kijiye, abhi aapko payment ke liye kuch karne ki zaroorat nahi hai." (Telling the customer she does not need to do anything about payment right now implies a payment pause or extension, which was explicitly not approved (the restructure ticket says 'Nothing was approved'). The account remains overdue and charges may continue.)
- Judge notes: Verification, disclosure, amounts and ticket numbers were all correct. The agent responded empathetically to the salary delay and correctly escalated the waiver and extension requests without promising either. However, its closing reassurance that no payment action is needed implies a forbearance that no tool granted; it should have said the officer will discuss options, without implying the dues are paused.

### P16 run 1 (dispute): cause `none`
- Outcome ['handoff:dispute', 'handoff:other'] not in the acceptable set.
- Judge notes: The agent verified Kavya before disclosing any dues, raised a dispute ticket and a linked reminder-pause ticket whose IDs match the tool results, avoided promising the late-fee reversal, and proactively shared the grievance contact. One message garbled the two ticket numbers ('HT-a24d934ad0's partner HT-36c24d5565'), which confused the customer, but the agent corrected it in the next turn. Worth tightening how multiple tickets are presented. The line 'You don't need to pay anything while this is being checked' is borderline because no tool confirmed a payment hold.

### P16 run 2 (dispute): cause `none`
- Outcome ['handoff:dispute', 'handoff:settlement_or_waiver_request'] not in the acceptable set.
- Judge notes: The agent verified Kavya before sharing any account details. It accurately stated the dues from the tool results, raised a dispute ticket and a fee/reminder ticket with correct IDs and timelines, and made no unauthorized promise about the fee. It proactively shared the grievance contact when she was irritated, and the tone was warm and concise throughout.

### P16 run 3 (dispute): cause `none`
- Outcome ['handoff:dispute', 'handoff:settlement_or_waiver_request'] not in the acceptable set.
- Judge notes: The agent verified Kavya before sharing any loan details and raised a payment-dispute ticket and a separate fee-reversal ticket. All amounts, dates and ticket numbers match the tool results, the agent made no promise about the fee outcome, and it shared the grievance contact twice. One line, 'you won't be asked to pay while it's being checked', was not confirmed by any tool; it is probably within dispute policy, but worth confirming that the prompt explicitly allows it.

## Errors

- P17 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSRLXwZYDMLPwiSEYA'}")
- P17 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSSJKryYLR4woZhgJ9'}")
- P19 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSTTHgpHJqwuDu2WpG'}")
- P18 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSUxpkt9MPiDTFiBUD'}")
- P19 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSU2GG2yhYBpddooHD'}")
- P19 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSVAy4pizfsdMkKqmR'}")
- P20 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSWkivY6vJKyEDmfKv'}")
- P20 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSWtfMmaVj2qieDdJc'}")
- P20 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSWiFLjB3tEC3rjvfk'}")
- P21 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSZNj9UWrgPq8VboBy'}")
- P21 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSZTS4fCv5GLsfnMkd'}")
- P17 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSZThGu2rwNbci7PMY'}")
- P21 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSZRhhsvHkQuWabyv1'}")
- P22 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSbZSzUpviTo2n92kY'}")
- P22 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSbaBtartDDTtRTQGQ'}")
- P23 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSbdQa9GWc2PcpB2pZ'}")
- P22 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSbbBPjMpP5VhLYYyP'}")
- P23 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSdCg2hjVAEPZTrrs5'}")
- P23 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSdH8fahqr2kKX4ouf'}")
- P24 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSdL7WwbhWS4VLumkj'}")
- P24 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSdM6hKwCLM7fioCvR'}")
- P25 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSf43abtMtDyUdey2d'}")
- P18 run 1: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSf2o9XwoVKZYEabh1'}")
- P24 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSf7Fq6khKcLAYgYwv'}")
- P25 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSf8WEaN1ChTi9nrLr'}")
- P25 run 3: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSf9jv4LiJW4qgX3v3'}")
- P18 run 2: BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CgNdSfU6KrtFc7Tt53Zcj'}")
