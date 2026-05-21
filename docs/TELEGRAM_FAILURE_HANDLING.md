# Telegram Failure Handling

## 1. Purpose

This document defines the expected failure handling model for future Telegram integration.

Current Phase 35 does not implement real sending. It only defines the expected behavior.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Failure categories

Future Telegram integration should classify failures into:

- token missing
- token invalid
- chat_id missing
- chat_id invalid
- network failure
- Telegram API error
- rate limit
- message too long
- formatting error
- permission denied
- unknown error

## 3. Default behavior

Failure to send a Telegram message must not stop report generation if the report itself was created successfully.

Recommended behavior:

- complete local report generation
- mark Telegram send status as failed
- write failure reason to log
- preserve generated Markdown report
- preserve daily log if applicable
- do not retry indefinitely
- do not trigger any trading behavior

## 4. Retry policy

Future implementation may use limited retry.

Recommended baseline:

- max retry count: 2
- retry delay: short fixed delay
- no infinite loop
- no blocking long-running scheduler indefinitely

## 5. Message size handling

Telegram messages have practical size limits.

If message is too long, future implementation should:

- send concise summary only
- reference local report path
- avoid splitting into excessive message chains
- preserve manual review reminder

## 6. Dry-run behavior

Dry-run should be the default before real sending.

Dry-run output should confirm:

- message generated
- destination resolved or placeholder used
- send skipped intentionally
- no trade action possible

## 7. Logging requirements

Future send log should include:

- run timestamp
- message category
- destination label
- send_allowed flag
- send result
- error category
- retry count
- no-trade assertion

Do not log:

- Bot token
- full private config
- account credentials
- broker credentials

## 8. Scheduler interaction

If Telegram send fails during a scheduled run:

- scheduler should continue to next scheduled run
- failure should be logged
- local report should remain available
- no trading action should be triggered

## 9. Manual review boundary

Even if Telegram delivery succeeds, the message remains informational only.

The user must manually review the report before any trading decision.

Required boundary:

    research-only / read-only / manual-only / no auto trade

## 10. Non-goals

Failure handling must not add:

- automatic order execution
- broker-side recovery
- automatic rebalance
- Telegram command execution
- emergency trading action
