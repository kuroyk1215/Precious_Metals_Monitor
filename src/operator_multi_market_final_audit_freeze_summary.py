from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


FALSE_TEXT = "false"
TRUE_TEXT = "true"

READY_STATUS = "POST_MVP_MULTI_MARKET_FREEZE_READY"
REVIEW_STATUS = "POST_MVP_MULTI_MARKET_FREEZE_REVIEW_REQUIRED"
NO_GO_STATUS = "POST_MVP_MULTI_MARKET_FREEZE_NO_GO"

FINAL_STATE_DEFINITION = (
    "manual-only / research-only / observation-only post-MVP multi-market freeze; "
    "not live production; not real market data verified; no automated trading, "
    "account reads, position reads, historical data requests, contract qualification, "
    "or Telegram real send"
)

AUDIT_FIELDS = (
    "generated_at",
    "final_audit_status",
    "batch_i_status",
    "batch_j_status",
    "batch_k_dashboard_status",
    "batch_l_telegram_status",
    "batch_m_schema_status",
    "batch_m_adapter_status",
    "final_packet_status",
    "dashboard_status",
    "telegram_dry_run_status",
    "telegram_manual_archive_status",
    "multi_market_schema_gate_status",
    "multi_market_adapter_gate_status",
    "real_market_data_verified",
    "live_production_ready",
    "strategy_execution_ready",
    "auto_trade_allowed",
    "telegram_real_send_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "manual_only",
    "research_only",
    "observation_only",
    "diagnostic_reason",
)

REQUIRED_ARTIFACTS = (
    "operator_batch_i_final_integration_audit_gate.csv",
    "operator_batch_j_final_integration_audit_gate.csv",
    "operator_dashboard_artifact_reader.csv",
    "operator_telegram_dry_run_payload.csv",
    "operator_telegram_approval_gate.csv",
    "operator_telegram_manual_send_archive.csv",
    "operator_multi_market_symbol_schema_gate.csv",
    "operator_multi_market_adapter_gate.csv",
    "operator_final_daily_packet.csv",
    "reports/operator_final_daily_packet.md",
    "reports/operator_dashboard_artifact_reader.md",
    "reports/operator_telegram_manual_send_archive_report.md",
    "reports/operator_multi_market_adapter_gate_report.md",
)

SAFETY_FALSE_FIELDS = (
    "real_market_data_verified",
    "live_production_ready",
    "strategy_execution_ready",
    "auto_trade_allowed",
    "telegram_real_send_allowed",
    "account_read_allowed",
    "position_read_allowed",
    "historical_data_request_allowed",
    "trading_actions_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "real_market_data_request_allowed",
    "contract_qualification_allowed",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latest(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _is_false(value: object) -> bool:
    return str(value or "").strip().lower() in {"", "false", "0", "no"}


def _any_true(rows: Sequence[Dict[str, str]], field: str) -> bool:
    return any(field in row and _is_true(row.get(field)) for row in rows)


def _any_allowed(rows: Sequence[Dict[str, str]], field: str) -> str:
    return TRUE_TEXT if any(field in row and not _is_false(row.get(field)) for row in rows) else FALSE_TEXT


def _all_marker_true(rows: Sequence[Dict[str, str]], field: str) -> str:
    matching = [row for row in rows if field in row]
    return TRUE_TEXT if matching and all(_is_true(row.get(field)) for row in matching) else FALSE_TEXT


def _git_commit(base_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(base_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "unknown"


def build_multi_market_final_audit_row(
    *,
    base_dir: PathLike = ".",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    base = Path(base_dir)
    missing = [name for name in REQUIRED_ARTIFACTS if not (base / name).exists()]

    batch_i = _latest(base / "operator_batch_i_final_integration_audit_gate.csv")
    batch_j = _latest(base / "operator_batch_j_final_integration_audit_gate.csv")
    dashboard = _latest(base / "operator_dashboard_artifact_reader.csv")
    telegram_payload = _latest(base / "operator_telegram_dry_run_payload.csv")
    telegram_approval = _latest(base / "operator_telegram_approval_gate.csv")
    telegram_archive = _latest(base / "operator_telegram_manual_send_archive.csv")
    schema_gate = _latest(base / "operator_multi_market_symbol_schema_gate.csv")
    adapter_gate = _latest(base / "operator_multi_market_adapter_gate.csv")
    final_packet = _latest(base / "operator_final_daily_packet.csv")
    rows = [
        row
        for row in (
            batch_i,
            batch_j,
            dashboard,
            telegram_payload,
            telegram_approval,
            telegram_archive,
            schema_gate,
            adapter_gate,
            final_packet,
        )
        if row
    ]

    batch_l_ready = (
        telegram_payload.get("telegram_payload_status") == "TELEGRAM_DRY_RUN_READY"
        and telegram_approval.get("approval_gate_status") == "TELEGRAM_APPROVAL_REVIEW_REQUIRED"
        and telegram_archive.get("manual_send_archive_status") == "TELEGRAM_MANUAL_SEND_ARCHIVE_READY"
    )
    safety_no_go = _any_true(rows, "live_production_ready") or _any_true(rows, "auto_trade_allowed")
    safety_fields_clean = all(not _any_true(rows, field) for field in SAFETY_FALSE_FIELDS)
    mode_markers_clean = all(_all_marker_true(rows, field) == TRUE_TEXT for field in ("manual_only", "research_only", "observation_only"))
    gate_statuses_present = all(
        (
            batch_i.get("audit_gate_status"),
            batch_j.get("audit_gate_status"),
            dashboard.get("dashboard_status"),
            telegram_payload.get("telegram_payload_status"),
            telegram_archive.get("manual_send_archive_status"),
            schema_gate.get("schema_gate_status"),
            adapter_gate.get("adapter_gate_status"),
            final_packet.get("final_packet_status"),
        )
    )

    if safety_no_go:
        status = NO_GO_STATUS
        reason = "live_production_ready_or_auto_trade_allowed_detected"
    elif missing:
        status = REVIEW_STATUS
        reason = "missing_required_artifacts:" + ",".join(missing)
    elif not gate_statuses_present:
        status = REVIEW_STATUS
        reason = "one_or_more_gate_statuses_unreadable"
    elif not batch_l_ready:
        status = REVIEW_STATUS
        reason = "telegram_dry_run_approval_manual_archive_chain_not_ready"
    elif not safety_fields_clean or not mode_markers_clean:
        status = REVIEW_STATUS
        reason = "safety_boundaries_or_manual_research_observation_markers_inconsistent"
    else:
        status = READY_STATUS
        reason = "all_required_post_mvp_multi_market_artifacts_present_safety_boundaries_false_manual_research_observation_only"

    return {
        "generated_at": generated_at or _now_timestamp(),
        "final_audit_status": status,
        "batch_i_status": batch_i.get("audit_gate_status", "MISSING"),
        "batch_j_status": batch_j.get("audit_gate_status", "MISSING"),
        "batch_k_dashboard_status": dashboard.get("dashboard_status", "MISSING"),
        "batch_l_telegram_status": "TELEGRAM_DRY_RUN_APPROVAL_ARCHIVE_READY" if batch_l_ready else "TELEGRAM_CHAIN_REVIEW_REQUIRED",
        "batch_m_schema_status": schema_gate.get("schema_gate_status", "MISSING"),
        "batch_m_adapter_status": adapter_gate.get("adapter_gate_status", "MISSING"),
        "final_packet_status": final_packet.get("final_packet_status", "MISSING"),
        "dashboard_status": dashboard.get("dashboard_status", "MISSING"),
        "telegram_dry_run_status": telegram_payload.get("telegram_payload_status", "MISSING"),
        "telegram_manual_archive_status": telegram_archive.get("manual_send_archive_status", "MISSING"),
        "multi_market_schema_gate_status": schema_gate.get("schema_gate_status", "MISSING"),
        "multi_market_adapter_gate_status": adapter_gate.get("adapter_gate_status", "MISSING"),
        "real_market_data_verified": _any_allowed(rows, "real_market_data_verified"),
        "live_production_ready": _any_allowed(rows, "live_production_ready"),
        "strategy_execution_ready": _any_allowed(rows, "strategy_execution_ready"),
        "auto_trade_allowed": _any_allowed(rows, "auto_trade_allowed"),
        "telegram_real_send_allowed": _any_allowed(rows, "telegram_real_send_allowed"),
        "account_read_allowed": _any_allowed(rows, "account_read_allowed"),
        "position_read_allowed": _any_allowed(rows, "position_read_allowed"),
        "historical_data_request_allowed": _any_allowed(rows, "historical_data_request_allowed"),
        "trading_actions_allowed": _any_allowed(rows, "trading_actions_allowed"),
        "manual_only": _all_marker_true(rows, "manual_only"),
        "research_only": _all_marker_true(rows, "research_only"),
        "observation_only": _all_marker_true(rows, "observation_only"),
        "diagnostic_reason": reason,
    }


def write_audit_csv(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(AUDIT_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def build_audit_markdown(row: Dict[str, str]) -> str:
    lines = [
        "# Operator Multi-Market Final Audit Gate Report",
        "",
        "## Scope",
        "",
        "- final audit / freeze summary for Phase 468-512",
        "- manual-only / research-only / observation-only",
        "- not live production",
        "- not real market data verified",
        "- no automatic trading, account read, position read, historical data request, contract qualification, or Telegram real send",
        "",
        "## Final Audit",
        "",
    ]
    lines.extend(f"- {field}={row[field]}" for field in AUDIT_FIELDS)
    lines.extend(
        [
            "",
            "## Current Final State Definition",
            "",
            FINAL_STATE_DEFINITION,
        ]
    )
    return "\n".join(lines) + "\n"


def write_audit_markdown(path: PathLike, row: Dict[str, str]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_audit_markdown(row), encoding="utf-8")


def build_freeze_summary_markdown(row: Dict[str, str], *, current_commit: str) -> str:
    return "\n".join(
        [
            "# Precious_Metals_Monitor Phase 468-512 Post-MVP Multi-Market Freeze Summary",
            "",
            "## Current Main State",
            "",
            "- Repository: Precious_Metals_Monitor",
            "- Branch: main",
            f"- Current main commit: {current_commit}",
            f"- final_audit_status={row['final_audit_status']}",
            f"- Current final state definition: {FINAL_STATE_DEFINITION}",
            "",
            "## PR #185-#195 Overview",
            "",
            "| PR | Batch / Phase | Summary |",
            "|---|---|---|",
            "| PR #185 | Batch I / Phase 468-471 | real market data environment validation skeleton |",
            "| PR #186 | Batch I / Phase 472-474 | safe unavailable review and permission evidence bridge |",
            "| PR #187 | Batch I / Phase 475-477 | final integration audit gate |",
            "| PR #188 | Batch J / Phase 478-481 | strategy threshold framework |",
            "| PR #189 | Batch J / Phase 482-485 | final packet / audit integration |",
            "| PR #190 | Batch K / Phase 486-489 | dashboard artifact reader |",
            "| PR #191 | Batch L / Phase 490-493 | Telegram dry-run payload and approval gate |",
            "| PR #192 | Batch L / Phase 494-497 | Telegram manual-send archive skeleton |",
            "| PR #193 | Batch M / Phase 498-502 | JP / CN / US symbol universe schema |",
            "| PR #194 | Batch M / Phase 503-508 | multi-market adapter skeleton |",
            "| PR #195 | Phase 509-512 | final audit and freeze summary |",
            "",
            "## Batch Completion Summary",
            "",
            f"- Batch I: real行情环境验证闭环 evidence is closed as {row['batch_i_status']}; it remains not real market data verified.",
            f"- Batch J: strategy threshold framework and final packet / audit bridge are closed as {row['batch_j_status']}; strategy_execution_ready=false.",
            f"- Batch K: dashboard artifact reader is {row['batch_k_dashboard_status']}; it is local artifact reading only, with no UI frontend.",
            f"- Batch L: Telegram dry-run / approval / manual archive chain is {row['batch_l_telegram_status']}; telegram_real_send_allowed=false.",
            f"- Batch M: JP / CN / US schema is {row['batch_m_schema_status']} and adapter skeleton is {row['batch_m_adapter_status']}; no live adapter validation has been performed.",
            "",
            "## Why This Is Not Live Production",
            "",
            "- not live production",
            "- real_market_data_verified=false",
            "- live_production_ready=false",
            "- strategy_execution_ready=false",
            "- multi-market live adapter validation has not been run",
            "- Telegram remains dry-run / manual archive only",
            "- dashboard UI frontend is not implemented in this phase",
            "",
            "## Safety Boundaries",
            "",
            "- auto_trade_allowed=false",
            "- account_read_allowed=false",
            "- position_read_allowed=false",
            "- historical_data_request_allowed=false",
            "- telegram_real_send_allowed=false",
            "- trading_actions_allowed=false",
            "- IBKR contract qualification is not allowed in this phase",
            "- manual-only",
            "- research-only",
            "- observation-only",
            "",
            "## Still Not Performed",
            "",
            "- automatic trading",
            "- account reads",
            "- position reads",
            "- historical data requests",
            "- Telegram real sending",
            "- IBKR contract qualification",
            "- IBKR / TWS / Gateway connection",
            "- real quote requests",
            "- order, cancel, or rebalance actions",
            "",
            "## Next Phase Options",
            "",
            "- Real market data environment validation",
            "- dashboard UI frontend",
            "- Telegram manual-send implementation with explicit user approval",
            "- multi-market live adapter validation",
            "",
            "These next items are not implemented in Phase 509-512.",
        ]
    ) + "\n"


def write_freeze_summary(path: PathLike, row: Dict[str, str], *, base_dir: PathLike = ".") -> None:
    base = Path(base_dir)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_freeze_summary_markdown(row, current_commit=_git_commit(base)), encoding="utf-8")


def generate_multi_market_final_audit_freeze_summary(
    *,
    base_dir: PathLike = ".",
    output_csv: PathLike = "operator_multi_market_final_audit_gate.csv",
    output_report: PathLike = "reports/operator_multi_market_final_audit_gate_report.md",
    freeze_summary: PathLike = "Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md",
    generated_at: Optional[str] = None,
) -> Dict[str, str]:
    row = build_multi_market_final_audit_row(base_dir=base_dir, generated_at=generated_at)
    write_audit_csv(output_csv, row)
    write_audit_markdown(output_report, row)
    write_freeze_summary(freeze_summary, row, base_dir=base_dir)
    return row


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 509-512 multi-market final audit and freeze summary.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output-csv", default="operator_multi_market_final_audit_gate.csv")
    parser.add_argument("--output-report", default="reports/operator_multi_market_final_audit_gate_report.md")
    parser.add_argument("--freeze-summary", default="Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    row = generate_multi_market_final_audit_freeze_summary(
        base_dir=args.base_dir,
        output_csv=args.output_csv,
        output_report=args.output_report,
        freeze_summary=args.freeze_summary,
        generated_at=args.generated_at,
    )
    print("[MULTI_MARKET_FINAL_AUDIT_FREEZE_SUMMARY] generated")
    print(
        "final_audit_status={}:manual_only={}:research_only={}:observation_only={}:auto_trade_allowed=false:telegram_real_send_allowed=false".format(
            row["final_audit_status"],
            row["manual_only"],
            row["research_only"],
            row["observation_only"],
        )
    )
    print("NOTICE: Final audit and freeze summary only. Not live production, not real market data verified, no IBKR connection, no account/position/historical-data reads, no contract qualification, no Telegram real send, and no trading/order/cancel/rebalance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
