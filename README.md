# HolePunch Cloud

<img src="docs/assets/logo.svg" alt="HolePunch logo" width="96">

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![Rust 1.91.1+](https://img.shields.io/badge/Rust-1.91.1%2B-orange.svg)

[English](README.md) | [简体中文](README-zh.md)

An open-source tunnel platform for multiple users, written in Rust.

HolePunch Cloud lets you run a tunnel service on your own infrastructure. It adds user accounts, email invitations, and resource allowances to the [HolePunch](https://github.com/philpm/HolePunch) core. Users enroll devices with the shared CLI and configure TCP, UDP, and HTTPS/WebSocket tunnels in the browser.

> **Development version: 0.4.0-dev.1.** Deployment is currently single-node. Source installation is available; release downloads and prebuilt images require an actually published version.

- [Features](#features)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Build from source](#build-from-source)
- [Planning](#planning)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Separate user workspaces.** Devices and tunnels belong to their owners. Administrator and member permissions are enforced by the server.
- **Email accounts and invitations.** Support optional registration, email verification, password reset, and administrator invitations through SMTP.
- **Per-user allowances.** Set default and individual client, tunnel, and bandwidth limits. Allocate each tunnel within its owner's bandwidth allowance.
- **Shared forwarding core.** Use HolePunch's CLI, one-time device enrollment, rathole connections, Caddy HTTPS routing, and recovery behavior.
- **Role-aware web console.** Manage users, policy, local websites, diagnostics, and setup from the administrator interface; members manage their own resources.
- **English and Simplified Chinese.** Both interfaces use the shared offline catalogs and preserve drafts when switching language.
- **Independent deployment.** Run natively or with Docker Compose using SQLite and an explicitly pinned core revision. There is no cumulative traffic accounting or monthly transfer quota.

For one administrator with no user management or account quotas, use [HolePunch Self-hosted](https://github.com/philpm/HolePunch). Both editions use Apache-2.0.

## Quickstart

You need a public Linux server, domains pointing to it, and a device running a local application. This example publishes a user's NAS web application through `nas.t.example.com`.

### 1. Start the platform

Install Git, Python 3.10+, Docker Engine, and Compose v2 on the server:

```sh
git clone --recurse-submodules https://github.com/philpm/HolePunch-Cloud.git
cd HolePunch-Cloud
python3 scripts/setup.py --public-host edge.example.com \
  --panel-domain panel.example.com --admin-email admin@example.com
python3 scripts/compose.py up
```

Use your own domains. Point the panel and control host at the server, and configure `*.t.example.com` for Web tunnels. Allow TCP 80/443, the control port (default TCP 2333), and any selected TCP/UDP tunnel ports. The control host must be DNS-only when using a conventional HTTP CDN.

After readiness succeeds, the command prints the management URL and bootstrap credentials. Protect `.env` and `.env.access.txt`; use `--hide-secrets` for captured logs. Native and source installation paths are in [Installation](docs/INSTALLATION.md).

### 2. Configure accounts and policy

Open `https://panel.example.com`, sign in, and complete **Setup guide**. Configure `t.example.com` as the domain suffix. Set default allowances in **Default policy** and configure SMTP before enabling registration or sending invitations.

The initial ordinary-user policy allows 1 client, 2 tunnels, and 1 Mbps of allocated bandwidth. Administrators can change defaults or set individual overrides. See the [administrator guide](docs/ADMIN_MULTI_USER.md).

### 3. Connect a device and publish a service

A verified user creates a device in **Clients**. On that user's machine, keep the shared `holepunch-client` and patched `rathole` binaries together in `bin/`, add it to `PATH`, and run:

```sh
holepunch-client connect --server https://panel.example.com
```

Enter the one-time code and keep the client running. Use a native package for the device's platform, or build the client using the [shared development guide](vendor/holepunch/docs/DEVELOPMENT.md).

Create a Web tunnel in the console:

| Field | Value |
|---|---|
| Name | `nas-web` |
| Protocol | Web |
| Local address | `127.0.0.1` |
| Local port | `8080` |
| Domain | `nas.t.example.com` |
| Bandwidth allocation | `1 Mbps`, within the user's remaining allowance |

After configuration synchronizes, open `https://nas.t.example.com`. The local application must be running. For TCP/UDP tunnels, connect to the public endpoint shown in the console.

## Configuration

Deployments use `.env` or the native installation's protected `config.json`. SMTP configuration includes `HP_SMTP_HOST`, `HP_SMTP_FROM`, optional `HP_SMTP_USER` / `HP_SMTP_PASSWORD`, `HP_SMTP_PORT`, and `HP_SMTP_TLS`. Restart after changing deployment settings; verify actual delivery before opening registration.

Manage user allowances and registration in **Default policy** and **User management**. Every tunnel reserves bandwidth, including disabled tunnels; each user's total must stay within their allowance. Limits apply across both directions and all connections. See [Administration](docs/ADMIN_MULTI_USER.md) and [Deployment](docs/DEPLOYMENT.md).

### Logging and troubleshooting

```sh
docker compose logs -f center rathole caddy
holepunch-client status
holepunch-client doctor
holepunch-client logs --follow
```

Local readiness does not establish public DNS, SMTP delivery, or application reachability. Use real tunnel requests and the deployment guide's backup, upgrade, and rollback procedures.

## Documentation

| Guide | What it covers |
|---|---|
| [Installation](docs/INSTALLATION.md) | Native, source, and Docker Compose installation |
| [Administration](docs/ADMIN_MULTI_USER.md) | Users, email, roles, and bandwidth allowances |
| [Deployment](docs/DEPLOYMENT.md) | Configuration, upgrades, backups, and rollback |
| [Architecture](docs/ARCHITECTURE.md) | Tenant isolation and the shared core boundary |
| [API](docs/API.md) | Cloud routes and shared API contracts |
| [Localization](docs/I18N.md) | Shared UI catalogs and translated documentation |

[All documentation](docs/README.md) · [中文文档](docs/zh-CN/README.md) · [Security](SECURITY.md)

## Build from source

Use Rust 1.91.1+, Python 3.10+, and native build tools. Node.js 24 runs the UI tests.

```sh
git submodule update --init --recursive
python3 scripts/build.py
cargo test --workspace --locked
```

Prepare Caddy and patched rathole using [Development](docs/DEVELOPMENT.md), then run `python3 scripts/dev-local.py start`. The local panel is `http://127.0.0.1:13011`; credentials stay in `output/local-dev/ACCESS.md`. Development email goes to a local outbox.

`apps/cloud/` owns the application, `vendor/holepunch/` pins the shared core, and `deploy/`, `scripts/`, `tests/`, and `docs/` hold deployment templates, tools, tests, and guides. Shared changes are reviewed in HolePunch before Cloud updates its pin.

## Planning

Current priorities are tested public releases, target-platform deployment, SMTP onboarding, and upgrade/restore exercises. Remote node placement and failover are future work. Billing, cumulative traffic quotas, and a separate Cloud desktop fork are outside the current scope. See [Roadmap](docs/ROADMAP.md) and [Testing](docs/TESTING.md).

## Contributing

Bug reports, pull requests, and translations are welcome. Start with [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), and the [Code of conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately through [Security](SECURITY.md).

## License

HolePunch Cloud is licensed under [Apache-2.0](LICENSE). Its pinned HolePunch core and third-party components retain their license notices; see [NOTICE](NOTICE.md).
