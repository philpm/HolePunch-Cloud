# Cloud installation

Clone `https://github.com/philpm/HolePunch-Cloud.git` with `--recurse-submodules`. The core is pinned to a commit. Python 3.10+ is required by deployment tools; source builds require Rust 1.91.1+ and platform build tools. Cloud release assets and images are published separately; the commands below do not assume that unpublished artifacts exist.

## 1. Interactive native installation

From the Cloud checkout:

```sh
sh scripts/install.sh --source . --prefix "$HOME/.local/share/holepunch-cloud"
```

The installer prompts for the public control host, panel domain, administrator email and ports. It builds the Cloud server and shared CLI/sidecar, verifies Caddy, creates protected configuration and prints the management URL, initial email/password and administrator API token. Linux, macOS and Windows x64 are supported by the shared installer; Linux/macOS ARM64 are also supported. On Windows use `scripts/install.ps1` with `--prefix` in a writable directory. Native foreground mode requires a terminal or a process supervisor.

For a fresh Linux systemd installation, run the installer as root with `--service systemd --prefix /opt/holepunch-cloud`. Do not run it over an existing deployment. The service runs as an unprivileged account and supervises the three processes. Existing listeners are checked; DNS and firewall rules are not modified.

To use a published native release, download its archive and matching `.sha256` from the project Releases page, unpack it, and run:

```sh
python3 deploy.py install --archive /path/to/holepunch-cloud-VERSION-TARGET.tar.gz --prefix /opt/holepunch-cloud --service systemd
```

`--archive` rejects a Self-hosted archive or the wrong platform. For a published version, `python3 scripts/deploy.py install --version VERSION` downloads the Cloud archive and verifies its checksum, edition, version, and platform. This requires an actual release with the expected archive and checksum filenames. The installer never overwrites an existing prefix. Use `--hide-secrets` when capturing terminal logs.

## 2. Clone, build and run

```sh
python3 scripts/build.py --release
python3 vendor/holepunch/scripts/build-rathole.py
```

The server is `target/release/holepunch-cloud`; the compatibility binary `holepunch-center` runs the same Cloud application. Install Caddy and the pinned patched rathole, configure environment variables, and supervise all three processes as described in [Deployment](DEPLOYMENT.md). For an easier supervised source installation, use the native installer with `--source .` as above.

## 3. Docker Compose on Linux

```sh
python3 scripts/setup.py --interactive
python3 scripts/compose.py up
```

The helper starts the source build, waits for actual readiness and prints browser access. `.env` and `.env.access.txt` contain random initial credentials and must remain private. For prebuilt images use `deploy/compose.release.yml`, set `HP_IMAGE_PREFIX` to your verified registry prefix and `HP_VERSION` to its exact tag, authenticate the registry if required, then pass `--file deploy/compose.release.yml --pull` to the helper. The image names are `PREFIX-center:TAG` and `PREFIX-rathole:TAG`. Images must be built from this Cloud checkout and its pinned core. Do not substitute a Self-hosted server image.

These Compose files require Linux host networking. Docker Desktop is not a verified substitute for production deployment.

## First browser visit

Sign in with the printed initial administrator email and password. The four-step Setup guide covers the account, control address and domain suffix, local service checks, and CLI enrollment. Choose Language in the login or console header; the preference persists in the browser. Saving a replacement password requires the current password and signs out existing sessions.

After server setup, open Default policy to configure user allowances and registration. Configure SMTP before registration or invitations. Defaults are 1 client, 2 tunnels and 1 Mbps per ordinary user; administrators can override each user. The administrator API token is not a web password or client enrollment token.

Without a panel domain, the panel listens on loopback: use the printed SSH forwarding command. With a domain, point DNS to the VPS and allow HTTPS/ACME to reach Caddy. For a shared Nginx/BT Panel host, follow the [coexistence guide](../vendor/holepunch/docs/COEXISTENCE.md) before assigning 80/443.
