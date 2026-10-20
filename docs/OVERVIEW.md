# HolePunch Cloud product requirements

[English](OVERVIEW.md) | [简体中文](zh-CN/OVERVIEW.md)

## Product and audience

An Apache-2.0 multi-user tunnel platform for operators running their own service. The public Self-hosted product targets people running their own unlimited server and domains. Cloud shares its forwarding core, API primitives, CLI and console while adding users, email identity and resource policy. Initially one node; global routing is future work.

## Required experience

- Email/password login, optional email registration and verification; new accounts are members.
- Administrators invite/manage users, set defaults and individual limits. Defaults: 1 client, 2 tunnels, 1 Mbps.
- Every tunnel receives a rate allocation. Total allocations stay within its user's allowance; changes are atomic. No cumulative traffic statistics, billing or transfer quotas.
- A device runs one CLI connect command with a one-time enrollment code. All tunnel settings belong in the web console; the desktop app is optional.
- One sidebar menu per function, with role-scoped navigation, preserved drafts and explicit English/Simplified Chinese switching.
- All deployment paths explain browser access and initial credentials. Fresh administrators get detailed setup; existing deployments preserve data and can revisit setup.
- Native installer, source build and Linux Compose use the same application and preserve coexisting website configuration.

## Release acceptance

Verify user isolation, authentication/CSRF, quota enforcement, rate limiting, CLI enrollment, TCP/UDP/HTTPS, language switching and setup. Rehearse migration/rollback against a production backup copy. Check public endpoints after deployment. Never treat local readiness as proof of DNS, SMTP or a remote application.
