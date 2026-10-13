"""Syntri client SDK for Python.

A thin, dependency-light (stdlib-only) wrapper over Syntri's ``POST /v1/capture``
HTTP API. Exposes ``input``, ``output`` and ``outcome`` capture methods, both
sync and async, and never raises on transport failures.
"""
from __future__ import annotations

from syntri.capture import CaptureClient
from syntri.client import Syntri
from syntri.types import (
    CaptureResponse,
    CaptureStatus,
    SyntriConfig,
    SyntriError,
)

__version__ = "0.1.0"

__all__ = [
    "Syntri",
    "CaptureClient",
    "SyntriConfig",
    "CaptureResponse",
    "SyntriError",
    "CaptureStatus",
]
