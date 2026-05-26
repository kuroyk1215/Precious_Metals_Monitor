from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


PHASE = "Phase 537-540"
CONNECT_ONLY_DRYRUN_CONNECTED_STATUS = "CONNECTED_THEN_DISCONNECTED"
CONNECT_ONLY_DRYRUN_FAILED_STATUS = "FAILED"
YES_TEXT = "YES"
NO_TEXT = "NO"
NOT_REQUIRED_TEXT = "NOT_REQUIRED"

CSV_FIELDS = (
    "phase",
    "run_id",
    "check_id",
    "category",
    "action",
    "status",
    "severity",
    "operator_approved",
    "connection_attempted",
    "connected",
    "disconnected",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
    "external_effect",
    "host_redacted",
    "port_present",
    "client_id_present",
    "error_type",
    "error_message_redacted",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

OUTPUT_FIELDS = (
    "operator_approved",
    "connection_attempted",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
    "orders_submitted",
    "telegram_real_send_attempted",
)

PathLike = Union[str, Path]
ConnectFunc = Callable[[Dict[str, Any]], Tuple[bool, bool, Optional[str], str]]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_id(timestamp: str) -> str:
    safe = timestamp.replace("+00:00", "Z").replace(":", "").replace("-", "")
    return f"IBKR-CONNECT-ONLY-DRYRUN-{safe}"


def _redact_error_message(message: str) -> str:
    if not message:
        return ""
    lowered = message.lower()
    sensitive_markers = ("token", "secret", "password", "authorization", "bearer", "api_key", "apikey")
    if any(marker in lowered for marker in sensitive_markers):
        return "REDACTED_SENSITIVE_ERROR"
    return " ".join(message.replace("\n", " ").replace("\r", " ").split())[:180]


def classify_error(error_message: str) -> str:
    lowered = error_message.lower()
    if not error_message:
        return ""
    if "ib_insync" in lowered and ("no module" in lowered or "not installed" in lowered or "missing" in lowered):
        return "IB_INSYNC_MISSING"
    if "config" in lowered or "host" in lowered or "port" in lowered or "client_id" in lowered:
        return "CONFIG_MISSING"
    if "timeout" in lowered or "timed out" in lowered:
        return "TIMEOUT"
    if "refused" in lowered or "connect call failed" in lowered or "connectionreset" in lowered:
        return "PORT_REFUSED"
    if "client id" in lowered or "clientid" in lowered or "already in use" in lowered:
        return "CLIENT_ID_CONFLICT"
    if "api" in lowered and ("disabled" in lowered or "not enabled" in lowered):
        return "API_DISABLED"
    if "connect" in lowered or "socket" in lowered or "gateway" in lowered or "tws" in lowered:
        return "TWS_NOT_RUNNING"
    return "UNKNOWN_ERROR"


def _load_ibkr_config(config_path: PathLike) -> Dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        yaml = None

    path = Path(config_path)
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = {"ibkr": _parse_simple_ibkr_yaml(text)}
    ibkr = data.get("ibkr")
    if not isinstance(ibkr, dict):
        raise ValueError("config_missing: ibkr section missing")
    for key in ("host", "port", "client_id"):
        if key not in ibkr or ibkr[key] in ("", None):
            raise ValueError(f"config_missing: ibkr.{key} missing")
    return dict(ibkr)


def _parse_simple_ibkr_yaml(text: str) -> Dict[str, Any]:
    ibkr: Dict[str, Any] = {}
    in_ibkr = False
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and raw_line.rstrip() == "ibkr:":
            in_ibkr = True
            continue
        if in_ibkr and not raw_line.startswith(" "):
            break
        if in_ibkr and ":" in raw_line:
            key, value = raw_line.strip().split(":", 1)
            cleaned = value.strip().strip("'\"")
            if cleaned.lower() in {"true", "false"}:
                ibkr[key] = cleaned.lower() == "true"
            else:
                ibkr[key] = cleaned
    return ibkr


def _import_ib_class() -> Any:
    try:
        from ib_insync import IB

        return IB
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]
        local_site_packages = (
            repo_root
            / ".venv"
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )
        if local_site_packages.exists():
            sys.path.insert(0, str(local_site_packages))
            try:
                from ib_insync import IB

                return IB
            except ImportError:
                pass
    raise ImportError("ib_insync not installed")


def _ib_insync_connect_only(config: Dict[str, Any]) -> Tuple[bool, bool, Optional[str], str]:
    try:
        IB = _import_ib_class()
    except ImportError:
        return False, False, "IB_INSYNC_MISSING", "ib_insync not installed"

    ib = IB()
    connected = False
    disconnected = False
    try:
        ib.connect(
            host=str(config["host"]),
            port=int(config["port"]),
            clientId=int(config["client_id"]),
            timeout=float(config.get("timeout_sec", 5)),
            readonly=bool(config.get("readonly", True)),
        )
        connected = bool(ib.isConnected())
    except Exception as exc:  # pragma: no cover - depends on local TWS/Gateway state
        message = str(exc)
        return False, False, classify_error(message), message
    finally:
        if connected:
            ib.disconnect()
            disconnected = True
        elif ib.isConnected():  # pragma: no cover
            ib.disconnect()
            disconnected = True
    return connected, disconnected, None if connected else "UNKNOWN_ERROR", "" if connected else "connect returned without connected state"


def _status_values(
    *,
    operator_approved: bool,
    connection_attempted: bool,
    connected: bool,
    disconnected: bool,
    error_type: str,
) -> Dict[str, str]:
    return {
        "operator_approved": YES_TEXT if operator_approved else NO_TEXT,
        "connection_attempted": YES_TEXT if connection_attempted else NO_TEXT,
        "connected": YES_TEXT if connected else NO_TEXT,
        "disconnected": YES_TEXT if disconnected else (NOT_REQUIRED_TEXT if not connected else NO_TEXT),
        "market_data_requested": NO_TEXT,
        "account_read_attempted": NO_TEXT,
        "positions_read_attempted": NO_TEXT,
        "historical_data_requested": NO_TEXT,
        "contract_qualification_attempted": NO_TEXT,
        "orders_submitted": NO_TEXT,
        "telegram_real_send_attempted": NO_TEXT,
        "connect_only_dryrun_status": (
            CONNECT_ONLY_DRYRUN_CONNECTED_STATUS if connected and disconnected else CONNECT_ONLY_DRYRUN_FAILED_STATUS
        ),
        "ibkr_connected": YES_TEXT if connected else NO_TEXT,
        "ibkr_disconnected": YES_TEXT if disconnected else (NOT_REQUIRED_TEXT if not connected else NO_TEXT),
        "error_type": error_type,
    }


def _row(
    *,
    run_id: str,
    check_id: str,
    category: str,
    action: str,
    status: str,
    severity: str,
    values: Dict[str, str],
    external_effect: str,
    host_present: bool,
    port_present: bool,
    client_id_present: bool,
    error_type: str,
    error_message_redacted: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "run_id": run_id,
        "check_id": check_id,
        "category": category,
        "action": action,
        "status": status,
        "severity": severity,
        "operator_approved": values["operator_approved"],
        "connection_attempted": values["connection_attempted"],
        "connected": values["connected"],
        "disconnected": values["disconnected"],
        "market_data_requested": values["market_data_requested"],
        "account_read_attempted": values["account_read_attempted"],
        "positions_read_attempted": values["positions_read_attempted"],
        "historical_data_requested": values["historical_data_requested"],
        "contract_qualification_attempted": values["contract_qualification_attempted"],
        "orders_submitted": values["orders_submitted"],
        "telegram_real_send_attempted": values["telegram_real_send_attempted"],
        "external_effect": external_effect,
        "host_redacted": "PRESENT_REDACTED" if host_present else "MISSING",
        "port_present": YES_TEXT if port_present else NO_TEXT,
        "client_id_present": YES_TEXT if client_id_present else NO_TEXT,
        "error_type": error_type,
        "error_message_redacted": error_message_redacted,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def build_ibkr_connect_only_dryrun_execute_rows(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    generated_at: Optional[str] = None,
    connect_func: Optional[ConnectFunc] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    run_id = _run_id(timestamp)
    if not operator_approved:
        values = _status_values(
            operator_approved=False,
            connection_attempted=False,
            connected=False,
            disconnected=False,
            error_type="OPERATOR_APPROVAL_REQUIRED",
        )
        return [
            _row(
                run_id=run_id,
                check_id="IBKR-CONNECT-ONLY-DRYRUN-000",
                category="operator_approval",
                action="deny_connect_only_dryrun_without_operator_approval",
                status="DENIED",
                severity="CRITICAL",
                values=values,
                external_effect="NONE",
                host_present=False,
                port_present=False,
                client_id_present=False,
                error_type="OPERATOR_APPROVAL_REQUIRED",
                error_message_redacted="OPERATOR_APPROVAL_REQUIRED",
                evidence="--operator-approved flag was not supplied",
                recommendation="rerun only after explicit operator approval for one connect/disconnect dry-run",
                timestamp_utc=timestamp,
            )
        ]

    config: Dict[str, Any] = {}
    config_error = ""
    try:
        config = _load_ibkr_config(config_path)
    except Exception as exc:
        config_error = str(exc)

    host_present = bool(config.get("host"))
    port_present = bool(config.get("port"))
    client_id_present = bool(config.get("client_id"))
    connected = False
    disconnected = False
    error_type = ""
    error_message = ""

    if config_error:
        error_type = "CONFIG_MISSING"
        error_message = config_error
    else:
        connector = connect_func or _ib_insync_connect_only
        connected, disconnected, error_type_from_connect, error_message = connector(config)
        error_type = error_type_from_connect or ("" if connected and disconnected else classify_error(error_message))

    values = _status_values(
        operator_approved=True,
        connection_attempted=True,
        connected=connected,
        disconnected=disconnected,
        error_type=error_type,
    )
    status = values["connect_only_dryrun_status"]
    external_effect = "CONNECT_DISCONNECT_ONLY" if connected and disconnected else "CONNECT_ONLY_ATTEMPT_FAILED"
    return [
        _row(
            run_id=run_id,
            check_id="IBKR-CONNECT-ONLY-DRYRUN-001",
            category="connect_only_execution",
            action="connect_then_disconnect_without_requests_reads_orders_or_sends",
            status=status,
            severity="INFO" if status == CONNECT_ONLY_DRYRUN_CONNECTED_STATUS else "HIGH",
            values=values,
            external_effect=external_effect,
            host_present=host_present,
            port_present=port_present,
            client_id_present=client_id_present,
            error_type=error_type,
            error_message_redacted=_redact_error_message(error_message),
            evidence="single_authorized_connect_disconnect_path_no_other_ibkr_api_calls",
            recommendation=(
                "do_not_treat_connect_success_as_market_data_verified_or_production_ready"
                if status == CONNECT_ONLY_DRYRUN_CONNECTED_STATUS
                else "resolve_tws_gateway_api_or_config_issue_before_any_later_separately_authorized_phase"
            ),
            timestamp_utc=timestamp,
        )
    ]


def write_ibkr_connect_only_dryrun_execute_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_ibkr_connect_only_dryrun_execute_report(rows: Sequence[Dict[str, str]]) -> str:
    row = rows[0]
    final_status = row["status"]
    output_values = _status_values(
        operator_approved=row["operator_approved"] == YES_TEXT,
        connection_attempted=row["connection_attempted"] == YES_TEXT,
        connected=row["connected"] == YES_TEXT,
        disconnected=row["disconnected"] == YES_TEXT,
        error_type=row["error_type"],
    )
    lines = [
        "# Phase 537-540 IBKR Connect-Only Dry-Run Execute",
        "",
        "## Final Result",
        "",
        f"- connect_only_dryrun_status={final_status}",
        f"- ibkr_connected={output_values['ibkr_connected']}",
        f"- ibkr_disconnected={output_values['ibkr_disconnected']}",
        f"- error_type={row['error_type']}",
        "",
        "## Scope Boundary",
        "",
        "- one authorized real IBKR/TWS/IB Gateway connect/disconnect attempt only",
        "- no market data verification and no production readiness reclassification",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- market_data_requested=NO",
        "- account_read_attempted=NO",
        "- positions_read_attempted=NO",
        "- historical_data_requested=NO",
        "- contract_qualification_attempted=NO",
        "- orders_submitted=NO",
        "- telegram_real_send_attempted=NO",
        "",
        "## Operator Approval",
        "",
        f"- operator_approved={row['operator_approved']}",
        "",
        "## Connection Attempt Summary",
        "",
        f"- connection_attempted={row['connection_attempted']}",
        f"- connected={row['connected']}",
        f"- host_redacted={row['host_redacted']}",
        f"- port_present={row['port_present']}",
        f"- client_id_present={row['client_id_present']}",
        "",
        "## Disconnect Summary",
        "",
        f"- disconnected={row['disconnected']}",
        "- disconnect action is only attempted after a connected state",
        "",
        "## Error Taxonomy",
        "",
        f"- error_type={row['error_type']}",
        f"- error_message_redacted={row['error_message_redacted']}",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_ibkr_connect_only_dryrun_execute.csv",
        "- report=reports/operator_ibkr_connect_only_dryrun_execute_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- connect success does not verify market data entitlement",
        "- connect success does not verify account, position, historical, contract, order, cancel, rebalance, or Telegram behavior",
        "- connect success does not mean production-ready",
        "",
        "## Next Phase Preconditions",
        "",
        "- separate explicit authorization for any future IBKR API behavior beyond connect/disconnect",
        "- continued prohibition on secret, token, password, or account identifier output",
    ]
    return "\n".join(lines) + "\n"


def write_ibkr_connect_only_dryrun_execute_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ibkr_connect_only_dryrun_execute_report(rows), encoding="utf-8")


def generate_ibkr_connect_only_dryrun_execute(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    output_csv: PathLike = "operator_ibkr_connect_only_dryrun_execute.csv",
    output_report: PathLike = "reports/operator_ibkr_connect_only_dryrun_execute_report.md",
    generated_at: Optional[str] = None,
    connect_func: Optional[ConnectFunc] = None,
) -> List[Dict[str, str]]:
    rows = build_ibkr_connect_only_dryrun_execute_rows(
        operator_approved=operator_approved,
        config_path=config_path,
        generated_at=generated_at,
        connect_func=connect_func,
    )
    write_ibkr_connect_only_dryrun_execute_csv(output_csv, rows)
    write_ibkr_connect_only_dryrun_execute_report(output_report, rows)
    return rows


def output_status_values(row: Dict[str, str]) -> Dict[str, str]:
    values = _status_values(
        operator_approved=row["operator_approved"] == YES_TEXT,
        connection_attempted=row["connection_attempted"] == YES_TEXT,
        connected=row["connected"] == YES_TEXT,
        disconnected=row["disconnected"] == YES_TEXT,
        error_type=row["error_type"],
    )
    return values


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute Phase 537-540 IBKR connect-only dry-run.")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-csv", default="operator_ibkr_connect_only_dryrun_execute.csv")
    parser.add_argument("--output-report", default="reports/operator_ibkr_connect_only_dryrun_execute_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_ibkr_connect_only_dryrun_execute(
        operator_approved=args.operator_approved,
        config_path=args.config,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    row = rows[0]
    values = output_status_values(row)
    print("[IBKR_CONNECT_ONLY_DRYRUN_EXECUTE] generated")
    for field in OUTPUT_FIELDS:
        print(f"{field}={values[field]}")
    print(f"connect_only_dryrun_status={values['connect_only_dryrun_status']}")
    print(f"ibkr_connected={values['ibkr_connected']}")
    print(f"ibkr_disconnected={values['ibkr_disconnected']}")
    print(f"error_type={row['error_type']}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    if not args.operator_approved:
        print("DENIED / OPERATOR_APPROVAL_REQUIRED")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
