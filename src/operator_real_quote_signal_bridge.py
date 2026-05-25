from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


TRUE_TEXT = "true"
FALSE_TEXT = "false"

SIGNAL_BRIDGE_FIELDS = (
    "generated_at",
    "symbol",
    "quote_status",
    "normalized_status",
    "decision",
    "research_plan_available",
    "signal_bridge_status",
    "observation_signal",
    "manual_action_allowed",
    "auto_trade_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "diagnostic_reason",
    "operator_next_step",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _latest_row(path: PathLike) -> Dict[str, str]:
    rows = _read_rows(path)
    return rows[-1] if rows else {}


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def build_signal_bridge_rows(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    decision_gate_csv: PathLike = "operator_real_marketdata_decision_gate.csv",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    generated = generated_at or _now_timestamp()
    quote_rows = _read_rows(normalization_csv)
    research_symbols = {_symbol(row) for row in _read_rows(research_plan_csv) if _symbol(row)}
    decision = _latest_row(decision_gate_csv).get("operator_decision", "")
    rows: List[Dict[str, str]] = []
    for quote in quote_rows:
        symbol = _symbol(quote)
        quote_available = quote.get("quote_status") == "AVAILABLE" and quote.get("normalized_status") == "NORMALIZED"
        if quote_available:
            status = "OBSERVATION_READY"
            signal = "REAL_QUOTE_OBSERVATION_REVIEW_ONLY"
            reason = "real_quote_normalized_for_manual_research_observation"
            next_step = "manual_observation_review_only"
        else:
            status = "HOLD_NO_REAL_QUOTE"
            signal = "NO_REAL_QUOTE_REVIEW_ONLY"
            reason = quote.get("diagnostic_reason") or "real_quote_unavailable"
            next_step = "review_real_marketdata_connection"
        rows.append(
            {
                "generated_at": generated,
                "symbol": symbol,
                "quote_status": quote.get("quote_status", "UNAVAILABLE"),
                "normalized_status": quote.get("normalized_status", "SAFE_UNAVAILABLE"),
                "decision": decision,
                "research_plan_available": TRUE_TEXT if symbol in research_symbols else FALSE_TEXT,
                "signal_bridge_status": status,
                "observation_signal": signal,
                "manual_action_allowed": FALSE_TEXT,
                "auto_trade_allowed": FALSE_TEXT,
                "order_action_allowed": FALSE_TEXT,
                "cancel_action_allowed": FALSE_TEXT,
                "rebalance_action_allowed": FALSE_TEXT,
                "diagnostic_reason": reason,
                "operator_next_step": next_step,
            }
        )
    return rows


def write_signal_bridge_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SIGNAL_BRIDGE_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(rows: Sequence[Dict[str, str]]) -> str:
    lines = [f"- {row['symbol']}: signal_bridge_status={row['signal_bridge_status']}; observation_signal={row['observation_signal']}; manual_action_allowed={row['manual_action_allowed']}; auto_trade_allowed={row['auto_trade_allowed']}" for row in rows]
    return "\n".join(
        [
            "# Operator Real Quote Signal Bridge Report",
            "",
            "## Safety Banner",
            "",
            "- observation-only signal bridge",
            "- no automatic trading",
            "- no account read",
            "- no position read",
            "- no historical data request",
            "- no Telegram real send",
            "- no order/cancel/rebalance",
            "",
            "## Bridge Rows",
            "",
            *lines,
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows), encoding="utf-8")


def generate_signal_bridge(
    *,
    normalization_csv: PathLike = "operator_real_quote_normalization.csv",
    research_plan_csv: PathLike = "research_trading_plan.csv",
    decision_gate_csv: PathLike = "operator_real_marketdata_decision_gate.csv",
    output_csv: PathLike = "operator_real_quote_signal_bridge.csv",
    output_report: PathLike = "reports/operator_real_quote_signal_bridge_report.md",
    generated_at: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = build_signal_bridge_rows(
        normalization_csv=normalization_csv,
        research_plan_csv=research_plan_csv,
        decision_gate_csv=decision_gate_csv,
        generated_at=generated_at,
    )
    write_signal_bridge_csv(output_csv, rows)
    write_markdown_report(output_report, rows)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 448 real quote research signal bridge.")
    parser.add_argument("--normalization-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--research-plan-csv", default="research_trading_plan.csv")
    parser.add_argument("--decision-gate-csv", default="operator_real_marketdata_decision_gate.csv")
    parser.add_argument("--output-csv", default="operator_real_quote_signal_bridge.csv")
    parser.add_argument("--output-report", default="reports/operator_real_quote_signal_bridge_report.md")
    parser.add_argument("--generated-at", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_signal_bridge(
        normalization_csv=args.normalization_csv,
        research_plan_csv=args.research_plan_csv,
        decision_gate_csv=args.decision_gate_csv,
        output_csv=args.output_csv,
        output_report=args.output_report,
        generated_at=args.generated_at,
    )
    print("[PASS] Operator real quote signal bridge generated")
    for row in rows:
        print(f"{row['symbol']}:signal_bridge_status={row['signal_bridge_status']}:observation_signal={row['observation_signal']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
