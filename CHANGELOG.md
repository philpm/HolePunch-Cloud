# Changelog

[English](CHANGELOG.md) | [简体中文](docs/zh-CN/CHANGELOG.md)

## 0.4.0-dev.1 — First public pre-release

- Publish portable server/CLI archives for Linux x64/ARM64, macOS x64/ARM64, and Windows x64 with SHA256 checksums.
- Verify the packaged installer, binary versions, login, restart, retained credentials, and shutdown on each target platform.
- Record both product and shared-core source revisions in release metadata.
- This development pre-release excludes signed desktop installers and published container images.

- Fix standalone Cloud tools when the archive includes shared-core documentation.

### CI and dependency maintenance

- Update the shared core and Cloud lockfile with cryptography compatibility fixes and patched TLS/QUIC dependencies.
- Audit Cloud dependencies in CI and release builds, including explicit failures when the advisory service remains unavailable.
- Update Actions, group dependency PRs, avoid duplicate CI runs, and preserve the tested compiler baseline.

### bilingual documentation

- Rewrite both project homepages around features, a complete quickstart, configuration, and contributor resources.
- Add Simplified Chinese homepages and matching user, developer, and community guides with source revision checks.
- Include translated documentation and project artwork in native archives.

### open-source maintenance

- Enable checksum-verified downloads of published Cloud release archives.
- Adopt Apache-2.0 across both products and package metadata.
- Publish contributor, support, conduct, localization, and maintenance guides.
- Consolidate product documentation and remove internal acceptance diaries from public history.
- Check repository hygiene and documentation links in CI; retain English/Simplified Chinese validation.

### Cloud experience alignment

- Pin the English-first shared core and console with persistent language selection.
- Enable administrator setup without exposing it to members or changing tenant allowances.
- Reuse interactive native, source and Compose deployment tools with private bootstrap summaries and edition checks.
- Translate Cloud diagnostics and email content to English and localize console errors.
- Document schema 2 migration, backup and rollback for existing native installations.
