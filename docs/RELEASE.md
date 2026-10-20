# Cloud release guide

Cloud is an Apache-2.0 development build. Its version is defined in `Cargo.toml`; the shared core is pinned by `vendor/holepunch`. Public release assets and container images must actually exist before documenting them as downloadable.

## Build and verify

Start from a clean recursive checkout. Run [Testing](TESTING.md), review dependency advisories and licenses, and verify the pin is fetchable from the public core repository. Prepare patched rathole and Caddy as described in [Development](DEVELOPMENT.md).

```sh
python3 scripts/build.py --release
python3 vendor/holepunch/scripts/build-rathole.py
# Example for binaries built on macOS ARM64:
python3 scripts/package.py --target aarch64-apple-darwin --bin-dir target/release --rathole vendor/holepunch/apps/desktop/src-tauri/binaries/holepunch-rathole-aarch64-apple-darwin --out dist
```

The archive is `holepunch-cloud-<version>-<target>.tar.gz` (ZIP on Windows), with an adjacent `.sha256`. It includes Cloud, the shared CLI, patched rathole, installation tools, generic documentation, Apache-2.0 and third-party notices, a dependency inventory, and build metadata. Caddy is supplied separately or checksum-verified by the installer. The installed compatibility server name is `holepunch-center`.

The manual release workflow builds Linux x64/ARM64, macOS ARM64, and Windows x64 archives as Actions artifacts. It does not create releases or publish images. Native installers must be exercised on their target OS; a passing local build does not establish cross-platform support.

## Publish a tested release

After release acceptance, create a tag exactly matching `v<Cargo version>` and upload each archive and checksum under its generated filename. The Cloud installer resolves `--version` against the HolePunch-Cloud release, then checks checksum, edition, version, and target. Test an actual download and fresh install before announcing it. Keep source and local `--archive` installation documented when assets are unavailable.

Build Cloud and rathole images from this checkout and its pinned core; use a tested registry prefix and immutable version in `deploy/compose.release.yml`. Verify fresh bootstrap, tenant isolation, and actual tunnel traffic with the published images. Self-hosted images cannot replace Cloud images.

## Acceptance

Validate user isolation, SMTP with a real provider, one-time enrollment, quotas, forwarding/recovery, both UI locales, upgrade/rollback on a protected copy, public DNS/TLS, and sustained load. Inspect the final archive for operational data and preserve all license notices. Review Cloud's lockfile as well as shared core, desktop, and rathole dependencies where distributed; the shared dependency script does not scan the Cloud lockfile automatically.

Follow [Maintaining](MAINTAINING.md) for branch and GitHub publication settings. Keep production backups and detailed operational evidence outside public Git history and release assets.
