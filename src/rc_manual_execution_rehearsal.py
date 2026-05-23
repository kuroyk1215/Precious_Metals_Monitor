from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Iterable, List


DRY_RUN_COMMAND = "bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run"
EXECUTION_C_COMMAND = (
    "bash scripts/ibkr_execution_c_pipeline_validation.sh "
    "--execute-market-data --market-data-type=auto --telegram-dry-run"
)
TELEGRAM_DRY_RUN_COMMAND = "bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run"
TELEGRAM_SEND_GATE_COMMAND = (
    "bash scripts/ibkr_telegram_send_gate.sh --send-telegram "
    "--approval-file=.telegram_send_approval.local"
)


@dataclass(frozen=True)
class RCManualExecutionRehearsalDecision:
    rehearsal_status: str
    rehearsal_mode: str
    git_branch_status: str
    git_worktree_status: str
    config_local_only_status: str
    required_scripts_status: str
    contract_map_status: str
    universe_policy_status: str
    ibkr_first_validation_universe: str
    jp_optional_universe: str
    cn_non_ibkr_policy: str
    dry_run_command: str
    execution_c_command: str
    telegram_dry_run_command: str
    telegram_send_gate_command: str
    command_preview_status: str
    readiness_decision: str
    readiness_reason: str
    action_allowed: str
    broker_execution_triggered: str
    historical_data_request_triggered: str
    account_read_triggered: str
    position_read_triggered: str
    telegram_send_triggered: str
    manual_review_required: str
    safety_flags: str
    next_step: str


def build_rc_manual_execution_rehearsal_decision(
    *,
    git_branch_ok: bool = True,
    git_worktree_ok: bool = True,
    config_local_only_ok: bool = True,
    required_scripts_ok: bool = True,
    contract_map_ok: bool = True,
    universe_policy_ok: bool = True,
    command_preview_ok: bool = True,
    missing_inputs: Iterable[str] = (),
    market_data_type: str = "auto",
    contract_map: str = "ibkr_verified_contract_map.csv",
    log_root: str = "logs/ibkr_daily",
    retention_days: str = "30",
) -> RCManualExecutionRehearsalDecision:
    safety_flags: List[str] = list(missing_inputs)
    checks = (
        ("git_branch", git_branch_ok),
        ("git_worktree", git_worktree_ok),
        ("config_local_only", config_local_only_ok),
        ("required_scripts", required_scripts_ok),
        ("contract_map", contract_map_ok),
        ("universe_policy", universe_policy_ok),
        ("command_preview", command_preview_ok),
    )
    for name, ok in checks:
        if not ok and not any(flag.startswith(f"{name}:") for flag in safety_flags):
            safety_flags.append(f"{name}:blocked")

    ready = not safety_flags
    execution_c_command = (
        "bash scripts/ibkr_execution_c_pipeline_validation.sh "
        f"--execute-market-data --market-data-type={market_data_type} "
        "--telegram-dry-run "
        f"--contract-map={contract_map} --log-root={log_root} --retention-days={retention_days}"
    )
    local_runner_execution_command = (
        "bash scripts/ibkr_local_daily_runner.sh "
        f"--execute-market-data --market-data-type={market_data_type} "
        "--telegram-dry-run "
        f"--contract-map={contract_map} --log-root={log_root} --retention-days={retention_days}"
    )
    dry_run_command = "bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run"

    return RCManualExecutionRehearsalDecision(
        rehearsal_status="RC_REHEARSAL_READY" if ready else "RC_REHEARSAL_BLOCKED",
        rehearsal_mode="dry_run_preview_only",
        git_branch_status="PASS" if git_branch_ok else "BLOCKED_BRANCH_STATE",
        git_worktree_status="PASS" if git_worktree_ok else "BLOCKED_WORKTREE_STATE",
        config_local_only_status="PASS" if config_local_only_ok else "BLOCKED_CONFIG_NOT_LOCAL_ONLY",
        required_scripts_status="PASS" if required_scripts_ok else "BLOCKED_REQUIRED_SCRIPT_MISSING",
        contract_map_status="PASS" if contract_map_ok else "BLOCKED_CONTRACT_MAP_MISSING",
        universe_policy_status="USER_WATCHLIST_ONLY" if universe_policy_ok else "UNDEFINED",
        ibkr_first_validation_universe="GLD_SLV",
        jp_optional_universe="1540_1542_OPTIONAL",
        cn_non_ibkr_policy="518880_EXCLUDED_FROM_IBKR",
        dry_run_command=dry_run_command,
        execution_c_command=execution_c_command,
        telegram_dry_run_command=local_runner_execution_command,
        telegram_send_gate_command=TELEGRAM_SEND_GATE_COMMAND,
        command_preview_status="PASS" if command_preview_ok else "BLOCKED_COMMAND_PREVIEW",
        readiness_decision="READY_FOR_MANUAL_EXECUTION_C" if ready else "BLOCKED_BEFORE_MANUAL_EXECUTION_C",
        readiness_reason=(
            "manual Execution C command preview is ready; no IBKR request was made"
            if ready
            else "manual Execution C rehearsal is blocked by readiness flags"
        ),
        action_allowed="false",
        broker_execution_triggered="false",
        historical_data_request_triggered="false",
        account_read_triggered="false",
        position_read_triggered="false",
        telegram_send_triggered="false",
        manual_review_required="true",
        safety_flags=";".join(safety_flags),
        next_step=(
            "operator_may_manually_copy_execution_c_command"
            if ready
            else "stop_and_resolve_rehearsal_flags"
        ),
    )


def write_rehearsal_csv(path: str | Path, decision: RCManualExecutionRehearsalDecision) -> None:
    fields = list(RCManualExecutionRehearsalDecision.__dataclass_fields__.keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerow([getattr(decision, field) for field in fields])


def write_rehearsal_report(path: str | Path, decision: RCManualExecutionRehearsalDecision) -> None:
    Path(path).write_text(
        "\n".join(
            [
                "# RC Manual Execution Rehearsal Report",
                "",
                "## RC Rehearsal Decision",
                "",
                f"- rehearsal_status={decision.rehearsal_status}",
                f"- rehearsal_mode={decision.rehearsal_mode}",
                f"- readiness_decision={decision.readiness_decision}",
                f"- readiness_reason={decision.readiness_reason}",
                f"- next_step={decision.next_step}",
                "",
                "## Required Scripts Check",
                "",
                f"- required_scripts_status={decision.required_scripts_status}",
                f"- contract_map_status={decision.contract_map_status}",
                f"- git_branch_status={decision.git_branch_status}",
                f"- git_worktree_status={decision.git_worktree_status}",
                f"- config_local_only_status={decision.config_local_only_status}",
                "",
                "## Universe / Watchlist Policy",
                "",
                f"- universe_policy_status={decision.universe_policy_status}",
                "- only user-provided watchlist or universe symbols are in scope",
                "",
                "## GLD / SLV First Validation Plan",
                "",
                f"- ibkr_first_validation_universe={decision.ibkr_first_validation_universe}",
                "- use GLD and SLV first for the manual IBKR market data validation path",
                "",
                "## JP Optional ETF Plan",
                "",
                f"- jp_optional_universe={decision.jp_optional_universe}",
                "- 1540.T and 1542.T are optional JP ETF validation symbols",
                "",
                "## CN / 518880 Non-IBKR Policy",
                "",
                f"- cn_non_ibkr_policy={decision.cn_non_ibkr_policy}",
                "- 518880.SH is not part of the IBKR contract universe",
                "",
                "## Manual Command Preview",
                "",
                f"- dry_run_command=`{decision.dry_run_command}`",
                f"- execution_c_command=`{decision.execution_c_command}`",
                f"- local_runner_execution_preview=`{decision.telegram_dry_run_command}`",
                f"- telegram_send_gate_command=`{decision.telegram_send_gate_command}`",
                "- commands are preview-only in this rehearsal",
                "",
                "## Safety Confirmation",
                "",
                "- action_allowed=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- telegram_send_triggered=false",
                "- manual_review_required=true",
                "",
                "## Next Phase Handoff",
                "",
                "Phase 417-432 may ingest first operator-run results and perform post-run analysis.",
                "",
                "## Flags",
                "",
                f"- safety_flags={decision.safety_flags or 'none'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_command_preview(path: str | Path, decision: RCManualExecutionRehearsalDecision) -> None:
    Path(path).write_text(
        "\n".join(
            [
                "# RC Execution C Command Preview",
                "",
                "These commands are for manual copy and execution only. This rehearsal script does not run them.",
                "",
                "## Manual Execution C Validation",
                "",
                "Use this command when the operator is ready to validate the IBKR market data path:",
                "",
                f"```bash\n{decision.execution_c_command}\n```",
                "",
                "Use this local runner variant only for manual Execution C validation:",
                "",
                f"```bash\n{decision.telegram_dry_run_command}\n```",
                "",
                "## Telegram Send Gate",
                "",
                "Only use this command manually after the environment, token, chat id, and approval file are prepared:",
                "",
                f"```bash\n{decision.telegram_send_gate_command}\n```",
                "",
                "## Safety Boundary",
                "",
                "- the system does not automatically place orders",
                "- the system does not authorize trades",
                "- action_allowed=false",
                "- broker_execution_triggered=false",
                "- historical_data_request_triggered=false",
                "- account_read_triggered=false",
                "- position_read_triggered=false",
                "- telegram_send_triggered=false",
                "",
                "## Universe Notes",
                "",
                "- GLD / SLV first validation",
                "- 1540.T / 1542.T optional JP ETF validation",
                "- 518880.SH excluded from IBKR",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
