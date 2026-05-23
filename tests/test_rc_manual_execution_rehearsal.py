from pathlib import Path

from src.rc_manual_execution_rehearsal import (
    build_rc_manual_execution_rehearsal_decision,
    evaluate_config_local_only_status,
    evaluate_first_validation_contract_map,
    write_command_preview,
    write_rehearsal_report,
)


def test_default_rehearsal_status_ready():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.rehearsal_status == "RC_REHEARSAL_READY"


def test_blocked_when_required_inputs_missing():
    result = build_rc_manual_execution_rehearsal_decision(required_scripts_ok=False)
    assert result.rehearsal_status == "RC_REHEARSAL_BLOCKED"
    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"


def test_rehearsal_mode_preview_only():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.rehearsal_mode == "dry_run_preview_only"


def test_universe_policy_status_user_watchlist_only():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.universe_policy_status == "USER_WATCHLIST_ONLY"


def test_ibkr_first_validation_universe_gld_slv():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.ibkr_first_validation_universe == "GLD_SLV"


def test_jp_optional_universe():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.jp_optional_universe == "1540_1542_OPTIONAL"


def test_cn_non_ibkr_policy():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.cn_non_ibkr_policy == "518880_EXCLUDED_FROM_IBKR"


def test_ready_for_manual_execution_c_when_inputs_exist():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.readiness_decision == "READY_FOR_MANUAL_EXECUTION_C"
    assert result.first_validation_contract_map_status == "PASS"
    assert result.first_validation_symbols_status == "PASS"
    assert result.ibkr_excluded_symbol_status == "518880_EXCLUDED_FROM_IBKR"


def test_safety_markers_false_and_manual_review_true():
    result = build_rc_manual_execution_rehearsal_decision()
    assert result.action_allowed == "false"
    assert result.broker_execution_triggered == "false"
    assert result.historical_data_request_triggered == "false"
    assert result.account_read_triggered == "false"
    assert result.position_read_triggered == "false"
    assert result.telegram_send_triggered == "false"
    assert result.manual_review_required == "true"


def test_command_preview_contains_execute_market_data_without_running(tmp_path: Path):
    result = build_rc_manual_execution_rehearsal_decision()
    preview = tmp_path / "preview.md"
    write_command_preview(preview, result)
    text = preview.read_text(encoding="utf-8")
    assert "--execute-market-data" in text
    assert "This rehearsal script does not run them" in text
    assert "--contract-map=ibkr_verified_contract_map_gld_slv.csv" in text
    assert result.rehearsal_mode == "dry_run_preview_only"


def test_report_does_not_include_token_chat_id_or_secret(tmp_path: Path):
    result = build_rc_manual_execution_rehearsal_decision()
    report = tmp_path / "report.md"
    write_rehearsal_report(report, result)
    text = report.read_text(encoding="utf-8").lower()
    assert "token" not in text
    assert "chat_id" not in text
    assert "secret" not in text


def test_only_unstaged_modified_config_yaml_passes_local_only_gate():
    result = evaluate_config_local_only_status(
        git_status_short_lines=[" M config.yaml"],
        cached_config_names=[],
        tracked_secret_names=[],
    )

    assert result.ok is True
    assert result.flags == ()


def test_staged_config_yaml_blocks_local_only_gate():
    result = evaluate_config_local_only_status(
        git_status_short_lines=["M  config.yaml"],
        cached_config_names=["config.yaml"],
        tracked_secret_names=[],
    )

    assert result.ok is False
    assert "config_yaml_staged" in result.flags


def test_other_modified_file_blocks_local_only_gate():
    result = evaluate_config_local_only_status(
        git_status_short_lines=[" M config.yaml", " M main.py"],
        cached_config_names=[],
        tracked_secret_names=[],
    )

    assert result.ok is False
    assert "other_worktree_change:main.py" in result.flags


def test_untracked_non_secret_file_blocks_local_only_gate():
    result = evaluate_config_local_only_status(
        git_status_short_lines=[" M config.yaml", "?? notes.txt"],
        cached_config_names=[],
        tracked_secret_names=[],
    )

    assert result.ok is False
    assert "other_worktree_change:notes.txt" in result.flags


def test_tracked_secret_env_or_approval_file_blocks_local_only_gate():
    result = evaluate_config_local_only_status(
        git_status_short_lines=[" M config.yaml"],
        cached_config_names=[],
        tracked_secret_names=["telegram.env.local"],
    )

    assert result.ok is False
    assert "tracked_secret_env_or_approval:telegram.env.local" in result.flags


def test_rehearsal_ready_when_only_unstaged_config_yaml_exists():
    local_only = evaluate_config_local_only_status(
        git_status_short_lines=[" M config.yaml"],
        cached_config_names=[],
        tracked_secret_names=[],
    )
    result = build_rc_manual_execution_rehearsal_decision(
        config_local_only_ok=local_only.ok,
        missing_inputs=local_only.flags,
    )

    assert result.config_local_only_status == "PASS"
    assert result.rehearsal_status == "RC_REHEARSAL_READY"
    assert result.readiness_decision == "READY_FOR_MANUAL_EXECUTION_C"


def write_contract_map(path: Path, symbols: list[str]) -> None:
    header = (
        "run_id,run_timestamp,timezone,branch,commit,workflow,display_symbol,status,symbol,"
        "sec_type,exchange,primary_exchange,currency,conid,local_symbol,trading_class,"
        "data_source_route,market_data_allowed,historical_data_allowed,broker_execution_allowed,"
        "manual_review_required,action_allowed,notes\n"
    )
    rows = []
    for symbol in symbols:
        symbol_value = symbol.split(".", 1)[0] if symbol == "518880.SH" else symbol
        rows.append(
            "r,t,Asia/Tokyo,main,abc,test,{display},MAP_READY,{symbol_value},STK,SMART,ARCA,USD,,,"
            ",SYMBOL_BASED_FIRST_VALIDATION,false,false,false,true,false,symbol-based first validation map; no broker execution.\n".format(
                display=symbol,
                symbol_value=symbol_value,
            )
        )
    path.write_text(header + "".join(rows), encoding="utf-8")


def test_gld_slv_contract_map_present_ready(tmp_path: Path):
    contract_map = tmp_path / "ibkr_verified_contract_map_gld_slv.csv"
    write_contract_map(contract_map, ["GLD", "SLV"])
    check = evaluate_first_validation_contract_map(contract_map)

    result = build_rc_manual_execution_rehearsal_decision(
        contract_map_ok=check.contract_map_exists,
        first_validation_contract_map_ok=check.contract_map_exists,
        first_validation_symbols_ok=check.contains_gld and check.contains_slv,
        ibkr_excluded_symbol_ok=not check.contains_518880,
        missing_inputs=check.flags,
        contract_map=str(contract_map),
    )

    assert check.ok is True
    assert result.readiness_decision == "READY_FOR_MANUAL_EXECUTION_C"


def test_first_validation_map_missing_blocks(tmp_path: Path):
    check = evaluate_first_validation_contract_map(tmp_path / "missing.csv")
    result = build_rc_manual_execution_rehearsal_decision(
        contract_map_ok=check.contract_map_exists,
        first_validation_contract_map_ok=check.contract_map_exists,
        first_validation_symbols_ok=check.contains_gld and check.contains_slv,
        ibkr_excluded_symbol_ok=not check.contains_518880,
        missing_inputs=check.flags,
    )

    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"
    assert result.first_validation_contract_map_status == "BLOCKED_FIRST_VALIDATION_CONTRACT_MAP"


def test_first_validation_map_contains_518880_blocks(tmp_path: Path):
    contract_map = tmp_path / "map.csv"
    write_contract_map(contract_map, ["GLD", "SLV", "518880.SH"])
    check = evaluate_first_validation_contract_map(contract_map)
    result = build_rc_manual_execution_rehearsal_decision(
        ibkr_excluded_symbol_ok=not check.contains_518880,
        missing_inputs=check.flags,
    )

    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"
    assert result.ibkr_excluded_symbol_status == "BLOCKED_518880_PRESENT"


def test_first_validation_map_missing_gld_blocks(tmp_path: Path):
    contract_map = tmp_path / "map.csv"
    write_contract_map(contract_map, ["SLV"])
    check = evaluate_first_validation_contract_map(contract_map)
    result = build_rc_manual_execution_rehearsal_decision(
        first_validation_symbols_ok=check.contains_gld and check.contains_slv,
        missing_inputs=check.flags,
    )

    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"
    assert "first_validation_symbol_missing:GLD" in result.safety_flags


def test_first_validation_map_missing_slv_blocks(tmp_path: Path):
    contract_map = tmp_path / "map.csv"
    write_contract_map(contract_map, ["GLD"])
    check = evaluate_first_validation_contract_map(contract_map)
    result = build_rc_manual_execution_rehearsal_decision(
        first_validation_symbols_ok=check.contains_gld and check.contains_slv,
        missing_inputs=check.flags,
    )

    assert result.readiness_decision == "BLOCKED_BEFORE_MANUAL_EXECUTION_C"
    assert "first_validation_symbol_missing:SLV" in result.safety_flags


def test_old_jp_cn_map_does_not_pass_first_validation_readiness(tmp_path: Path):
    contract_map = tmp_path / "ibkr_verified_contract_map.csv"
    write_contract_map(contract_map, ["1540.T", "1542.T", "518880.SH"])
    check = evaluate_first_validation_contract_map(contract_map)

    assert check.ok is False
    assert check.contains_gld is False
    assert check.contains_slv is False
    assert check.contains_518880 is True
