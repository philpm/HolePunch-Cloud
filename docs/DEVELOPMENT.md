# Local Cloud development

[English](DEVELOPMENT.md) | [简体中文](zh-CN/DEVELOPMENT.md)

Initialize the pinned submodule with `git submodule update --init --recursive`. Install Rust 1.91.1+, Python 3.10+, Node.js 24 for UI tests and native build tools. Run `python3 scripts/build.py`, then place Caddy 2.11.4 and the patched rathole in `output/tools/`. Build rathole with `python3 vendor/holepunch/scripts/build-rathole.py` and copy the resulting sidecar.

`python3 scripts/dev-local.py start` starts a native isolated stack at `http://127.0.0.1:13011`; private credentials are in `output/local-dev/ACCESS.md`. `stop` stops its processes and retains data. Development mail is written to `output/local-dev/mail/`, never sent. The local configuration permits HTTP cookies and uses Caddy's local CA without installing trust globally.

Ports: panel 13011, Caddy Admin 12039, Noise control 12353, HTTP 18100, HTTPS 18463 and tunnel pool 25000–25020. Internal forwarding ports start at 30000; stop other test stacks before end-to-end tests to prevent conflicts. These settings are not production defaults.

Follow [Testing](TESTING.md). Modify shared code in its original public repository, test and commit it there, then update the gitlink here. Keep local data and evidence in ignored, protected `output/` directories. Never include passwords, enrollment codes or tokens in committed screenshots/logs.
