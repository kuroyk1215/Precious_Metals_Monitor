# Generated Artifact Cleanup

## 1. Purpose

This document defines how to clean generated runtime artifacts after running tests or local workflows.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Problem

Running tests may generate local CSV and Markdown artifacts.

Common examples:

- conversion_factor_calibration_log.csv
- historical_quality_gate_log.csv
- ibkr_historical_fetch_log.csv
- ibkr_smoke_log.csv
- precious_metals_signal_log.csv
- theoretical_price_snapshot.csv
- upstream_factor_snapshot.csv
- reports/latest_report.md
- reports/theoretical_price_report.md
- reports/upstream_factor_report.md

One tracked report may also be modified:

- reports/ibkr_smoke_report.md

## 3. Cleanup command

Use:

    ./scripts/cleanup_generated_artifacts.sh

This script removes known generated runtime artifacts and restores the tracked smoke report.

## 4. What the script does not remove

The cleanup script does not remove:

- config.yaml
- .venv/
- source code
- docs
- examples
- committed project files

## 5. Expected clean local state

After cleanup, normal local state may still show:

    M config.yaml
    ?? .venv/

These are local-only items and should not be committed.

## 6. Safety boundary

The cleanup workflow does not:

- place orders
- cancel orders
- rebalance positions
- trigger broker behavior
- trigger Telegram behavior
- modify trading logic
