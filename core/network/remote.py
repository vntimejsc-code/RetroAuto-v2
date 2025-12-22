"""
RetroAuto v2 - Remote Control API

REST API for remote script control.
Part of RetroScript Phase 16 - Network Features.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse


class ScriptState(Enum):
    """Script execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ScriptStatus:
    """Current script status."""

    state: ScriptState = ScriptState.IDLE
    script_name: str = ""
    started_at: float = 0
    elapsed: float = 0
    current_flow: str = ""
    error: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "script_name": self.script_name,
            "started_at": self.started_at,
            "elapsed": self.elapsed,
            "current_flow": self.current_flow,
            "error": self.error,
            "variables": self.variables,
        }


class RemoteAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for remote control API."""

    # Class-level references
    controller: RemoteController | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _get_body(self) -> dict[str, Any]:
        """Get request body as JSON."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length:
                body = self.rfile.read(length)
                return json.loads(body.decode("utf-8"))
        except Exception:
            pass
        return {}

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests."""
        path = urlparse(self.path).path

        if path == "/api/status":
            self._handle_status()
        elif path == "/api/scripts":
            self._handle_list_scripts()
        elif path == "/api/health":
            self._send_json({"status": "ok", "time": time.time()})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        """Handle POST requests."""
        # Security Check
        if self.controller and not self.controller.check_auth(
            self.headers.get("Authorization")
        ):
            self._send_json({"error": "Unauthorized"}, 401)
            return

        path = urlparse(self.path).path
        body = self._get_body()

        if path == "/api/start":
            self._handle_start(body)
        elif path == "/api/stop":
            self._handle_stop()
        elif path == "/api/pause":
            self._handle_pause()
        elif path == "/api/resume":
            self._handle_resume()
        elif path == "/api/execute":
            # Execution protection
            if self.controller and not self.controller.enable_execution:
                self._send_json({"error": "Remote execution disabled"}, 403)
                return
            self._handle_execute(body)
        else:
            self._send_json({"error": "Not found"}, 404)

    # ... handlers ...


class RemoteController:
    """Remote control server for RetroScript.

    Usage:
        controller = RemoteController(port=8080, auth_token="secret")
        # By default binds to localhost only
    """

    def __init__(
        self,
        host: str = "127.0.0.1",  # P0 Fix: Bind only to localhost
        port: int = 8080,
        auth_token: str | None = None,  # P0 Fix: Auth token
        enable_execution: bool = False,  # P0 Fix: Disable eval by default
    ) -> None:
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.enable_execution = enable_execution

        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._status = ScriptStatus()
        self._scripts_dir = "scripts"

        # Callbacks
        self.on_start: Callable[[str], None] | None = None
        self.on_stop: Callable[[], None] | None = None
        self.on_pause: Callable[[], None] | None = None
        self.on_execute: Callable[[str], Any] | None = None

    def check_auth(self, header: str | None) -> bool:
        """Check authorization header."""
        if not self.auth_token:
            return True  # No auth required/configured

        if not header:
            return False

        parts = header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1] == self.auth_token

        return False

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._server is not None

    def start(self) -> bool:
        """Start the remote control server.

        Returns:
            True if started successfully
        """
        if self._server:
            return True

        try:
            # Set controller reference
            RemoteAPIHandler.controller = self

            self._server = HTTPServer((self.host, self.port), RemoteAPIHandler)
            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()

            print(f"[INFO] Remote API started at http://{self.host}:{self.port}/api/")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to start remote API: {e}")
            return False

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.shutdown()
            self._server = None

    def _serve(self) -> None:
        """Server loop."""
        if self._server:
            self._server.serve_forever()

    def get_status(self) -> ScriptStatus:
        """Get current script status."""
        if self._status.state == ScriptState.RUNNING:
            self._status.elapsed = time.time() - self._status.started_at
        return self._status

    def set_status(self, **kwargs: Any) -> None:
        """Update status fields."""
        for key, value in kwargs.items():
            if hasattr(self._status, key):
                setattr(self._status, key, value)

    def list_scripts(self) -> list[str]:
        """List available scripts."""
        from pathlib import Path

        scripts_path = Path(self._scripts_dir)
        if not scripts_path.exists():
            return []

        return [f.stem for f in scripts_path.glob("*.retro")]

    def start_script(self, name: str) -> bool:
        """Start a script by name."""
        self._status.state = ScriptState.RUNNING
        self._status.script_name = name
        self._status.started_at = time.time()
        self._status.error = None

        if self.on_start:
            self.on_start(name)

        return True

    def stop_script(self) -> None:
        """Stop current script."""
        self._status.state = ScriptState.STOPPED
        self._status.elapsed = time.time() - self._status.started_at

        if self.on_stop:
            self.on_stop()

    def pause_script(self) -> None:
        """Pause current script."""
        self._status.state = ScriptState.PAUSED

        if self.on_pause:
            self.on_pause()

    def resume_script(self) -> None:
        """Resume paused script."""
        self._status.state = ScriptState.RUNNING

    def execute_code(self, code: str) -> Any:
        """Execute inline code."""
        if self.on_execute:
            return self.on_execute(code)
        return None


# Global instance
_controller: RemoteController | None = None


def get_controller() -> RemoteController:
    """Get the default remote controller."""
    global _controller
    if _controller is None:
        _controller = RemoteController()
    return _controller


def start_server(port: int = 8080) -> RemoteController:
    """Start the remote control server."""
    controller = get_controller()
    controller.port = port
    controller.start()
    return controller


def stop_server() -> None:
    """Stop the remote control server."""
    if _controller:
        _controller.stop()
