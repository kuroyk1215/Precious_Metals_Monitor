# Telegram Dry-Run Operation Plan

## 1. Purpose

This document defines a Telegram dry-run operation plan.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

Phase 46 in this combined pack does not send real Telegram messages.

## 2. Dry-run goal

Telegram dry-run should validate notification content before real Bot integration.

Allowed:

- generate Telegram-ready text
- validate message structure
- validate no secret leakage
- validate manual review reminder
- validate no-trade wording
- validate send_allowed is false by default

Not allowed:

- real Telegram send
- real Bot token use
- real chat_id use
- Telegram command handling
- Telegram-triggered trading
- broker execution

## 3. Message checks

A Telegram dry-run message should include:

- concise summary
- run status
- report availability
- final research trading plan summary
- data status warning if applicable
- manual review reminder
- no-trade assertion

## 4. Forbidden content

Telegram dry-run message must not include:

- real Bot token
- real chat_id
- broker credentials
- account ID
- order instruction
- cancel instruction
- rebalance instruction
- auto trade instruction

## 5. Config rules

Default Telegram config must remain:

    enabled: false
    mode: ready_text_only
    send_allowed: false

Real send must require a separate reviewed phase.

## 6. Failure handling

If Telegram dry-run fails:

- preserve local report
- write failure reason
- do not retry indefinitely
- do not trigger scheduler fallback
- do not trigger broker action

## 7. Safety boundary

Telegram remains notification-only.

It must not become:

- trade command channel
- broker control channel
- remote execution interface
- automatic trading interface
