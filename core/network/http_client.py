"""
RetroAuto v2 - HTTP Client

HTTP request utilities for RetroScript.
Part of RetroScript Phase 16 - Network Features.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

# Try to import requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None


@dataclass
class HttpResponse:
    """HTTP response wrapper."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    text: str = ""
    json_data: Any = None
    error: str | None = None
    elapsed_ms: float = 0

    @property
    def ok(self) -> bool:
        """Check if request was successful (2xx)."""
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        """Get JSON data."""
        if self.json_data is not None:
            return self.json_data
        try:
            self.json_data = json.loads(self.text)
            return self.json_data
        except json.JSONDecodeError:
            return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for script access."""
        return {
            "status": self.status_code,
            "ok": self.ok,
            "text": self.text,
            "json": self.json(),
            "headers": self.headers,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
        }


class HttpClient:
    """HTTP client for RetroScript.

    Usage:
        client = HttpClient()
        response = client.get("https://api.example.com/data")
        if response.ok:
            data = response.json()
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}

        if not HAS_REQUESTS:
            print("[WARN] requests library not installed. Using stub mode.")

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform GET request.

        Args:
            url: URL or path (if base_url set)
            params: Query parameters
            headers: Additional headers

        Returns:
            HttpResponse
        """
        return self._request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform POST request.

        Args:
            url: URL or path
            data: Form data
            json_data: JSON data
            headers: Additional headers

        Returns:
            HttpResponse
        """
        return self._request("POST", url, data=data, json_data=json_data, headers=headers)

    def put(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform PUT request."""
        return self._request("PUT", url, data=data, json_data=json_data, headers=headers)

    def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform DELETE request."""
        return self._request("DELETE", url, headers=headers)

    def patch(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform PATCH request."""
        return self._request("PATCH", url, data=data, json_data=json_data, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Perform HTTP request."""
        # Build full URL
        if not url.startswith(("http://", "https://")):
            url = f"{self.base_url}/{url.lstrip('/')}"

        # Merge headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        if not HAS_REQUESTS:
            return self._stub_request(method, url)

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
            )

            return HttpResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.content,
                text=response.text,
                elapsed_ms=response.elapsed.total_seconds() * 1000,
            )

        except requests.exceptions.Timeout:
            return HttpResponse(status_code=0, error="Request timeout")
        except requests.exceptions.ConnectionError:
            return HttpResponse(status_code=0, error="Connection error")
        except Exception as e:
            return HttpResponse(status_code=0, error=str(e))

    def _stub_request(self, method: str, url: str) -> HttpResponse:
        """Stub request for when requests library is not available."""
        print(f"[STUB] {method} {url}")
        return HttpResponse(
            status_code=200,
            text='{"stub": true}',
        )


# Convenience functions
_default_client: HttpClient | None = None


def get_client() -> HttpClient:
    """Get the default HTTP client."""
    global _default_client
    if _default_client is None:
        _default_client = HttpClient()
    return _default_client


def fetch(url: str, params: dict[str, Any] | None = None) -> HttpResponse:
    """Convenience GET request."""
    return get_client().get(url, params=params)


def post(
    url: str,
    data: dict[str, Any] | None = None,
    json_data: Any = None,
) -> HttpResponse:
    """Convenience POST request."""
    return get_client().post(url, data=data, json_data=json_data)


def put(url: str, json_data: Any = None) -> HttpResponse:
    """Convenience PUT request."""
    return get_client().put(url, json_data=json_data)


def delete(url: str) -> HttpResponse:
    """Convenience DELETE request."""
    return get_client().delete(url)
