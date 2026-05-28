from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


PHASE = "Phase 569-572"
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
    "market_data_request_attempted",
    "market_data_status",
    "ticker_received",
    "bid_present",
    "ask_present",
    "last_present",
    "close_present",
    "delayed_or_realtime",
    "account_read_attempted",
    "positions_read_attempted",
    "historical_data_requested",
    "contract_qualification_attempted",
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
    "REALTIME",
    "DELAYED",
    "DELAYED_FROZEN",
    "PERMISSION_DENIED",
    "NO_DATA",
    "TIMEOUT",
    "IBKR_CONNECTION_FAILED",
    "API_DISABLED",
    "PORT_REFUSED",
    "CLIENT_ID_CONFLICT",
    "IB_INSYNC_MISSING",
    "CONFIG_MISSING",
    "OPERATOR_APPROVAL_REQUIRED",
    "UNKNOWN_ERROR",
)

PathLike = Union[str, Path]
MarketDataFunc = Callable[[Dict[str, Any], Sequence[str]], Tuple[Dict[str, Dict[str, Any]], Optional[str], str]]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_id(timestamp: str) -> str:
    safe = timestamp.replace("+00:00", "Z").replace(":", "").replace("-", "")
    return f"US-ETF-MARKET-DATA-EXECUTE-{safe}"


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
    if "10089" in lowered:
        return "PERMISSION_DENIED"
    if "ib_insync" in lowered and ("no module" in lowered or "not installed" in lowered or "missing" in lowered):
        return "IB_INSYNC_MISSING"
    if "market data farm connection is inactive" in lowered or "no market data permissions" in lowered:
        return "PERMISSION_DENIED"
    if "market data" in lowered and ("permission" in lowered or "subscription" in lowered or "entitlement" in lowered):
        return "PERMISSION_DENIED"
    if "api" in lowered and ("disabled" in lowered or "not enabled" in lowered):
        return "API_DISABLED"
    if "timeout" in lowered or "timed out" in lowered:
        return "TIMEOUT"
    if "refused" in lowered or "connect call failed" in lowered or "connectionreset" in lowered:
        return "PORT_REFUSED"
    if "client id" in lowered or "clientid" in lowered or "already in use" in lowered:
        return "CLIENT_ID_CONFLICT"
    if "config" in lowered or "host" in lowered or "port" in lowered or "client_id" in lowered:
        return "CONFIG_MISSING"
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


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


def _ticker_market_data_type(ticker: Any) -> str:
    market_data_type = getattr(ticker, "marketDataType", None)
    if market_data_type == 1:
        return "REALTIME"
    if market_data_type == 3:
        return "DELAYED"
    if market_data_type == 4:
        return "DELAYED_FROZEN"
    if market_data_type == 2:
        return "FROZEN"
    return "UNKNOWN"


def _status_from_ticker(ticker: Any) -> Tuple[str, str]:
    delayed_or_realtime = _ticker_market_data_type(ticker)
    any_present = any(
        _present(getattr(ticker, name, None))
        for name in ("bid", "ask", "last", "close")
    )
    if delayed_or_realtime in {"REALTIME", "DELAYED", "DELAYED_FROZEN"}:
        return delayed_or_realtime, delayed_or_realtime
    if any_present:
        return "REALTIME_OR_DELAYED_UNSPECIFIED", "UNKNOWN_ERROR"
    return "NO_DATA", "NO_DATA"


def _ib_insync_request_us_etf_market_data(
    config: Dict[str, Any], symbols: Sequence[str]
) -> Tuple[Dict[str, Dict[str, Any]], Optional[str], str]:
    try:
        IB, Stock = _import_ib_classes()
    except ImportError:
        return {}, "IB_INSYNC_MISSING", "ib_insync not installed"

    ib = IB()
    connected = False
    api_errors: List[Tuple[int, str]] = []

    def on_error(req_id: int, error_code: int, error_string: str, contract: Any) -> None:
        symbol = getattr(contract, "symbol", "") if contract is not None else ""
        api_errors.append((error_code, f"{symbol} {error_code} {error_string}".strip()))

    try:
        ib.errorEvent += on_error
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

        wait_seconds = float(config.get("market_data_wait_sec", config.get("timeout_sec", 5)))
        results: Dict[str, Dict[str, Any]] = {}
        for symbol in symbols:
            contract = Stock(symbol, EXCHANGE, CURRENCY)
            ticker = ib.reqMktData(contract, "", False, False)
            ib.sleep(wait_seconds)
            results[symbol] = {
                "ticker_received": ticker is not None,
                "bid_present": _present(getattr(ticker, "bid", None)),
                "ask_present": _present(getattr(ticker, "ask", None)),
                "last_present": _present(getattr(ticker, "last", None)),
                "close_present": _present(getattr(ticker, "close", None)),
                "delayed_or_realtime": _ticker_market_data_type(ticker),
            }
        for symbol in symbols:
            symbol_errors = [message for _, message in api_errors if symbol in message]
            if symbol_errors:
                message = " | ".join(symbol_errors)
                results.setdefault(symbol, {})
                results[symbol]["symbol_error_type"] = classify_error(message)
                results[symbol]["symbol_error_message"] = message
        return results, None, ""
    except Exception as exc:  # pragma: no cover - depends on local TWS/Gateway state
        message = str(exc)
        return {}, classify_error(message), message
    finally:
        try:
            ib.errorEvent -= on_error
        except Exception:
            pass
        if connected or ib.isConnected():  # pragma: no cover
            ib.disconnect()


def _row(
    *,
    run_id: str,
    symbol: str,
    operator_approved: bool,
    market_data_request_attempted: bool,
    market_data_status: str,
    ticker_received: bool,
    bid_present: bool,
    ask_present: bool,
    last_present: bool,
    close_present: bool,
    delayed_or_realtime: str,
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
        "market_data_request_attempted": YES_TEXT if market_data_request_attempted else NO_TEXT,
        "market_data_status": market_data_status,
        "ticker_received": YES_TEXT if ticker_received else NO_TEXT,
        "bid_present": YES_TEXT if bid_present else NO_TEXT,
        "ask_present": YES_TEXT if ask_present else NO_TEXT,
        "last_present": YES_TEXT if last_present else NO_TEXT,
        "close_present": YES_TEXT if close_present else NO_TEXT,
        "delayed_or_realtime": delayed_or_realtime,
        "account_read_attempted": NO_TEXT,
        "positions_read_attempted": NO_TEXT,
        "historical_data_requested": NO_TEXT,
        "contract_qualification_attempted": NO_TEXT,
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
        result = results.get(symbol, {})
        ticker_received = bool(result.get("ticker_received", False))
        bid_present = bool(result.get("bid_present", False))
        ask_present = bool(result.get("ask_present", False))
        last_present = bool(result.get("last_present", False))
        close_present = bool(result.get("close_present", False))
        delayed_or_realtime = str(result.get("delayed_or_realtime", "UNKNOWN"))
        if global_error_type:
            status = global_error_type
            error_type = global_error_type
            evidence = "market_data_not_completed_due_to_shared_connection_or_runtime_error"
        elif result.get("symbol_error_type"):
            error_type = str(result["symbol_error_type"])
            status = error_type
            error_message = str(result.get("symbol_error_message", error_message))
            evidence = f"{symbol}_ibkr_api_error_captured"
        else:
            status, error_type = _status_from_result(result)
            evidence = (
                f"{symbol}_market_data_request_completed_ticker_received_{YES_TEXT if ticker_received else NO_TEXT}"
            )
        rows.append(
            _row(
                run_id=run_id,
                symbol=symbol,
                operator_approved=True,
                market_data_request_attempted=True,
                market_data_status=status,
                ticker_received=ticker_received,
                bid_present=bid_present,
                ask_present=ask_present,
                last_present=last_present,
                close_present=close_present,
                delayed_or_realtime=delayed_or_realtime,
                external_effect="CONNECT_DISCONNECT_REQ_MKT_DATA_GLD_SLV_ONLY",
                error_type=error_type,
                error_message_redacted=_redact_error_message(error_message) if error_type not in {"REALTIME", "DELAYED", "DELAYED_FROZEN"} else "",
                evidence=evidence,
                recommendation=(
                    "archive_market_data_result_without_account_positions_historical_data_contract_qualification_orders_or_telegram"
                    if error_type in {"REALTIME", "DELAYED", "DELAYED_FROZEN"}
                    else "review_ibkr_connection_market_data_permission_or_subscription_before_any_later_phase"
                ),
                timestamp_utc=timestamp,
            )
        )
    return rows


def _status_from_result(result: Dict[str, Any]) -> Tuple[str, str]:
    delayed_or_realtime = str(result.get("delayed_or_realtime", "UNKNOWN"))
    any_present = any(bool(result.get(name, False)) for name in ("bid_present", "ask_present", "last_present", "close_present"))
    if delayed_or_realtime in {"REALTIME", "DELAYED", "DELAYED_FROZEN"}:
        return delayed_or_realtime, delayed_or_realtime
    if any_present:
        return "REALTIME_OR_DELAYED_UNSPECIFIED", "UNKNOWN_ERROR"
    return "NO_DATA", "NO_DATA"


def build_us_etf_market_data_execute_rows(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    generated_at: Optional[str] = None,
    market_data_func: Optional[MarketDataFunc] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    run_id = _run_id(timestamp)
    if not operator_approved:
        return [
            _row(
                run_id=run_id,
                symbol=symbol,
                operator_approved=False,
                market_data_request_attempted=False,
                market_data_status="DENIED",
                ticker_received=False,
                bid_present=False,
                ask_present=False,
                last_present=False,
                close_present=False,
                delayed_or_realtime="UNKNOWN",
                external_effect="NONE",
                error_type="OPERATOR_APPROVAL_REQUIRED",
                error_message_redacted="OPERATOR_APPROVAL_REQUIRED",
                evidence="--operator-approved flag was not supplied",
                recommendation="rerun only after explicit operator approval for one GLD and one SLV market data request",
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

    requester = market_data_func or _ib_insync_request_us_etf_market_data
    results, global_error_type, error_message = requester(config, SYMBOLS)
    return _rows_from_results(
        run_id=run_id,
        timestamp=timestamp,
        results=results,
        global_error_type=global_error_type,
        error_message=error_message,
    )


def write_us_etf_market_data_execute_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_market_data_execute_report(rows: Sequence[Dict[str, str]]) -> str:
    summary_lines = [
        f"- {row['symbol']}_market_data_status={row['market_data_status']} error_type={row['error_type']} bid_present={row['bid_present']} ask_present={row['ask_present']} last_present={row['last_present']} close_present={row['close_present']}"
        for row in rows
    ]
    error_lines = [f"- {error_type}" for error_type in ERROR_TYPES]
    any_present = any(
        row[field] == YES_TEXT
        for row in rows
        for field in ("bid_present", "ask_present", "last_present", "close_present")
    )
    lines = [
        "# Phase 569-572 GLD / SLV Market Data Execute",
        "",
        "## Final Result",
        "",
        f"- operator_approved={rows[0]['operator_approved'] if rows else NO_TEXT}",
        "- symbols_requested=GLD,SLV",
        f"- any_bid_ask_last_close_present={YES_TEXT if any_present else NO_TEXT}",
        *[f"- {row['symbol']}_market_data_status={row['market_data_status']}" for row in rows],
        "",
        "## Scope Boundary",
        "",
        "- authorized symbols: GLD, SLV",
        "- authorized action: connect, reqMktData once per symbol, disconnect",
        "",
        "## Market Data Summary",
        "",
        *summary_lines,
        "",
        "## Error Taxonomy",
        "",
        *error_lines,
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- account_read_attempted=NO",
        "- positions_read_attempted=NO",
        "- historical_data_requested=NO",
        "- contract_qualification_attempted=NO",
        "- orders_submitted=NO",
        "- telegram_real_send_attempted=NO",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_market_data_execute.csv",
        "- report=reports/operator_us_etf_market_data_execute_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- market data status only reflects this single authorized GLD / SLV request run",
        "- this phase does not verify account, position, historical data, contract qualification, order, cancel, rebalance, or Telegram behavior",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_market_data_execute_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_market_data_execute_report(rows), encoding="utf-8")


def generate_us_etf_market_data_execute(
    *,
    operator_approved: bool,
    config_path: PathLike = "config.yaml",
    output_csv: PathLike = "operator_us_etf_market_data_execute.csv",
    output_report: PathLike = "reports/operator_us_etf_market_data_execute_report.md",
    generated_at: Optional[str] = None,
    market_data_func: Optional[MarketDataFunc] = None,
) -> List[Dict[str, str]]:
    rows = build_us_etf_market_data_execute_rows(
        operator_approved=operator_approved,
        config_path=config_path,
        generated_at=generated_at,
        market_data_func=market_data_func,
    )
    write_us_etf_market_data_execute_csv(output_csv, rows)
    write_us_etf_market_data_execute_report(output_report, rows)
    return rows


def any_market_data_field_present(rows: Sequence[Dict[str, str]]) -> bool:
    return any(
        row[field] == YES_TEXT
        for row in rows
        for field in ("bid_present", "ask_present", "last_present", "close_present")
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute Phase 569-572 GLD/SLV market data requests.")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-csv", default="operator_us_etf_market_data_execute.csv")
    parser.add_argument(
        "--output-report",
        default="reports/operator_us_etf_market_data_execute_report.md",
    )
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_us_etf_market_data_execute(
        operator_approved=args.operator_approved,
        config_path=args.config,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    if not args.operator_approved:
        print("[US_ETF_MARKET_DATA_EXECUTE] denied")
        print("operator_approved=NO")
        print("market_data_request_attempted=NO")
        print("error_type=OPERATOR_APPROVAL_REQUIRED")
        print("DENIED / OPERATOR_APPROVAL_REQUIRED")
        print(f"csv={args.output_csv}")
        print(f"report={args.output_report}")
        return 2

    print("[US_ETF_MARKET_DATA_EXECUTE] generated")
    print("operator_approved=YES")
    print("symbols_requested=GLD,SLV")
    print("market_data_request_attempted=YES")
    print("account_read_attempted=NO")
    print("positions_read_attempted=NO")
    print("historical_data_requested=NO")
    print("contract_qualification_attempted=NO")
    print("orders_submitted=NO")
    print("telegram_real_send_attempted=NO")
    for row in rows:
        print(f"{row['symbol']}_market_data_status={row['market_data_status']}")
        print(f"{row['symbol']}_error_type={row['error_type']}")
        print(f"{row['symbol']}_bid_present={row['bid_present']}")
        print(f"{row['symbol']}_ask_present={row['ask_present']}")
        print(f"{row['symbol']}_last_present={row['last_present']}")
        print(f"{row['symbol']}_close_present={row['close_present']}")
    print(f"any_bid_ask_last_close_present={YES_TEXT if any_market_data_field_present(rows) else NO_TEXT}")
    print(f"csv={args.output_csv}")
    print(f"report={args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
