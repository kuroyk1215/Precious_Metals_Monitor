from __future__ import annotations

from pathlib import Path

from src.historical_quality_gate import run_quality_gate, write_quality_gate_report, append_quality_gate_log
from src.monitor import PreciousMetalsMonitor


def _write_csv(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_missing_file_fail(tmp_path: Path) -> None:
    result = run_quality_gate(str(tmp_path / "missing.csv"))
    assert result.status == "fail"


def test_empty_csv_fail(tmp_path: Path) -> None:
    p = tmp_path / "e.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n")
    result = run_quality_gate(str(p))
    assert result.status == "fail"


def test_missing_fields_fail(tmp_path: Path) -> None:
    p = tmp_path / "m.csv"
    _write_csv(p, "date,symbol,close\n2024-01-01,1540.T,1\n")
    result = run_quality_gate(str(p))
    assert result.status == "fail"


def test_non_positive_close_fail(tmp_path: Path) -> None:
    p = tmp_path / "n.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2024-01-01,1540.T,0,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    result = run_quality_gate(str(p))
    assert result.status == "fail"


def test_duplicate_and_future_fail(tmp_path: Path) -> None:
    p = tmp_path / "d.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2999-01-01,1540.T,1,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2999-01-01,1540.T,2,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    result = run_quality_gate(str(p))
    assert result.status == "fail"


def test_insufficient_samples_warn(tmp_path: Path) -> None:
    p = tmp_path / "w.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2024-01-01,1540.T,1,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    result = run_quality_gate(str(p))
    assert result.status == "warn"


def test_extreme_jump_warn(tmp_path: Path) -> None:
    p = tmp_path / "j.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2024-01-01,1540.T,100,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-02,1540.T,200,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-03,1540.T,201,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-04,1540.T,202,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-05,1540.T,203,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    result = run_quality_gate(str(p))
    assert result.status == "warn"


def test_normal_sample_pass(tmp_path: Path) -> None:
    p = tmp_path / "p.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2024-01-01,1540.T,100,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-02,1540.T,101,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-03,1540.T,102,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-04,1540.T,103,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-05,1540.T,104,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    result = run_quality_gate(str(p))
    assert result.status == "pass"


def test_cli_generates_report_and_log(tmp_path: Path) -> None:
    p = tmp_path / "c.csv"
    _write_csv(p, "date,symbol,close,currency,source,notes\n2024-01-01,1540.T,100,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-02,1540.T,101,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-03,1540.T,102,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-04,1540.T,103,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n2024-01-05,1540.T,104,JPY,ibkr_historical_fetch,read_only not_calibrated user_must_validate\n")
    m = PreciousMetalsMonitor("config.yaml", "watchlist.yaml", mock_mode=True)
    summary, report, log = m.run_historical_quality_gate(str(p))
    assert summary["status"] == "pass"
    assert Path(report).exists()
    assert Path(log).exists()

    # direct function IO coverage
    r = run_quality_gate(str(p))
    out_md = tmp_path / "r.md"
    out_log = tmp_path / "l.csv"
    write_quality_gate_report(str(out_md), str(p), r, "2026-01-01T00:00:00+09:00")
    append_quality_gate_log(str(out_log), str(p), r, "2026-01-01T00:00:00+09:00")
    assert out_md.exists() and out_log.exists()
