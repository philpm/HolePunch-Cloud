# HolePunch Cloud

Open-source TCP, UDP, and HTTPS/WebSocket tunneling for operators serving multiple users. Licensed under [Apache-2.0](LICENSE).

**0.4.0-dev.1 development build** · [Documentation](docs/README.md) · [Self-hosted edition](https://github.com/philpm/HolePunch)

Cloud adds email registration and verification, invitations, tenant administration, and per-user resource allowances to the shared HolePunch core. Each tunnel has a bandwidth allocation; total allocations must fit its owner's allowance. There is no cumulative traffic accounting or monthly transfer quota. Deployment is currently single-node.

English is the default interface language. The shared web console supports English and Simplified Chinese, with persistent manual selection and preserved form drafts. Users enroll devices with the shared CLI and manage tunnels in the browser.

## Get started

```sh
git clone --recurse-submodules https://github.com/philpm/HolePunch-Cloud.git
cd HolePunch-Cloud
python3 scripts/setup.py --interactive
python3 scripts/compose.py up
```

This source-based Compose path requires Linux with Docker Compose. Configure DNS and firewall access as described in [Installation](docs/INSTALLATION.md). The setup helper generates initial credentials locally; protect `.env` and `.env.access.txt`. Sign in using the printed management URL and follow the Setup guide. Configure SMTP before enabling registration or invitations.

For native installation without Docker, or a clone/build/run setup, use the [installation guide](docs/INSTALLATION.md). Release downloads require published archives and matching checksums; source installation works before a release exists.

## Develop

Install Rust 1.91.1+, Python 3.10+, Node.js 24 for UI tests, and native build tools.

```sh
git submodule update --init --recursive
python3 scripts/build.py
cargo test --workspace --locked
# Prepare Caddy and patched rathole in output/tools first.
python3 scripts/dev-local.py start
```

The local panel is `http://127.0.0.1:13011`; generated credentials are in `output/local-dev/ACCESS.md`. Development mail is saved to a local outbox. See [Development](docs/DEVELOPMENT.md), [Testing](docs/TESTING.md), and [Localization](docs/I18N.md).

## Repository layout

| Path | Responsibility |
|---|---|
| `apps/cloud/` | Cloud server, tenant/email handlers, and Rust integration tests |
| `vendor/holepunch/` | Pinned Git submodule with the shared core, CLI, console, and desktop app |
| `deploy/` | Generic deployment templates |
| `scripts/` | Cloud build, installation, packaging, and integration tools |
| `tests/` | Deployment and localization contract tests |
| `docs/` | User, contributor, architecture, and release guides |

Both repositories are independent Apache-2.0 projects with separate releases. Shared changes go to HolePunch first, then Cloud updates its tested dependency pin. Runtime credentials, customer data, and private operational evidence stay outside Git.

[Contributing](CONTRIBUTING.md) · [Support](SUPPORT.md) · [Code of conduct](CODE_OF_CONDUCT.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Third-party notices](NOTICE.md)
