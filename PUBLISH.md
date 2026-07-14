# Publishing `hermes-keenable-web`

Published to PyPI via **Trusted Publishing** (OIDC) — no API tokens stored.

## One-time setup (on PyPI)

Register a pending publisher before the first release
(https://pypi.org/manage/account/publishing/):

- **PyPI Project Name:** `hermes-keenable-web`
- **Owner:** `keenableai`
- **Repository name:** `hermes-keenable-web`
- **Workflow name:** `publish.yml`
- **Environment name:** `pypi`

Then, in the GitHub repo, create an Environment named `pypi`
(Settings → Environments) — optionally with a required reviewer gate.

## Cut a release

1. Bump `version` in `pyproject.toml`.
2. Tag and release on GitHub with a matching tag (e.g. `v0.1.0`).
   Publishing the Release triggers `.github/workflows/publish.yml`, which builds
   with `uv` and publishes via `pypa/gh-action-pypi-publish`.

The tag version must equal the `pyproject.toml` version.

## Local build check

```bash
uv build
uvx twine check dist/*
```

## Source of truth

The canonical source lives in the `keenable-integrations` monorepo under
`hermes/plugin/`. This repo is the publish mirror; sync changes from there.
