"""Tests for the Syntri client entry point and public surface."""
from __future__ import annotations

import syntri
from syntri import CaptureClient, Syntri, SyntriConfig


def test_client_exposes_capture() -> None:
    client = Syntri(
        SyntriConfig(
            instance_id="my-app",
            api_key="syn_test",
            base_url="https://api.syntri.test",
        )
    )
    assert isinstance(client.capture, CaptureClient)


def test_config_defaults() -> None:
    config = SyntriConfig(
        instance_id="my-app",
        api_key="syn_test",
        base_url="https://api.syntri.test",
    )
    assert config.timeout == 2.0
    assert config.on_error is None


def test_version_exported() -> None:
    assert isinstance(syntri.__version__, str)
    assert syntri.__version__ == "0.1.0"


def test_public_exports() -> None:
    for name in ("Syntri", "SyntriConfig", "CaptureResponse", "SyntriError", "CaptureStatus"):
        assert name in syntri.__all__
        assert hasattr(syntri, name)
