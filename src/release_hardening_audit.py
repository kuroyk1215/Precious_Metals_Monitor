from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import re
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class ReleaseHardeningAuditDecision:
    audit_status: str
    audit_scope: str
    forbidden_trading_call_status: str
    forbidden_account_read_status: str
    forbidden_historical_request_status: str
    default_external_request_status: str
    default_telegram_send_status: str
    config_file_status: str
    runtime_artifact_status: str
    universe_policy_status: str
    ibkr_universe_policy_status: str
    cn_market_policy_status: str
    dashboard_ready_status: str
    operator_manual_status: str
    release_candidate_status: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    telegram_send_triggered: str
    manual_review_required: str
    safety_flags: str
    next_step: str


_TRADING_CALLS = (
    "place" + "Order",
    "cancel" + "Order",
    "what" + "IfOrder",
    "bracket" + "Order",
    "exercise" + "Options",
    "req" + "GlobalCancel",
)
_ACCOUNT_READS = (
    "req" + "Account",
    "req" + "Positions",
    "account" + "Summary",
    "managed" + "Accounts",
)
_HISTORICAL_REQUESTS = ("req" + "HistoricalData",)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _call_pattern(names: Sequence[str]) -> re.Pattern[str]:
    joined = "|".join(re.escape(name) for name in names)
    return re.compile(rf"\.\s*({joined})\s*\(")


def scan_call_patterns(paths: Iterable[str | Path], names: Sequence[str]) -> List[str]:
    pattern = _call_pattern(names)
    hits: List[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{path}:{line_number}")
    return hits


def check_required_text(path: str | Path, required: Iterable[str]) -> List[str]:
    candidate = Path(path)
    if not candidate.exists():
        return [f"missing:{candidate}"]
    text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
    missing = []
    for marker in required:
        if marker.lower() not in text:
            missing.append(marker)
    return missing


def check_gitignore_markers(path: str | Path = ".gitignore") -> List[str]:
    required = (
        "logs/",
        "ibkr_*_packet.csv",
        "reports/*_report.md",
        ".env",
        ".telegram_send_approval",
        "release_hardening_audit.csv",
        "reports/release_hardening_audit_report.md",
    )
    return check_required_text(path, required)


def build_release_hardening_audit_decision(
    *,
    forbidden_trading_hits: Iterable[str] = (),
    forbidden_account_hits: Iterable[str] = (),
    forbidden_historical_hits: Iterable[str] = (),
    default_external_request_ok: bool = True,
    default_telegram_send_ok: bool = True,
    config_file_ok: bool = True,
    runtime_artifact_ok: bool = True,
    universe_policy_ok: bool = True,
    ibkr_universe_policy_ok: bool = True,
    cn_market_policy_ok: bool = True,
    dashboard_ready_ok: bool = True,
    operator_manual_ok: bool = True,
) -> ReleaseHardeningAuditDecision:
    trading_hits = list(forbidden_trading_hits)
    account_hits = list(forbidden_account_hits)
    historical_hits = list(forbidden_historical_hits)

    forbidden_trading_call_status = "PASS" if not trading_hits else "BLOCKED_FORBIDDEN_TRADING_CALL"
    forbidden_account_read_status = "PASS" if not account_hits else "BLOCKED_ACCOUNT_READ"
    forbidden_historical_request_status = "PASS" if not historical_hits else "BLOCKED_HISTORICAL_REQUEST"
    default_external_request_status = "PASS" if default_external_request_ok else "BLOCKED_DEFAULT_EXTERNAL_REQUEST"
    default_telegram_send_status = "PASS" if default_telegram_send_ok else "BLOCKED_DEFAULT_TELEGRAM_SEND"
    config_file_status = "PASS" if config_file_ok else "BLOCKED_CONFIG_FILE_CHANGED"
    runtime_artifact_status = "PASS" if runtime_artifact_ok else "BLOCKED_RUNTIME_ARTIFACT_POLICY"
    universe_policy_status = "USER_WATCHLIST_ONLY" if universe_policy_ok else "UNDEFINED"
    ibkr_universe_policy_status = (
        "GLD_SLV_FIRST_TEST_UNIVERSE|JP_ETF_OPTIONAL|CN_ETF_EXCLUDED_FROM_IBKR"
        if ibkr_universe_policy_ok
        else "UNDEFINED"
    )
    cn_market_policy_status = "CN_ETF_NON_IBKR_OR_MANUAL_ADAPTER_ONLY" if cn_market_policy_ok else "UNDEFINED"
    dashboard_ready_status = "PASS" if dashboard_ready_ok else "BLOCKED_DASHBOARD_MANIFEST"
    operator_manual_status = "PASS" if operator_manual_ok else "BLOCKED_OPERATOR_MANUAL"

    safety_flags: List[str] = []
    if trading_hits:
        safety_flags.append("forbidden_trading_call:" + ",".join(trading_hits))
    if account_hits:
        safety_flags.append("forbidden_account_read:" + ",".join(account_hits))
    if historical_hits:
        safety_flags.append("forbidden_historical_request:" + ",".join(historical_hits))
    for flag_name, ok in (
        ("default_external_request", default_external_request_ok),
        ("default_telegram_send", default_telegram_send_ok),
        ("config_file", config_file_ok),
        ("runtime_artifact", runtime_artifact_ok),
        ("universe_policy", universe_policy_ok),
        ("ibkr_universe_policy", ibkr_universe_policy_ok),
        ("cn_market_policy", cn_market_policy_ok),
        ("dashboard_ready", dashboard_ready_ok),
        ("operator_manual", operator_manual_ok),
    ):
        if not ok:
            safety_flags.append(f"{flag_name}:blocked")

    audit_passed = not safety_flags
    return ReleaseHardeningAuditDecision(
        audit_status="RELEASE_AUDIT_PASS" if audit_passed else "RELEASE_AUDIT_BLOCKED",
        audit_scope="release_hardening_default_dry_run_paths",
        forbidden_trading_call_status=forbidden_trading_call_status,
        forbidden_account_read_status=forbidden_account_read_status,
        forbidden_historical_request_status=forbidden_historical_request_status,
        default_external_request_status=default_external_request_status,
        default_telegram_send_status=default_telegram_send_status,
        config_file_status=config_file_status,
        runtime_artifact_status=runtime_artifact_status,
        universe_policy_status=universe_policy_status,
        ibkr_universe_policy_status=ibkr_universe_policy_status,
        cn_market_policy_status=cn_market_policy_status,
        dashboard_ready_status=dashboard_ready_status,
        operator_manual_status=operator_manual_status,
        release_candidate_status="RC_READY_FOR_MANUAL_EXECUTION_C" if audit_passed else "RC_BLOCKED",
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        telegram_send_triggered="false",
        manual_review_required="true",
        safety_flags=";".join(safety_flags),
        next_step=(
            "manual_operator_may_run_execution_c_validation"
            if audit_passed
            else "stop_and_resolve_release_audit_flags"
        ),
    )


def write_release_hardening_audit_csv(path: str | Path, decision: ReleaseHardeningAuditDecision) -> None:
    fields = list(ReleaseHardeningAuditDecision.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(decision, field) for field in fields])


def write_release_hardening_audit_report(path: str | Path, decision: ReleaseHardeningAuditDecision) -> None:
    Path(path).write_text(
        "\n".join(
            [
                "# Release Hardening Audit Report",
                "",
                "## Decision",
                "",
                "| field | value |",
                "|---|---|",
                f"| audit_status | {decision.audit_status} |",
                f"| release_candidate_status | {decision.release_candidate_status} |",
                f"| universe_policy_status | {decision.universe_policy_status} |",
                f"| ibkr_universe_policy_status | {decision.ibkr_universe_policy_status} |",
                f"| dashboard_ready_status | {decision.dashboard_ready_status} |",
                f"| operator_manual_status | {decision.operator_manual_status} |",
                f"| next_step | {decision.next_step} |",
                "| action_allowed | false |",
                "",
                "## Safety Confirmation",
                "",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- telegram_send_triggered=false",
                "- manual_review_required=true",
                "",
                "## Scope",
                "",
                f"- audit_scope={decision.audit_scope}",
                "- default mode is dry-run and does not connect to IBKR",
                "- default mode does not send Telegram messages",
                "- output is research-only and manual-review-only",
                "",
                "## Flags",
                "",
                f"- safety_flags={decision.safety_flags or 'none'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
