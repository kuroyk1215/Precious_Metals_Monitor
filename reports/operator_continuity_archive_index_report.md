# Operator Continuity Archive Index Report

## Continuity

- continuity_status=CONTINUITY_INDEX_READY
- operator_next_step=review_multi_run_continuity

## Sources

- operator_real_marketdata_smoke_summary.csv: exists=true; detected_status=REAL_MARKETDATA_SMOKE_AUDIT_READY; archive_role=marketdata_smoke_source
- operator_real_marketdata_smoke_archive.csv: exists=true; detected_status=REAL_MARKETDATA_SMOKE_AUDIT_READY; archive_role=marketdata_smoke_archive
- operator_real_marketdata_decision_gate.csv: exists=true; detected_status=HOLD_SAFE_FAILURE; archive_role=marketdata_decision_gate
- operator_real_marketdata_latest.csv: exists=true; detected_status=HOLD_SAFE_FAILURE; archive_role=marketdata_latest_pointer
- operator_real_marketdata_daily_run_summary.csv: exists=true; detected_status=HOLD_SAFE_FAILURE; archive_role=daily_marketdata_summary
- operator_real_quote_normalization.csv: exists=true; detected_status=SAFE_UNAVAILABLE; archive_role=quote_normalization
- operator_real_quote_signal_bridge.csv: exists=true; detected_status=SAFE_UNAVAILABLE; archive_role=quote_signal_bridge
- operator_daily_real_market_report.csv: exists=true; detected_status=SAFE_UNAVAILABLE; archive_role=daily_real_market_report
- operator_real_market_mvp_status.csv: exists=true; detected_status=MVP_SAFE_UNAVAILABLE; archive_role=mvp_status
- operator_real_market_archive_compare.csv: exists=true; detected_status=CONSISTENT_OBSERVATION_STATE; archive_role=archive_compare
- operator_signal_threshold_explainer.csv: exists=true; detected_status=SAFE_UNAVAILABLE; archive_role=threshold_explainer
- operator_strategy_quality_report.csv: exists=true; detected_status=MVP_SAFE_UNAVAILABLE; archive_role=strategy_quality
- operator_daily_checklist.csv: exists=true; detected_status=STATUS_NOT_DETECTED; archive_role=daily_checklist
- operator_real_market_mvp_regression.csv: exists=true; detected_status=MVP_SAFE_UNAVAILABLE; archive_role=mvp_regression
- operator_daily_master_run_summary.csv: exists=true; detected_status=MASTER_SAFE_UNAVAILABLE; archive_role=master_run
- reports/operator_daily_master_run_report.md: exists=true; detected_status=MASTER_SAFE_UNAVAILABLE; archive_role=master_run_report
