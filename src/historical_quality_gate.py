from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import csv

REQUIRED_FIELDS = ["date", "symbol", "close", "currency", "source", "notes"]
ALLOWED_SYMBOLS = {"1540.T", "1542.T"}
ALLOWED_CURRENCY = "JPY"
ALLOWED_SOURCES = {"ibkr_historical_readonly", "ibkr_historical_fetch"}
MIN_SAMPLES_PER_SYMBOL = 5
EXTREME_JUMP_PCT = 30.0
MAX_CONTINUOUS_GAP_DAYS = 10

@dataclass
class GateResult:
    status: str
    total_rows: int
    symbols: list[str]
    start_date: str
    end_date: str
    warning_flags: list[str]
    fail_reasons: list[str]
    checks: list[dict[str, str]]
    per_symbol_counts: dict[str, int]


def run_quality_gate(input_path: str) -> GateResult:
    checks: list[dict[str, str]] = []
    warnings: list[str] = []
    fails: list[str] = []
    p = Path(input_path)
    if not p.exists():
        checks.append({"name": "csv_exists", "status": "fail", "detail": "file_not_found"})
        return GateResult("fail", 0, [], "", "", warnings, ["file_not_found"], checks, {})
    checks.append({"name": "csv_exists", "status": "pass", "detail": "ok"})

    try:
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:
        checks.append({"name": "csv_readable", "status": "fail", "detail": str(exc)})
        return GateResult("fail", 0, [], "", "", warnings, ["csv_unreadable"], checks, {})

    checks.append({"name": "csv_readable", "status": "pass", "detail": "ok"})
    missing_fields = [x for x in REQUIRED_FIELDS if x not in fields]
    if missing_fields:
        fails.append(f"missing_fields:{','.join(missing_fields)}")
        checks.append({"name": "required_fields", "status": "fail", "detail": ",".join(missing_fields)})
        return GateResult("fail", len(rows), [], "", "", warnings, fails, checks, {})
    checks.append({"name": "required_fields", "status": "pass", "detail": "ok"})

    if not rows:
        fails.append("empty_csv")
        checks.append({"name": "has_rows", "status": "fail", "detail": "empty_csv"})
        return GateResult("fail", 0, [], "", "", warnings, fails, checks, {})
    checks.append({"name": "has_rows", "status": "pass", "detail": str(len(rows))})

    counts: dict[str, int] = defaultdict(int)
    symbol_dates: set[tuple[str, str]] = set()
    per_symbol_dates: dict[str, list[date]] = defaultdict(list)
    symbol_prices: dict[str, list[tuple[date, float]]] = defaultdict(list)

    for row in rows:
        symbol = row["symbol"].strip()
        counts[symbol] += 1
        if symbol not in ALLOWED_SYMBOLS:
            fails.append(f"symbol_not_allowed:{symbol}")

        if row["currency"].strip() != ALLOWED_CURRENCY:
            fails.append(f"invalid_currency:{symbol}")

        if row["source"].strip() not in ALLOWED_SOURCES:
            fails.append(f"invalid_source:{symbol}")

        ds = row["date"].strip()
        try:
            d = datetime.strptime(ds, "%Y-%m-%d").date()
        except ValueError:
            fails.append(f"invalid_date:{symbol}:{ds}")
            continue

        if d > datetime.now(timezone.utc).date():
            fails.append(f"future_date:{symbol}:{ds}")

        key = (symbol, ds)
        if key in symbol_dates:
            fails.append(f"duplicate_symbol_date:{symbol}:{ds}")
        symbol_dates.add(key)
        per_symbol_dates[symbol].append(d)

        try:
            close = float(row["close"])
            if close <= 0:
                fails.append(f"non_positive_close:{symbol}:{ds}")
            else:
                symbol_prices[symbol].append((d, close))
        except ValueError:
            fails.append(f"invalid_close:{symbol}:{ds}")

        notes = row["notes"].lower()
        for flag in ("read_only", "not_calibrated", "user_must_validate"):
            if flag not in notes:
                warnings.append(f"notes_missing_{flag}:{symbol}:{ds}")

    for sym, c in counts.items():
        if c < MIN_SAMPLES_PER_SYMBOL:
            warnings.append(f"insufficient_samples:{sym}:{c}")

    for sym, dts in per_symbol_dates.items():
        dts = sorted(set(dts))
        for i in range(1, len(dts)):
            if (dts[i] - dts[i - 1]).days > MAX_CONTINUOUS_GAP_DAYS:
                warnings.append(f"continuous_gap:{sym}:{dts[i - 1]}->{dts[i]}")

    for sym, px in symbol_prices.items():
        px = sorted(px, key=lambda x: x[0])
        for i in range(1, len(px)):
            prev = px[i - 1][1]
            cur = px[i][1]
            jump = abs((cur - prev) / prev) * 100
            if jump > EXTREME_JUMP_PCT:
                warnings.append(f"extreme_jump:{sym}:{px[i][0]}:{jump:.2f}%")

    def check(name: str, fail_prefixes: tuple[str, ...], warn_prefixes: tuple[str, ...] = ()) -> None:
        if any(x.startswith(fail_prefixes) for x in fails):
            checks.append({"name": name, "status": "fail", "detail": "triggered"})
        elif any(x.startswith(warn_prefixes) for x in warnings):
            checks.append({"name": name, "status": "warn", "detail": "triggered"})
        else:
            checks.append({"name": name, "status": "pass", "detail": "ok"})

    check("symbol_allowed", ("symbol_not_allowed",))
    check("currency_valid", ("invalid_currency",))
    check("source_valid", ("invalid_source",))
    check("date_validity", ("invalid_date", "future_date", "duplicate_symbol_date"), ("continuous_gap",))
    check("close_validity", ("non_positive_close", "invalid_close"), ("extreme_jump",))
    check("sample_sufficiency", (), ("insufficient_samples",))
    check("notes_research_only", (), ("notes_missing_",))

    uniq_dates = sorted({d for vals in per_symbol_dates.values() for d in vals})
    status = "fail" if fails else ("warn" if warnings else "pass")
    return GateResult(status, len(rows), sorted(counts.keys()), str(uniq_dates[0]) if uniq_dates else "", str(uniq_dates[-1]) if uniq_dates else "", sorted(set(warnings)), sorted(set(fails)), checks, dict(counts))


def write_quality_gate_report(path: str, input_path: str, result: GateResult, checked_at: str) -> None:
    lines = ["# Historical Data Quality Gate Report", "", f"- input_path: {input_path}", f"- checked_at: {checked_at}", f"- overall_status: {result.status}", "", "## checks", "| check | status | detail |", "|---|---|---|"]
    for c in result.checks:
        lines.append(f"| {c['name']} | {c['status']} | {c['detail']} |")
    lines += ["", "## per_symbol_counts", "| symbol | rows |", "|---|---:|"]
    for sym, cnt in sorted(result.per_symbol_counts.items()):
        lines.append(f"| {sym} | {cnt} |")
    lines += ["", f"- date_range: {result.start_date} -> {result.end_date}", f"- warning_flags: {', '.join(result.warning_flags) if result.warning_flags else 'none'}", f"- fail_reasons: {', '.join(result.fail_reasons) if result.fail_reasons else 'none'}", "", "Manual confirmation is required before validate-history / calibration-csv.", "This report is research-only and does not trigger trading or calibration."]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def append_quality_gate_log(path: str, input_path: str, result: GateResult, timestamp: str) -> None:
    fields = ["timestamp", "input_path", "status", "total_rows", "symbols", "start_date", "end_date", "warning_flags", "fail_reasons", "notes"]
    p = Path(path)
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if f.tell() == 0:
            w.writeheader()
        w.writerow({"timestamp": timestamp, "input_path": input_path, "status": result.status, "total_rows": result.total_rows, "symbols": ",".join(result.symbols), "start_date": result.start_date, "end_date": result.end_date, "warning_flags": "|".join(result.warning_flags), "fail_reasons": "|".join(result.fail_reasons), "notes": "research_only_no_auto_trade_no_auto_calibration"})
