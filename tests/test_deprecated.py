"""0.2.0 is a deprecation release: register() must leave the built-in provider alone."""

from __future__ import annotations

import logging

import hermes_keenable_web


class _RecordingContext:
    """Plugin context stand-in that records every method the plugin calls."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __getattr__(self, name: str):
        def record(*args, **kwargs) -> None:
            self.calls.append(name)

        return record


def test_register_adds_nothing_and_warns(caplog):
    ctx = _RecordingContext()
    with caplog.at_level(logging.WARNING, logger="hermes_keenable_web"):
        hermes_keenable_web.register(ctx)
    assert ctx.calls == []
    assert "built into Hermes Agent" in caplog.text
    assert "pip uninstall hermes-keenable-web" in caplog.text
