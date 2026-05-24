from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

DASHBOARD_READY = "DASHBOARD_READY"
DASHBOARD_PARTIAL = "DASHBOARD_PARTIAL"
DASHBOARD_SAFETY_REVIEW_REQUIRED = "DASHBOARD_SAFETY_REVIEW_REQUIRED"
DASHBOARD_BLOCKED = "DASHBOARD_BLOCKED"

CORE_ARTIFACTS = (
    "latest_daily_operator_handoff_summary.csv",
    "research_trading_plan.csv",
    "watchlist_universe.csv",
    "telegram_notification_gate.csv",
)

OPTIONAL_ARTIFACTS = (
    "latest_run_manifest.csv",
    "reports/latest_operator_handoff_summary.md",
    "reports/latest_run_manifest.md",
    "reports/research_trading_plan_report.md",
    "reports/watchlist_universe_report.md",
    "reports/telegram_notification_gate_report.md",
    "reports/telegram_notification_approval_preview.md",
    "first_operator_run_post_analysis.csv",
    "ibkr_market_data_api_errors.csv",
)

REPORT_LINKS = (
    ("Operator handoff summary", "latest_operator_handoff_summary.md"),
    ("Latest run manifest", "latest_run_manifest.md"),
    ("Research trading plan report", "research_trading_plan_report.md"),
    ("Watchlist universe report", "watchlist_universe_report.md"),
    ("Telegram gate report", "telegram_notification_gate_report.md"),
    ("Telegram approval preview", "telegram_notification_approval_preview.md"),
)

SAFETY_FIELDS = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)

FORBIDDEN_OPERATOR_WORDS = (
    "BUY",
    "SELL",
    "ORDER",
    "CANCEL",
    "REBALANCE",
    "AUTO_TRADE",
    "EXECUTE",
)

PathLike = Union[str, Path]


@dataclass(frozen=True)
class CsvArtifact:
    relative_path: str
    status: str
    rows: List[Dict[str, str]]


@dataclass(frozen=True)
class DashboardData:
    dashboard_status: str
    generated_at: str
    artifact_statuses: Dict[str, str]
    missing_artifacts: List[str]
    optional_missing_artifacts: List[str]
    safety_flags: Dict[str, str]
    operator_status: str
    research_status: str
    watchlist_status: str
    telegram_status: str
    symbol_rows: List[Dict[str, str]]
    api_error_summary: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _truthy(value: object) -> bool:
    return _lower(value) in {"1", "yes", "y", "true", "triggered", "allowed"}


def _read_csv(root: Path, relative_path: str) -> CsvArtifact:
    path = root / relative_path
    if not path.exists():
        return CsvArtifact(relative_path, "MISSING", [])
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return CsvArtifact(relative_path, "PRESENT" if rows else "EMPTY", rows)


def _artifact_status(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.exists():
        return "MISSING"
    return "PRESENT" if path.stat().st_size > 0 else "EMPTY"


def _symbol(row: Dict[str, str]) -> str:
    return _clean(row.get("display_symbol")) or _clean(row.get("symbol")) or _clean(row.get("local_symbol"))


def _index_by_symbol(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}
    for row in rows:
        symbol = _symbol(row)
        if symbol and symbol not in result:
            result[symbol] = row
    return result


def _first_value(rows: Sequence[Dict[str, str]], fields: Sequence[str], default: str = "missing") -> str:
    for row in rows:
        for field in fields:
            value = _clean(row.get(field))
            if value:
                return value
    return default


def _status_values(rows: Sequence[Dict[str, str]], fields: Sequence[str]) -> str:
    values: List[str] = []
    for row in rows:
        for field in fields:
            value = _clean(row.get(field))
            if value and value not in values:
                values.append(value)
    return ", ".join(values[:4]) if values else "missing"


def _has_forbidden_operator_word(text: str) -> bool:
    upper = text.upper()
    return any(re.search(rf"(?<![A-Z0-9_]){re.escape(word)}(?![A-Z0-9_])", upper) for word in FORBIDDEN_OPERATOR_WORDS)


def _safe_operator_action(value: str) -> str:
    text = _clean(value) or "manual review only"
    if _has_forbidden_operator_word(text):
        return "manual review only"
    return text


def _field_or_missing(row: Optional[Dict[str, str]], field: str) -> str:
    if not row:
        return "missing"
    return _clean(row.get(field)) or "missing"


def _aggregate_safety_flags(artifacts: Sequence[CsvArtifact]) -> Dict[str, str]:
    flags: Dict[str, str] = {field: FALSE_TEXT for field in SAFETY_FIELDS}
    for artifact in artifacts:
        for row in artifact.rows:
            if not _clean(row.get("action_allowed")) or _lower(row.get("action_allowed")) != FALSE_TEXT:
                flags["action_allowed"] = TRUE_TEXT
            for field in SAFETY_FIELDS[1:]:
                if _truthy(row.get(field)):
                    flags[field] = TRUE_TEXT
    return flags


def _build_symbol_rows(
    handoff: CsvArtifact,
    research: CsvArtifact,
    watchlist: CsvArtifact,
) -> List[Dict[str, str]]:
    handoff_by_symbol = _index_by_symbol(handoff.rows)
    research_by_symbol = _index_by_symbol(research.rows)
    watchlist_by_symbol = _index_by_symbol(watchlist.rows)
    ordered_symbols: List[str] = ["GLD", "SLV"]
    for symbol in ("1540", "1542", "518880"):
        if symbol in watchlist_by_symbol:
            ordered_symbols.append(symbol)
    for source in (handoff_by_symbol, research_by_symbol, watchlist_by_symbol):
        for symbol in source:
            if symbol not in ordered_symbols:
                ordered_symbols.append(symbol)

    rows: List[Dict[str, str]] = []
    for symbol in ordered_symbols:
        handoff_row = handoff_by_symbol.get(symbol)
        research_row = research_by_symbol.get(symbol)
        watchlist_row = watchlist_by_symbol.get(symbol)
        rows.append(
            {
                "symbol": symbol,
                "price_status": _field_or_missing(handoff_row, "price_status")
                if handoff_row
                else _field_or_missing(research_row, "price_status"),
                "data_delay_flag": _field_or_missing(handoff_row, "data_delay_flag")
                if handoff_row
                else _field_or_missing(research_row, "data_delay_flag"),
                "research_plan_status": _field_or_missing(research_row, "research_plan_status"),
                "recommended_operator_action": _safe_operator_action(
                    _field_or_missing(handoff_row, "recommended_operator_action")
                    if handoff_row
                    else _field_or_missing(research_row, "recommended_operator_action")
                ),
                "ibkr_universe_allowed": _field_or_missing(watchlist_row, "ibkr_universe_allowed"),
                "manual_review_required": _field_or_missing(watchlist_row, "manual_review_required")
                if watchlist_row
                else _field_or_missing(handoff_row, "manual_review_required"),
            }
        )
    return rows


def _api_error_summary(root: Path, handoff: CsvArtifact, research: CsvArtifact) -> str:
    error_file = _read_csv(root, "ibkr_market_data_api_errors.csv")
    codes: List[str] = []
    for row in list(error_file.rows) + list(handoff.rows) + list(research.rows):
        for field in ("error_code", "api_error_codes", "error_codes_detected"):
            for part in _clean(row.get(field)).replace(";", ",").split(","):
                code = part.strip()
                if code and code not in codes:
                    codes.append(code)
    if not codes and error_file.status == "MISSING":
        return "optional artifact missing"
    if not codes:
        return "none"
    return ", ".join(codes[:12])


def build_dashboard_data(root: PathLike = ".") -> DashboardData:
    root_path = Path(root)
    handoff = _read_csv(root_path, "latest_daily_operator_handoff_summary.csv")
    research = _read_csv(root_path, "research_trading_plan.csv")
    watchlist = _read_csv(root_path, "watchlist_universe.csv")
    telegram = _read_csv(root_path, "telegram_notification_gate.csv")
    core_artifacts = (handoff, research, watchlist, telegram)

    artifact_statuses = {path: _artifact_status(root_path, path) for path in CORE_ARTIFACTS + OPTIONAL_ARTIFACTS}
    missing_core = [artifact.relative_path for artifact in core_artifacts if artifact.status != "PRESENT"]
    optional_missing = [path for path in OPTIONAL_ARTIFACTS if artifact_statuses[path] != "PRESENT"]
    safety_flags = _aggregate_safety_flags(core_artifacts)

    if any(value == TRUE_TEXT for value in safety_flags.values()):
        dashboard_status = DASHBOARD_SAFETY_REVIEW_REQUIRED
    elif all(artifact.status != "PRESENT" for artifact in core_artifacts):
        dashboard_status = DASHBOARD_BLOCKED
    elif missing_core or optional_missing:
        dashboard_status = DASHBOARD_PARTIAL
    else:
        dashboard_status = DASHBOARD_READY

    operator_status = _first_value(handoff.rows, ("top_level_status", "operator_status"))
    research_status = _status_values(research.rows, ("top_level_status", "research_plan_status", "plan_status"))
    watchlist_status = _status_values(watchlist.rows, ("top_level_status", "universe_status", "validation_status"))
    telegram_status = _first_value(telegram.rows, ("top_level_status", "telegram_send_status"))

    return DashboardData(
        dashboard_status=dashboard_status,
        generated_at=datetime.now(timezone.utc).isoformat(),
        artifact_statuses=artifact_statuses,
        missing_artifacts=missing_core,
        optional_missing_artifacts=optional_missing,
        safety_flags=safety_flags,
        operator_status=operator_status,
        research_status=research_status,
        watchlist_status=watchlist_status,
        telegram_status=telegram_status,
        symbol_rows=_build_symbol_rows(handoff, research, watchlist),
        api_error_summary=_api_error_summary(root_path, handoff, research),
    )


def _html_cell(value: object) -> str:
    return escape(_clean(value))


def _kv_table(rows: Sequence[Tuple[str, str]]) -> str:
    body = "\n".join(f"<tr><th>{_html_cell(key)}</th><td>{_html_cell(value)}</td></tr>" for key, value in rows)
    return f"<table>{body}</table>"


def _symbol_table(rows: Sequence[Dict[str, str]]) -> str:
    fields = (
        "symbol",
        "price_status",
        "data_delay_flag",
        "research_plan_status",
        "recommended_operator_action",
        "ibkr_universe_allowed",
        "manual_review_required",
    )
    header = "".join(f"<th>{_html_cell(field)}</th>" for field in fields)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{_html_cell(row.get(field))}</td>" for field in fields) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"


def _artifact_list(items: Sequence[str], empty_text: str) -> str:
    if not items:
        return f"<p>{_html_cell(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{_html_cell(item)}</li>" for item in items) + "</ul>"


def build_dashboard_html(data: DashboardData) -> str:
    safety_rows = [(field, data.safety_flags[field]) for field in SAFETY_FIELDS]
    artifact_rows = [(path, status) for path, status in data.artifact_statuses.items()]
    link_items = "\n".join(
        f'<li><a href="{escape(path, quote=True)}">{_html_cell(label)}</a></li>' for label, path in REPORT_LINKS
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Precious Metals Local Dashboard</title>",
            "<style>",
            "body{font-family:Arial,sans-serif;margin:24px;color:#1f2933;background:#f7f8fa;line-height:1.45}",
            "main{max-width:1120px;margin:0 auto}",
            "section{background:#fff;border:1px solid #d8dde3;border-radius:6px;margin:16px 0;padding:16px}",
            "h1{font-size:28px;margin:0 0 8px}h2{font-size:18px;margin:0 0 12px}",
            "table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}",
            "th,td{border:1px solid #d8dde3;padding:8px;text-align:left;vertical-align:top}th{background:#eef1f4}",
            ".status{display:inline-block;padding:4px 8px;border-radius:4px;background:#e8f0fe;font-weight:700}",
            ".warning{color:#8a4b00}.safety{font-weight:700}",
            "a{color:#075985}",
            "</style>",
            "</head>",
            "<body><main>",
            "<section>",
            "<h1>Precious Metals Local Dashboard</h1>",
            f'<p><span class="status">dashboard_status={_html_cell(data.dashboard_status)}</span></p>',
            _kv_table(
                [
                    ("generated_at", data.generated_at),
                    ("offline_only", TRUE_TEXT),
                    ("manual_review_only", TRUE_TEXT),
                    ("operator_handoff_status", data.operator_status),
                    ("research_plan_status", data.research_status),
                    ("watchlist_status", data.watchlist_status),
                    ("telegram_gate_status", data.telegram_status),
                ]
            ),
            "<p>Offline only: this static page is generated from local artifacts and does not start a server or contact broker, market data, account, position, historical, or Telegram services.</p>",
            "<p>Manual review only: the dashboard is a local status view and does not provide execution instructions.</p>",
            "</section>",
            '<section id="safety-summary"><h2>Safety Summary</h2>',
            _kv_table(safety_rows),
            "</section>",
            '<section id="operator-handoff-summary"><h2>Operator Handoff Summary</h2>',
            _kv_table([("top_level_operator_handoff_status", data.operator_status)]),
            "</section>",
            '<section id="research-trading-plan-summary"><h2>Research Trading Plan Summary</h2>',
            _kv_table([("research_plan_top_level_status", data.research_status)]),
            "</section>",
            '<section id="watchlist-universe-summary"><h2>Watchlist Universe Summary</h2>',
            _kv_table([("watchlist_top_level_status", data.watchlist_status)]),
            "</section>",
            '<section id="telegram-gate-summary"><h2>Telegram Gate Summary</h2>',
            _kv_table([("telegram_gate_top_level_status", data.telegram_status)]),
            "</section>",
            '<section id="symbol-summary"><h2>Symbol Summary</h2>',
            _symbol_table(data.symbol_rows),
            "</section>",
            '<section id="api-error-summary"><h2>API Error Summary</h2>',
            _kv_table([("api_error_summary", data.api_error_summary)]),
            "</section>",
            '<section id="latest-report-links"><h2>Latest Report Links</h2>',
            f"<ul>{link_items}</ul>",
            "</section>",
            '<section id="missing-artifact-warnings"><h2>Missing Artifact Warnings</h2>',
            '<div class="warning">',
            "<h3>Core artifacts</h3>",
            _artifact_list(data.missing_artifacts, "none"),
            "<h3>Optional artifacts</h3>",
            _artifact_list(data.optional_missing_artifacts, "none"),
            "</div>",
            "</section>",
            '<section id="artifact-status"><h2>Artifact Status</h2>',
            _kv_table(artifact_rows),
            "</section>",
            '<section id="next-manual-operator-step"><h2>Next Manual Operator Step</h2>',
            "<p>Review the local summaries, resolve any missing core artifacts or safety review flags, then record the operator decision outside this dashboard.</p>",
            "</section>",
            "</main></body></html>",
            "",
        ]
    )


def write_dashboard(path: PathLike, html_text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")


def generate_dashboard(root: PathLike = ".", output_html: PathLike = "reports/dashboard.html") -> DashboardData:
    data = build_dashboard_data(root)
    write_dashboard(Path(root) / output_html, build_dashboard_html(data))
    return data


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an offline static local operator dashboard from local artifacts.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-html", default="reports/dashboard.html")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    data = generate_dashboard(args.root, args.output_html)
    print("[PASS] Local dashboard generated")
    print(f"dashboard_status={data.dashboard_status}")
    print("offline_only=true")
    for field in SAFETY_FIELDS:
        print(f"{field}={data.safety_flags[field]}")
    print(f"dashboard path: {args.output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
