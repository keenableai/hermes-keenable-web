# hermes-keenable-web

[Keenable](https://keenable.ai) as a web search + content-fetch backend for
[Hermes Agent](https://github.com/NousResearch/hermes-agent).

Keenable is low-latency web search and page-to-markdown extraction built for
agents. This is a **standalone plugin** (per Hermes' third-party-provider
policy, `AGENTS.md`): it implements the `WebSearchProvider` ABC and registers
through the normal plugin discovery path, so nothing in Hermes core changes.

- **Search** and **extract** in one provider (`web_search` + `web_extract`).
- **Keyless by default**: the free tier works with no key (rate-limited public
  endpoint). Set `KEENABLE_API_KEY` to raise limits.
- Every request sends `X-Keenable-Title: Hermes` for traffic attribution.

## Install

### pip (recommended)

```bash
pip install hermes-keenable-web
```

Hermes discovers it via the `hermes_agent.plugins` entry point. Enable it in
`plugins.enabled`, then select it as the web backend.

### User plugin directory

Copy the package into your Hermes plugin dir:

```bash
mkdir -p ~/.hermes/plugins/web/keenable
cp -r hermes_keenable_web/* ~/.hermes/plugins/web/keenable/
```

## Configure

In `config.yaml`:

```yaml
web:
  backend: keenable          # both search + extract
  # or per-capability:
  # search_backend: keenable
  # extract_backend: keenable
```

Environment variables:

```bash
KEENABLE_API_KEY=...   # optional — blank uses the keyless free tier
KEENABLE_API_URL=...   # optional — override https://api.keenable.ai
```

Keenable stays opt-in: it is never auto-selected in the no-credential fallback.
It only services calls when you choose it explicitly via `web.backend` /
`web.*_backend`.

## Develop

```bash
uv run --with pytest --with httpx --no-project python -m pytest tests/ -q
```

## License

MIT
