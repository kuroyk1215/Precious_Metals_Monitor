# Retention Validation Policy

## 1. Purpose

This document defines the retention validation policy for local manual operation outputs.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Retention goal

Retention should support personal review while avoiding unnecessary accumulation of sensitive or stale runtime artifacts.

## 3. Suggested retention classes

Suggested classes:

- daily reports: keep as needed for review
- final plans: keep as needed for strategy review
- Telegram-ready text: short retention unless manually archived
- failure logs: keep until reviewed and resolved
- debug logs: short retention
- sensitive logs: avoid creating when possible

## 4. Retention metadata

Archived items should be traceable by:

- run_id
- timestamp
- market
- workflow
- output_type
- data_status
- manual_review_status
- no_trade_assertion

## 5. Delete policy

Before deleting any archived output, confirm:

- it is not needed for active review
- it does not contain unresolved failure context
- it does not contain unique manual notes
- deletion does not break audit trail needed by the user

## 6. Git policy

Runtime archive contents should not be committed by default.

Commit only:

- docs
- examples
- scripts
- non-sensitive sample files

Do not commit:

- private reports
- local logs
- account data
- broker output
- tokens
- private configs

## 7. Safety boundary

Retention validation is file management only.

It must not trigger:

- broker execution
- Telegram real send
- scheduler deployment
- automatic trading
