# Output Acceptance Criteria

## 1. Purpose

This document defines the acceptance criteria for MVP v1.0 output review.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Required output categories

The one-command workflow should produce human-reviewable research outputs.

Expected categories:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

## 3. Markdown report acceptance

A Markdown report is acceptable if it includes:

- run context
- instrument or market reference
- research summary
- data status notes where applicable
- final review or plan summary
- manual review boundary

## 4. Daily log acceptance

A daily log is acceptable if it supports later audit.

Expected content:

- run date or timestamp
- workflow status
- output status
- relevant file references
- data availability notes if applicable

## 5. Telegram-ready text acceptance

Telegram-ready text is acceptable if it is:

- concise
- copyable
- research-only
- notification-only
- free of real secrets
- free of broker commands
- not phrased as auto execution

It must not include:

- real Bot token
- account ID
- broker credentials
- order instruction
- cancel instruction
- rebalance instruction

## 6. Final research trading plan acceptance

A final research trading plan is acceptable if it includes:

- short-term view
- medium-term view
- long-term view
- rolling trade reference if applicable
- invalidation conditions
- risk triggers
- data status notes
- manual review checklist
- no-trade assertion

## 7. Data status acceptance

Where market data is used, output should expose:

- data_status
- source_status
- timestamp
- timezone
- fallback_method
- quality_note where applicable

If data is delayed, inferred, stale, or unavailable, manual review should be escalated.

## 8. Safety acceptance

Output must not create:

- order ticket
- broker instruction
- auto trade signal
- automatic rebalance instruction
- Telegram trade command
- scheduler execution instruction

## 9. Final acceptance statement

An output is acceptable only if it remains suitable for manual review and does not imply automatic execution.
