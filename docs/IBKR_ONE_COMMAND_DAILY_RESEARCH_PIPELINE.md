# IBKR One-Command Daily Research Pipeline

## Pipeline Chain

Phase 305-320 adds one command around the IBKR market data research chain:

```bash
bash scripts/ibkr_daily_research_pipeline.sh
```

The full chain is:

```text
ibkr_market_data_snapshot.csv
-> ibkr_daily_integration_preflight.csv
-> ibkr_daily_integration_review_pack.csv
-> ibkr_final_research_review_pack.csv
-> ibkr_daily_operator_packet.csv
-> reports/ibkr_daily_operator_packet_report.md
```

The pipeline also writes:

- `ibkr_daily_research_pipeline_summary.csv`
- `reports/ibkr_daily_research_pipeline_report.md`

## Dry-Run Default

Default mode is dry-run, NO_GO, research-only:

```bash
bash scripts/ibkr_daily_research_pipeline.sh
```

Dry-run mode does not connect to IBKR and does not request market data. If the snapshot file is missing, the downstream scripts create NO_GO outputs instead of crashing.

## Execution C

Execution C market data snapshot mode is explicit:

```bash
bash scripts/ibkr_daily_research_pipeline.sh --execute-market-data --market-data-type=auto
```

Only this mode calls:

```bash
scripts/ibkr_market_data_snapshot_oneshot.sh --execute --market-data-type=auto
```

The existing snapshot script still controls the config gate and read-only market data guard. Execution C does not permit trading, account reads, position reads, or historical data requests.

## Why Default Does Not Connect

The daily operator packet is designed for repeatable local research review. Defaulting to dry-run prevents accidental IBKR sessions and allows operators to validate the CSV/report chain even when market data input is absent.

## Delayed And Delayed Frozen

Delayed and delayed_frozen data remain reference-only:

- `delayed_reference` asks the operator to compare with manual market context
- `stale_reference` asks the operator to verify market-open state or latest quote

Neither bucket becomes a real-time signal.

## Operator Packet Fields

`ibkr_daily_operator_packet.csv` includes:

- `operator_packet_status`: ready, blocked, or safety rejected for manual operator review
- `operator_instruction`: manual instruction label such as `manual_review_reference_only`
- `final_research_bucket`: reference bucket from the final research review pack
- `execution_c_mode`: `dry_run` or `execute_market_data`
- `pipeline_stage`: always `operator_packet`
- safety fields: all forced to false except `manual_review_required=true`

## Safety Boundary

Every row and pipeline summary preserves:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`
- `manual_review_required=true`

The operator packet is not a trading plan and does not authorize orders.

## Next Phase

Phase 321-336 can add scheduler support, local daily run wiring, and log rotation around this one-command pipeline. The default should remain dry-run-first unless a later phase explicitly defines a reviewed operator workflow.
