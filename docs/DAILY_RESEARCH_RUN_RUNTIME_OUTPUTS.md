# Phase 61-64 Daily Research Run Runtime Outputs

## 1. Purpose

This document defines the runtime output workflow for the manual daily research run.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Runtime output goal

The daily research run should provide a repeatable local command that generates:

- final research plan orchestration output
- report template output
- daily log output
- Telegram-ready text output
- local run summary
- Markdown run report

## 3. Allowed scope

Allowed:

- run existing research-only CLI commands
- generate local CSV summaries
- generate local Markdown reports
- generate Telegram-ready text artifact
- require manual review

## 4. Forbidden scope

Forbidden:

- real Telegram API call
- real scheduler deployment
- background daemon
- broker execution
- market order
- cancel order
- bracket order
- what-if order
- options exercise
- automatic trading

## 5. Required safety assertions

Each daily research run must assert:

- ibkr_connection_allowed=false
- market_data_request_allowed=false
- historical_data_request_allowed=false
- contract_details_request_allowed=false
- telegram_api_called=false
- scheduler_deployed=false
- broker_execution_triggered=false
- final_action_allowed=false
- manual_review_required=true

## 6. Final boundary

Daily research run runtime outputs are local review artifacts only.

They do not authorize unattended operation, broker execution, or automatic trading.
