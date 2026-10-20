# Cloud architecture

[English](ARCHITECTURE.md) | [简体中文](zh-CN/ARCHITECTURE.md)

Cloud is a small Rust application linked to a pinned `holepunch-server-core`. Its router adds email registration/verification/reset, SMTP delivery, administrator users/invitations and default policy. The shared core provides sessions, ownership enforcement, clients/tunnels, enrollment, configuration reconciliation, local websites, setup and the console. SQLite schema 4 stores metadata; rathole carries Noise-encrypted device connections and Caddy routes HTTPS.

Each Cloud tunnel passes through an in-process gateway with one token bucket shared across connections and both directions. User quotas constrain allocations at configuration time; the data plane enforces each tunnel's rate. Disabled tunnels retain their allocation. No cumulative transfer billing is implemented.

The console has one sidebar per role and complete English/Simplified Chinese catalogs. Bootstrap setup is available only to administrators. Mutations require sessions and CSRF; client tokens only authenticate device APIs. Password hashing runs outside async request workers with a bounded concurrency pool.

Native, source and Compose deployments run the same Cloud binary. Initial credentials are generated locally and are never returned by the setup API. Existing instances preserve setup status and configuration. See the [shared architecture](../vendor/holepunch/docs/ARCHITECTURE.md) and [deployment guide](DEPLOYMENT.md).

## Tenant isolation and allocation design

Users own clients through `client_owners`; tunnels inherit ownership from their client. Session authentication and CSRF protect browser mutations. Administrative resource delegation requires an active administrator; a member cannot use another user's client ID or read its resources. Devices enroll with expiring one-time codes and retain independent scoped tokens.

`user_limits` holds nullable overrides, while settings hold default client/tunnel/bandwidth allowances. Configuration transactions validate the sum of tunnel limits against the resolved owner allowance. Lowering defaults validates all affected users before committing; per-user changes can atomically reallocate their tunnels. Zero bandwidth disables the tunnel. Disabling a tunnel preserves its reserved allocation.

`tunnel_limits` allocates private backend ports and rates. Public sockets forward through a gateway with a token bucket shared by both directions and all connections. Reconfiguration tears down old sessions before changing listeners/rates. Counts and allocation values are configuration data, not cumulative traffic measurement.

Email challenges expire after 30 minutes and are stored hashed; device enrollment expires after 10 minutes and is single-use. Password processing uses Argon2 and bounded background work. Email delivery uses TLS; local outbox is only a development tool. Production registration defaults to closed.

Setup is an administrator-only shared server function. It never exposes bootstrap secrets. Atomic setup updates preserve tenant policy; changing a password verifies the current password and revokes sessions. Existing databases bypass automatic onboarding but keep a manual sidebar entry. See [API](API.md) and [migration/rollback](DEPLOYMENT.md).
