# Phase 57 Daily Research Run Acceptance

## 1. Purpose

This document defines the acceptance criteria for a manual daily research run.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Acceptance checks

A daily research run is accepted only if:

- Python syntax check passes
- unit tests pass
- daily manual check passes
- operation handoff check passes
- config.yaml is not staged
- no broker execution is triggered
- no real Telegram message is sent
- no real scheduler is deployed
- no automatic trading path is enabled

## 3. Manual review requirements

The operator must manually review:

- Markdown reports
- CSV summaries
- data_status fields
- manual_review_required flags
- risk trigger descriptions
- final research trading plan

## 4. Excluded scope

This phase does not authorize:

- broker order submission
- broker order cancellation
- bracket order construction
- what-if order simulation
- options exercise
- rebalance execution
- automatic trading
- real Telegram send
- real scheduler deployment

## 5. Final boundary

Daily research run acceptance means the project is ready for disciplined manual research review.

It does not mean the project is ready for unattended 24h operation or automated execution.
