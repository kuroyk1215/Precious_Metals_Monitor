# UI Security Model

## 1. Purpose

This document defines the security model for any future personal-use UI.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Local-first principle

The first UI should be local-only.

Recommended default:

- bind to localhost
- no public internet exposure
- no account credentials displayed
- no token displayed
- no order capability

## 3. Secret handling

The UI must not display:

- Telegram Bot token
- broker credentials
- account IDs
- API keys
- private config values
- private endpoints

## 4. Forbidden endpoints

Future API or UI must not expose endpoints such as:

- /buy
- /sell
- /cancel
- /rebalance
- /execute
- /place-order
- /cancel-order

## 5. Allowed UI actions

Allowed future UI actions may include:

- refresh report list
- open latest report
- show latest daily log
- show Telegram-ready text
- show final research trading plan
- show data status
- show scheduler status
- run dry-run research workflow after explicit gate review

## 6. Run button restrictions

If a run button is ever added, it must only trigger research workflow.

It must not trigger:

- order placement
- order cancellation
- rebalance
- Telegram trade command
- broker execution

## 7. Network exposure

Default UI should not be exposed outside the local machine.

If remote access is ever considered, it requires separate review for:

- authentication
- HTTPS
- firewall
- token protection
- log sanitization
- no-trade assertion

## 8. Logging

UI logs may include:

- timestamp
- report path
- run status
- data status
- error category

UI logs must not include:

- credentials
- tokens
- account numbers
- private config content

## 9. No-trade assertion

Every UI route and future button must preserve:

    no order action
    no cancel action
    no rebalance action
    no auto trade
