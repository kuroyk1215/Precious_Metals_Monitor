from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_batch_i_real_market_env_check import (
    ENV_FIELDS,
    GATE_FIELDS,
    PERMISSION_FIELDS,
    REVIEW_FIELDS,
    SAFETY_ASSERTIONS,
    generate_batch_i_real_market_env_check,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "ibkr:",
                "  host: 127.0.0.1",
                "  port: 7496",
                "  client_id: 1",
                "  readonly: true",
                "  read_only_required: true",
                "  real_connection_allowed: false",
                "  market_data_request_allowed: false",
                "  historical_data_request_allowed: false",
                "  trading_actions_allowed: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _assert_safety(row: dict[str, str]) -> None:
    for key, value in SAFETY_ASSERTIONS.items():
        assert row[key] == value


def test_batch_i_outputs_safe_unavailable_when_api_errors_exist(tmp_path: Path):
    config = tmp_path / "config.yaml"
    errors = tmp_path / "ibkr_market_data_api_errors.csv"
    _write_config(config)
    errors.write_text(
        "symbol,error_code,error_message,status\n"
        "GLD,10089,Market data subscription missing,SAFE_UNAVAILABLE\n",
        encoding="utf-8",
    )

    result = generate_batch_i_real_market_env_check(
        config_path=config,
        api_errors_csv=errors,
        env_csv=tmp_path / "operator_batch_i_real_market_env_check.csv",
        permission_csv=tmp_path / "operator_batch_i_marketdata_permission_check.csv",
        review_csv=tmp_path / "operator_batch_i_safe_unavailable_review.csv",
        gate_csv=tmp_path / "operator_batch_i_real_market_env_gate.csv",
        env_report=tmp_path / "reports/operator_batch_i_real_market_env_check.md",
        permission_report=tmp_path / "reports/operator_batch_i_marketdata_permission_check.md",
        review_report=tmp_path / "reports/operator_batch_i_safe_unavailable_review.md",
        gate_report=tmp_path / "reports/operator_batch_i_real_market_env_gate_report.md",
        generated_at="2026-05-25T00:00:00+00:00",
    )

    assert result["environment"]["real_market_environment_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert result["gate"]["gate_status"] == "SAFE_UNAVAILABLE_REVIEW_REQUIRED"
    assert "error_code=10089" in result["review"]["reference_reason"]

    env_rows = _read_rows(tmp_path / "operator_batch_i_real_market_env_check.csv")
    permission_rows = _read_rows(tmp_path / "operator_batch_i_marketdata_permission_check.csv")
    review_rows = _read_rows(tmp_path / "operator_batch_i_safe_unavailable_review.csv")
    gate_rows = _read_rows(tmp_path / "operator_batch_i_real_market_env_gate.csv")

    assert set(env_rows[0]) == set(ENV_FIELDS)
    assert set(permission_rows[0]) == set(PERMISSION_FIELDS)
    assert set(review_rows[0]) == set(REVIEW_FIELDS)
    assert set(gate_rows[0]) == set(GATE_FIELDS)
    assert {row["symbol"] for row in permission_rows} == {"GLD", "SLV"}
    assert gate_rows[0]["gate_status"] != "PASS"

    for row in [env_rows[0], *permission_rows, review_rows[0], gate_rows[0]]:
        _assert_safety(row)

    for report in (tmp_path / "reports").glob("operator_batch_i_*.md"):
        text = report.read_text(encoding="utf-8")
        for key, value in SAFETY_ASSERTIONS.items():
            assert f"{key}={value}" in text
        assert "manual-only / research-only / observation-only" in text


def test_batch_i_main_cli_generates_outputs(tmp_path: Path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--config",
            str(config),
            "--batch-i-real-market-env-check",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "manual_only=true research_only=true observation_only=true" in result.stdout
    for relative in (
        "operator_batch_i_real_market_env_check.csv",
        "operator_batch_i_marketdata_permission_check.csv",
        "operator_batch_i_safe_unavailable_review.csv",
        "operator_batch_i_real_market_env_gate.csv",
        "reports/operator_batch_i_real_market_env_check.md",
        "reports/operator_batch_i_marketdata_permission_check.md",
        "reports/operator_batch_i_safe_unavailable_review.md",
        "reports/operator_batch_i_real_market_env_gate_report.md",
    ):
        assert (tmp_path / relative).exists()


def test_batch_i_output_has_no_forbidden_runtime_markers(tmp_path: Path):
    config = tmp_path / "config.yaml"
    _write_config(config)
    generate_batch_i_real_market_env_check(
        config_path=config,
        api_errors_csv=tmp_path / "missing_errors.csv",
        env_csv=tmp_path / "env.csv",
        permission_csv=tmp_path / "permission.csv",
        review_csv=tmp_path / "review.csv",
        gate_csv=tmp_path / "gate.csv",
        env_report=tmp_path / "env.md",
        permission_report=tmp_path / "permission.md",
        review_report=tmp_path / "review.md",
        gate_report=tmp_path / "gate.md",
    )

    text = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.glob("*.*"))
    forbidden = [
        "place" + "Order(",
        "cancel" + "Order(",
        "req" + "Historical" + "Data(",
        "req" + "Account" + "Updates(",
        "req" + "Positions(",
    ]
    assert not any(marker in text for marker in forbidden)
