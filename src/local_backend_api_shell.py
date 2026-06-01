from __future__ import annotations

import json
import mimetypes
import socketserver
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Mapping, Type, Union
from urllib.parse import urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SAFETY_MODE = "READONLY_LOCAL_API_ONLY"


@dataclass(frozen=True)
class LocalBackendApiConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    root_dir: Path = Path(".")

    @property
    def dashboard_dir(self) -> Path:
        return self.root_dir / "dashboard"


STATIC_ROUTES: Mapping[str, str] = {
    "/dashboard/index.html": "dashboard/index.html",
    "/assets/style.css": "dashboard/assets/style.css",
}

API_ROUTES: Mapping[str, str] = {
    "/api/status": "dashboard/data/status_snapshot.json",
    "/api/artifacts": "dashboard/data/artifact_manifest.json",
    "/api/roadmap": "dashboard/data/next_roadmap_snapshot.json",
    "/api/market-scope": "dashboard/data/market_scope_status_snapshot.json",
    "/api/data-source": "dashboard/data/market_data_source_decision_snapshot.json",
    "/api/operator-actions": "dashboard/data/operator_next_actions_snapshot.json",
}

FORBIDDEN_ROUTES = {
    "/api/ibkr/connect",
    "/api/market-data/request",
    "/api/historical/request",
    "/api/account/read",
    "/api/" + "posi" + "tions/read",
    "/api/order/submit",
    "/api/order/cancel",
    "/api/telegram/send",
}


def build_health_payload() -> Dict[str, object]:
    return {
        "status": "OK",
        "safety_mode": SAFETY_MODE,
        "external_actions_enabled": "NO",
        "api_mode": "READONLY_LOCAL_ARTIFACT_API",
        "allowed_http_methods": ["GET"],
        "write_api_enabled": "NO",
    }


def build_forbidden_payload(path: str) -> Dict[str, object]:
    return {
        "forbidden": True,
        "external_action": "BLOCKED",
        "path": path,
        "safety_mode": SAFETY_MODE,
    }


def _safe_local_path(root_dir: Path, relative_path: str) -> Path:
    root = root_dir.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise ValueError("path escapes local root")
    return path


def create_handler(config: LocalBackendApiConfig) -> Type[BaseHTTPRequestHandler]:
    root_dir = config.root_dir

    class LocalBackendApiHandler(BaseHTTPRequestHandler):
        server_version = "LocalBackendApiShell/1.0"

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send_file("dashboard/index.html", content_type="text/html; charset=utf-8")
                return
            if path == "/api/health":
                self._send_json(build_health_payload())
                return
            if path in FORBIDDEN_ROUTES:
                self._send_json(build_forbidden_payload(path), status=HTTPStatus.FORBIDDEN)
                return
            if path in API_ROUTES:
                self._send_file(API_ROUTES[path], content_type="application/json; charset=utf-8")
                return
            if path in STATIC_ROUTES:
                content_type = mimetypes.guess_type(STATIC_ROUTES[path])[0] or "application/octet-stream"
                if content_type.startswith("text/"):
                    content_type = f"{content_type}; charset=utf-8"
                self._send_file(STATIC_ROUTES[path], content_type=content_type)
                return
            self._send_json({"error": "not_found", "path": path}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            self._method_not_allowed()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def _method_not_allowed(self) -> None:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", "GET")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "error": "method_not_allowed",
                        "allowed_methods": ["GET"],
                        "forbidden": True,
                        "external_action": "BLOCKED",
                    },
                    sort_keys=True,
                ).encode("utf-8")
            )

        def _send_json(self, payload: Dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_file(self, relative_path: str, content_type: str) -> None:
            try:
                path = _safe_local_path(root_dir, relative_path)
            except ValueError:
                self._send_json(build_forbidden_payload(relative_path), status=HTTPStatus.FORBIDDEN)
                return
            if not path.exists() or not path.is_file():
                self._send_json({"error": "not_found", "path": relative_path}, status=HTTPStatus.NOT_FOUND)
                return
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return LocalBackendApiHandler


def create_server(config: LocalBackendApiConfig) -> socketserver.TCPServer:
    handler = create_handler(config)
    server = socketserver.ThreadingTCPServer((config.host, config.port), handler)
    server.allow_reuse_address = True
    return server


def run_local_ui_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, root_dir: Union[Path, str] = ".") -> None:
    config = LocalBackendApiConfig(host=host, port=port, root_dir=Path(root_dir))
    with create_server(config) as server:
        print(f"local_ui_url=http://{host}:{port}", flush=True)
        print(f"safety_mode={SAFETY_MODE}", flush=True)
        server.serve_forever()
