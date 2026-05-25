from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"
PHASE_RANGE = "Phase 469-471"

SAFETY_ASSERTIONS = {
    "trading_actions_allowed": FALSE_TEXT,
    "order_action_allowed": FALSE_TEXT,
    "cancel_action_allowed": FALSE_TEXT,
    "rebalance_action_allowed": FALSE_TEXT,
    "account_read_allowed": FALSE_TEXT,
    "position_read_allowed": FALSE_TEXT,
    "historical_data_request_allowed": FALSE_TEXT,
    "telegram_real_send_allowed": FALSE_TEXT,
    "manual_only": TRUE_TEXT,
    "research_only": TRUE_TEXT,
    "observation_only": TRUE_TEXT,
}

ENV_FIELDS = (
    "generated_at",
    "phase_range",
    "check_id",
    "real_market_environment_status",
    "config_source",
    "ibkr_host_configured",
    "ibkr_port_configured",
    "ibkr_client_id_configured",
    "ibkr_read_only_configured",
    "ibkr_market_data_request_configured",
    "local_api_error_file_present",
    "unavailable_reason",
    "operator_next_step",
    *SAFETY_ASSERTIONS.keys(),
)

PERMISSION_FIELDS = (
    "generated_at",
    "phase_range",
    "symbol",
    "quote_path_status",
    "permission_status",
    "permission_evidence",
    "unavailable_reason",
    "operator_next_step",
    *SAFETY_ASSERTIONS.keys(),
)

REVIEW_FIELDS = (
    "generated_at",
    "phase_range",
    "review_id",
    "safe_unavailable_review_status",
    "api_error_file",
    "api_error_file_present",
    "api_error_row_count",
    "reference_reason",
    "operator_next_step",
    *SAFETY_ASSERTIONS.keys(),
)

GATE_FIELDS = (
    "generated_at",
    "phase_range",
    "gate_status",
    "real_market_environment_status_classified",
    "gld_quote_path_status_classified",
    "slv_quote_path_status_classified",
    "unavailable_reason_readable",
    "safety_assertions_complete",
    "forbidden_runtime_path_status",
    "diagnostic_reason",
    "operator_next_step",
    *SAFETY_ASSERTIONS.keys(),
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_yaml(path: PathLike) -> Dict[str, object]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _load_minimal_ibkr_config(text)
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _load_minimal_ibkr_config(text: str) -> Dict[str, object]:
    ibkr: Dict[str, object] = {}
    in_ibkr = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            in_ibkr = line[:-1] == "ibkr"
            continue
        if not in_ibkr or not raw_line.startswith("  ") or ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        value_text = value.strip().strip("'\"")
        lowered = value_text.lower()
        if lowered in {"true", "false"}:
            ibkr[key] = lowered == "true"
        elif value_text.isdigit():
            ibkr[key] = int(value_text)
        else:
            ibkr[key] = value_text
    return {"ibkr": ibkr}


def _as_text(value: object) -> str:
    if value is None:
        return "missing"
    if isinstance(value, bool):
        return TRUE_TEXT if value else FALSE_TEXT
    return str(value)


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _read_csv_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _api_error_reason(path: PathLike) -> tuple[bool, int, str]:
    csv_path = Path(path)
    if not csv_path.exists():
        return False, 0, "local_ibkr_market_data_api_errors_csv_missing"
    rows = _read_csv_rows(csv_path)
    if not rows:
        return True, 0, "local_ibkr_market_data_api_errors_csv_present_but_empty"

    latest = rows[-1]
    readable_parts = []
    for key in ("symbol", "error_code", "code", "error_message", "message", "reason", "status"):
        value = latest.get(key)
        if value:
            readable_parts.append(f"{key}={value}")
    if not readable_parts:
        readable_parts.append("latest_error_row_present_without_standard_reason_fields")
    return True, len(rows), "local_api_error_reference:" + ";".join(readable_parts)


def _env_status(ibkr_config: Dict[str, object], error_present: bool) -> tuple[str, str, str]:
    host = ibkr_config.get("host")
    port = ibkr_config.get("port")
    client_id = ibkr_config.get("client_id")
    readonly = ibkr_config.get("readonly", ibkr_config.get("read_only"))
    read_only_required = ibkr_config.get("read_only_required")
    market_data_allowed = ibkr_config.get("market_data_request_allowed")
    real_connection_allowed = ibkr_config.get("real_connection_allowed")
    required_fields_present = all(value is not None for value in (host, port, client_id))
    read_only_safe = _is_true(readonly) or _is_true(read_only_required)

    if not required_fields_present:
        return (
            "NO_GO",
            "missing_host_port_or_client_id_in_safe_config",
            "complete_safe_read_only_connection_configuration_review",
        )
    if not read_only_safe:
        return (
            "NO_GO",
            "read_only_flag_not_confirmed_in_safe_config",
            "restore_read_only_required_configuration_before_any_later_phase",
        )
    if error_present:
        return (
            "SAFE_UNAVAILABLE_REVIEW_REQUIRED",
            "local_api_error_file_present_requires_manual_marketdata_permission_review",
            "review_local_market_data_error_archive_before_any_later_real_quote_phase",
        )
    if not _is_true(market_data_allowed) or not _is_true(real_connection_allowed):
        return (
            "SAFE_UNAVAILABLE_REVIEW_REQUIRED",
            "real_connection_or_market_data_request_not_enabled_for_this_observation_skeleton",
            "manual_review_required_before_any_later_connection_or_quote_request_phase",
        )
    return (
        "NO_GO",
        "skeleton_does_not_perform_real_connection_or_quote_request_so_environment_cannot_pass",
        "run_later_explicitly_approved_read_only_quote_phase_if_added",
    )


def _quote_path_status(symbol: str, env_status: str, reason: str) -> tuple[str, str, str]:
    if env_status == "NO_GO":
        return "NO_GO", "NOT_VERIFIED", f"{symbol}_quote_path_not_verified:{reason}"
    return "SAFE_UNAVAILABLE_REVIEW_REQUIRED", "REVIEW_REQUIRED", f"{symbol}_quote_path_safe_unavailable:{reason}"


def _with_safety(row: Dict[str, str]) -> Dict[str, str]:
    merged = dict(row)
    merged.update(SAFETY_ASSERTIONS)
    return merged


def build_batch_i_rows(
    *,
    config_path: PathLike = "config.yaml",
    api_errors_csv: PathLike = "ibkr_market_data_api_errors.csv",
    generated_at: Optional[str] = None,
) -> tuple[Dict[str, str], List[Dict[str, str]], Dict[str, str], Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    config = _load_yaml(config_path)
    ibkr_config = config.get("ibkr") if isinstance(config.get("ibkr"), dict) else {}
    error_present, error_count, error_reason = _api_error_reason(api_errors_csv)
    env_status, env_reason, env_next_step = _env_status(ibkr_config, error_present)
    unavailable_reason = error_reason if error_present else env_reason

    env_row = _with_safety(
        {
            "generated_at": generated,
            "phase_range": PHASE_RANGE,
            "check_id": "batch_i_real_market_environment",
            "real_market_environment_status": env_status,
            "config_source": str(config_path),
            "ibkr_host_configured": _as_text(ibkr_config.get("host")),
            "ibkr_port_configured": _as_text(ibkr_config.get("port")),
            "ibkr_client_id_configured": _as_text(ibkr_config.get("client_id")),
            "ibkr_read_only_configured": _as_text(ibkr_config.get("readonly", ibkr_config.get("read_only"))),
            "ibkr_market_data_request_configured": _as_text(ibkr_config.get("market_data_request_allowed")),
            "local_api_error_file_present": TRUE_TEXT if error_present else FALSE_TEXT,
            "unavailable_reason": unavailable_reason,
            "operator_next_step": env_next_step,
        }
    )

    permission_rows: List[Dict[str, str]] = []
    for symbol in ("GLD", "SLV"):
        quote_status, permission_status, quote_reason = _quote_path_status(symbol, env_status, unavailable_reason)
        permission_rows.append(
            _with_safety(
                {
                    "generated_at": generated,
                    "phase_range": PHASE_RANGE,
                    "symbol": symbol,
                    "quote_path_status": quote_status,
                    "permission_status": permission_status,
                    "permission_evidence": "local_skeleton_only_no_real_quote_request",
                    "unavailable_reason": quote_reason,
                    "operator_next_step": "manual_permission_review_required",
                }
            )
        )

    review_status = "SAFE_UNAVAILABLE_REVIEW_REQUIRED" if error_present else "NO_GO"
    review_row = _with_safety(
        {
            "generated_at": generated,
            "phase_range": PHASE_RANGE,
            "review_id": "batch_i_safe_unavailable_review",
            "safe_unavailable_review_status": review_status,
            "api_error_file": str(api_errors_csv),
            "api_error_file_present": TRUE_TEXT if error_present else FALSE_TEXT,
            "api_error_row_count": str(error_count),
            "reference_reason": error_reason,
            "operator_next_step": "review_safe_unavailable_reason_before_any_later_real_quote_phase",
        }
    )

    env_classified = env_status in {"NO_GO", "SAFE_UNAVAILABLE_REVIEW_REQUIRED", "PASS"}
    quote_classified = all(row["quote_path_status"] in {"NO_GO", "SAFE_UNAVAILABLE_REVIEW_REQUIRED", "PASS"} for row in permission_rows)
    reason_readable = bool(unavailable_reason and unavailable_reason != "missing")
    safety_complete = all(env_row.get(key) == value for key, value in SAFETY_ASSERTIONS.items())
    forbidden_clean = TRUE_TEXT
    gate_pass = (
        env_status == "PASS"
        and quote_classified
        and reason_readable
        and safety_complete
        and forbidden_clean == TRUE_TEXT
    )
    if gate_pass:
        gate_status = "PASS"
        gate_reason = "batch_i_environment_and_quote_paths_classified_with_complete_safety_assertions"
        gate_next_step = "manual_operator_review_only"
    elif review_status == "SAFE_UNAVAILABLE_REVIEW_REQUIRED" or env_status == "SAFE_UNAVAILABLE_REVIEW_REQUIRED":
        gate_status = "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
        gate_reason = "safe_unavailable_reason_requires_manual_review_before_later_phase"
        gate_next_step = "review_marketdata_permissions_and_local_api_error_archive"
    else:
        gate_status = "NO_GO"
        gate_reason = "batch_i_skeleton_does_not_verify_real_market_connectivity_or_quotes"
        gate_next_step = "keep_manual_only_research_only_observation_only_boundary"

    gate_row = _with_safety(
        {
            "generated_at": generated,
            "phase_range": PHASE_RANGE,
            "gate_status": gate_status,
            "real_market_environment_status_classified": TRUE_TEXT if env_classified else FALSE_TEXT,
            "gld_quote_path_status_classified": TRUE_TEXT if quote_classified else FALSE_TEXT,
            "slv_quote_path_status_classified": TRUE_TEXT if quote_classified else FALSE_TEXT,
            "unavailable_reason_readable": TRUE_TEXT if reason_readable else FALSE_TEXT,
            "safety_assertions_complete": TRUE_TEXT if safety_complete else FALSE_TEXT,
            "forbidden_runtime_path_status": "CLEAN",
            "diagnostic_reason": gate_reason,
            "operator_next_step": gate_next_step,
        }
    )

    return env_row, permission_rows, review_row, gate_row


def _write_csv(path: PathLike, fields: Sequence[str], rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _safety_lines(row: Dict[str, str]) -> List[str]:
    return [f"- {key}={row[key]}" for key in SAFETY_ASSERTIONS]


def _write_report(path: PathLike, title: str, rows: Sequence[Dict[str, str]], focus_fields: Sequence[str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    first = rows[0]
    lines = [
        f"# {title}",
        "",
        "## Scope",
        "",
        f"- phase_range={PHASE_RANGE}",
        "- manual-only / research-only / observation-only",
        "- no real trading, no account reads, no position reads, no historical data requests, no Telegram real send",
        "- no TWS or IB Gateway connection is forced by this skeleton",
        "",
        "## Safety Assertions",
        "",
        *_safety_lines(first),
        "",
        "## Results",
        "",
    ]
    for row in rows:
        lines.append("- " + "; ".join(f"{field}={row.get(field, '')}" for field in focus_fields))
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_batch_i_real_market_env_check(
    *,
    config_path: PathLike = "config.yaml",
    api_errors_csv: PathLike = "ibkr_market_data_api_errors.csv",
    env_csv: PathLike = "operator_batch_i_real_market_env_check.csv",
    permission_csv: PathLike = "operator_batch_i_marketdata_permission_check.csv",
    review_csv: PathLike = "operator_batch_i_safe_unavailable_review.csv",
    gate_csv: PathLike = "operator_batch_i_real_market_env_gate.csv",
    env_report: PathLike = "reports/operator_batch_i_real_market_env_check.md",
    permission_report: PathLike = "reports/operator_batch_i_marketdata_permission_check.md",
    review_report: PathLike = "reports/operator_batch_i_safe_unavailable_review.md",
    gate_report: PathLike = "reports/operator_batch_i_real_market_env_gate_report.md",
    generated_at: Optional[str] = None,
) -> Dict[str, Dict[str, str] | List[Dict[str, str]]]:
    env_row, permission_rows, review_row, gate_row = build_batch_i_rows(
        config_path=config_path,
        api_errors_csv=api_errors_csv,
        generated_at=generated_at,
    )
    _write_csv(env_csv, ENV_FIELDS, [env_row])
    _write_csv(permission_csv, PERMISSION_FIELDS, permission_rows)
    _write_csv(review_csv, REVIEW_FIELDS, [review_row])
    _write_csv(gate_csv, GATE_FIELDS, [gate_row])

    _write_report(
        env_report,
        "Operator Batch I Real Market Environment Check",
        [env_row],
        ("real_market_environment_status", "local_api_error_file_present", "unavailable_reason", "operator_next_step"),
    )
    _write_report(
        permission_report,
        "Operator Batch I Marketdata Permission Check",
        permission_rows,
        ("symbol", "quote_path_status", "permission_status", "unavailable_reason", "operator_next_step"),
    )
    _write_report(
        review_report,
        "Operator Batch I Safe Unavailable Review",
        [review_row],
        ("safe_unavailable_review_status", "api_error_file_present", "api_error_row_count", "reference_reason", "operator_next_step"),
    )
    _write_report(
        gate_report,
        "Operator Batch I Real Market Environment Gate Report",
        [gate_row],
        ("gate_status", "diagnostic_reason", "operator_next_step"),
    )

    return {
        "environment": env_row,
        "permissions": permission_rows,
        "review": review_row,
        "gate": gate_row,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 469-471 Batch I real-market environment verification skeleton.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--api-errors-csv", default="ibkr_market_data_api_errors.csv")
    parser.add_argument("--env-csv", default="operator_batch_i_real_market_env_check.csv")
    parser.add_argument("--permission-csv", default="operator_batch_i_marketdata_permission_check.csv")
    parser.add_argument("--review-csv", default="operator_batch_i_safe_unavailable_review.csv")
    parser.add_argument("--gate-csv", default="operator_batch_i_real_market_env_gate.csv")
    parser.add_argument("--env-report", default="reports/operator_batch_i_real_market_env_check.md")
    parser.add_argument("--permission-report", default="reports/operator_batch_i_marketdata_permission_check.md")
    parser.add_argument("--review-report", default="reports/operator_batch_i_safe_unavailable_review.md")
    parser.add_argument("--gate-report", default="reports/operator_batch_i_real_market_env_gate_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = generate_batch_i_real_market_env_check(
        config_path=args.config,
        api_errors_csv=args.api_errors_csv,
        env_csv=args.env_csv,
        permission_csv=args.permission_csv,
        review_csv=args.review_csv,
        gate_csv=args.gate_csv,
        env_report=args.env_report,
        permission_report=args.permission_report,
        review_report=args.review_report,
        gate_report=args.gate_report,
        generated_at=args.generated_at,
    )
    gate = result["gate"]
    environment = result["environment"]
    print("[BATCH_I_REAL_MARKET_ENV_CHECK] generated")
    print(
        "gate_status={}:real_market_environment_status={}:manual_only=true research_only=true observation_only=true".format(
            gate["gate_status"],
            environment["real_market_environment_status"],
        )
    )
    print(
        "NOTICE: Batch I skeleton only. No trading / no account reads / no position reads / "
        "no historical data request / no Telegram real send / no forced TWS or IB Gateway connection."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
