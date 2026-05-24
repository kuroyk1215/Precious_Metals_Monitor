from pathlib import Path
import csv
import os
import subprocess

from src.watchlist_universe import (
    ACTION_STATUS_FIELDS,
    FORBIDDEN_EXECUTION_WORDS,
    build_watchlist_universe,
    write_markdown_report,
    write_universe_csv,
)


HEADERS = [
    "market",
    "display_symbol",
    "symbol",
    "exchange",
    "currency",
    "asset_type",
    "data_source_route",
    "ibkr_universe_allowed",
    "first_validation_allowed",
    "optional_symbol",
    "manual_review_required",
    "action_allowed",
    "notes",
]


def _write_config(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def _fixture_configs(root: Path):
    _write_config(
        root / "config/watchlist_us.csv",
        [
            {
                "market": "US",
                "display_symbol": "GLD",
                "symbol": "GLD",
                "exchange": "ARCA",
                "currency": "USD",
                "asset_type": "ETF",
                "data_source_route": "IBKR_FIRST_VALIDATION",
                "ibkr_universe_allowed": "true",
                "first_validation_allowed": "true",
                "optional_symbol": "false",
                "manual_review_required": "true",
                "action_allowed": "false",
                "notes": "US_ETF_FIRST_VALIDATION_ONLY",
            },
            {
                "market": "US",
                "display_symbol": "SLV",
                "symbol": "SLV",
                "exchange": "ARCA",
                "currency": "USD",
                "asset_type": "ETF",
                "data_source_route": "IBKR_FIRST_VALIDATION",
                "ibkr_universe_allowed": "true",
                "first_validation_allowed": "true",
                "optional_symbol": "false",
                "manual_review_required": "true",
                "action_allowed": "false",
                "notes": "US_ETF_FIRST_VALIDATION_ONLY",
            },
        ],
    )
    _write_config(
        root / "config/watchlist_jp.csv",
        [
            {
                "market": "JP",
                "display_symbol": "1540",
                "symbol": "1540",
                "exchange": "TSE",
                "currency": "JPY",
                "asset_type": "ETF",
                "data_source_route": "JP_OPTIONAL_MANUAL_OR_FUTURE_IBKR",
                "ibkr_universe_allowed": "false",
                "first_validation_allowed": "false",
                "optional_symbol": "true",
                "manual_review_required": "true",
                "action_allowed": "false",
                "notes": "JP_OPTIONAL_MANUAL_REVIEW_ONLY",
            },
            {
                "market": "JP",
                "display_symbol": "1542",
                "symbol": "1542",
                "exchange": "TSE",
                "currency": "JPY",
                "asset_type": "ETF",
                "data_source_route": "JP_OPTIONAL_MANUAL_OR_FUTURE_IBKR",
                "ibkr_universe_allowed": "false",
                "first_validation_allowed": "false",
                "optional_symbol": "true",
                "manual_review_required": "true",
                "action_allowed": "false",
                "notes": "JP_OPTIONAL_MANUAL_REVIEW_ONLY",
            },
        ],
    )
    _write_config(
        root / "config/watchlist_cn.csv",
        [
            {
                "market": "CN",
                "display_symbol": "518880",
                "symbol": "518880",
                "exchange": "SSE",
                "currency": "CNY",
                "asset_type": "ETF",
                "data_source_route": "CN_MANUAL_OR_EXTERNAL_ONLY",
                "ibkr_universe_allowed": "false",
                "first_validation_allowed": "false",
                "optional_symbol": "false",
                "manual_review_required": "true",
                "action_allowed": "false",
                "notes": "518880_EXCLUDED_FROM_IBKR",
            }
        ],
    )


def test_initial_watchlist_statuses(tmp_path: Path):
    _fixture_configs(tmp_path)

    top_status, rows = build_watchlist_universe(tmp_path)

    by_symbol = {row.display_symbol: row for row in rows}
    assert top_status == "WATCHLIST_UNIVERSE_REVIEW_REQUIRED"
    for symbol in ("GLD", "SLV"):
        assert by_symbol[symbol].universe_status == "ACTIVE_FIRST_VALIDATION"
        assert by_symbol[symbol].ibkr_universe_allowed == "true"
        assert by_symbol[symbol].first_validation_allowed == "true"
    for symbol in ("1540", "1542"):
        assert by_symbol[symbol].universe_status == "OPTIONAL_MANUAL_REVIEW"
        assert by_symbol[symbol].ibkr_universe_allowed == "false"
    assert by_symbol["518880"].universe_status in {"IBKR_EXCLUDED", "MANUAL_EXTERNAL_ONLY"}
    assert by_symbol["518880"].ibkr_universe_allowed == "false"


def test_518880_never_appears_as_ibkr_allowed(tmp_path: Path):
    _fixture_configs(tmp_path)
    _, rows = build_watchlist_universe(tmp_path)

    ibkr_allowed_symbols = {row.display_symbol for row in rows if row.ibkr_universe_allowed == "true"}

    assert "518880" not in ibkr_allowed_symbols


def test_manual_review_true_and_action_allowed_false_for_all_rows(tmp_path: Path):
    _fixture_configs(tmp_path)
    _, rows = build_watchlist_universe(tmp_path)

    assert all(row.action_allowed == "false" for row in rows)
    assert all(row.manual_review_required == "true" for row in rows)


def test_invalid_boolean_config_is_caught(tmp_path: Path):
    _fixture_configs(tmp_path)
    text = (tmp_path / "config/watchlist_jp.csv").read_text(encoding="utf-8")
    (tmp_path / "config/watchlist_jp.csv").write_text(text.replace(",false,false,true,true,false,", ",maybe,false,true,true,false,", 1), encoding="utf-8")

    top_status, rows = build_watchlist_universe(tmp_path)

    assert top_status == "WATCHLIST_UNIVERSE_INVALID"
    assert any(row.validation_status == "INVALID_CONFIG" for row in rows)


def test_writers_emit_outputs_without_forbidden_execution_words(tmp_path: Path):
    _fixture_configs(tmp_path)
    top_status, rows = build_watchlist_universe(tmp_path)
    csv_path = tmp_path / "watchlist_universe.csv"
    report_path = tmp_path / "reports/watchlist_universe_report.md"

    write_universe_csv(csv_path, rows)
    write_markdown_report(report_path, top_status, rows)

    csv_rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    assert csv_rows[0]["universe_run_id"]
    assert "top_level_status=WATCHLIST_UNIVERSE_REVIEW_REQUIRED" in report_path.read_text(encoding="utf-8")
    for row in rows:
        for field in ACTION_STATUS_FIELDS:
            value = getattr(row, field).upper()
            assert not any(word in value for word in FORBIDDEN_EXECUTION_WORDS), (field, value)


def test_script_runs_offline(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    _fixture_configs(tmp_path)

    result = subprocess.run(
        [
            "bash",
            str(repo_root / "scripts/watchlist_universe.sh"),
            "--root",
            str(tmp_path),
            "--output-csv",
            str(tmp_path / "watchlist_universe.csv"),
            "--output-report",
            str(tmp_path / "reports/watchlist_universe_report.md"),
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert "offline_only=true" in result.stdout
    assert (tmp_path / "watchlist_universe.csv").exists()
    assert (tmp_path / "reports/watchlist_universe_report.md").exists()
