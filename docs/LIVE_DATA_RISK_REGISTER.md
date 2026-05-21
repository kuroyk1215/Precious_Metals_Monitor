# Live Data Risk Register

## 1. Purpose

This document lists risks that must be reviewed before future live or near-live data usage.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Market data risk

Risk:

- data may be delayed
- data may be frozen
- subscription may be missing
- exchange permission may be unavailable
- timestamp may be stale

Mitigation:

- expose data_status
- expose timestamp
- expose source_status
- require manual review

## 3. Broker integration risk

Risk:

- unintended access to broker APIs
- accidental exposure of credentials
- accidental addition of trading path

Mitigation:

- read-only gate
- no-trade assertion
- targeted code review
- no secrets in Git

## 4. Scheduler risk

Risk:

- scheduled runs happen during wrong session
- timezone mismatch
- repeated failures
- stale report generation

Mitigation:

- explicit timezone
- log run timestamp
- avoid infinite retry
- preserve previous report

## 5. Telegram risk

Risk:

- notification may be misunderstood as trade instruction
- token leakage
- wrong chat destination
- message truncation

Mitigation:

- notification-only policy
- no trade wording
- token stored outside Git
- manual review reminder

## 6. Data interpretation risk

Risk:

- inferred data may appear precise
- ETF and underlying reference may diverge
- FX conversion may distort value

Mitigation:

- show fallback_method
- label inferred values
- include quality_note
- require manual validation

## 7. Operational risk

Risk:

- local Mac sleeps
- cloud server failure
- network outage
- dependency failure

Mitigation:

- failure logging
- no infinite retry
- manual fallback
- report availability check

## 8. Final boundary

Live data improves observation quality only.

It must not create an automatic trading workflow.
