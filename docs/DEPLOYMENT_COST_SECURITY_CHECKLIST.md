# Deployment Cost and Security Checklist

## 1. Purpose

This checklist defines cost and security review items before any 24h deployment.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Cost checklist

Before cloud deployment, confirm:

- monthly server cost
- storage cost
- backup cost
- network cost
- monitoring cost
- maintenance burden

## 3. Security checklist

Before any deployment, confirm:

- no secrets in Git
- no Telegram Bot token in docs or examples
- no broker credentials in logs
- no account IDs in sample configs
- no public UI exposure
- no public API exposure
- SSH keys protected
- firewall reviewed if cloud is used

## 4. Operational checklist

Confirm:

- cleanup script works
- acceptance script works
- daily manual check works
- local automation dry-run works
- tests pass
- output paths are known
- failure behavior is documented

## 5. Safety checklist

Confirm:

- no placeOrder
- no cancelOrder
- no auto trade
- no auto rebalance
- no Telegram trade command
- no scheduler trade path
- no UI trade path

## 6. Rejection conditions

Reject deployment if:

- config secrets are staged
- sample configs enable trading
- scheduler can trigger trade action
- Telegram can trigger trade action
- logs expose tokens
- tests fail
- cleanup script fails
