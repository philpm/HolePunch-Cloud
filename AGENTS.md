# Cloud repository conventions

- Maintain this repository as the Apache-2.0 Cloud product. Keep tenant business logic, SMTP and generic operator guides here. Shared forwarding, authentication primitives, console assets and CLI changes belong in the public core repository first, then update its pinned submodule commit.
- Use English for code, comments, developer diagnostics, CLI help, canonical documentation and examples. Maintain Simplified Chinese documentation in `README-zh.md` and `docs/zh-CN/`, keeping commands and identifiers unchanged.
- Localize browser-visible diagnostics in the shared catalogs. Edit `web/locales/*.json` in the public repository, run its `scripts/sync-i18n.py`, test, commit and update the gitlink. Never hand-edit generated bundles.
- Preserve user data, quotas, tokens and deployment topology when upgrading. Back up databases, configuration, binaries and Caddy state before a production cutover.
- Never commit runtime credentials, generated configurations, databases or unredacted test evidence. Store private operational artifacts under ignored `output/` with restrictive permissions.
- Keep `main` suitable for public distribution. Never push local archive branches or merge private history into `main`; follow `docs/MAINTAINING.md`.
- Run the repository hygiene check in addition to the relevant build, test, and localization checks.
