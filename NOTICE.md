# Third-party notices

[English](NOTICE.md) | [简体中文](docs/zh-CN/NOTICE.md)

HolePunch Cloud is licensed under the [Apache License 2.0](LICENSE). Its forwarding core, CLI, and shared console come from the pinned Apache-2.0 `vendor/holepunch` submodule. Preserve the [shared core notices](vendor/holepunch/NOTICE.md), including the rathole patch description, when redistributing these components.

- [rathole](https://github.com/rathole-org/rathole): Apache-2.0; Copyright Yujia Qiao and contributors. The project uses the patched `0.5.0-holepunch.2` build.
- [Caddy](https://github.com/caddyserver/caddy): Apache-2.0; runs as a separate process.

Native packages include `DEPENDENCIES.json`, available upstream license texts under `licenses/`, and build lockfiles. Third-party components retain their respective licenses; this notice does not replace their license texts or change the Apache-2.0 terms for Cloud. Inventory entries may include platform-specific dependencies that are not linked into every binary.
