# IBKR Execution C Real Delayed/Frozen Validation

## Purpose

Phase 369-384 adds an Execution C validation packet for the IBKR daily research pipeline. It gives the operator a controlled way to validate real delayed or delayed_frozen market data behavior later, while keeping the default command dry-run only.

## Default Dry-Run

The default command does not connect to IBKR, does not request market data, does not send Telegram, and does not access external networks.

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh
```

Default output:

- `ibkr_execution_c_validation_packet.csv`
- `reports/ibkr_execution_c_validation_report.md`
- `execution_c_status=EXECUTION_C_DRY_RUN_READY`
- `validation_decision=NO_GO`

## Manual Real Execution C Command

Only run real Execution C manually after confirming local IBKR/TWS readiness:

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh --execute-market-data --market-data-type=auto --telegram-dry-run
```

This forwards the explicit market data execution request to the local daily runner. It still keeps Telegram in dry-run mode.

## Telegram Send Boundary

Do not use `--telegram-send` for first validation. Only use it after the Phase 353-368 send gate has already been reviewed with local approval and environment variables.

Telegram delivery is notification transport only. It is not trading authorization.

## Checking The Validation Packet

Open `ibkr_execution_c_validation_packet.csv` and inspect:

- `execution_c_status`
- `execution_c_mode`
- `market_data_execution_requested`
- `snapshot_status`
- `effective_market_data_type`
- `data_delay_flag`
- `validation_decision`
- `validation_reason`
- `action_allowed`

`action_allowed` must remain `false`.

## Delayed And Delayed Frozen

`delayed` and `delayed_frozen` results are classified as `REVIEW_READY_REFERENCE_ONLY`. They are not real-time data and must only be used for manual reference review.

If the snapshot is missing, unsupported, or has no usable price, the validation decision is `REVIEW_BLOCKED`.

## First Real GLD/SLV Result Pattern

For the first real GLD/SLV Execution C validation, a successful delayed fallback can look like:

- `execution_c_status=EXECUTION_C_VALIDATION_READY`
- `validation_decision=REVIEW_READY_REFERENCE_ONLY`
- `snapshot_status=DELAYED_SNAPSHOT_RETURNED`
- `effective_market_data_type=delayed`
- `data_delay_flag=delayed`
- `action_allowed=false`

IBKR Error 10089 and Error 354 can both indicate a recognizable live market data not subscribed / delayed market data available scenario when delayed data is offered. Error 10089 is visible on US ETF validation symbols such as GLD and SLV. Error 354 is visible on some venues or instruments. This is not a real-time entitlement and must remain reference-only.

Post-run analysis should be generated from existing local outputs only:

```bash
bash scripts/first_operator_run_post_analysis.sh
```

This post-run step must not connect to IBKR, request market data, send Telegram, read accounts, read positions, request historical data, or run the Execution C validation command again.

Post-run analysis normalizes reference-ready counts by `display_symbol`, so duplicate GLD or SLV rows across snapshot and operator packets are not added twice. A GLD/SLV delayed run should report `delayed_reference_count=2` when both symbols have delayed reference rows.

If the terminal shows Error 10089 or Error 354 but `ibkr_market_data_snapshot.csv` does not contain the error code or delayed-available message, check that the local error capture version is current before interpreting `live_subscription_status`.

## NO_GO vs REVIEW_READY

`NO_GO` is not equivalent to chain failure. In this project, global `NO_GO` means `action_allowed=false` and no trade. Row-level `OPERATOR_REVIEW_READY` means the operator can inspect delayed or delayed_frozen reference-only results. Delayed reference-only prices cannot trigger trades.

After a live test, optionally turn the local config gate back off:

```yaml
real_connection_allowed: false
market_data_request_allowed: false
```

## Safety Boundary

Execution C validation never authorizes:

- broker execution
- historical data requests
- account reads
- position reads
- trading actions

The validation packet always writes:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`

## Failure Recovery

If a real validation run fails, return to the dry-run command:

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh
```

Review the local runner report, pipeline summary, market data snapshot report, and Execution C validation report before attempting another explicit run.

## Next Phase Handoff

Phase 385-400 may cover release hardening, a full safety audit, and the operator manual.
