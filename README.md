# hermes-keenable-web (deprecated)

**Keenable is built into [Hermes Agent](https://github.com/NousResearch/hermes-agent).**
Hermes has bundled a Keenable web backend for `web_search` and `web_extract` since
August 2026, keyless by default, so this plugin is no longer needed.

It registered its own provider under the same name, `keenable`, which replaced the
built-in one. From 0.2.0 it registers nothing and logs a warning asking to be removed.

## Switch to the built-in backend

```bash
pip uninstall hermes-keenable-web       # in the environment Hermes runs in
hermes config set web.backend keenable  # or pick "Keenable · Free (keyless)" in `hermes tools`
```

If you copied the plugin into `~/.hermes/plugins/web/keenable/` instead, delete that
directory. An API key is optional and raises the rate limits:

```bash
hermes config set KEENABLE_API_KEY keen_<your_key>
```

Setup guide: [docs.keenable.ai/integrations/hermes-agent](https://docs.keenable.ai/integrations/hermes-agent).

## License

MIT
