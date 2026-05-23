# Release Candidate Checklist

## Environment Check

- Confirm Python dependencies are available in `.venv`.
- Confirm `gh` authentication is available for PR creation.
- Confirm TWS/Gateway is closed unless running explicit Execution C validation.

## Git Status Check

- Run `git status --short`.
- Confirm `config.yaml` is local-only and not staged.
- Confirm `.venv`, runtime logs, generated CSV files, and generated reports are not staged.

## IBKR TWS/Gateway Check

- For default dry-run, no IBKR connection is required.
- For Execution C validation, start TWS/Gateway manually before running the explicit command.
- Confirm the validation is market-data-only and reference-only.

## Market Data Expectation

- Live data may be unavailable depending on subscriptions.
- Delayed or delayed_frozen fallback is acceptable for reference-only validation.
- No historical data request is part of this release candidate flow.

## Universe Validation

- GLD/SLV first validation is the preferred IBKR data-path check.
- JP ETF optional validation may include 1540.T and 1542.T.
- CN ETF excluded from IBKR means 518880.SH must not enter the IBKR contract universe.
- China ETF support should use manual, CSV, non-IBKR, or future broker adapter paths.

## Telegram Check

- Run Telegram dry-run before any send-gate test.
- Confirm the message preview has no credentials.
- Run the send gate only with an explicit approval file and explicit send flag.

## Final No-Trade Safety Checklist

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- no automatic order placement
- no account reads
- no position reads
- no funds reads
- manual review required before any external action
