"""Keenable web search + extract — standalone Hermes plugin.

Installed via pip (entry point ``hermes_agent.plugins``) or copied into
``~/.hermes/plugins/web/keenable/``. Registers the Keenable provider through
the standard plugin context; nothing in Hermes core needs to change.
"""

from __future__ import annotations

from hermes_keenable_web.provider import KeenableWebSearchProvider

__version__ = "0.1.0"


def register(ctx) -> None:
    """Register the Keenable provider with the plugin context."""
    ctx.register_web_search_provider(KeenableWebSearchProvider())
