# Telegram Security Model

## 1. Purpose

This document defines the security boundary for future Telegram integration.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Security principles

Telegram must only be used as a notification channel.

It must not become:

- a trading command channel
- a broker control interface
- an order execution interface
- a rebalance trigger
- a privileged remote control surface

## 3. Token classification

Telegram Bot token is secret.

It must be treated like an API key.

Do not commit it to:

- Git
- docs/
- examples/
- README
- reports/
- logs/
- PR descriptions
- screenshots

## 4. Allowed token storage

Allowed:

- environment variable
- local config.yaml
- private config ignored by Git
- external secret manager in a later phase

Example environment variable name:

    TELEGRAM_BOT_TOKEN

Example local-only config field:

    telegram.bot_token_env: TELEGRAM_BOT_TOKEN

## 5. Forbidden token storage

Forbidden:

- examples/telegram_config.sample.yaml with real token
- committed config.yaml
- hard-coded Python string
- committed test fixture with real token
- Markdown documentation with real token

## 6. chat_id and channel_id

chat_id and channel_id are less sensitive than Bot token but should still be treated as private runtime information.

Public examples must use placeholders.

## 7. Send permission model

Future implementation should require an explicit send gate.

Recommended fields:

    telegram.enabled: true
    telegram.mode: real_send
    telegram.send_allowed: true

Default sample config should use:

    telegram.enabled: false
    telegram.mode: ready_text_only
    telegram.send_allowed: false

## 8. Command handling

Telegram commands should not be enabled by default.

If command handling is ever considered, it must be limited to non-trading actions such as:

- status
- latest report path
- last run summary

Forbidden commands:

- /buy
- /sell
- /cancel
- /rebalance
- /trade
- /execute

## 9. Output sanitization

Telegram messages must not include:

- account numbers
- real API keys
- real Bot tokens
- private broker session data
- sensitive local file paths when avoidable
- credentials
- personally identifiable secrets

## 10. Auditability

Future real send implementation should log:

- timestamp
- message type
- destination alias
- send status
- error category if failed
- no-trade assertion status

Logs should not include real Bot token.

## 11. Safety assertion

Every future Telegram path should preserve:

    no order action
    no cancel action
    no rebalance action
    no auto trade

Telegram is notification-only.
