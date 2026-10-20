# Cloud testing

[English](TESTING.md) | [简体中文](zh-CN/TESTING.md)

## Required local checks

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

Cloud Rust tests cover tenant isolation, CSRF, scoped tokens, atomic allocation, policy inheritance, profile/session lifecycle and administrator setup preserving member resources. Deployment tests cover private credentials, overwrite refusal, archive edition checks, standalone tool loading and localization of Cloud diagnostics. The public repository separately runs core tests and portable installer tests.

## Real local integration

Stop local development stacks first to avoid private gateway port collisions. Then run:

```sh
python3 scripts/e2e-multi-user.py --caddy output/tools/caddy --rathole output/tools/rathole --rate-seconds 60
python3 scripts/e2e.py --caddy output/tools/caddy --rathole output/tools/rathole
```

These launch actual subprocesses, exercise CLI enrollment, isolation, TCP/UDP/HTTPS, reconnect/reload/revocation and sampled rate limits, and clean up their processes. They use local certificates, never public ACME. Restore the development stack with `python3 scripts/dev-local.py start` afterward.

Validate both Compose configurations with `docker compose --env-file tests/compose.env config --quiet`; for the release file supply explicit placeholder image prefix/tag. A config check is not a container runtime test. CI builds the Linux images and runs the real integration suite.

## Browser acceptance

Verify English default and persistent manual switching on login and console, administrator/member navigation, setup start/skip/reopen/save, password replacement, draft preservation while switching languages, policy/user management and mobile layout. Keep evidence redacted under ignored `output/playwright/`.

## Production upgrade acceptance

Back up and rehearse migration on a copy. Verify schema, edition, client/token/Noise preservation, ownership and original tunnel endpoints. Check public TLS, login, readiness, actual tunnel traffic and service restart. SMTP needs a real provider test before opening registration. See [Deployment](DEPLOYMENT.md).

Record the tested commit, platform, commands, and limitations in each pull request. Keep production acceptance diaries and raw evidence outside public Git history. See [Release](RELEASE.md) and [Maintaining](MAINTAINING.md).
