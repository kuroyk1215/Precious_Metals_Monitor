from __future__ import annotations

from pathlib import Path
import csv

from src.manual_market_data_adapter import (
    ManualMarketDataRow,
    load_manual_market_data_csv,
    normalize_manual_market_data_rows,
)
from src.market_data_adapter_interface import (
    MarketDataAdapterRequest,
    MarketDataAdapterResult,
    validate_adapter_request_safety,
)


MANUAL_CSV_ADAPTER_TARGETS = [
    ("XAUUSD", "upstream_factor", "GLOBAL", "gold_spot_usd"),
    ("XAGUSD", "upstream_factor", "GLOBAL", "silver_spot_usd"),
    ("USDJPY", "upstream_factor", "FX", "fx_rate"),
    ("USDCNY", "upstream_factor", "FX", "fx_rate"),
    ("SGE_AU99_99", "upstream_factor", "CN", "shanghai_gold_benchmark"),
    ("1540.T", "etf_actual_price", "JP", "jp_gold_etf_actual_price"),
    ("1542.T", "etf_actual_price", "JP", "jp_silver_etf_actual_price"),
    ("518880.SH", "etf_actual_price", "CN", "cn_gold_etf_actual_price"),
]


def _join_flags(*values: str) -> str:
    flags: set[str] = set()
    for value in values:
        if not value or value == "none":
            continue
        flags.update(flag.strip() for flag in value.split(";") if flag.strip())

    flags.add("manual_csv_adapter")
    flags.add("adapter_interface")
    flags.add("local_file_only")
    flags.add("no_api_request")
    flags.add("no_ibkr_connection")
    flags.add("no_reqMktData")
    flags.add("no_reqHistoricalData")
    flags.add("no_order")
    flags.add("no_auto_trade")

    return ";".join(sorted(flags))


def build_manual_csv_adapter_requests() -> list[MarketDataAdapterRequest]:
    return [
        MarketDataAdapterRequest(
            provider_id="manual_csv",
            target_id=target_id,
            target_type=target_type,
            market=market,
            data_role=data_role,
            requested_mode="snapshot",
            requested_timeframe="latest",
            allow_network=False,
            allow_broker_connection=False,
            allow_trading=False,
            notes="manual CSV adapter interface request",
        )
        for target_id, target_type, market, data_role in MANUAL_CSV_ADAPTER_TARGETS
    ]


class ManualCsvMarketDataAdapter:
    provider_id = "manual_csv"

    def __init__(self, csv_path: str, tz_cfg: dict[str, str]) -> None:
        self.csv_path = csv_path
        self.tz_cfg = tz_cfg
        self.rows_by_target = self._load_rows(csv_path)

    def _load_rows(self, csv_path: str) -> dict[str, ManualMarketDataRow]:
        path = Path(csv_path)
        if not path.exists():
            return {}

        raw_rows, missing_fields = load_manual_market_data_csv(str(path))
        normalized_rows = normalize_manual_market_data_rows(raw_rows, missing_fields, self.tz_cfg)
        return {row.target_id: row for row in normalized_rows if row.target_id}

    def fetch_snapshot(self, request: MarketDataAdapterRequest) -> MarketDataAdapterResult:
        violations = validate_adapter_request_safety(request)
        if violations:
            return self._blocked_result(request, violations)

        row = self.rows_by_target.get(request.target_id)
        if row is None:
            return self._missing_result(request)

        adapter_status = "ok" if row.normalized_status == "ok" else row.normalized_status
        value = row.value if row.normalized_status == "ok" else "unavailable"

        return MarketDataAdapterResult(
            provider_id=request.provider_id,
            target_id=request.target_id,
            target_type=request.target_type,
            market=request.market,
            data_role=request.data_role,
            value=value,
            currency=row.currency,
            source=row.source,
            source_status=row.source_status,
            adapter_status=adapter_status,
            warning_flags=_join_flags(row.warning_flags),
            notes=row.notes,
            timestamp_jst=row.timestamp_jst,
            timestamp_et=row.timestamp_et,
        )

    def _blocked_result(self, request: MarketDataAdapterRequest, violations: list[str]) -> MarketDataAdapterResult:
        return MarketDataAdapterResult(
            provider_id=request.provider_id,
            target_id=request.target_id,
            target_type=request.target_type,
            market=request.market,
            data_role=request.data_role,
            value="unavailable",
            currency="unavailable",
            source="manual_csv_adapter",
            source_status="blocked_by_safety_violation",
            adapter_status="blocked_by_safety_violation",
            warning_flags=_join_flags(";".join(violations)),
            notes="request blocked by adapter safety validation",
            timestamp_jst="unavailable",
            timestamp_et="unavailable",
        )

    def _missing_result(self, request: MarketDataAdapterRequest) -> MarketDataAdapterResult:
        return MarketDataAdapterResult(
            provider_id=request.provider_id,
            target_id=request.target_id,
            target_type=request.target_type,
            market=request.market,
            data_role=request.data_role,
            value="unavailable",
            currency="unavailable",
            source="manual_csv_adapter",
            source_status="missing_target",
            adapter_status="unavailable",
            warning_flags=_join_flags("missing_manual_csv_target"),
            notes="target not found in manual CSV input",
            timestamp_jst="unavailable",
            timestamp_et="unavailable",
        )


def write_manual_csv_adapter_interface_csv(path: Path, rows: list[MarketDataAdapterResult]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "provider_id",
                "target_id",
                "target_type",
                "market",
                "data_role",
                "value",
                "currency",
                "source",
                "source_status",
                "adapter_status",
                "warning_flags",
                "notes",
                "timestamp_jst",
                "timestamp_et",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.provider_id,
                    r.target_id,
                    r.target_type,
                    r.market,
                    r.data_role,
                    r.value,
                    r.currency,
                    r.source,
                    r.source_status,
                    r.adapter_status,
                    r.warning_flags,
                    r.notes,
                    r.timestamp_jst,
                    r.timestamp_et,
                ]
            )


def write_manual_csv_adapter_interface_report(path: Path, rows: list[MarketDataAdapterResult], input_csv: str) -> None:
    statuses = sorted({r.adapter_status for r in rows})
    ok_count = sum(1 for r in rows if r.adapter_status == "ok")
    unavailable_count = sum(1 for r in rows if r.adapter_status == "unavailable")

    lines = [
        "# Manual CSV Market Data Adapter Interface Report",
        "",
        "- phase: Phase 7C",
        "- scope: manual CSV adapter implements market data interface",
        "- action: local CSV only; no connection and no data request is performed",
        f"- input_csv: {input_csv}",
        f"- row_count: {len(rows)}",
        f"- statuses: {','.join(statuses) if statuses else 'none'}",
        f"- ok_count: {ok_count}",
        f"- unavailable_count: {unavailable_count}",
        "",
        "## Adapter Results",
        "",
        "| target_id | target_type | market | value | currency | source_status | adapter_status |",
        "|---|---|---|---:|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r.target_id} | {r.target_type} | {r.market} | {r.value} | {r.currency} | {r.source_status} | {r.adapter_status} |"
        )

    lines.extend(
        [
            "",
            "## Safety Statement",
            "",
            "- local CSV only",
            "- no connection",
            "- no API request",
            "- no IBKR connection",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "- no automatic execution",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
