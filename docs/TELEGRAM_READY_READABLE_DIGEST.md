# Phase 101-108 Telegram-ready Readable Digest

## 1. Purpose

This document defines the local Telegram-ready readable digest workflow.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The workflow generates a text digest that can be manually copied by the operator.

It does not send messages, does not store tokens, and does not call any external notification service.

## 3. Runtime outputs

Generated local artifacts:

- telegram_ready_summary.csv
- reports/telegram_ready_report.md
- reports/telegram_ready_daily_digest.txt

## 4. Required content

The digest should include:

- run_id
- timestamp in Asia/Tokyo
- daily summary status
- final plan status
- data source status
- Telegram-ready status
- blocked reason
- manual review flag
- action allowed flag
- no external execution assertion

## 5. Safety boundary

This workflow must not trigger:

- real Telegram send
- token usage
- scheduler deployment
- broker execution
- IBKR connection
- market data request
- historical data request
- automatic trading

## 6. Final boundary

Telegram-ready output is a local text artifact only.

It is not an alerting system and not an execution system.
