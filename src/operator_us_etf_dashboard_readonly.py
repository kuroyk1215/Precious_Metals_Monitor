from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 589-600"
DASHBOARD_ID = "US_ETF_DASHBOARD_READONLY"
SYMBOLS = ("GLD", "SLV")
CONNECTIVITY_STATUS = "VERIFIED_CONNECT_DISCONNECT"
CONTRACT_QUALIFICATION_STATUS = "GLD_SLV_QUALIFIED"
MARKET_DATA_STATUS = "BLOCKED_BY_SUBSCRIPTION"
MARKET_DATA_CLASSIFICATION = "MARKET_DATA_BLOCKED_BY_SUBSCRIPTION"
IBKR_ERROR_CODE = "10089"
YES_TEXT = "YES"
NO_TEXT = "NO"
JP_STATUS = "FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION"
CN_STATUS = "FROZEN_PENDING_DATA_SOURCE_DECISION"
OPERATOR_ACTION = "SUBSCRIBE_NETWORK_B_OR_CONTINUE_FRAMEWORK_ONLY_MVP"
DASHBOARD_ARTIFACT = "dashboard/us_etf_dashboard_readonly.html"
RECOMMENDATION = (
    "Keep the dashboard as a read-only artifact viewer; do not promote realtime market data readiness "
    "until a later verified subscription or explicitly approved delayed-data workflow exists."
)

CSV_FIELDS = (
    "phase",
    "dashboard_id",
    "symbol",
    "panel",
    "connectivity_status",
    "contract_qualification_status",
    "market_data_status",
    "market_data_classification",
    "subscription_required",
    "delayed_available",
    "realtime_market_data_verified",
    "operator_review_required",
    "operator_action",
    "dashboard_artifact",
    "dashboard_ready",
    "jp_status",
    "cn_status",
    "external_effect",
    "evidence",
    "recommendation",
    "timestamp_utc",
)

PROHIBITED_ACTIONS = (
    "ibkr_connection=NO",
    "market_data_request=NO",
    "account_read=NO",
    "positions_read=NO",
    "historical_data_request=NO",
    "contract_qualification=NO",
    "order_submit=NO",
    "cancel_order=NO",
    "rebalance=NO",
    "telegram_real_send=NO",
    "network_probe=NO",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_source_rows(path: PathLike) -> Dict[str, Dict[str, str]]:
    source_path = Path(path)
    if not source_path.exists():
        return {}
    with source_path.open(newline="", encoding="utf-8") as f:
        return {row.get("symbol", ""): row for row in csv.DictReader(f)}


def _source_value(row: Dict[str, str], field: str, default: str) -> str:
    value = row.get(field)
    return value if value not in (None, "") else default


def _row(symbol: str, source_row: Dict[str, str], timestamp: str) -> Dict[str, str]:
    source_evidence = _source_value(
        source_row,
        "evidence",
        f"{symbol}_phase_581_588_operator_packet_market_data_blocked",
    )
    source_status = _source_value(source_row, "market_data_status", "PERMISSION_DENIED")
    source_classification = _source_value(
        source_row,
        "market_data_classification",
        MARKET_DATA_CLASSIFICATION,
    )
    return {
        "phase": PHASE,
        "dashboard_id": DASHBOARD_ID,
        "symbol": symbol,
        "panel": f"{symbol}_READONLY_STATUS_CARD",
        "connectivity_status": CONNECTIVITY_STATUS,
        "contract_qualification_status": CONTRACT_QUALIFICATION_STATUS,
        "market_data_status": MARKET_DATA_STATUS,
        "market_data_classification": MARKET_DATA_CLASSIFICATION,
        "subscription_required": YES_TEXT,
        "delayed_available": YES_TEXT,
        "realtime_market_data_verified": NO_TEXT,
        "operator_review_required": YES_TEXT,
        "operator_action": OPERATOR_ACTION,
        "dashboard_artifact": DASHBOARD_ARTIFACT,
        "dashboard_ready": YES_TEXT,
        "jp_status": JP_STATUS,
        "cn_status": CN_STATUS,
        "external_effect": "NONE_LOCAL_READONLY_ARTIFACT_GENERATION_ONLY",
        "evidence": (
            f"phase_581_588_status={source_status}; classification={source_classification}; "
            f"ibkr_error_code={IBKR_ERROR_CODE}; {source_evidence}"
        ),
        "recommendation": RECOMMENDATION,
        "timestamp_utc": timestamp,
    }


def build_us_etf_dashboard_readonly_rows(
    *,
    source_csv: PathLike = "operator_us_etf_operator_packet_artifact_integration.csv",
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    timestamp = generated_at or _now_timestamp()
    source_rows = _read_source_rows(source_csv)
    return [_row(symbol, source_rows.get(symbol, {}), timestamp) for symbol in SYMBOLS]


def write_us_etf_dashboard_readonly_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_us_etf_dashboard_readonly_report(rows: Sequence[Dict[str, str]]) -> str:
    panel_lines = [
        f"- {row['symbol']}: panel={row['panel']}; market_data_status={row['market_data_status']}; "
        f"market_data_classification={row['market_data_classification']}; operator_review_required={row['operator_review_required']}"
        for row in rows
    ]
    lines = [
        "# Phase 589-600 US ETF Dashboard Readonly",
        "",
        "## Final Dashboard Status",
        "",
        f"- dashboard_status={DASHBOARD_ID}_READY",
        "- dashboard_mode=READ_ONLY_ARTIFACT_VIEWER",
        "- symbols=GLD,SLV",
        "",
        "## Scope Boundary",
        "",
        "- local CSV and Markdown artifact viewer only",
        "- no IBKR connection, market data request, account read, position read, historical data request, contract qualification, order, cancel, rebalance, Telegram real send, or network probe",
        "",
        "## Dashboard Artifacts",
        "",
        "- csv=operator_us_etf_dashboard_readonly.csv",
        "- report=reports/operator_us_etf_dashboard_readonly_report.md",
        f"- html={DASHBOARD_ARTIFACT}",
        "",
        "## GLD / SLV Panels",
        "",
        *panel_lines,
        "",
        "## Market Data Blocked Panel",
        "",
        "- source_status=PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE",
        f"- ibkr_error_code={IBKR_ERROR_CODE}",
        "- market data blocked by subscription",
        "- subscription_required=YES",
        "- delayed_available=YES",
        "- realtime_market_data_verified=NO",
        "- delayed_available does not imply realtime readiness",
        "",
        "## JP / CN Frozen Panel",
        "",
        f"- jp_status={JP_STATUS}",
        f"- cn_status={CN_STATUS}",
        "",
        "## Operator Review Workflow",
        "",
        f"- operator_action={OPERATOR_ACTION}",
        "- operator_review_required=YES",
        "- next_phase_telegram_skeleton_candidate=YES",
        "",
        "## Explicitly Prohibited Actions",
        "",
        *[f"- {action}" for action in PROHIBITED_ACTIONS],
        "",
        "## Artifact Summary",
        "",
        f"- row_count={len(rows)}",
        "- dashboard_artifact_ready=YES",
        "- trading_enabled=NO",
        "- account_read_enabled=NO",
        "- positions_read_enabled=NO",
        "- telegram_real_send_enabled=NO",
        "",
        "## Residual Risks",
        "",
        "- US ETF realtime market data remains blocked by subscription permission",
        "- Dashboard readiness means artifact readiness only",
        "",
        "## Next Phase Preconditions",
        "",
        "- subscribe Network B or continue framework-only MVP",
        "- do not mark market data ready without later verified entitlement evidence",
    ]
    return "\n".join(lines) + "\n"


def write_us_etf_dashboard_readonly_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_dashboard_readonly_report(rows), encoding="utf-8")


def build_us_etf_dashboard_readonly_html(rows: Sequence[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
      <section class="card">
        <h2>{escape(row['symbol'])}</h2>
        <dl>
          <dt>Connectivity</dt><dd>{escape(row['connectivity_status'])}</dd>
          <dt>Contract qualification</dt><dd>{escape(row['contract_qualification_status'])}</dd>
          <dt>Market data</dt><dd>{escape(row['market_data_status'])}</dd>
          <dt>Classification</dt><dd>{escape(row['market_data_classification'])}</dd>
          <dt>Realtime verified</dt><dd>{escape(row['realtime_market_data_verified'])}</dd>
        </dl>
      </section>"""
        )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "  <title>US ETF Dashboard Readonly</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; }\n"
        "    body { margin: 0; background: #f5f7f9; color: #1b1f24; }\n"
        "    header, main { max-width: 1040px; margin: 0 auto; padding: 24px; }\n"
        "    header { border-bottom: 1px solid #d7dde3; }\n"
        "    h1 { margin: 0 0 8px; font-size: 28px; }\n"
        "    h2 { margin: 0 0 16px; font-size: 20px; }\n"
        "    .status { display: inline-block; padding: 6px 10px; border: 1px solid #9b6a00; background: #fff4d6; color: #4f3600; font-weight: 700; }\n"
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 20px 0; }\n"
        "    .card, .panel { background: #ffffff; border: 1px solid #d7dde3; border-radius: 8px; padding: 18px; }\n"
        "    dl { display: grid; grid-template-columns: minmax(130px, 45%) 1fr; gap: 8px 12px; margin: 0; }\n"
        "    dt { color: #5c6670; }\n"
        "    dd { margin: 0; font-weight: 700; overflow-wrap: anywhere; }\n"
        "    ul { margin: 10px 0 0; padding-left: 20px; }\n"
        "    li { margin: 6px 0; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <header>\n"
        "    <h1>US ETF Dashboard Readonly</h1>\n"
        f"    <div class=\"status\">{DASHBOARD_ID}_READY</div>\n"
        "    <p>Read-only artifact viewer for GLD / SLV. No trading terminal functions are enabled.</p>\n"
        "  </header>\n"
        "  <main>\n"
        "    <div class=\"grid\">\n"
        f"{''.join(cards)}\n"
        "    </div>\n"
        "    <section class=\"panel\">\n"
        "      <h2>Market Data Blocked</h2>\n"
        "      <ul>\n"
        "        <li>PERMISSION_DENIED / IBKR_ERROR_10089 / SUBSCRIPTION_REQUIRED / DELAYED_AVAILABLE</li>\n"
        "        <li>market data blocked by subscription</li>\n"
        "        <li>IBKR 10089</li>\n"
        "        <li>realtime_market_data_verified=NO</li>\n"
        "      </ul>\n"
        "    </section>\n"
        "    <section class=\"panel\">\n"
        "      <h2>JP / CN Frozen</h2>\n"
        f"      <ul><li>{JP_STATUS}</li><li>{CN_STATUS}</li></ul>\n"
        "    </section>\n"
        "    <section class=\"panel\">\n"
        "      <h2>Operator Review</h2>\n"
        f"      <p>{OPERATOR_ACTION}</p>\n"
        "      <ul>\n"
        "        <li>read-only</li>\n"
        "        <li>no trading</li>\n"
        "        <li>no account reads</li>\n"
        "        <li>no positions reads</li>\n"
        "        <li>no external network resources</li>\n"
        "      </ul>\n"
        "    </section>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def write_us_etf_dashboard_readonly_html(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_us_etf_dashboard_readonly_html(rows), encoding="utf-8")


def generate_us_etf_dashboard_readonly(
    *,
    source_csv: PathLike = "operator_us_etf_operator_packet_artifact_integration.csv",
    output_csv: PathLike = "operator_us_etf_dashboard_readonly.csv",
    output_report: PathLike = "reports/operator_us_etf_dashboard_readonly_report.md",
    output_html: PathLike = DASHBOARD_ARTIFACT,
    generated_at: Optional[str] = None,
) -> list[Dict[str, str]]:
    rows = build_us_etf_dashboard_readonly_rows(source_csv=source_csv, generated_at=generated_at)
    write_us_etf_dashboard_readonly_csv(output_csv, rows)
    write_us_etf_dashboard_readonly_report(output_report, rows)
    write_us_etf_dashboard_readonly_html(output_html, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 589-600 US ETF read-only dashboard artifacts.")
    parser.add_argument("--source-csv", default="operator_us_etf_operator_packet_artifact_integration.csv")
    parser.add_argument("--output-csv", default="operator_us_etf_dashboard_readonly.csv")
    parser.add_argument("--output-report", default="reports/operator_us_etf_dashboard_readonly_report.md")
    parser.add_argument("--output-html", default=DASHBOARD_ARTIFACT)
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generate_us_etf_dashboard_readonly(
        source_csv=args.source_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        output_html=args.output_html,
        generated_at=args.generated_at,
    )
    print("[US_ETF_DASHBOARD_READONLY] generated")
    print("dashboard_status=US_ETF_DASHBOARD_READONLY_READY")
    print("dashboard_mode=READ_ONLY_ARTIFACT_VIEWER")
    print("symbols=GLD,SLV")
    print(f"connectivity_status={CONNECTIVITY_STATUS}")
    print(f"contract_qualification_status={CONTRACT_QUALIFICATION_STATUS}")
    print(f"market_data_status={MARKET_DATA_STATUS}")
    print(f"market_data_classification={MARKET_DATA_CLASSIFICATION}")
    print(f"ibkr_error_code={IBKR_ERROR_CODE}")
    print("subscription_required=YES")
    print("delayed_available=YES")
    print("realtime_market_data_verified=NO")
    print(f"jp_status={JP_STATUS}")
    print(f"cn_status={CN_STATUS}")
    print("operator_review_required=YES")
    print("dashboard_artifact_ready=YES")
    print("trading_enabled=NO")
    print("account_read_enabled=NO")
    print("positions_read_enabled=NO")
    print("telegram_real_send_enabled=NO")
    print("next_phase_telegram_skeleton_candidate=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
