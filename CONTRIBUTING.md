# Contributing

Start with the [documentation](docs/README.md), [architecture](docs/ARCHITECTURE.md), and [code of conduct](CODE_OF_CONDUCT.md). Open a focused issue or pull request with a reproducible problem and the intended behavior. Security vulnerabilities use the private process in [Security](SECURITY.md).

## Set up and validate

Clone recursively, or run `git submodule update --init --recursive`. Use Rust 1.91.1+, Python 3.10+, Node.js 24, and native build tools. Follow [Development](docs/DEVELOPMENT.md) and run:

```sh
python3 vendor/holepunch/scripts/check-repository.py --root .
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 vendor/holepunch/scripts/sync-i18n.py --check
node --test vendor/holepunch/tests/i18n.test.cjs
python3 scripts/build.py
```

Authentication, tenant policy, database, or data-plane changes also require the relevant [integration checks](docs/TESTING.md). Preserve tenant ownership, tokens, quotas, setup state, and released data compatibility. Include migration and rollback implications in the pull request. State untested platforms clearly.

## Shared core and localization

Make shared forwarding, CLI, console, and translation changes in HolePunch first. Publish the reviewed commit, update Cloud's submodule to that exact revision, and rerun Cloud validation. Do not duplicate shared modules or hand-edit generated catalogs.

Use English for documentation, code comments, identifiers, CLI help, diagnostics, and examples. Localize every browser-visible message through the shared English and Simplified Chinese catalogs. Preserve interpolation, accessible labels, user content, and form drafts; see [Localization](docs/I18N.md). Questions in any language are welcome.

## Pull requests and licensing

Keep changes focused, update current documentation and the changelog, and include tests for changed behavior. Submit from a feature branch to `main`. Follow [Maintaining](docs/MAINTAINING.md); keep private archive history and operational files out of commits and pull requests.

Unless explicitly stated otherwise, contributions intentionally submitted for inclusion are provided under this project's Apache-2.0 license, as described in Section 5 of [LICENSE](LICENSE). Preserve third-party copyright and license notices. No additional contributor agreement is required by this repository.
