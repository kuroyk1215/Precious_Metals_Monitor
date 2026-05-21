# Daily Review Workflow

## 1. Purpose

This document defines how to review daily outputs from Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Review order

Recommended review order:

1. Confirm run completed
2. Review data status
3. Review Markdown report
4. Review final research trading plan
5. Review risk triggers
6. Review invalidation conditions
7. Review Telegram-ready text
8. Decide whether any manual action is needed outside the system

## 3. Report review

When reviewing Markdown report, confirm:

- input config reference
- run timestamp
- instrument list
- market context
- data quality notes
- research summary
- final review
- safety boundary

## 4. Final research trading plan review

Check:

- short-term view
- medium-term view
- long-term view
- rolling trade reference
- entry reference zone
- exit reference zone
- invalidation condition
- risk trigger checklist
- manual review checklist

## 5. Telegram-ready text review

Telegram-ready text should be treated as notification content only.

Confirm:

- concise summary
- no secret values
- no broker instruction
- no buy-now wording
- no sell-now wording
- no automatic execution wording
- manual review reminder included

## 6. Data status review

Confirm:

- data_status
- source_status
- timestamp
- timezone
- fallback_method
- quality_note

If data is delayed, inferred, stale, or unavailable, do not treat the plan as execution-ready.

## 7. Manual trade review

The system may support research. It does not make the decision.

Any trade must be decided and executed manually through an external broker or trading terminal.

## 8. Archive review

Keep useful output for later review if needed.

Do not commit generated runtime reports unless a phase explicitly requires it.

## 9. Safety boundary

Daily review does not authorize:

- automatic trading
- order placement
- order cancellation
- automatic rebalance
- Telegram trading command
- scheduler trading action
