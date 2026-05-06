# Manual CSV Market Data Operator Runbook

## Scope

This runbook describes the manual CSV workflow for the precious metals research pipeline.

This workflow is for research artifacts only. It does not generate execution instructions.

## Safety Boundary

The manual CSV workflow must preserve all of the following:

- manual CSV only
- explicit manual trigger only
- action_allowed=false
- no IBKR connection
- no reqMktData
- no reqHistoricalData
- no order
- no cancel
- no rebalance
- no auto trade
- no automatic execution

Any future change that violates these boundaries must be rejected.

## Input Files

Template input:

data/manual_market_data_template.csv

Filled scenario input:

data/manual_market_data_sample_valid.csv

Required columns:

target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes

## Supported Targets

| target_id | role |
|---|---|
| XAUUSD | gold spot USD/oz |
| XAGUSD | silver spot USD/oz |
| USDJPY | FX rate |
| USDCNY | FX rate |
| SGE_AU99_99 | Shanghai gold benchmark |
| 1540.T | JP gold ETF actual price |
| 1542.T | JP silver ETF actual price |
| 518880.SH | CN gold ETF actual price |

## Basic Commands

Validate and normalize manual CSV:

python main.py --config config.yaml --manual-market-data-adapter data/manual_market_data_template.csv

Integrate manual market data snapshot:

python main.py --config config.yaml --integrate-manual-market-data manual_market_data_snapshot.csv

Run manual CSV end-to-end research pipeline:

python main.py --config config.yaml --manual-market-data-pipeline data/manual_market_data_template.csv

Run filled sample scenario:

python main.py --config config.yaml --manual-market-data-pipeline data/manual_market_data_sample_valid.csv

Validate filled sample scenario:

python main.py --config config.yaml --validate-filled-manual-scenario data/manual_market_data_sample_valid.csv

Expected output:

[FILLED_MANUAL_SCENARIO] checks=8 statuses=pass action_allowed=false

## Full Manual CSV Chain

manual input CSV
-> manual_market_data_snapshot.csv
-> manual_upstream_factor_snapshot.csv
-> manual_actual_etf_price_snapshot.csv
-> theoretical_price_snapshot.csv
-> deviation_snapshot.csv
-> reference_signal_snapshot.csv
-> daily_trade_plan_snapshot.csv
-> multi_horizon_strategy_snapshot.csv
-> manual_market_data_pipeline_summary.csv

## Output Interpretation

Adapter status:

| status | meaning |
|---|---|
| ok | Manual row exists and value is positive numeric |
| unavailable | Manual row exists but value or source_timestamp is invalid |
| invalid | Required header or key field is invalid |

Integration status:

| status | meaning |
|---|---|
| ok | Manual target can be converted into pipeline-compatible snapshot |
| unavailable | Missing or invalid manual target |
| partial | Mixed available and unavailable rows |

Scenario validation status:

| status | meaning |
|---|---|
| pass | Check passed |
| fail | Check failed and needs review |

## Common Failure Checks

If adapter report shows missing_required_fields, check the input CSV schema:

target_id,target_type,market,data_role,value,currency,source,source_status,source_timestamp,notes

If theoretical pricing stays unavailable, check these targets:

XAUUSD
XAGUSD
USDJPY
USDCNY
SGE_AU99_99

If ETF actual price is unavailable, check these targets:

1540.T
1542.T
518880.SH

If risk_off appears in the filled scenario, inspect:

deviation_snapshot.csv
reference_signal_snapshot.csv
reports/deviation_report.md
reports/reference_signal_report.md

Likely causes:

- invalid input price
- currency mismatch
- extreme deviation
- missing source_timestamp
- unavailable theoretical price

## Recommended Operator Sequence

Offline validation:

python3 -m py_compile main.py src/*.py
PYTHONPATH=. pytest -q
python main.py --config config.yaml --validate-filled-manual-scenario data/manual_market_data_sample_valid.csv

Manual CSV research:

python main.py --config config.yaml --manual-market-data-pipeline path/to/your_manual_market_data.csv

Then inspect:

reports/manual_market_data_pipeline_report.md
reports/filled_manual_scenario_validation_report.md

## Files That Should Usually Not Be Committed

manual_market_data_snapshot.csv
manual_upstream_factor_snapshot.csv
manual_actual_etf_price_snapshot.csv
manual_market_data_integration_summary.csv
manual_market_data_pipeline_summary.csv
filled_manual_scenario_validation.csv
theoretical_price_snapshot.csv
deviation_snapshot.csv
reference_signal_snapshot.csv
daily_trade_plan_snapshot.csv
multi_horizon_strategy_snapshot.csv
reports/*_report.md generated during local runs

## Static Files That May Be Committed

data/manual_market_data_template.csv
data/manual_market_data_sample_valid.csv
docs/manual_csv_operator_runbook.md

## Final Guardrail

The output of this system is not an execution instruction.

It is a manual research pipeline that compares:

ETF actual price
vs
ETF theoretical price
vs
manual upstream factors

Any real transaction decision must remain outside the code path.
