# Report Examples

## 1. Purpose

This document describes the expected output categories from the MVP workflow.

The current MVP remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Main command

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 3. Expected output categories

The workflow may produce:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan

Exact filenames may vary by command and phase.

## 4. Markdown report example

A Markdown report should be suitable for manual review and archive.

Expected content categories:

- input summary
- primary metals context
- main market inference
- research plan
- final review
- final research trading plan
- safety boundary statement
- data status labels where applicable

Required safety language:

- research-only
- read-only
- manual-only
- no auto trade

## 5. Daily log example

A daily log should support later review and audit.

Expected content categories:

- run date or timestamp
- input config reference
- observed instruments
- generated research status
- output status
- data status
- manual review notes if applicable

## 6. Telegram-ready text example

Telegram-ready text is formatted for sending or copying to Telegram.

Current boundary:

- ready text only
- no real push required
- no Bot token required
- no trade trigger
- no auto execution

Expected content categories:

- concise summary
- key market observations
- risk notes
- final plan summary
- manual review reminder

## 7. Final research trading plan example

The final research trading plan should organize the research conclusion into a human-reviewable structure.

Expected content categories:

- short-term view
- medium-term view
- long-term view
- invalidation conditions
- risk triggers
- manual review checklist
- data limitations
- no auto trade statement

## 8. Review checklist

Before using any report:

- Confirm data status
- Confirm market session and timestamp
- Confirm whether data is real_time, delayed, inferred, or unavailable
- Confirm that no automatic order action was generated
- Confirm that any trade decision is manually reviewed
- Confirm that execution, if any, is performed manually outside this system

## 9. Non-goals

The report output is not:

- an automatic trading signal
- an order ticket
- a broker instruction
- a rebalance instruction
- a guarantee of real-time data completeness
