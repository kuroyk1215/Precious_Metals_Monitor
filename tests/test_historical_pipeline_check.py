from pathlib import Path

from src.historical_pipeline_check import run_historical_pipeline_check, write_historical_pipeline_check_report, append_historical_pipeline_check_log


def _touch(path: Path, content: str = "x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_missing_candidate_ready_for_fetch(tmp_path: Path):
    result = run_historical_pipeline_check(
        candidate_csv=str(tmp_path / "missing.csv"),
        quality_gate_report=str(tmp_path / "qg.md"),
        quality_gate_log=str(tmp_path / "qg.csv"),
        validated_csv=str(tmp_path / "validated.csv"),
        calibration_log=str(tmp_path / "cal.csv"),
    )
    assert result.status == "ready_for_fetch"


def test_candidate_no_quality_gate_blocked(tmp_path: Path):
    c = tmp_path / "candidate.csv"
    _touch(c)
    result = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(tmp_path / "qg.md"), quality_gate_log=str(tmp_path / "qg.csv"), validated_csv=str(tmp_path / "validated.csv"), calibration_log=str(tmp_path / "cal.csv"))
    assert result.status == "blocked_at_quality_gate"


def test_quality_gate_fail_blocked(tmp_path: Path):
    c = tmp_path / "candidate.csv"; _touch(c)
    qgr = tmp_path / "qg.md"; _touch(qgr)
    qgl = tmp_path / "qg.csv"; _touch(qgl, "status\nfail\n")
    result = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(qgr), quality_gate_log=str(qgl), validated_csv=str(tmp_path / "validated.csv"), calibration_log=str(tmp_path / "cal.csv"))
    assert result.status == "blocked_at_quality_gate"


def test_quality_gate_warn_manual_confirmation(tmp_path: Path):
    c = tmp_path / "candidate.csv"; _touch(c)
    qgr = tmp_path / "qg.md"; _touch(qgr)
    qgl = tmp_path / "qg.csv"; _touch(qgl, "status\nwarn\n")
    result = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(qgr), quality_gate_log=str(qgl), validated_csv=str(tmp_path / "validated.csv"), calibration_log=str(tmp_path / "cal.csv"))
    assert result.status == "blocked_before_calibration"


def test_pass_to_validate_and_calibration_states(tmp_path: Path):
    c = tmp_path / "candidate.csv"; _touch(c)
    qgr = tmp_path / "qg.md"; _touch(qgr)
    qgl = tmp_path / "qg.csv"; _touch(qgl, "status\npass\n")
    validated = tmp_path / "validated.csv"
    cal = tmp_path / "cal.csv"

    result1 = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(qgr), quality_gate_log=str(qgl), validated_csv=str(validated), calibration_log=str(cal))
    assert result1.status == "blocked_before_calibration"

    _touch(validated)
    result2 = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(qgr), quality_gate_log=str(qgl), validated_csv=str(validated), calibration_log=str(cal))
    assert result2.status == "ready_for_calibration_review"

    _touch(cal)
    result3 = run_historical_pipeline_check(candidate_csv=str(c), quality_gate_report=str(qgr), quality_gate_log=str(qgl), validated_csv=str(validated), calibration_log=str(cal))
    assert result3.status == "complete_for_research_review"


def test_report_and_log_generation(tmp_path: Path):
    result = run_historical_pipeline_check(
        candidate_csv=str(tmp_path / "missing.csv"), quality_gate_report=str(tmp_path / "qg.md"), quality_gate_log=str(tmp_path / "qg.csv"), validated_csv=str(tmp_path / "validated.csv"), calibration_log=str(tmp_path / "cal.csv")
    )
    report = tmp_path / "reports" / "historical_pipeline_check_report.md"
    log = tmp_path / "historical_pipeline_check_log.csv"
    write_historical_pipeline_check_report(str(report), result)
    append_historical_pipeline_check_log(str(log), result)
    assert report.exists()
    assert log.exists()
