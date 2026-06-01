from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 801-1000"
STATUS = "RESEARCH_REPORT_FRAMEWORK_READY"
SYMBOLS = ("GLD", "SLV")
HORIZONS = ("INTRADAY", "SHORT_TERM", "MID_TERM", "LONG_TERM")
PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_research_report_framework_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": STATUS,
        "symbols": list(SYMBOLS),
        "horizons": list(HORIZONS),
        "real_market_data_status": "NO_REAL_MARKET_DATA",
        "directional_signal_enabled": "NO",
        "price_levels_enabled": "NO",
        "framework_sections": [
            "market_context_placeholder",
            "data_source_status",
            "risk_boundary",
            "next_required_data",
            "manual_review_checklist",
        ],
        "generated_at_utc": timestamp,
    }


def build_research_report_markdown(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    symbol_sections = "\n\n".join(
        f"""## {symbol}

### Market Context Placeholder
NO_REAL_MARKET_DATA. Fill this area only after an approved data source is connected and manually reviewed.

### Data Source Status
- IBKR Network B / ARCA: NOT_SUBSCRIBED_NOT_CONNECTED
- Free delayed public source: CANDIDATE_NOT_CONNECTED
- Manual CSV source: FALLBACK_READY_AS_DESIGN_ONLY

### Risk Boundary
- Research framework only.
- No live monitor activation without an approved data source.
- No trading instruction, no directional label, and no price-level output.

### Next Required Data
- Approved data source decision.
- Verified timestamped local input artifact.
- Manual review of symbol coverage and data freshness.

### Manual Review Checklist
- Confirm symbol is {symbol}.
- Confirm data source status is documented.
- Confirm external actions remain blocked.
- Confirm report contains no trading instruction."""
        for symbol in SYMBOLS
    )
    return f"""# GLD / SLV Local Research Report Framework

- phase: {PHASE}
- status: {STATUS}
- real_market_data_status: NO_REAL_MARKET_DATA
- generated_at_utc: {timestamp}

Supported horizons: 日内 / 短期 / 中期 / 长期

{symbol_sections}
"""


def generate_research_report_framework(
    output_markdown: PathLike = "reports/local_research_report_framework_GLD_SLV.md",
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    _write_text(output_markdown, build_research_report_markdown(timestamp))
    return build_research_report_framework_snapshot(timestamp)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build GLD / SLV local research report framework.")
    parser.parse_args(argv)
    snapshot = generate_research_report_framework()
    print("[LOCAL_RESEARCH_REPORT_BUILD] generated")
    print(f"phase={snapshot['phase']}")
    print(f"status={snapshot['status']}")
    print("real_market_data_status=NO_REAL_MARKET_DATA")
    print("report=reports/local_research_report_framework_GLD_SLV.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
