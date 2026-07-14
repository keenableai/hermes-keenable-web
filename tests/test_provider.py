"""Unit tests for the Keenable Hermes web provider.

Network is faked via a tiny httpx stub; every test asserts endpoint choice,
headers/attribution, keyless behavior, and response-shape mapping against the
WebSearchProvider contract.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Dict

import pytest

from hermes_keenable_web.provider import KeenableWebSearchProvider


class _FakeResponse:
    def __init__(self, payload: Dict[str, Any], status: int = 200) -> None:
        self._payload = payload
        self.status_code = status

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _install_httpx(monkeypatch, capture: dict, payload: Dict[str, Any], status: int = 200):
    """Replace ``import httpx`` with a stub that records the last GET call."""

    def _get(url, headers=None, params=None, timeout=None):
        capture["url"] = url
        capture["headers"] = headers or {}
        capture["params"] = params or {}
        return _FakeResponse(payload, status)

    fake = types.ModuleType("httpx")
    fake.get = _get  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "httpx", fake)
    return capture


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("KEENABLE_API_KEY", raising=False)
    monkeypatch.delenv("KEENABLE_API_URL", raising=False)


def test_identity_and_capabilities():
    p = KeenableWebSearchProvider()
    assert p.name == "keenable"
    assert p.display_name == "Keenable"
    assert p.supports_search() is True
    assert p.supports_extract() is True


def test_is_available_key_gated(monkeypatch):
    p = KeenableWebSearchProvider()
    assert p.is_available() is False
    monkeypatch.setenv("KEENABLE_API_KEY", "keen_live_x")
    assert p.is_available() is True


def test_search_keyless_hits_public_endpoint(monkeypatch):
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": [
        {"title": "T", "url": "https://a.com", "description": "d"},
    ]})
    out = KeenableWebSearchProvider().search("hello", limit=5)

    assert cap["url"] == "https://api.keenable.ai/v1/search/public"
    assert "X-API-Key" not in cap["headers"]
    assert cap["headers"]["X-Keenable-Title"] == "Hermes"
    assert cap["params"] == {"query": "hello"}
    assert out == {
        "success": True,
        "data": {"web": [
            {"title": "T", "url": "https://a.com", "description": "d", "position": 1},
        ]},
    }


def test_search_keyed_hits_private_endpoint(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "keen_live_x")
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": []})
    KeenableWebSearchProvider().search("q")

    assert cap["url"] == "https://api.keenable.ai/v1/search"
    assert cap["headers"]["X-API-Key"] == "keen_live_x"


def test_search_limit_applied_client_side(monkeypatch):
    cap: dict = {}
    results = [{"title": f"t{i}", "url": f"https://x/{i}", "description": ""} for i in range(10)]
    _install_httpx(monkeypatch, cap, {"results": results})
    out = KeenableWebSearchProvider().search("q", limit=3)

    assert len(out["data"]["web"]) == 3
    assert [r["position"] for r in out["data"]["web"]] == [1, 2, 3]


def test_search_error_is_typed(monkeypatch):
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {}, status=500)
    out = KeenableWebSearchProvider().search("q")

    assert out["success"] is False
    assert "Keenable search failed" in out["error"]


def test_url_override_respected(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_URL", "https://staging.keenable.ai/")
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": []})
    KeenableWebSearchProvider().search("q")

    assert cap["url"] == "https://staging.keenable.ai/v1/search/public"


def test_extract_shape_and_public_endpoint(monkeypatch):
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {
        "url": "https://a.com",
        "title": "Title",
        "content": "Body",
        "metadata": {"lang": "en"},
    })
    docs = KeenableWebSearchProvider().extract(["https://a.com"])

    assert cap["url"] == "https://api.keenable.ai/v1/fetch/public"
    assert len(docs) == 1
    d = docs[0]
    assert d["url"] == "https://a.com"
    assert d["title"] == "Title"
    assert d["content"] == "Body"
    assert d["raw_content"] == "Body"
    assert d["metadata"]["sourceURL"] == "https://a.com"
    assert d["metadata"]["lang"] == "en"


def test_register_calls_context():
    from hermes_keenable_web import register

    class _Ctx:
        def __init__(self) -> None:
            self.registered: Any = None

        def register_web_search_provider(self, p: Any) -> None:
            self.registered = p

    ctx = _Ctx()
    register(ctx)
    assert isinstance(ctx.registered, KeenableWebSearchProvider)
