from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from src.local_market_data_store import DEFAULT_STORE_PATH, build_empty_store, load_manual_csv_to_store, load_store
from src.manual_csv_market_data_loader import (
    DEFAULT_SAMPLE_CSV,
    DEFAULT_TEMPLATE_CSV,
    preview_manual_csv,
    write_manual_csv_template,
    write_sample_manual_csv,
)
from src.market_data_validation import REQUIRED_FIELDS
from src.operator_final_product_ui_lock_pack import (
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    CN_STATUS,
    DASHBOARD_CSS,
    DASHBOARD_INDEX,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    IBKR_ERROR_CODE,
    JP_STATUS,
    NAVIGATION,
    NO_TEXT,
    OPERATOR_TIMELINE,
    POSITION_READ_FIELD,
    STATUS_SNAPSHOT,
    SYMBOLS_TEXT,
    UI_GENERATION,
    YES_TEXT,
    build_dashboard_css,
    build_dashboard_html as build_final_dashboard_html,
)
from src.public_data_pilot_adapter import build_public_data_pilot_dry_run, public_data_pilot_fetch
from src.public_data_source_registry import build_public_data_source_registry


PHASE = "Phase 1321-1520"
STATUS = "MANUAL_CSV_PUBLIC_DATA_PILOT_READY"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"

MANUAL_CSV_IMPORT_SNAPSHOT = "dashboard/data/manual_csv_import_snapshot.json"
PUBLIC_DATA_PILOT_SNAPSHOT = "dashboard/data/public_data_pilot_snapshot.json"
PUBLIC_DATA_SOURCE_REGISTRY_SNAPSHOT = "dashboard/data/public_data_source_registry_snapshot.json"
MARKET_DATA_VALIDATION_SNAPSHOT = "dashboard/data/market_data_validation_snapshot.json"
LOCAL_MARKET_DATA_STORE_SNAPSHOT = "dashboard/data/local_market_data_store_snapshot.json"
GLD_SLV_DATA_STATUS_SNAPSHOT = "dashboard/data/gld_slv_data_status_snapshot.json"
DATA_DRIVEN_RESEARCH_FRAMEWORK_SNAPSHOT = "dashboard/data/data_driven_research_framework_snapshot.json"
OUTPUT_CSV = "operator_manual_csv_public_data_pilot_pack.csv"
OUTPUT_REPORT = "reports/operator_manual_csv_public_data_pilot_pack_report.md"
OUTPUT_MANUAL_CSV_GUIDE = "reports/manual_csv_market_data_user_guide.md"
OUTPUT_PUBLIC_DATA_REPORT = "reports/public_data_pilot_report.md"
OUTPUT_DATA_DRIVEN_FRAMEWORK = "reports/data_driven_research_framework_GLD_SLV.md"
OUTPUT_PACK = "Precious_Metals_Monitor_Manual_CSV_Public_Data_Pilot_Pack.md"

ARTIFACTS = (
    DEFAULT_TEMPLATE_CSV,
    DEFAULT_SAMPLE_CSV,
    DEFAULT_STORE_PATH,
    DASHBOARD_INDEX,
    DASHBOARD_CSS,
    STATUS_SNAPSHOT,
    ARTIFACT_MANIFEST,
    BUILD_SNAPSHOT,
    OPERATOR_TIMELINE,
    MANUAL_CSV_IMPORT_SNAPSHOT,
    PUBLIC_DATA_PILOT_SNAPSHOT,
    PUBLIC_DATA_SOURCE_REGISTRY_SNAPSHOT,
    MARKET_DATA_VALIDATION_SNAPSHOT,
    LOCAL_MARKET_DATA_STORE_SNAPSHOT,
    GLD_SLV_DATA_STATUS_SNAPSHOT,
    DATA_DRIVEN_RESEARCH_FRAMEWORK_SNAPSHOT,
    FINAL_LANDING_AUDIT_SNAPSHOT,
    OUTPUT_CSV,
    OUTPUT_REPORT,
    OUTPUT_MANUAL_CSV_GUIDE,
    OUTPUT_PUBLIC_DATA_REPORT,
    OUTPUT_DATA_DRIVEN_FRAMEWORK,
    OUTPUT_PACK,
)
CSV_FIELDS = (
    "phase",
    "status",
    "ui_generation",
    "ui_final_locked",
    "manual_csv_loader_status",
    "manual_csv_import_status",
    "local_market_data_store_status",
    "public_data_registry_status",
    "public_data_pilot_status",
    "public_data_auto_fetch_enabled",
    "public_data_fetch_requires_explicit_allow",
    "real_time_market_data_enabled",
    "live_market_data_enabled",
    "source_connection_implemented",
    "ibkr_connection_enabled",
    "ibkr_error_code",
    "account_read_enabled",
    POSITION_READ_FIELD,
    "historical_data_enabled",
    "trading_enabled",
    "telegram_real_send_enabled",
    "jp_status",
    "cn_status",
    "symbols",
    "generated_at_utc",
)
PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _artifact_category(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".html":
        return "HTML"
    if suffix == ".css":
        return "CSS"
    if suffix == ".json":
        return "JSON"
    if suffix == ".csv":
        return "CSV"
    return "REPORT" if path.startswith("reports/") else "PACK"


def _artifact_local_href(path: str) -> str:
    return path.replace("dashboard/", "", 1) if path.startswith("dashboard/") else f"../{path}"


def build_status_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "ui_final_locked": YES_TEXT,
        "manual_csv_loader_status": "MANUAL_CSV_LOADER_READY",
        "manual_csv_import_status": "MANUAL_CSV_IMPORT_PREVIEW_READY",
        "local_market_data_store_status": "LOCAL_MARKET_DATA_STORE_READY",
        "public_data_registry_status": "PUBLIC_DATA_SOURCE_REGISTRY_READY",
        "public_data_pilot_status": "PUBLIC_DATA_PILOT_DRY_RUN_READY",
        "public_data_auto_fetch_enabled": NO_TEXT,
        "public_data_fetch_requires_explicit_allow": YES_TEXT,
        "real_time_market_data_enabled": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "source_connection_implemented": "PUBLIC_PILOT_ONLY_MANUAL_OR_EXPLICIT",
        "ibkr_connection_enabled": NO_TEXT,
        "market_data_status": MARKET_DATA_STATUS,
        "ibkr_error_code": IBKR_ERROR_CODE,
        "realtime_market_data_verified": NO_TEXT,
        "production_ready": NO_TEXT,
        "trading_enabled": NO_TEXT,
        "account_read_enabled": NO_TEXT,
        POSITION_READ_FIELD: NO_TEXT,
        "historical_data_enabled": NO_TEXT,
        "telegram_real_send_enabled": NO_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "symbols": SYMBOLS_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_build_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "ui_generation": UI_GENERATION,
        "ui_final_locked": YES_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_operator_timeline(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "timeline": [
            {"phase": "Phase 1161-1320", "theme": "Final product UI lock", "status": "READY"},
            {"phase": PHASE, "theme": "Manual CSV and public data pilot", "status": STATUS},
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_artifact_manifest(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "artifacts": [
            {
                "artifact_path": path,
                "type": Path(path).suffix.lstrip(".").upper() or "PACK",
                "category": _artifact_category(path),
                "local_href": _artifact_local_href(path),
                "external_effect": "NONE_UNLESS_EXPLICIT_PUBLIC_PILOT_FETCH",
            }
            for path in ARTIFACTS
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_final_landing_audit_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "LOCAL_PLATFORM_MVP_FINAL_AUDIT_READY",
        "ui_final_locked": YES_TEXT,
        "manual_csv_first_input": YES_TEXT,
        "public_data_auto_fetch_enabled": NO_TEXT,
        "all_external_actions_blocked_by_default": YES_TEXT,
        "no_ibkr_connection": YES_TEXT,
        "no_trading": YES_TEXT,
        "no_telegram_real_send": YES_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_gld_slv_data_status_snapshot(store: Dict[str, object], generated_at: Optional[str] = None) -> Dict[str, object]:
    symbols = store.get("symbols", {})
    return {
        "phase": PHASE,
        "status": "GLD_SLV_DATA_STATUS_READY",
        "symbols": symbols,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_data_driven_research_framework_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "DATA_DRIVEN_RESEARCH_FRAMEWORK_READY",
        "supported_symbols": ["GLD", "SLV"],
        "data_input_priority": ["Manual CSV", "Public Pilot"],
        "signal_generation_enabled": NO_TEXT,
        "report_mode": "FRAMEWORK_ONLY_UNTIL_VERIFIED_DATA",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_market_data_validation_snapshot(preview: Dict[str, object], generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "MARKET_DATA_VALIDATION_READY",
        "required_fields": list(REQUIRED_FIELDS),
        "preview_status": preview["status"],
        "row_count": preview["row_count"],
        "valid_row_count": preview["valid_row_count"],
        "invalid_row_count": preview["invalid_row_count"],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_dashboard_html(store: Dict[str, object], generated_at: Optional[str] = None) -> str:
    html = build_final_dashboard_html(generated_at)
    symbols = store.get("symbols", {})
    for symbol in ("GLD", "SLV"):
        entry = symbols.get(symbol, {}) if isinstance(symbols, dict) else {}
        data_status = entry.get("data_status", "待导入")
        source_display = entry.get("source_display", "None")
        latest_time = entry.get("latest_timestamp_utc", "暂无")
        old = (
            f"<div><dt>数据状态</dt><dd>等待数据源</dd></div>\n"
            f"                  <div><dt>报告状态</dt><dd>研究框架可用</dd></div>"
        )
        new = (
            f"<div><dt>数据状态</dt><dd>{data_status}</dd></div>\n"
            f"                  <div><dt>数据来源</dt><dd>{source_display}</dd></div>\n"
            f"                  <div><dt>最近更新时间</dt><dd>{latest_time}</dd></div>\n"
            f"                  <div><dt>报告状态</dt><dd>研究框架可用</dd></div>"
        )
        html = html.replace(old, new, 1)
    html = html.replace(
        '<article><span>手动 CSV</span><strong>可作为后续 fallback</strong></article>',
        '<article><span>手动 CSV</span><strong>第一优先输入</strong></article>',
    )
    return html


def build_operator_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Phase 1321-1520 Manual CSV Public Data Pilot Pack

- status: {STATUS}
- manual CSV loader ready
- local market data store ready
- GLD / SLV only
- public data source registry ready
- public data pilot dry-run ready
- public data auto fetch disabled
- public data fetch requires explicit allow
- no real-time market data
- no IBKR connection
- no IBKR market data request
- no account/position read
- no contract qualification
- no trading
- no Telegram real send
- no directional trading signal
- no target, stop, or take-profit levels
- JP / CN remain frozen
- generated_at_utc: {timestamp}
"""


def build_manual_csv_user_guide(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Manual CSV Market Data User Guide

Manual CSV is the first priority input path for GLD / SLV. Required fields: symbol, market, timestamp_utc, price, currency, source_name, source_type, data_delay_status.

Only GLD / SLV, market US, currency USD, and source_type manual or public_pilot are accepted. Valid data updates the local store only; it does not create trading instructions.

generated_at_utc: {timestamp}
"""


def build_public_data_pilot_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Public Data Pilot Report

- default network behavior: disabled
- explicit allow required: YES
- supported symbols: GLD / SLV
- candidates: Stooq, Alpha Vantage, Yahoo Finance
- Yahoo Finance automation: disabled
- fetch failure leaves local store unchanged
- no fabricated data

generated_at_utc: {timestamp}
"""


def build_data_driven_framework_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Data Driven Research Framework GLD / SLV

The framework can read validated local market data when available. Without verified data it remains a research framework and does not create trading instructions.

- GLD: research framework available
- SLV: research framework available
- data input priority: Manual CSV, Public Pilot
- real-time market data: disabled

generated_at_utc: {timestamp}
"""


def generate_manual_csv_public_data_pilot_pack(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    write_manual_csv_template(DEFAULT_TEMPLATE_CSV)
    write_sample_manual_csv(DEFAULT_SAMPLE_CSV)
    preview = preview_manual_csv(DEFAULT_SAMPLE_CSV)
    store = build_empty_store(timestamp)
    _write_json(DEFAULT_STORE_PATH, store)
    registry = build_public_data_source_registry(timestamp)
    pilot = build_public_data_pilot_dry_run(timestamp)
    status = build_status_snapshot(timestamp)
    row = {field: status.get(field, "") for field in CSV_FIELDS}

    _write_text(DASHBOARD_INDEX, build_dashboard_html(store, timestamp))
    _write_text(DASHBOARD_CSS, build_dashboard_css())
    _write_json(STATUS_SNAPSHOT, status)
    _write_json(ARTIFACT_MANIFEST, build_artifact_manifest(timestamp))
    _write_json(BUILD_SNAPSHOT, build_build_snapshot(timestamp))
    _write_json(OPERATOR_TIMELINE, build_operator_timeline(timestamp))
    _write_json(MANUAL_CSV_IMPORT_SNAPSHOT, preview)
    _write_json(PUBLIC_DATA_PILOT_SNAPSHOT, pilot)
    _write_json(PUBLIC_DATA_SOURCE_REGISTRY_SNAPSHOT, registry)
    _write_json(MARKET_DATA_VALIDATION_SNAPSHOT, build_market_data_validation_snapshot(preview, timestamp))
    _write_json(LOCAL_MARKET_DATA_STORE_SNAPSHOT, store)
    _write_json(GLD_SLV_DATA_STATUS_SNAPSHOT, build_gld_slv_data_status_snapshot(store, timestamp))
    _write_json(DATA_DRIVEN_RESEARCH_FRAMEWORK_SNAPSHOT, build_data_driven_research_framework_snapshot(timestamp))
    _write_json(FINAL_LANDING_AUDIT_SNAPSHOT, build_final_landing_audit_snapshot(timestamp))

    csv_path = Path(OUTPUT_CSV)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)
    _write_text(OUTPUT_REPORT, build_operator_report(timestamp))
    _write_text(OUTPUT_MANUAL_CSV_GUIDE, build_manual_csv_user_guide(timestamp))
    _write_text(OUTPUT_PUBLIC_DATA_REPORT, build_public_data_pilot_report(timestamp))
    _write_text(OUTPUT_DATA_DRIVEN_FRAMEWORK, build_data_driven_framework_report(timestamp))
    _write_text(OUTPUT_PACK, build_operator_report(timestamp))
    return row


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1321-1520 manual CSV public data pilot pack.")
    parser.parse_args(argv)
    row = generate_manual_csv_public_data_pilot_pack()
    print("[MANUAL_CSV_PUBLIC_DATA_PILOT_PACK] generated")
    print(f"phase={row['phase']}")
    print(f"status={row['status']}")
    print(f"manual_csv_loader_status={row['manual_csv_loader_status']}")
    print(f"local_market_data_store_status={row['local_market_data_store_status']}")
    print(f"public_data_pilot_status={row['public_data_pilot_status']}")
    print(f"public_data_auto_fetch_enabled={row['public_data_auto_fetch_enabled']}")
    print(f"csv={OUTPUT_CSV}")
    print(f"report={OUTPUT_REPORT}")
    print(f"pack={OUTPUT_PACK}")
    return 0


def manual_csv_import_preview_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Preview the sample GLD / SLV manual CSV without writing the store.")
    parser.add_argument("--input", default=DEFAULT_SAMPLE_CSV)
    args = parser.parse_args(argv)
    preview = preview_manual_csv(args.input)
    print("[MANUAL_CSV_IMPORT_PREVIEW] generated")
    print(f"status={preview['status']}")
    print(f"row_count={preview['row_count']}")
    print(f"valid_row_count={preview['valid_row_count']}")
    print(f"invalid_row_count={preview['invalid_row_count']}")
    print("store_written=NO")
    return 0 if preview["status"] == "MANUAL_CSV_IMPORT_PREVIEW_READY" else 2


def manual_csv_load_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Load an explicit GLD / SLV manual CSV into the local market data store.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--store", default=DEFAULT_STORE_PATH)
    args = parser.parse_args(argv)
    try:
        store = load_manual_csv_to_store(args.input, args.store)
    except ValueError as exc:
        print(f"[MANUAL_CSV_LOAD] failed: {exc}")
        return 2
    print("[MANUAL_CSV_LOAD] generated")
    print(f"status={store['status']}")
    print(f"store={args.store}")
    print("trade_signal_generated=NO")
    return 0


def public_data_pilot_dry_run_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Public data pilot dry-run without network.")
    parser.parse_args(argv)
    pilot = build_public_data_pilot_dry_run()
    print("[PUBLIC_DATA_PILOT_DRY_RUN] generated")
    print(f"status={pilot['status']}")
    print(f"public_data_auto_fetch_enabled={pilot['public_data_auto_fetch_enabled']}")
    print(f"public_data_fetch_requires_explicit_allow={pilot['public_data_fetch_requires_explicit_allow']}")
    return 0


def public_data_pilot_fetch_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Explicitly gated public data pilot fetch.")
    parser.add_argument("--allow-public-network", action="store_true")
    args = parser.parse_args(argv)
    result = public_data_pilot_fetch(args.allow_public_network)
    print("[PUBLIC_DATA_PILOT_FETCH] generated")
    print(f"status={result['status']}")
    print(f"network_request_made={result['network_request_made']}")
    return 0 if args.allow_public_network else 2


if __name__ == "__main__":
    raise SystemExit(main())
