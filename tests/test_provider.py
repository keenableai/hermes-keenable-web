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

from hermes_keenable_web.provider import (
    MAX_DESCRIPTION_CHARS,
    KeenableWebSearchProvider,
)


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


def test_is_available_true_keyless(monkeypatch):
    # Keyless-by-default: available even with no key, so per-capability
    # backend selection (web.search_backend / web.extract_backend) works.
    p = KeenableWebSearchProvider()
    assert p.is_available() is True
    monkeypatch.setenv("KEENABLE_API_KEY", "keen_live_x")
    assert p.is_available() is True


def test_search_keyless_hits_public_endpoint(monkeypatch):
    cap: dict = {}
    # A realistic result: the API returns both fields, `description` is
    # frequently empty and `snippet` carries the page text.
    _install_httpx(monkeypatch, cap, {"results": [
        {"title": "T", "url": "https://a.com", "description": "", "snippet": "page text"},
    ]})
    out = KeenableWebSearchProvider().search("hello", limit=5)

    assert cap["url"] == "https://api.keenable.ai/v1/search/public"
    assert "X-API-Key" not in cap["headers"]
    assert cap["headers"]["X-Keenable-Title"] == "Hermes"
    assert cap["params"] == {"query": "hello"}
    assert out == {
        "success": True,
        "data": {"web": [
            {"title": "T", "url": "https://a.com", "description": "page text", "position": 1},
        ]},
    }


def test_search_falls_back_to_description(monkeypatch):
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": [
        {"title": "T", "url": "https://a.com", "description": "a description"},
    ]})
    out = KeenableWebSearchProvider().search("hello")

    assert out["data"]["web"][0]["description"] == "a description"


def test_search_collapses_whitespace_and_caps_the_description(monkeypatch):
    # Snippets arrive as raw page text, newlines included, and run far longer
    # than the snippet other providers return.
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": [
        {
            "title": "T",
            "url": "https://a.com",
            "description": "",
            "snippet": "line one\n\nline two" + " padding" * 500,
        },
    ]})
    out = KeenableWebSearchProvider().search("hello")

    description = out["data"]["web"][0]["description"]
    assert len(description) == MAX_DESCRIPTION_CHARS
    assert "\n" not in description
    assert description.startswith("line one line two")


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


def test_search_negative_limit_returns_none(monkeypatch):
    cap: dict = {}
    results = [{"title": f"t{i}", "url": f"https://x/{i}", "description": ""} for i in range(5)]
    _install_httpx(monkeypatch, cap, {"results": results})
    out = KeenableWebSearchProvider().search("q", limit=-2)

    # Negative limit must yield an empty list, not an all-but-last slice.
    assert out["data"]["web"] == []


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


def test_url_override_http_loopback_ok(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_URL", "http://127.0.0.1:8080")
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": []})
    KeenableWebSearchProvider().search("q")

    assert cap["url"] == "http://127.0.0.1:8080/v1/search/public"


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://evil.example.com",       # plain http, non-loopback
        "https://",                       # no host
        "ftp://api.keenable.ai",          # wrong scheme
        "https://key@evil.example.com",   # userinfo (credential-forwarding)
    ],
)
def test_url_override_rejected(monkeypatch, bad_url):
    monkeypatch.setenv("KEENABLE_API_KEY", "keen_live_x")
    monkeypatch.setenv("KEENABLE_API_URL", bad_url)
    cap: dict = {}
    _install_httpx(monkeypatch, cap, {"results": []})
    # search() catches the ValueError and returns a typed error (no request made)
    out = KeenableWebSearchProvider().search("q")
    assert out["success"] is False
    assert "url" not in cap  # never dispatched — key not forwarded to a bad host


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


def test_extract_interrupted_keeps_full_shape(monkeypatch):
    # Force is_interrupted() -> True by injecting a tools.interrupt module.
    tools_pkg = types.ModuleType("tools")
    tools_pkg.__path__ = []  # type: ignore[attr-defined]
    interrupt_mod = types.ModuleType("tools.interrupt")
    interrupt_mod.is_interrupted = lambda: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tools", tools_pkg)
    monkeypatch.setitem(sys.modules, "tools.interrupt", interrupt_mod)

    docs = KeenableWebSearchProvider().extract(["https://a.com"])
    assert len(docs) == 1
    d = docs[0]
    # Interrupted record must match the documented extract-item shape.
    for key in ("url", "title", "content", "raw_content", "metadata"):
        assert key in d, f"missing {key}"
    assert d["error"] == "Interrupted"
    assert d["metadata"]["sourceURL"] == "https://a.com"


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
