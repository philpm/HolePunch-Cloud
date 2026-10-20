# Cloud deployment and upgrades

See [Installation](INSTALLATION.md) for fresh installations. Production uses the Cloud binary with a pinned public core, patched rathole and Caddy. Docker is optional. Keep panel, Caddy Admin and internal bandwidth gateway listeners private; expose only intended public HTTPS, control and tunnel ports.

## Configuration

Required bootstrap configuration: `HP_ADMIN_TOKEN` (random, at least 32 bytes), `HP_BOOTSTRAP_EMAIL`, `HP_BOOTSTRAP_PASSWORD` (at least 12 bytes), `HP_PUBLIC_ADDR` (public control host:port), and `HP_DATA_DIR`. The first administrator is created only when no administrator exists; subsequent restarts never reset its password. Store credentials in a protected environment file or native `config.json`.

Listener configuration includes `HP_BIND`, `HP_RATHOLE_BIND`, `HP_CADDY_URL`, `HP_CADDY_LISTEN`, `HP_TLS_ASK_URL`, `HP_PANEL_DOMAIN`, `HP_HTTP_PORT`, `HP_HTTPS_LISTEN`, `HP_PORT_START` and `HP_PORT_END`. The shared [deployment reference](../vendor/holepunch/docs/DEPLOYMENT.md) explains their meaning. Cloud launchers select the edition; `HP_EDITION` does not convert an existing database.

Configure `HP_SMTP_HOST`, `HP_SMTP_FROM`, optional `HP_SMTP_USER` / `HP_SMTP_PASSWORD`, `HP_SMTP_PORT`, and `HP_SMTP_TLS` (`starttls` or `tls`). Native supervisor deployments read these from `config.json`'s `env`; systemd environment-file deployments read the service environment; Compose reads `.env`. Restart the server after editing. Never use development-only `HP_MAIL_OUTBOX` or `HP_ALLOW_HTTP=1` for a public production panel. Registration remains closed until an administrator enables it. Missing SMTP leaves invitations, verification and password reset unavailable.

## Existing native systemd deployments

Retain the existing service topology and data paths when upgrading. Older installations commonly use three units: `holepunch-center`, `rathole`, and `holepunch-caddy`; `holepunch-center` is a compatible executable name for the Cloud binary. The new single-unit installer is for fresh installations, not an in-place unit conversion.

1. Build and test a release in a separate directory. Check free disk, memory, current versions, active units and readiness.
2. Create a consistent online database backup using `HP_DATA_DIR=DATA holepunch-center backup BACKUP.db`. Back up the environment file, units, Caddy certificate/state directories and installed binaries. Keep an encrypted or access-controlled off-server copy.
3. Rehearse migration on a database copy with isolated listeners, local-only certificates and test credentials. Do not start a staging server with the production Caddy Admin URL or public ACME settings.
4. Before cutover, stop the server and rathole, take a final consistent data-directory snapshot, stage the tested binary and update only necessary environment entries. Restart server and rathole; retain Caddy configuration and certificates.
5. Check `/healthz`, `/readyz`, public HTTPS, administrator sign-in, capabilities, database ownership and at least one real TCP/UDP/Web tunnel. Preserve existing client tokens and endpoint assignments.

## Schema 2 to schema 4

The Cloud server migrates old databases on startup. Configure the bootstrap administrator before the first start. Legacy clients are assigned to that administrator; IDs, tokens, tunnel names, public ports and Noise keys are preserved. Existing tunnels receive a 1 Mbps allocation each. The bootstrap administrator gets a separate large allowance, while ordinary users inherit 1 client / 2 tunnels / 1 Mbps. Adjust allocations in the console after verifying migration. Existing installations are not forced into first-run setup; the guide remains available in the sidebar.

A database marked `self_hosted` must not be opened as Cloud; the server refuses an edition mismatch. This upgrade path is for older unlabeled installations or existing Cloud databases.

## Rollback

Stop the new server and rathole. Restore the matching old binaries, environment and the final pre-upgrade database/data snapshot; never run the old binary against an upgraded schema. Restore Caddy state only if the cutover changed it, then restart the prior units. Verify readiness and original tunnel endpoints. Changes made after the snapshot are lost on rollback, so keep the verification window short.

## Initial access and operations

`python3 scripts/access.py --env-file /path/to/env --hide-secrets` or `--config PREFIX/config.json` explains initial browser access without asserting service readiness. Omit `--hide-secrets` only in a private terminal. The summary contains bootstrap credentials; a password changed in the web console is not reflected in it. Keep local summaries outside version control.

Use journalctl for systemd or `docker compose logs` for containers. `/readyz` checks local configuration and control readiness; it does not prove public DNS, provider firewall, SMTP or remote application availability. Back up regularly and rehearse restore before wider rollout.
