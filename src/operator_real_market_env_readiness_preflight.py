from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 513-516"
FINAL_DECISION = "NO_GO"
READINESS_STATUS = "REAL_MARKET_ENV_READINESS_PREFLIGHT_READY"
NEXT_PHASE_CANDIDATE = "YES"
NO_TEXT = "NO"
YES_TEXT = "YES"

CSV_FIELDS = (
    "phase",
    "check_id",
    "category",
    "check_name",
    "status",
    "severity",
    "expected",
    "observed",
    "safe_default",
    "external_effect",
    "blocked_capability",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

SAFETY_STATUS_FIELDS = (
    "final_decision",
    "readiness_status",
    "external_connections_attempted",
    "ibkr_connected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
)

SAFETY_STATUS_VALUES = {
    "final_decision": FINAL_DECISION,
    "readiness_status": READINESS_STATUS,
    "external_connections_attempted": NO_TEXT,
    "ibkr_connected": NO_TEXT,
    "market_data_requested": NO_TEXT,
    "account_read_attempted": NO_TEXT,
    "positions_read_attempted": NO_TEXT,
    "historical_data_requested": NO_TEXT,
    "contract_qualification_attempted": NO_TEXT,
    "orders_submitted": NO_TEXT,
    "telegram_real_send_attempted": NO_TEXT,
}

PROHIBITED_ACTIONS = (
    ("RMENV-001", "safety_gate", "No IBKR connection", "IBKR_CONNECT"),
    ("RMENV-002", "safety_gate", "No market data request", "MARKET_DATA_REQUEST"),
    ("RMENV-003", "safety_gate", "No account read", "ACCOUNT_READ"),
    ("RMENV-004", "safety_gate", "No positions read", "POSITIONS_READ"),
    ("RMENV-005", "safety_gate", "No historical data request", "HISTORICAL_DATA_REQUEST"),
    ("RMENV-006", "safety_gate", "No contract qualification", "CONTRACT_QUALIFICATION"),
    ("RMENV-007", "safety_gate", "No orders submitted", "ORDER_SUBMISSION"),
    ("RMENV-008", "safety_gate", "No Telegram real send", "TELEGRAM_REAL_SEND"),
    ("RMENV-009", "safety_gate", "No network probe", "NETWORK_PROBE"),
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_yaml_shape(path: PathLike) -> Dict[str, object]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _load_minimal_yaml_shape(text)
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _load_minimal_yaml_shape(text: str) -> Dict[str, object]:
    data: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            current = line[:-1]
            data.setdefault(current, {})
            continue
        if current and raw_line.startswith("  ") and ":" in line:
            key, value = line.strip().split(":", 1)
            data[current][key] = value.strip()
    return data


def _section(config: Dict[str, object], name: str) -> Dict[str, object]:
    value = config.get(name)
    return value if isinstance(value, dict) else {}


def _present(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def _observed_presence(value: object) -> str:
    return "present_redacted" if _present(value) else "missing"


def _row(
    *,
    check_id: str,
    category: str,
    check_name: str,
    status: str,
    severity: str,
    expected: str,
    observed: str,
    blocked_capability: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "check_id": check_id,
        "category": category,
        "check_name": check_name,
        "status": status,
        "severity": severity,
        "expected": expected,
        "observed": observed,
        "safe_default": YES_TEXT,
        "external_effect": "NONE",
        "blocked_capability": blocked_capability,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_real_market_env_readiness_preflight_rows(
    *,
    config_path: PathLike = "config.yaml",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    config_file = Path(config_path)
    config = _load_yaml_shape(config_file)
    ibkr = _section(config, "ibkr")
    telegram = _section(config, "telegram")
    runtime = _section(config, "runtime")

    rows: List[Dict[str, str]] = []
    for check_id, category, check_name, blocked_capability in PROHIBITED_ACTIONS:
        rows.append(
            _row(
                check_id=check_id,
                category=category,
                check_name=check_name,
                status="PASS",
                severity="CRITICAL",
                expected="capability_blocked_in_this_preflight",
                observed="blocked_no_runtime_call_attempted",
                blocked_capability=blocked_capability,
                evidence="static_preflight_generation_only",
                recommendation="keep_blocked_until_later_explicit_operator_approved_phase",
                timestamp_utc=timestamp,
            )
        )

    config_exists = config_file.exists()
    rows.append(
        _row(
            check_id="RMENV-010",
            category="configuration_readiness",
            check_name="Config file readability",
            status="PASS" if config_exists else "WARN",
            severity="MEDIUM" if config_exists else "HIGH",
            expected="config_file_can_be_read_without_secret_output",
            observed="present_redacted" if config_exists else "missing",
            blocked_capability="CONFIG_SECRET_OUTPUT",
            evidence="config_path_checked_only",
            recommendation="keep_config_yaml_local_and_uncommitted",
            timestamp_utc=timestamp,
        )
    )

    for suffix, key, name in (
        ("011", "host", "IBKR host configured"),
        ("012", "port", "IBKR port configured"),
        ("013", "client_id", "IBKR client id configured"),
    ):
        value = ibkr.get(key)
        rows.append(
            _row(
                check_id=f"RMENV-{suffix}",
                category="configuration_readiness",
                check_name=name,
                status="PASS" if _present(value) else "WARN",
                severity="LOW" if _present(value) else "MEDIUM",
                expected="presence_only_redacted",
                observed=_observed_presence(value),
                blocked_capability="IBKR_CONNECT",
                evidence=f"ibkr.{key}_presence_checked_without_value",
                recommendation="verify_value_manually_before_any_later_real_connection_phase",
                timestamp_utc=timestamp,
            )
        )

    rows.append(
        _row(
            check_id="RMENV-014",
            category="configuration_readiness",
            check_name="Telegram config presence",
            status="PASS" if telegram else "WARN",
            severity="LOW" if telegram else "MEDIUM",
            expected="presence_only_no_token_read_or_output",
            observed="section_present_redacted" if telegram else "section_missing",
            blocked_capability="TELEGRAM_REAL_SEND",
            evidence="telegram_section_shape_checked_without_secret_values",
            recommendation="keep_real_send_disabled_until_explicit_manual_send_phase",
            timestamp_utc=timestamp,
        )
    )

    rows.append(
        _row(
            check_id="RMENV-015",
            category="mode",
            check_name="Preflight mode is artifact-only",
            status="PASS",
            severity="CRITICAL",
            expected="artifact_generation_only",
            observed="csv_and_markdown_only",
            blocked_capability="NETWORK_PROBE",
            evidence="main_cli_branch_does_not_call_ibkr_or_telegram_clients",
            recommendation="do_not_chain_to_real_market_commands",
            timestamp_utc=timestamp,
        )
    )

    rows.append(
        _row(
            check_id="RMENV-016",
            category="freeze_state",
            check_name="Post-MVP freeze state unchanged",
            status="PASS",
            severity="HIGH",
            expected="POST_MVP_MULTI_MARKET_FREEZE_READY_not_rewritten",
            observed="preflight_reports_readiness_only_not_production_ready",
            blocked_capability="PRODUCTION_READY_RECLASSIFICATION",
            evidence="final_decision_NO_GO_next_phase_candidate_only",
            recommendation="do_not_label_this_phase_as_real_market_ready_or_production_ready",
            timestamp_utc=timestamp,
        )
    )

    rows.append(
        _row(
            check_id="RMENV-017",
            category="configuration_readiness",
            check_name="Runtime section presence",
            status="PASS" if runtime else "WARN",
            severity="LOW" if runtime else "MEDIUM",
            expected="runtime_section_presence_only",
            observed="section_present_redacted" if runtime else "section_missing",
            blocked_capability="AUTO_RUNTIME_CHAIN",
            evidence="runtime_section_shape_checked_without_values",
            recommendation="confirm_no_auto_chain_before_later_phase",
            timestamp_utc=timestamp,
        )
    )

    return rows


def write_real_market_env_readiness_preflight_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_real_market_env_readiness_preflight_report(rows: Sequence[Dict[str, str]]) -> str:
    status_lines = [f"- {field}={SAFETY_STATUS_VALUES[field]}" for field in SAFETY_STATUS_FIELDS]
    gate_lines = [
        f"- {row['check_id']} {row['check_name']}: {row['status']} / external_effect={row['external_effect']} / blocked_capability={row['blocked_capability']}"
        for row in rows
        if row["category"] == "safety_gate"
    ]
    config_lines = [
        f"- {row['check_id']} {row['check_name']}: {row['status']} / observed={row['observed']} / evidence={row['evidence']}"
        for row in rows
        if row["category"] in {"configuration_readiness", "mode", "freeze_state"}
    ]
    findings = [row for row in rows if row["status"] != "PASS"]
    finding_lines = [
        f"- {row['check_id']} {row['severity']}: {row['recommendation']}"
        for row in findings
    ] or ["- none"]

    lines = [
        "# Phase 513-516 Real Market Env Readiness Preflight",
        "",
        "## Final Decision",
        "",
        *status_lines,
        f"- next_phase_candidate={NEXT_PHASE_CANDIDATE}",
        "- connection_decision=NO_GO",
        "",
        "## Scope Boundary",
        "",
        "- readiness preflight only",
        "- artifact generation only",
        "- no secret, token, or account id values are written",
        "- POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged and is not reclassified as real-market-ready or production-ready",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- IBKR connection",
        "- market data request",
        "- account read",
        "- positions read",
        "- historical data request",
        "- contract qualification",
        "- order submission",
        "- Telegram real send",
        "- network probe",
        "",
        "## Safety Gates",
        "",
        *gate_lines,
        "",
        "## Configuration Readiness",
        "",
        *config_lines,
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_real_market_env_readiness_preflight.csv",
        "- report=reports/operator_real_market_env_readiness_preflight_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Findings",
        "",
        *finding_lines,
        "",
        "## Residual Risks",
        "",
        "- preflight does not prove IBKR connectivity",
        "- preflight does not prove market data entitlement",
        "- preflight does not prove account, position, historical data, contract qualification, order, or Telegram send behavior",
        "- all real external behavior remains blocked for this phase",
        "",
        "## Next Phase Preconditions",
        "",
        "- explicit operator approval for any later real connection phase",
        "- separate safety gate for any later market data request",
        "- separate approval for any later Telegram real send",
        "- no automatic transition from this NO_GO preflight to production behavior",
    ]
    return "\n".join(lines) + "\n"


def write_real_market_env_readiness_preflight_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_real_market_env_readiness_preflight_report(rows), encoding="utf-8")


def generate_real_market_env_readiness_preflight(
    *,
    config_path: PathLike = "config.yaml",
    output_csv: PathLike = "operator_real_market_env_readiness_preflight.csv",
    output_report: PathLike = "reports/operator_real_market_env_readiness_preflight_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_real_market_env_readiness_preflight_rows(config_path=config_path, generated_at=generated_at)
    write_real_market_env_readiness_preflight_csv(output_csv, rows)
    write_real_market_env_readiness_preflight_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 513-516 real-market environment readiness preflight.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-csv", default="operator_real_market_env_readiness_preflight.csv")
    parser.add_argument("--output-report", default="reports/operator_real_market_env_readiness_preflight_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_real_market_env_readiness_preflight(
        config_path=args.config,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[REAL_MARKET_ENV_READINESS_PREFLIGHT] generated")
    print(f"final_decision={FINAL_DECISION}")
    print(f"readiness_status={READINESS_STATUS}")
    print("external_connections_attempted=NO")
    print("ibkr_connected=NO")
    print("market_data_requested=NO")
    print("account_read_attempted=NO")
    print("positions_read_attempted=NO")
    print("historical_data_requested=NO")
    print("contract_qualification_attempted=NO")
    print("orders_submitted=NO")
    print("telegram_real_send_attempted=NO")
    print(f"next_phase_candidate={NEXT_PHASE_CANDIDATE}")
    print(f"checks={len(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    print("NOTICE: Preflight artifacts only. No IBKR connection, no market data, no account/position/historical-data reads, no contract qualification, no order, no Telegram real send, and no network probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
