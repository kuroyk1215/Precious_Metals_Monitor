from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PHASE = "Phase 557-560"
SOURCE_PHASE = "Phase 553-556"
SYMBOLS = ("GLD", "SLV")
ASSET_CLASS = "ETF"
EXCHANGE = "SMART"
CURRENCY = "USD"
YES_TEXT = "YES"
NO_TEXT = "NO"
READY_STATUS = "US_ETF_SYMBOL_MASTER_SNAPSHOT_READY"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
DATA_SUBSCRIPTION_DEPENDENCY = "US_ETF_MARKET_DATA_PERMISSION_AND_SUBSCRIPTION_NOT_VERIFIED"

CSV_FIELDS = (
    "phase",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "source_phase",
    "qualification_status",
    "qualified",
    "contract_metadata_available",
    "con_id_present",
    "primary_exchange_redacted",
    "market_data_verified",
    "historical_data_verified",
    "account_read_verified",
    "positions_read_verified",
    "trading_enabled",
    "jp_status",
    "cn_status",
    "data_subscription_dependency",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _source_by_symbol(path: PathLike) -> Dict[str, Dict[str, str]]:
    rows = _read_rows(path)
    return {row.get("symbol", ""): row for row in rows if row.get("symbol") in SYMBOLS}


def build_us_etf_symbol_master_snapshot_rows(
    *,
    source_csv: PathLike = "operator_us_etf_contract_qualification_execute.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    source_rows = _source_by_symbol(source_csv)
    rows: List[Dict[str, str]] = []
    for symbol in SYMBOLS:
        source = source_rows.get(symbol, {})
        qualification_status = source.get("qualification_status", "SOURCE_MISSING")
        qualified = YES_TEXT if source.get("qualified") == YES_TEXT and qualification_status == "QUALIFIED" else NO_TEXT
        con_id_present = YES_TEXT if source.get("con_id_present") == YES_TEXT else NO_TEXT
        primary_exchange_redacted = source.get("primary_exchange_redacted") or "MISSING"
        contract_metadata_available = YES_TEXT if qualified == YES_TEXT and con_id_present == YES_TEXT else NO_TEXT
        rows.append(
            {
                "phase": PHASE,
                "symbol": symbol,
                "asset_class": source.get("asset_class") or ASSET_CLASS,
                "exchange": source.get("exchange") or EXCHANGE,
                "currency": source.get("currency") or CURRENCY,
                "source_phase": SOURCE_PHASE,
                "qualification_status": qualification_status,
                "qualified": qualified,
                "contract_metadata_available": contract_metadata_available,
                "con_id_present": con_id_present,
                "primary_exchange_redacted": primary_exchange_redacted,
                "market_data_verified": NO_TEXT,
                "historical_data_verified": NO_TEXT,
                "account_read_verified": NO_TEXT,
                "positions_read_verified": NO_TEXT,
                "trading_enabled": NO_TEXT,
                "jp_status": JP_STATUS,
                "cn_status": CN_STATUS,
                "data_subscription_dependency": DATA_SUBSCRIPTION_DEPENDENCY,
                "external_effect": "NONE",
                "evidence": source.get("evidence") or f"{symbol}_source_qualification_result_missing",
                "recommendation": (
                    "use_as_us_etf_symbol_master_input_after_separate_market_data_permission_gate"
                    if qualified == YES_TEXT
                    else "do_not_use_until_source_qualification_artifact_is_qualified"
                ),
                "timestamp_utc": timestamp,
            }
        )
    return rows


def write_us_etf_symbol_master_snapshot_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _qualified_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(1 for row in rows if row["qualified"] == YES_TEXT)


def build_us_etf_symbol_master_snapshot_report(rows: Sequence[Dict[str, str]]) -> str:
    snapshot_lines = [
        "| symbol | qualification_status | qualified | contract_metadata_available | con_id_present | primary_exchange_redacted |",
        "| --- | --- | --- | --- | --- | --- |",
        *[
            "| {symbol} | {qualification_status} | {qualified} | {contract_metadata_available} | {con_id_present} | {primary_exchange_redacted} |".format(
                **row
            )
            for row in rows
        ],
    ]
    lines = [
        "# Phase 557-560 GLD / SLV Symbol Master Snapshot",
        "",
        "## Final Snapshot Status",
        "",
        f"- symbol_master_status={READY_STATUS}",
        f"- source_phase={SOURCE_PHASE}",
        f"- symbols={','.join(SYMBOLS)}",
        f"- qualified_symbols_count={_qualified_count(rows)}",
        "",
        "## Scope Boundary",
        "",
        "- artifact-only / snapshot-only",
        "- source is archived Phase 553-556 qualification result",
        "- qualified does not mean market data verified",
        "",
        "## Source Qualification Summary",
        "",
        *[f"- {row['symbol']}_qualification_status={row['qualification_status']}" for row in rows],
        "",
        "## Symbol Master Snapshot",
        "",
        *snapshot_lines,
        "",
        "## JP / CN Frozen Status",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Explicitly Prohibited Actions",
        "",
        "- market_data_verified=NO",
        "- historical_data_verified=NO",
        "- account_read_verified=NO",
        "- positions_read_verified=NO",
        "- trading_enabled=NO",
        "- external_effect=NONE",
        "",
        "## Artifact Summary",
        "",
        "- csv=operator_us_etf_symbol_master_snapshot.csv",
        "- report=reports/operator_us_etf_symbol_master_snapshot_report.md",
        f"- row_count={len(rows)}",
        "",
        "## Residual Risks",
        "",
        "- market data permission and subscription remain unverified",
        "- historical data, account read, positions read, and trading remain unverified",
        "- primary exchange details remain redacted in the public artifact",
        "",
        "## Next Phase Preconditions",
        "",
        "- separate explicit permission gate is required before any market data request",
        "- US ETF adapter must consume this as a symbol master snapshot only",
        "- JP / CN remain frozen until subscription or data-source decision changes",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_symbol_master_snapshot_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_symbol_master_snapshot_report(rows), encoding="utf-8")


def generate_us_etf_symbol_master_snapshot(
    *,
    source_csv: PathLike = "operator_us_etf_contract_qualification_execute.csv",
    output_csv: PathLike = "operator_us_etf_symbol_master_snapshot.csv",
    output_report: PathLike = "reports/operator_us_etf_symbol_master_snapshot_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_us_etf_symbol_master_snapshot_rows(source_csv=source_csv, generated_at=generated_at)
    write_us_etf_symbol_master_snapshot_csv(output_csv, rows)
    write_us_etf_symbol_master_snapshot_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 557-560 GLD/SLV symbol master snapshot.")
    parser.add_argument("--source-csv", default="operator_us_etf_contract_qualification_execute.csv")
    parser.add_argument("--output-csv", default="operator_us_etf_symbol_master_snapshot.csv")
    parser.add_argument("--output-report", default="reports/operator_us_etf_symbol_master_snapshot_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_us_etf_symbol_master_snapshot(
        source_csv=args.source_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    by_symbol = {row["symbol"]: row for row in rows}
    print("[US_ETF_SYMBOL_MASTER_SNAPSHOT] generated")
    print(f"symbol_master_status={READY_STATUS}")
    print(f"source_phase={SOURCE_PHASE}")
    print("symbols=GLD,SLV")
    print(f"GLD_qualification_status={by_symbol['GLD']['qualification_status']}")
    print(f"SLV_qualification_status={by_symbol['SLV']['qualification_status']}")
    print(f"qualified_symbols_count={_qualified_count(rows)}")
    print("market_data_verified=NO")
    print("historical_data_verified=NO")
    print("account_read_verified=NO")
    print("positions_read_verified=NO")
    print("trading_enabled=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print("next_phase_market_data_permission_gate_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
