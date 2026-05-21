# Failure Log Format

## 1. Purpose

This document defines a future failure log format.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Failure log goal

A failure log should help diagnose failed local runs without exposing secrets or creating trading behavior.

## 3. Recommended fields

Recommended failure log fields:

- failure_id
- run_id
- timestamp
- timezone
- branch
- command
- phase
- failure_category
- failure_message
- affected_output
- data_status
- retry_allowed
- manual_action_required
- no_trade_assertion
- resolved_status
- notes

## 4. Failure categories

Suggested categories:

- config_missing
- config_invalid
- data_unavailable
- output_write_failed
- dependency_missing
- test_failed
- cleanup_failed
- telegram_dryrun_failed
- scheduler_dryrun_failed
- unknown

## 5. Required safety fields

Every failure log should include:

    no_trade_assertion: true
    broker_execution_triggered: false
    telegram_real_send_triggered: false
    scheduler_real_deployment_triggered: false

## 6. Forbidden contents

Failure logs must not contain:

- broker password
- account ID
- API keys
- Telegram Bot token
- real chat_id
- private endpoints
- full private config dump

## 7. Failure response policy

On failure:

- preserve existing reports
- do not retry indefinitely
- do not trigger broker fallback
- do not send trade command
- require manual review

## 8. Safety boundary

Failures must not cause:

- automatic buy
- automatic sell
- automatic cancel
- automatic rebalance
- Telegram trade command
- broker execution
