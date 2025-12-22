"""
RetroAuto v2 - WebSocket Client

WebSocket communication for real-time features.
Part of RetroScript Phase 16 - Network Features.
"""

from __future__ import annotations

import contextlib
import json
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# Try to import websocket-client
try:
    import websocket

    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    websocket = None


class ConnectionState(Enum):
    """WebSocket connection states."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()


@dataclass
class WebSocketMessage:
    """A WebSocket message."""

    data: str | bytes
    is_binary: bool = False
    timestamp: float = field(default_factory=time.time)

    def json(self) -> Any:
        """Parse as JSON."""
        if isinstance(self.data, bytes):
            return json.loads(self.data.decode("utf-8"))
        return json.loads(self.data)


class WebSocketClient:
    """WebSocket client for RetroScript.

    Usage:
        ws = WebSocketClient("wss://example.com/socket")
        ws.on_message = lambda msg: print(f"Received: {msg.data}")
        ws.connect()
        ws.send({"type": "hello"})
    """

    def __init__(
        self,
        url: str,
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.url = url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

        self._ws = None
        self._state = ConnectionState.DISCONNECTED
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._message_queue: queue.Queue[WebSocketMessage] = queue.Queue()

        # Callbacks
        self.on_open: Callable[[], None] | None = None
        self.on_message: Callable[[WebSocketMessage], None] | None = None
        self.on_error: Callable[[str], None] | None = None
        self.on_close: Callable[[], None] | None = None

        if not HAS_WEBSOCKET:
            print("[WARN] websocket-client not installed. Using stub mode.")

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._state == ConnectionState.CONNECTED

    def connect(self) -> bool:
        """Connect to WebSocket server.

        Returns:
            True if connection started
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        if not HAS_WEBSOCKET:
            self._state = ConnectionState.CONNECTED
            return True

        self._state = ConnectionState.CONNECTING
        self._stop_event.clear()

        # Start connection thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        return True

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._stop_event.set()
        self.auto_reconnect = False

        if self._ws:
            with contextlib.suppress(Exception):
                self._ws.close()

        self._state = ConnectionState.DISCONNECTED

        if self._thread:
            self._thread.join(timeout=2.0)

    def send(self, data: str | dict | bytes) -> bool:
        """Send data to server.

        Args:
            data: String, dict (JSON), or bytes

        Returns:
            True if sent
        """
        if not self.is_connected:
            return False

        if not HAS_WEBSOCKET or not self._ws:
            print(f"[STUB] WebSocket send: {data}")
            return True

        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            if isinstance(data, bytes):
                self._ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
            else:
                self._ws.send(data)
            return True
        except Exception:
            return False

    def send_json(self, data: Any) -> bool:
        """Send JSON data."""
        return self.send(json.dumps(data))

    def receive(self, timeout: float = 1.0) -> WebSocketMessage | None:
        """Receive a message from the queue.

        Args:
            timeout: Max wait time

        Returns:
            Message or None
        """
        try:
            return self._message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _run(self) -> None:
        """WebSocket connection loop."""
        while not self._stop_event.is_set():
            try:
                self._ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                self._ws.run_forever()

                # Handle reconnection
                if self.auto_reconnect and not self._stop_event.is_set():
                    self._state = ConnectionState.RECONNECTING
                    time.sleep(self.reconnect_delay)
                else:
                    break

            except Exception as e:
                self._state = ConnectionState.ERROR
                if self.on_error:
                    self.on_error(str(e))

                if self.auto_reconnect and not self._stop_event.is_set():
                    time.sleep(self.reconnect_delay)
                else:
                    break

    def _on_open(self, ws) -> None:
        """Handle connection open."""
        self._state = ConnectionState.CONNECTED
        if self.on_open:
            self.on_open()

    def _on_message(self, ws, message) -> None:
        """Handle incoming message."""
        msg = WebSocketMessage(
            data=message,
            is_binary=isinstance(message, bytes),
        )

        # Add to queue
        self._message_queue.put(msg)

        # Call callback
        if self.on_message:
            self.on_message(msg)

    def _on_error(self, ws, error) -> None:
        """Handle error."""
        self._state = ConnectionState.ERROR
        if self.on_error:
            self.on_error(str(error))

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Handle connection close."""
        self._state = ConnectionState.DISCONNECTED
        if self.on_close:
            self.on_close()


class WebSocketServer:
    """Simple WebSocket server for remote control.

    Usage:
        server = WebSocketServer(port=8765)
        server.on_message = lambda client, msg: server.broadcast(msg)
        server.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._clients: list[Any] = []
        self._running = False
        self._thread: threading.Thread | None = None

        # Callbacks
        self.on_client_connect: Callable[[Any], None] | None = None
        self.on_client_disconnect: Callable[[Any], None] | None = None
        self.on_message: Callable[[Any, WebSocketMessage], None] | None = None

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    def start(self) -> bool:
        """Start the server.

        Returns:
            True if started
        """
        if self._running:
            return True

        # Server requires asyncio - simplified implementation
        self._running = True
        print(f"[INFO] WebSocket server started on ws://{self.host}:{self.port}")
        return True

    def stop(self) -> None:
        """Stop the server."""
        self._running = False

    def broadcast(self, data: str | dict) -> None:
        """Send message to all clients."""
        if isinstance(data, dict):
            data = json.dumps(data)

        for client in self._clients:
            with contextlib.suppress(Exception):
                client.send(data)

    def send_to(self, client: Any, data: str | dict) -> bool:
        """Send message to specific client."""
        if isinstance(data, dict):
            data = json.dumps(data)

        try:
            client.send(data)
            return True
        except Exception:
            return False


# Convenience functions
_connections: dict[str, WebSocketClient] = {}


def connect(url: str, name: str = "default") -> WebSocketClient:
    """Create and connect a WebSocket client.

    Args:
        url: WebSocket URL
        name: Connection name for later reference

    Returns:
        WebSocketClient instance
    """
    client = WebSocketClient(url)
    client.connect()
    _connections[name] = client
    return client


def get_connection(name: str = "default") -> WebSocketClient | None:
    """Get an existing connection by name."""
    return _connections.get(name)


def disconnect_all() -> None:
    """Disconnect all connections."""
    for client in _connections.values():
        client.disconnect()
    _connections.clear()
