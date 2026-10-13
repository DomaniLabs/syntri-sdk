"""CaptureClient wraps POST /v1/capture.

Every method returns a :class:`CaptureResponse` — it never raises. If Syntri is
slow, unreachable, or misbehaving, the caller's app keeps running; the failure
surfaces as a status on the returned response and, where configured, through
``config.on_error``.
"""
from __future__ import annotations

import asyncio
from typing import Any, cast

from syntri import _http
from syntri.types import (
    CaptureResponse,
    CaptureStatus,
    SyntriConfig,
    SyntriError,
)

_CAPTURE_PATH = "/v1/capture"


class CaptureClient:
    def __init__(self, config: SyntriConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # sync API
    # ------------------------------------------------------------------

    def input(
        self,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        """Capture an input event. The returned ``correlation_id`` links later
        output/outcome events."""
        return self._send(
            self._event("input", payload, session_id, metadata)
        )

    def output(
        self,
        correlation_id: str,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        """Capture an output event, correlated to a prior input event."""
        return self._send(
            self._event("output", payload, session_id, metadata, correlation_id)
        )

    def outcome(
        self,
        correlation_id: str,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        """Capture an outcome event, correlated to a prior input event."""
        return self._send(
            self._event("outcome", payload, session_id, metadata, correlation_id)
        )

    # ------------------------------------------------------------------
    # async API — runs the sync transport in a thread pool so the SDK stays
    # stdlib-only (no aiohttp, no httpx).
    # ------------------------------------------------------------------

    async def ainput(
        self,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        return await self._asend(
            self._event("input", payload, session_id, metadata)
        )

    async def aoutput(
        self,
        correlation_id: str,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        return await self._asend(
            self._event("output", payload, session_id, metadata, correlation_id)
        )

    async def aoutcome(
        self,
        correlation_id: str,
        payload: dict[str, Any],
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CaptureResponse:
        return await self._asend(
            self._event("outcome", payload, session_id, metadata, correlation_id)
        )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _event(
        self,
        event_type: str,
        payload: dict[str, Any],
        session_id: str | None,
        metadata: dict[str, Any] | None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        event: dict[str, Any] = {
            "instance_id": self._config.instance_id,
            "event_type": event_type,
            "payload": payload,
        }
        if correlation_id is not None:
            event["correlation_id"] = correlation_id
        if session_id is not None:
            event["session_id"] = session_id
        if metadata is not None:
            event["metadata"] = metadata
        return event

    def _send(self, event: dict[str, Any]) -> CaptureResponse:
        body, status, latency_ms = _http.post(
            _join_url(self._config.base_url, _CAPTURE_PATH),
            event,
            self._config.api_key,
            self._config.timeout,
        )
        return self._interpret(body, status, latency_ms)

    async def _asend(self, event: dict[str, Any]) -> CaptureResponse:
        loop = asyncio.get_event_loop()
        body, status, latency_ms = await loop.run_in_executor(
            None,
            _http.post,
            _join_url(self._config.base_url, _CAPTURE_PATH),
            event,
            self._config.api_key,
            self._config.timeout,
        )
        return self._interpret(body, status, latency_ms)

    def _interpret(
        self,
        body: dict[str, Any] | None,
        status: int | None,
        latency_ms: float,
    ) -> CaptureResponse:
        # No response at all: timeout or a transport-level network failure.
        # Either way Syntri never answered — unreachable, never raise.
        if status is None:
            self._notify_error(
                SyntriError(
                    type="network",
                    message="Network error contacting Syntri (timeout or unreachable)",
                )
            )
            return self._unreachable(latency_ms)

        # Auth rejection. Report through on_error, surface as unreachable.
        if status in (401, 403):
            self._notify_error(
                SyntriError(
                    type="auth",
                    message=f"Syntri rejected the API key (HTTP {status})",
                    status=status,
                )
            )
            return self._unreachable(latency_ms)

        # Any other non-2xx, or a 2xx whose body could not be parsed.
        if body is None:
            self._notify_error(
                SyntriError(
                    type="unknown",
                    message=f"Unexpected response from Syntri (HTTP {status})",
                    status=status,
                )
            )
            return self._synthesized("unknown_error", latency_ms)

        # 2xx: trust the server's decision fields, but report SDK-measured
        # round-trip latency for consistency across success and failure paths.
        return CaptureResponse(
            event_id=body.get("event_id"),
            status=cast(CaptureStatus, body.get("status", "captured")),
            correlation_id=body.get("correlation_id"),
            latency_ms=latency_ms,
        )

    def _notify_error(self, error: SyntriError) -> None:
        if self._config.on_error is not None:
            try:
                self._config.on_error(error)
            except Exception:
                # A throwing on_error callback must never break the caller.
                pass

    def _unreachable(self, latency_ms: float) -> CaptureResponse:
        return CaptureResponse(
            event_id=None,
            status="unreachable",
            correlation_id=None,
            latency_ms=latency_ms,
        )

    def _synthesized(self, status: CaptureStatus, latency_ms: float) -> CaptureResponse:
        return CaptureResponse(
            event_id=None,
            status=status,
            correlation_id=None,
            latency_ms=latency_ms,
        )


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"
