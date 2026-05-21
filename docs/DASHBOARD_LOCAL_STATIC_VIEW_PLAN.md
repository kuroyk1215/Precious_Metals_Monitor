# Phase 121-132 Dashboard Local Static View Plan

## 1. Purpose

This document defines the local static dashboard readiness plan.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Goal

The dashboard local static view should read local runtime artifacts and render a human-readable status page.

It is not a web app, not a broker interface, and not an execution panel.

## 3. Runtime outputs

Generated local artifacts:

- dashboard_static_view_summary.csv
- reports/dashboard_static_view_report.md
- reports/dashboard/index.html

## 4. Committed sample artifact

Committed sample:

- examples/dashboard_manifest.sample.json

## 5. Dashboard display scope

Allowed display fields:

- latest run metadata
- data source status
- daily summary status
- Telegram-ready status
- scheduler dry-run status
- blocked reason
- manual review flag
- safety flags

## 6. Forbidden scope

The dashboard must not include:

- order submission controls
- cancellation controls
- broker execution controls
- Telegram send controls
- scheduler deployment controls
- IBKR connection controls
- automatic trading controls

## 7. Final boundary

The dashboard local static view is a read-only local review artifact.

It does not authorize external execution, background operation, broker connection, notification sending, or automatic trading.
