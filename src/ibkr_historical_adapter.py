from __future__ import annotations

from pathlib import Path
from typing import Any
import csv

SUPPORTED_SYMBOLS = {"1540.T", "1542.T"}


def build_ibkr_historical_request_plan(
    symbols: list[str],
    duration: str = "1 Y",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: int = 1,
) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for symbol in symbols:
        adapter_status = "supported" if symbol in SUPPORTED_SYMBOLS else "unsupported_symbol"
        plans.append(
            {
                "symbol": symbol,
                "duration": duration,
                "bar_size": bar_size,
                "what_to_show": what_to_show,
                "use_rth": use_rth,
                "adapter_status": adapter_status,
                "notes": "read_only|no_auto_trade|request_plan_only",
            }
        )
    return plans


def validate_ibkr_historical_plan(plan: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    validation_status = "valid"

    if not plan.get("symbol"):
        warnings.append("empty_symbol")
        validation_status = "invalid"
    if plan.get("bar_size") != "1 day":
        warnings.append("invalid_bar_size")
        validation_status = "invalid"
    if plan.get("what_to_show") != "TRADES":
        warnings.append("invalid_what_to_show")
        validation_status = "invalid"
    if plan.get("use_rth") != 1:
        warnings.append("invalid_use_rth")
        validation_status = "invalid"
    if plan.get("adapter_status") == "unsupported_symbol":
        warnings.append("unsupported_symbol")

    out = dict(plan)
    out["validation_status"] = validation_status
    out["warning_flags"] = "|".join(warnings) if warnings else "none"
    return out


def write_ibkr_historical_plan_csv(plans: list[dict[str, Any]], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol",
        "duration",
        "bar_size",
        "what_to_show",
        "use_rth",
        "adapter_status",
        "validation_status",
        "warning_flags",
        "notes",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for plan in plans:
            writer.writerow(plan)


def write_ibkr_raw_prices_csv(rows: list[dict[str, Any]], path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "symbol", "close", "currency", "source", "notes"]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            payload = dict(row)
            payload["source"] = "ibkr_historical_bars_candidate"
            payload["notes"] = "read_only|not_calibrated|user_must_validate"
            writer.writerow(payload)


def summarize_ibkr_historical_adapter(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": row.get("symbol"),
            "adapter_status": row.get("adapter_status"),
            "validation_status": row.get("validation_status", "unknown"),
            "warning_flags": row.get("warning_flags", "none"),
        }
        for row in plans
    ]


def build_ibkr_historical_fetch_config(
    execute: bool = False,
    symbols: list[str] | None = None,
    duration: str = "1 Y",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: int = 1,
) -> dict[str, Any]:
    selected_symbols = symbols or ["1540.T", "1542.T"]
    mode = "execute" if execute else "dry_run"
    safety_status = "read_only_historical_fetch" if execute else "plan_only"
    return {
        "execute": execute,
        "explicit_user_confirmed": bool(execute),
        "symbols": selected_symbols,
        "duration": duration,
        "bar_size": bar_size,
        "what_to_show": what_to_show,
        "use_rth": use_rth,
        "mode": mode,
        "safety_status": safety_status,
        "notes": "read_only|no_auto_trade|user_explicit_execute_required",
    }


def validate_ibkr_historical_fetch_config(config: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    validation_status = "valid"

    if not isinstance(config.get("execute"), bool):
        warnings.append("invalid_execute_type")
        validation_status = "invalid"
    symbols = config.get("symbols") or []
    if not symbols:
        warnings.append("empty_symbols")
        validation_status = "invalid"
    if any(symbol not in SUPPORTED_SYMBOLS for symbol in symbols):
        warnings.append("unsupported_symbol")
        validation_status = "invalid"
    if config.get("bar_size") != "1 day":
        warnings.append("invalid_bar_size")
        validation_status = "invalid"
    if config.get("what_to_show") != "TRADES":
        warnings.append("invalid_what_to_show")
        validation_status = "invalid"
    if config.get("use_rth") != 1:
        warnings.append("invalid_use_rth")
        validation_status = "invalid"
    if config.get("execute") is True and config.get("explicit_user_confirmed") is not True:
        warnings.append("explicit_user_confirmation_required")
        validation_status = "invalid"

    out = dict(config)
    out["validation_status"] = validation_status
    out["warning_flags"] = "|".join(warnings) if warnings else "none"
    return out


def convert_ibkr_bars_to_raw_rows(symbol: str, currency: str, bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not bars:
        return []
    rows: list[dict[str, Any]] = []
    for bar in bars:
        if isinstance(bar, dict):
            date_value = bar.get("date", "")
            close_value = bar.get("close", "")
        else:
            date_value = getattr(bar, "date", "")
            close_value = getattr(bar, "close", "")
        date_text = str(date_value)
        if len(date_text) == 8 and date_text.isdigit():
            date_text = f"{date_text[0:4]}-{date_text[4:6]}-{date_text[6:8]}"
        rows.append({
            "date": date_text,
            "symbol": symbol,
            "close": close_value,
            "currency": currency,
            "source": "ibkr_historical_bars",
            "notes": "read_only|not_calibrated|user_must_validate|ibkr_historical_bars",
        })
    return rows


def write_ibkr_historical_fetch_report(path: str, rows: list[dict[str, Any]], config: dict[str, Any], times: dict[str, str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# IBKR Historical Fetch Report",
        "",
        "## 当前时间",
        f"- JST: {times['jst']}",
        f"- CST: {times['cst']}",
        f"- ET: {times['et']}",
        "",
        "## 模型状态",
        "- ibkr_historical_fetch",
        "- research_only",
        "- no_auto_trade",
        f"- {config.get('mode', 'dry_run')}",
        "",
        "## 边界声明",
        "- 默认 dry-run；",
        "- execute 模式需要显式 CLI 开关；",
        "- 只读历史行情；",
        "- 不下单；",
        "- 不撤单；",
        "- 不写入 calibration 参数；",
        "- 用户必须再运行 validate-history。",
        "",
        "## Fetch Summary",
        "| symbol | row_count | fetch_status | warning_flags |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row.get('symbol','')} | {row.get('row_count',0)} | {row.get('fetch_status','')} | {row.get('warning_flags','none')} |")
    p.write_text("\n".join(lines), encoding="utf-8")
