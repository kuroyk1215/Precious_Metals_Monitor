# Telegram Dry-Run Check

## 1. Purpose

This document defines Telegram dry-run validation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Dry-run checks

Telegram dry-run validates:

- sample Telegram config exists
- send_allowed is false in sample config
- auto_trade_allowed is false in sample config
- message policy is documentation-only
- no real token is required
- no real chat_id is required

## 3. Forbidden behavior

Telegram dry-run must not:

- send real message
- use real Bot token
- use real chat_id
- trigger broker action
- trigger trade command
