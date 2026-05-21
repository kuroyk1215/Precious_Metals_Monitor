# Local Run Logging Policy

## 1. Purpose

This document defines local run logging policy for Precious_Metals_Monitor.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

Local run logging should make manual operation auditable without enabling automation.

Allowed:

- record run timestamp
- record command used
- record output paths
- record data status summary
- record failure category
- record manual review status
- record no-trade assertion

Not allowed:

- broker execution
- Telegram real send
- scheduler deployment
- auto trade
- account credential logging

## 3. Recommended local log categories

Recommended future local log categories:

- run summary log
- failure log
- output archive index
- data status summary
- manual review notes

## 4. Recommended directory structure

Recommended future structure:

    logs/local/
    logs/failures/
    archive/reports/
    archive/daily_logs/
    archive/telegram_ready/
    archive/final_plans/

Phase 51–53 only documents this structure. It does not require committing runtime log files.

## 5. Run summary fields

Recommended fields:

- run_id
- run_timestamp
- timezone
- branch
- commit
- command
- config_reference
- output_report_path
- output_daily_log_path
- telegram_ready_text_path
- final_research_trading_plan_path
- data_status_summary
- no_trade_assertion
- result

## 6. Secret handling

Logs must not contain:

- broker credentials
- account IDs
- Telegram Bot token
- real chat_id
- API keys
- private endpoints

## 7. Safety boundary

Logging must not trigger:

- placeOrder
- cancelOrder
- rebalance
- auto trade
- Telegram trade command
- scheduler trade execution
