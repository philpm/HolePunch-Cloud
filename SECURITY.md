# Security reporting and operations

Cloud source is public under Apache-2.0. Keep operational credentials and user data private. Coordinate shared-core fixes with the HolePunch security process before disclosure.

Use HTTPS for the public console, TLS for SMTP, separate client identities, CSRF-protected sessions and least-privilege service accounts. Keep raw panel, Caddy Admin and internal gateway ports private. Disable registration until real email delivery is verified. Never use development outbox or insecure HTTP settings in production.

Back up before upgrades and retain a matching binary/configuration/data snapshot for rollback. Rotate credentials if exposed and revoke affected sessions/devices. Installation summaries contain bootstrap secrets and must remain outside version control and public logs. See docs/DEPLOYMENT.md for operational procedures.

## Supported versions and reporting

Security fixes currently target `main` and the latest development release. Older previews have no maintenance guarantee; there is no stable support window yet.

Use [GitHub private vulnerability reporting](https://github.com/philpm/HolePunch-Cloud/security/advisories/new). Include the affected revision, impact, minimal reproduction, and sanitized diagnostics. Do not post exploit details, tokens, database dumps, or customer information in public issues.

If private reporting is unavailable, contact the owner using a private contact option on [their GitHub profile](https://github.com/philpm) to arrange a reporting channel. Do not disclose the vulnerability in a public support request. Maintainers must enable and verify private reporting before public launch. We coordinate remediation and disclosure with reporters; no response-time guarantee is currently offered.
