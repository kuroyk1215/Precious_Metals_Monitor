from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

from src.operator_real_market_env_readiness_preflight import (
    CSV_FIELDS,
    FINAL_DECISION,
    READINESS_STATUS,
    SAFETY_STATUS_VALUES,
    build_real_market_env_readiness_preflight_rows,
    generate_real_market_env_readiness_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_secret_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "ibkr:",
                "  host: 127.0.0.1",
                "  port: 7496",
                "  client_id: 123",
                "  account_id: DUSECRET123",
                "telegram:",
                "  bot_token: secret-token-abc",
                "  chat_id: secret-chat-xyz",
                "runtime:",
                "  timezone: Asia/Shanghai",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_preflight_rows_are_no_go_artifact_only_and_schema_stable(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    _write_secret_config(config)

    rows = generate_real_market_env_readiness_preflight(
        config_path=config,
        output_csv=tmp_path / "operator_real_market_env_readiness_preflight.csv",
        output_report=tmp_path / "reports/operator_real_market_env_readiness_preflight_report.md",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    csv_rows = _read_rows(tmp_path / "operator_real_market_env_readiness_preflight.csv")
    assert rows == csv_rows
    assert csv_rows
    assert set(csv_rows[0]) == set(CSV_FIELDS)
    assert all(row["external_effect"] == "NONE" for row in csv_rows)
    assert all(row["safe_default"] == "YES" for row in csv_rows)
    assert any(row["blocked_capability"] == "IBKR_CONNECT" for row in csv_rows)
    assert any(row["blocked_capability"] == "MARKET_DATA_REQUEST" for row in csv_rows)
    assert any(row["blocked_capability"] == "TELEGRAM_REAL_SEND" for row in csv_rows)

    report = (tmp_path / "reports/operator_real_market_env_readiness_preflight_report.md").read_text(encoding="utf-8")
    assert f"final_decision={FINAL_DECISION}" in report
    assert f"readiness_status={READINESS_STATUS}" in report
    for field, value in SAFETY_STATUS_VALUES.items():
        assert f"{field}={value}" in report
    assert "next_phase_candidate=YES" in report
    assert "connection_decision=GO" not in report
    assert "POST_MVP_MULTI_MARKET_FREEZE_READY remains unchanged" in report

    combined = "\n".join(
        [
            (tmp_path / "operator_real_market_env_readiness_preflight.csv").read_text(encoding="utf-8"),
            report,
        ]
    )
    for secret in ("DUSECRET123", "secret-token-abc", "secret-chat-xyz", "127.0.0.1", "7496", "123"):
        assert secret not in combined


def test_preflight_warns_but_stays_no_go_when_config_missing(tmp_path: Path) -> None:
    rows = build_real_market_env_readiness_preflight_rows(
        config_path=tmp_path / "missing_config.yaml",
        generated_at="2026-05-26T00:00:00+00:00",
    )

    assert any(row["status"] == "WARN" for row in rows)
    assert all(row["external_effect"] == "NONE" for row in rows)
    assert SAFETY_STATUS_VALUES["final_decision"] == "NO_GO"


def test_preflight_main_cli_generates_expected_outputs(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    _write_secret_config(config)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "main.py"),
            "--config",
            str(config),
            "--real-market-env-readiness-preflight",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "final_decision=NO_GO" in result.stdout
    assert "readiness_status=REAL_MARKET_ENV_READINESS_PREFLIGHT_READY" in result.stdout
    assert "external_connections_attempted=NO" in result.stdout
    assert "ibkr_connected=NO" in result.stdout
    assert "market_data_requested=NO" in result.stdout
    assert "account_read_attempted=NO" in result.stdout
    assert "positions_read_attempted=NO" in result.stdout
    assert "historical_data_requested=NO" in result.stdout
    assert "contract_qualification_attempted=NO" in result.stdout
    assert "orders_submitted=NO" in result.stdout
    assert "telegram_real_send_attempted=NO" in result.stdout
    assert "connection_decision=GO" not in result.stdout
    assert "secret-token-abc" not in result.stdout
    assert (tmp_path / "operator_real_market_env_readiness_preflight.csv").exists()
    assert (tmp_path / "reports/operator_real_market_env_readiness_preflight_report.md").exists()
