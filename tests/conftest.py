"""Stub Hermes' ``agent.web_search_provider`` so the plugin can be unit-tested
standalone (outside a Hermes checkout).

Hermes injects the real module at runtime; here we provide a minimal ABC plus a
``get_provider_env`` that reads ``os.environ``, matching the core helper's
observable behavior for tests.
"""

from __future__ import annotations

import abc
import os
import sys
import types


def _install_agent_stub() -> None:
    if "agent.web_search_provider" in sys.modules:
        return

    agent_pkg = types.ModuleType("agent")
    agent_pkg.__path__ = []  # mark as package
    mod = types.ModuleType("agent.web_search_provider")

    class WebSearchProvider(abc.ABC):
        @property
        def display_name(self) -> str:
            return self.name  # type: ignore[attr-defined]

        def supports_search(self) -> bool:
            return True

        def supports_extract(self) -> bool:
            return False

    def get_provider_env(name: str) -> str:
        return os.getenv(name, "")

    mod.WebSearchProvider = WebSearchProvider
    mod.get_provider_env = get_provider_env
    sys.modules["agent"] = agent_pkg
    sys.modules["agent.web_search_provider"] = mod


_install_agent_stub()
