# Operator MVP Codebase Map

## Safety Banner

- no auto trading
- no account reads
- no position reads
- no historical data requests
- no Telegram real send
- no order/cancel/rebalance

## Module Map

| module | script | source | csv | report | role |
| --- | --- | --- | --- | --- | --- |
| real marketdata smoke | scripts/operator_real_marketdata_smoke.sh | src/operator_real_marketdata_smoke_summary.py | operator_real_marketdata_smoke_summary.csv | reports/operator_real_marketdata_smoke_report.md | read-only real marketdata smoke summary |
| archive | scripts/operator_real_marketdata_smoke_archive.sh | src/operator_real_marketdata_smoke_archive.py | operator_real_marketdata_smoke_archive.csv | reports/operator_real_marketdata_smoke_archive_report.md | archive real marketdata smoke output for continuity |
| decision gate | scripts/operator_real_marketdata_decision_gate.sh | src/operator_real_marketdata_decision_gate.py | operator_real_marketdata_decision_gate.csv | reports/operator_real_marketdata_decision_gate_report.md | classify real marketdata smoke result |
| latest | scripts/operator_real_marketdata_latest.sh | src/operator_real_marketdata_latest.py | operator_real_marketdata_latest.csv | reports/operator_real_marketdata_latest_report.md | select latest real marketdata state |
| daily run | scripts/operator_real_marketdata_daily_run.sh | src/operator_real_marketdata_daily_run.py | operator_real_marketdata_daily_run_summary.csv | reports/operator_real_marketdata_daily_run_report.md | daily real marketdata chain wrapper summary |
| quote normalization | scripts/operator_real_quote_normalization.sh | src/operator_real_quote_normalization.py | operator_real_quote_normalization.csv | reports/operator_real_quote_normalization_report.md | normalize available real quote fields |
| signal bridge | scripts/operator_real_quote_signal_bridge.sh | src/operator_real_quote_signal_bridge.py | operator_real_quote_signal_bridge.csv | reports/operator_real_quote_signal_bridge_report.md | bridge quote availability into reference signals |
| daily real-market report | scripts/operator_daily_real_market_report.sh | src/operator_daily_real_market_report.py | operator_daily_real_market_report.csv | reports/operator_daily_real_market_report.md | daily human-readable real-market report |
| MVP status | scripts/operator_real_market_mvp_status.sh | src/operator_real_market_mvp_status.py | operator_real_market_mvp_status.csv | reports/operator_real_market_mvp_status_report.md | summarize MVP availability and safety |
| checklist | scripts/operator_daily_checklist.sh | src/operator_daily_checklist.py | operator_daily_checklist.csv | reports/operator_daily_checklist.md | fixed manual daily checklist |
| regression | scripts/operator_real_market_mvp_regression_check.sh | src/operator_real_market_mvp_regression.py | operator_real_market_mvp_regression.csv | reports/operator_real_market_mvp_regression_report.md | regression gate for read-only safety |
| strategy quality | scripts/operator_strategy_quality_report.sh | src/operator_strategy_quality_report.py | operator_strategy_quality_report.csv | reports/operator_strategy_quality_report.md | classify strategy quality under available data |
| master run | scripts/operator_daily_master_run.sh | src/operator_daily_master_run.py | operator_daily_master_run_summary.csv | reports/operator_daily_master_run_report.md | main daily operator entrypoint |
| continuity index | scripts/operator_continuity_archive_index.sh | src/operator_continuity_archive_index.py | operator_continuity_archive_index.csv | reports/operator_continuity_archive_index.md | index daily artifacts for handoff |
| readiness report | scripts/operator_mvp_readiness_report.sh | src/operator_mvp_readiness_report.py | operator_mvp_readiness_report.csv | reports/operator_mvp_readiness_report.md | MVP readiness summary |
| GLD/SLV spread | scripts/operator_gld_slv_spread_framework.sh | src/operator_gld_slv_spread_framework.py | operator_gld_slv_spread_framework.csv | reports/operator_gld_slv_spread_framework_report.md | GLD/SLV spread observation framework |
| range framework | scripts/operator_real_market_range_framework.sh | src/operator_real_market_range_framework.py | operator_real_market_range_framework.csv | reports/operator_real_market_range_framework_report.md | range observation framework |
| strategy explanation | scripts/operator_strategy_explanation_upgrade.sh | src/operator_strategy_explanation_upgrade.py | operator_strategy_explanation_upgrade.csv | reports/operator_strategy_explanation_upgrade_report.md | explain current strategy state for humans |
| final daily packet | scripts/operator_final_daily_packet.sh | src/operator_final_daily_packet.py | operator_final_daily_packet.csv | reports/operator_final_daily_packet.md | final daily human observation packet |
| latest strategy decision | scripts/operator_latest_strategy_decision.sh | src/operator_latest_strategy_decision.py | operator_latest_strategy_decision.csv | reports/operator_latest_strategy_decision_report.md | latest strategy state entrypoint |
| completion gate | scripts/operator_real_market_mvp_completion_gate.sh | src/operator_real_market_mvp_completion_gate.py | operator_real_market_mvp_completion_gate.csv | reports/operator_real_market_mvp_completion_gate_report.md | MVP completion state entrypoint |

## Operator Entrypoints

- daily master run is the primary daily command
- final daily packet is the final manual observation packet
- latest strategy decision is the latest strategy status entrypoint
- completion gate is the MVP completion status entrypoint
