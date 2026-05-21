# Phase 60 Dashboard Readiness Decision

## 1. Purpose

This document defines whether the project is ready to start dashboard implementation.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Dashboard readiness criteria

Dashboard work should start only after:

- daily research run check is stable
- data source labels are stable
- report fields are stable
- final research trading plan fields are stable
- generated artifacts have predictable names
- runtime archives are ignored
- no secrets are committed
- no automatic execution path exists

## 3. Recommended dashboard scope

Allowed initial dashboard scope:

- local static view
- read existing CSV / Markdown outputs
- show data_status
- show manual_review_required
- show no_trade_assertion
- show latest report links
- show risk triggers

## 4. Forbidden dashboard scope

Forbidden:

- order buttons
- broker execution buttons
- cancel buttons
- rebalance buttons
- automatic trade triggers
- Telegram real send buttons
- scheduler deployment controls

## 5. Decision

Dashboard implementation is not the immediate next step.

The immediate next step remains data-source quality and daily research run stability.

Dashboard should start only after these fields are stable enough to avoid misleading display.
