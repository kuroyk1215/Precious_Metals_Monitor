from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


PHASE = "Phase 553-556"
SYMBOLS = ("GLD", "SLV")
ASSET_CLASS = "ETF"
EXCHANGE = "SMART"
CURRENCY = "USD"
YES_TEXT = "YES"
NO_TEXT = "NO"

CSV_FIELDS = (
    "phase",
    "run_id",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "operator_approved",
    "qualification_attempted",
    "qualification_status",
    "qualified",
    "contract_count",
    "primary_exchange_redacted",
    "con_id_present",
    "market_data_requested",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "orders_submitted",
    "telegram_real_send_attempted",
    "external_effect",
    "error_type",
    "error_message_redacted",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

ERROR_TYPES = (
    "QUALIFIED",
    "CONTRACT_NOT_FOUND",
    "AMBIGUOUS_CONTRACT",
    "IBKR_CONNECTION_FAILED",
    "API_DISABLED",
    "PORT_REFUSED",
    "CLIENT_ID_CONFLICT",
    "TIMEOUT",
    "IB_INSYNC_MISSING",
    "CONFIG_MISSING",
    "OPERATOR_APPROVAL_REQUIRED",
    "UNKNOWN_ERROR",
)

PathLike = Union[str, Path]
QualifyFunc = Callable[[Dict[str, Any], Sequence[str]], Tuple[Dict[str, Dict[str, Any]], Optional[str], str]]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_id(timestamp: str) -> str:
    safe = timestamp.replace("+00:00", "Z").replace(":", "").replace("-", "")
    return f"US-ETF-CONTRACT-QUALIFICATION-{safe}"


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
        return "UNKNOWN_ERROR"
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
        return "IBKR_CONNECTION_FAILED"
    return "UNKNOWN_ERROR"


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
            cleaned: Any = value.strip().strip("'\"")
            if str(cleaned).lower() in {"true", "false"}:
                cleaned = str(cleaned).lower() == "true"
            ibkr[key] = cleaned
    return ibkr


def _load_ibkr_config(config_path: PathLike) -> Dict[str, Any]:
    try:
        import yaml
    except ImportError:
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


def _import_ib_classes() -> Tuple[Any, Any]:
    try:
        from ib_insync import IB, Stock

        return IB, Stock
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
                from ib_insync import IB, Stock

                return IB, Stock
            except ImportError:
                pass
    raise ImportError("ib_insync not installed")


def _ib_insync_qualify_us_etfs(
    config: Dict[str, Any], symbols: Sequence[str]
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], str]:
    try:
        IB, Stock = _import_ib_classes()
    except ImportError:
        return {}, "IB_INSYNC_MISSING", "ib_insync not installed"

    ib = IB()
    connected = False
    try:
        ib.connect(
            host=str(config["host"]),
            port=int(config["port"]),
            clientId=int(config["client_id"]),
            timeout=float(config.get("timeout_sec", 5)),
            readonly=bool(config.get("readonly", True)),
        )
        connected = bool(ib.isConnected())
        if not connected:
            return {}, "IBKR_CONNECTION_FAILED", "connect returned without connected state"

        results: Dict[str, Dict[str, Any]] = {}
        for symbol in symbols:
            contract = Stock(symbol, EXCHANGE, CURRENCY)
            qualified_contracts = ib.qualifyContracts(contract)
            results[symbol] = {"contracts": list(qualified_contracts or [])}
        return results, None, ""
    except Exception as exc:  # pragma: no cover - depends on local TWS/Gateway state
        message = str(exc)
        return {}, classify_error(message), message
    finally:
        if connected or ib.isConnected():  # pragma: no cover
            ib.disconnect()


def _contract_value(contract: Any, name: str) -> Any:
    return getattr(contract, name, None)


def _row(
    *,
    run_id: str,
    symbol: str,
    operator_approved: bool,
    qualification_attempted: bool,
    qualification_status: str,
    qualified: bool,
    contract_count: int,
    primary_exchange_present: bool,
    con_id_present: bool,
    external_effect: str,
    error_type: str,
    error_message_redacted: str,
    evidence: str,
    recommendation: str,
    timestamp_utc: str,
) -> Dict[str, str]:
    return {
        "phase": PHASE,
        "run_id": run_id,
        "symbol": symbol,
        "asset_class": ASSET_CLASS,
        "exchange": EXCHANGE,
        "currency": CURRENCY,
        "operator_approved": YES_TEXT if operator_approved else NO_TEXT,
        "qualification_attempted": YES_TEXT if qualification_attempted else NO_TEXT,
        "qualification_status": qualification_status,
        "qualified": YES_TEXT if qualified else NO_TEXT,
        "contract_count": str(contract_count),
        "primary_exchange_redacted": "PRESENT_REDACTED" if primary_exchange_present else "MISSING",
        "con_id_present": YES_TEXT if con_id_present else NO_TEXT,
        "market_data_requested": NO_TEXT,
        "account_read_attempted": NO_TEXT,
        "positions_read_attempted": NO_TEXT,
        "historical_data_requested": NO_TEXT,
        "orders_submitted": NO_TEXT,
        "telegram_real_send_attempted": NO_TEXT,
        "external_effect": external_effect,
        "error_type": error_type,
        "error_message_redacted": error_message_redacted,
        "evidence": evidence,
        "recommendation": recommendation,
        "timestamp_utc": timestamp_utc,
    }


def _rows_from_results(
    *,
    run_id: str,
    timestamp: str,
    results: Dict[str, Dict[str, Any]],
    global_error_type: Optional[str],
    error_message: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for symbol in SYMBOLS:
        contracts = list(results.get(symbol, {}).get("contracts", []))
        count = len(contracts)
        first = contracts[0] if contracts else None
        con_id_present = bool(_contract_value(first, "conId")) if first is not None else False
        primary_exchange_present = bool(_contract_value(first, "primaryExchange")) if first is not None else False
        if global_error_type:
            status = global_error_type
            error_type = global_error_type
            qualified = False
            evidence = "qualification_not_completed_due_to_shared_connection_or_runtime_error"
        elif count == 1:
            status = "QUALIFIED"
            error_type = "QUALIFIED"
            qualified = True
            evidence = f"{symbol}_qualified_once_contract_count_1"
        elif count == 0:
            status = "CONTRACT_NOT_FOUND"
            error_type = "CONTRACT_NOT_FOUND"
            qualified = False
            evidence = f"{symbol}_qualification_returned_zero_contracts"
        else:
            status = "AMBIGUOUS_CONTRACT"
            error_type = "AMBIGUOUS_CONTRACT"
            qualified = False
            evidence = f"{symbol}_qualification_returned_multiple_contracts"
        rows.append(
            _row(
                run_id=run_id,
                symbol=symbol,
                operator_approved=True,
                qualification_attempted=True,
                qualification_status=status,
                qualified=qualified,
                contract_count=count,
                primary_exchange_present=primary_exchange_present,
                con_id_present=con_id_present,
                external_effect="CONNECT_DISCONNECT_QUALIFY_GLD_SLV_ONLY",
                error_type=error_type,
                error_message_redacted=_redact_error_message(error_message) if error_type != "QUALIFIED" else "",
                evidence=evidence,
                recommendation=(
                    "archive_contract_identity_without_requesting_market_data_account_positions_historical_data_or_orders"
                    if qualified
                    else "resolve_contract_mapping_or_ibkr_connection_issue_before_any_later_phase"
                ),
                timestamp_utc=timestamp,
            )
        )
    return rows


def build_us_etf_contract_qualification_execute_rows(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    generated_at: Optional[str] = None,
    qualify_func: Optional[QualifyFunc] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    run_id = _run_id(timestamp)
    if not operator_approved:
        return [
            _row(
                run_id=run_id,
                symbol=symbol,
                operator_approved=False,
                qualification_attempted=False,
                qualification_status="DENIED",
                qualified=False,
                contract_count=0,
                primary_exchange_present=False,
                con_id_present=False,
                external_effect="NONE",
                error_type="OPERATOR_APPROVAL_REQUIRED",
                error_message_redacted="OPERATOR_APPROVAL_REQUIRED",
                evidence="--operator-approved flag was not supplied",
                recommendation="rerun only after explicit operator approval for one GLD and one SLV qualification",
                timestamp_utc=timestamp,
            )
            for symbol in SYMBOLS
        ]

    try:
        config = _load_ibkr_config(config_path)
    except Exception as exc:
        return _rows_from_results(
            run_id=run_id,
            timestamp=timestamp,
            results={},
            global_error_type="CONFIG_MISSING",
            error_message=str(exc),
        )

    qualifier = qualify_func or _ib_insync_qualify_us_etfs
    results, global_error_type, error_message = qualifier(config, SYMBOLS)
    return _rows_from_results(
        run_id=run_id,
        timestamp=timestamp,
        results=results,
        global_error_type=global_error_type,
        error_message=error_message,
    )


def write_us_etf_contract_qualification_execute_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_contract_qualification_execute_report(rows: Sequence[Dict[str, str]]) -> str:
    qualified_rows = [row for row in rows if row["qualified"] == YES_TEXT]
    error_lines = [f"- {error_type}" for error_type in ERROR_TYPES]
    summary_lines = [
        f"- {row['symbol']}_qualification_status={row['qualification_status']} error_type={row['error_type']} contract_count={row['contract_count']}"
        for row in rows
    ]
    qualified_lines = [
        f"- {row['symbol']}: qualified={row['qualified']} con_id_present={row['con_id_present']} primary_exchange_redacted={row['primary_exchange_redacted']}"
        for row in rows
    ]
    lines = [
        "# Phase 553-556 GLD / SLV Contract Qualification Execute",
        "",
        "## Final Result",
        "",
        f"- qualified_symbols_count={len(qualified_rows)}",
        *[f"- {row['symbol']}_qualification_status={row['qualification_status']}" for row in rows],
        "",
        "## Scope Boundary",
        "",
        "- authorized symbols: GLD, SLV",
        "- authorized action: connect, qualifyContracts for GLD and SLV, disconnect",
        "",
        "## Operator Approval",
        "",
        f"- operator_approved={rows[0]['operator_approved'] if rows else NO_TEXT}",
        "",
        "## Qualification Summary",
        "",
        *summary_lines,
        "",
        "## Qualified Contracts",
        "",
        *qualified_lines,
        "",
        "## Error Taxonomy",
        "",
        *error_lines,
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- market_data_requested=NO",
        "- account_read_attempted=NO",
        "- positions_read_attempted=NO",
        "- historical_data_requested=NO",
        "- orders_submitted=NO",
        "- telegram_real_send_attempted=NO",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_contract_qualification_execute.csv",
        "- report=reports/operator_us_etf_contract_qualification_execute_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- contract qualification does not verify market data entitlement",
        "- contract qualification does not verify account, position, historical data, order, cancel, rebalance, or Telegram behavior",
        "",
        "## Next Phase Preconditions",
        "",
        "- separate explicit authorization is required before any future IBKR action beyond archived contract qualification",
        "- continue redacting primary exchange details and any sensitive runtime error content",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_contract_qualification_execute_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_contract_qualification_execute_report(rows), encoding="utf-8")


def generate_us_etf_contract_qualification_execute(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    output_csv: PathLike = "operator_us_etf_contract_qualification_execute.csv",
    output_report: PathLike = "reports/operator_us_etf_contract_qualification_execute_report.md",
    generated_at: Optional[str] = None,
    qualify_func: Optional[QualifyFunc] = None,
) -> List[Dict[str, str]]:
    rows = build_us_etf_contract_qualification_execute_rows(
        operator_approved=operator_approved,
        config_path=config_path,
        generated_at=generated_at,
        qualify_func=qualify_func,
    )
    write_us_etf_contract_qualification_execute_csv(output_csv, rows)
    write_us_etf_contract_qualification_execute_report(output_report, rows)
    return rows


def qualified_symbols_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(1 for row in rows if row["qualified"] == YES_TEXT)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute Phase 553-556 GLD/SLV contract qualification.")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-csv", default="operator_us_etf_contract_qualification_execute.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_us_etf_contract_qualification_execute_report.md",
    )
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_us_etf_contract_qualification_execute(
        operator_approved=args.operator_approved,
        config_path=args.config,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    if not args.operator_approved:
        print("[US_ETF_CONTRACT_QUALIFICATION_EXECUTE] denied")
        print("operator_approved=NO")
        print("qualification_attempted=NO")
        print("error_type=OPERATOR_APPROVAL_REQUIRED")
        print("DENIED / OPERATOR_APPROVAL_REQUIRED")
        print(f"csv={args.output_csv}")
        print(f"report={args.output_report}")
        return 2

    print("[US_ETF_CONTRACT_QUALIFICATION_EXECUTE] generated")
    print("operator_approved=YES")
    print("symbols_requested=GLD,SLV")
    print("qualification_attempted=YES")
    print("market_data_requested=NO")
    print("account_read_attempted=NO")
    print("positions_read_attempted=NO")
    print("historical_data_requested=NO")
    print("orders_submitted=NO")
    print("telegram_real_send_attempted=NO")
    for row in rows:
        print(f"{row['symbol']}_qualification_status={row['qualification_status']}")
        print(f"{row['symbol']}_error_type={row['error_type']}")
    print(f"qualified_symbols_count={qualified_symbols_count(rows)}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
