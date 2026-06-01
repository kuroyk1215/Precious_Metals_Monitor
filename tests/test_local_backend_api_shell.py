from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.local_backend_api_shell import (
    LocalBackendApiConfig,
    build_health_payload,
    create_handler,
)


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prepare_root(tmp_path: Path) -> None:
    (tmp_path / "dashboard/assets").mkdir(parents=True)
    (tmp_path / "dashboard/index.html").write_text("<html>local</html>", encoding="utf-8")
    (tmp_path / "dashboard/assets/style.css").write_text("body { color: white; }", encoding="utf-8")
    _write_json(tmp_path / "dashboard/data/status_snapshot.json", {"status": "LOCAL_BACKEND_API_SHELL_READY"})
    _write_json(tmp_path / "dashboard/data/artifact_manifest.json", {"status": "LOCAL_BACKEND_API_SHELL_READY", "artifacts": []})
    _write_json(tmp_path / "dashboard/data/next_roadmap_snapshot.json", {"status": "NEXT_ROADMAP_READY"})
    _write_json(tmp_path / "dashboard/data/market_scope_status_snapshot.json", {"status": "MARKET_SCOPE_STATUS_LOCAL_BACKEND_API_SHELL_READY"})
    _write_json(tmp_path / "dashboard/data/market_data_source_decision_snapshot.json", {"status": "MARKET_DATA_SOURCE_DECISION_READY"})
    _write_json(tmp_path / "dashboard/data/operator_next_actions_snapshot.json", {"status": "OPERATOR_NEXT_ACTIONS_LOCAL_BACKEND_API_READY"})
    _write_json(tmp_path / "dashboard/data/local_workflow_automation_snapshot.json", {"status": "LOCAL_WORKFLOW_AUTOMATION_READY"})
    _write_json(tmp_path / "dashboard/data/research_report_framework_snapshot.json", {"status": "RESEARCH_REPORT_FRAMEWORK_READY"})
    _write_json(tmp_path / "dashboard/data/us_gld_slv_data_source_dry_run_snapshot.json", {"status": "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY"})
    _write_json(tmp_path / "dashboard/data/operator_daily_packet_snapshot.json", {"status": "OPERATOR_DAILY_PACKET_PREVIEW_READY"})
    _write_json(tmp_path / "dashboard/data/telegram_preview_snapshot.json", {"status": "TELEGRAM_PREVIEW_LOCAL_ONLY_READY"})
    _write_json(tmp_path / "dashboard/data/watchlist_policy_snapshot.json", {"status": "WATCHLIST_POLICY_READY"})
    _write_json(tmp_path / "dashboard/data/local_research_platform_mvp_status_snapshot.json", {"status": "LOCAL_RESEARCH_PLATFORM_MVP_READY"})


class _FakeSocket:
    def __init__(self, request: bytes) -> None:
        self.rfile = BytesIO(request)
        self.wfile = BytesIO()

    def makefile(self, mode: str, buffering: Optional[int] = None) -> BytesIO:
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data: bytes) -> None:
        self.wfile.write(data)


def _request(tmp_path: Path, raw_request: bytes) -> Tuple[int, Dict[str, str], bytes]:
    config = LocalBackendApiConfig(host="127.0.0.1", port=8765, root_dir=tmp_path)
    handler_cls = create_handler(config)
    socket = _FakeSocket(raw_request)
    handler_cls(socket, ("127.0.0.1", 1), object())
    response = socket.wfile.getvalue()
    head, _, body = response.partition(b"\r\n\r\n")
    lines = head.decode("iso-8859-1").split("\r\n")
    status = int(lines[0].split()[1])
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower()] = value.strip()
    return status, headers, body


def _request_json(tmp_path: Path, raw_request: bytes) -> Tuple[int, Dict[str, object]]:
    status, _headers, body = _request(tmp_path, raw_request)
    return status, json.loads(body.decode("utf-8"))


def test_can_create_handler_and_server_config(tmp_path: Path) -> None:
    config = LocalBackendApiConfig(host="127.0.0.1", port=0, root_dir=tmp_path)
    handler = create_handler(config)

    assert handler.__name__ == "LocalBackendApiHandler"
    assert config.dashboard_dir == tmp_path / "dashboard"


def test_health_payload_is_readonly_and_local() -> None:
    payload = build_health_payload()

    assert payload["status"] == "OK"
    assert payload["safety_mode"] == "READONLY_LOCAL_API_ONLY"
    assert payload["external_actions_enabled"] == "NO"
    assert payload["write_api_enabled"] == "NO"


def test_server_serves_allowed_local_api_and_blocks_writes(tmp_path: Path) -> None:
    _prepare_root(tmp_path)
    assert _request_json(tmp_path, b"GET /api/health HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "OK"
    assert _request_json(tmp_path, b"GET /api/status HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "LOCAL_BACKEND_API_SHELL_READY"
    assert _request_json(tmp_path, b"GET /api/artifacts HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "LOCAL_BACKEND_API_SHELL_READY"
    assert _request_json(tmp_path, b"GET /api/data-source HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "MARKET_DATA_SOURCE_DECISION_READY"
    assert _request_json(tmp_path, b"GET /api/workflow/status HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "LOCAL_WORKFLOW_AUTOMATION_READY"
    assert _request_json(tmp_path, b"GET /api/workflow/run-preview HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "LOCAL_WORKFLOW_AUTOMATION_READY"
    assert _request_json(tmp_path, b"GET /api/research/report-framework HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "RESEARCH_REPORT_FRAMEWORK_READY"
    assert _request_json(tmp_path, b"GET /api/data-source/dry-run HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY"
    assert _request_json(tmp_path, b"GET /api/operator/daily-packet HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "OPERATOR_DAILY_PACKET_PREVIEW_READY"
    assert _request_json(tmp_path, b"GET /api/telegram/preview HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "TELEGRAM_PREVIEW_LOCAL_ONLY_READY"
    assert _request_json(tmp_path, b"GET /api/watchlist/policy HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "WATCHLIST_POLICY_READY"
    assert _request_json(tmp_path, b"GET /api/mvp/status HTTP/1.1\r\nHost: local\r\n\r\n")[1]["status"] == "LOCAL_RESEARCH_PLATFORM_MVP_READY"

    for method in (b"POST", b"PUT", b"DELETE"):
        status, body = _request_json(
            tmp_path,
            method + b" /api/status HTTP/1.1\r\nHost: local\r\nContent-Length: 2\r\n\r\n{}",
        )
        assert status == 405
        assert body["forbidden"] is True
        assert body["external_action"] == "BLOCKED"

    status, body = _request_json(tmp_path, b"GET /api/order/submit HTTP/1.1\r\nHost: local\r\n\r\n")
    assert status in {403, 404}
    assert body["forbidden"] is True
    assert body["external_action"] == "BLOCKED"


def test_server_code_omits_blocked_runtime_integrations() -> None:
    source = Path("src/local_backend_api_shell.py").read_text(encoding="utf-8")

    for forbidden in (
        "ib_insync",
        "reqMktData",
        "reqHistoricalData",
        "placeOrder",
        "accountSummary",
        "positions",
        "telegram send",
    ):
        assert forbidden not in source
