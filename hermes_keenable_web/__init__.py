"""Deprecated: Keenable is built into Hermes Agent.

Hermes has bundled a Keenable web backend since August 2026
(``plugins/web/keenable``), keyless by default and with a Free/Paid choice in
``hermes tools``. This package registered its own provider under the same name,
which replaced the built-in one, so from 0.2.0 it registers nothing and only
asks to be uninstalled.
"""

from __future__ import annotations

import logging

__version__ = "0.2.0"

DEPRECATION_MESSAGE = (
    "hermes-keenable-web is deprecated: Keenable is built into Hermes Agent. "
    "This plugin no longer registers a provider, so the built-in Keenable backend stays active. "
    "Remove it with `pip uninstall hermes-keenable-web`; select Keenable with "
    "`hermes config set web.backend keenable`."
)

_log = logging.getLogger(__name__)


def register(ctx) -> None:
    """Register nothing, so Hermes' built-in Keenable provider keeps its place."""
    del ctx
    _log.warning(DEPRECATION_MESSAGE)
