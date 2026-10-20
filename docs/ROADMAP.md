# Cloud iteration plan

## Current iteration: align the operator experience

Shared core pin, English source documentation/diagnostics, visible persistent language switching, administrator setup, role-scoped sidebar, and deployment summaries across native/source/Compose. Preserve existing tenant isolation and per-tunnel allocations. Deliver a tested upgrade path from the older unlabeled server to Cloud schema 4, with backup and rollback.

## Small trial readiness

Configure and verify production SMTP delivery before enabling registration. Run onboarding with a small set of users, test invitations and password reset, verify restore from an off-server backup, and monitor process health and error logs. Collect usability feedback without adding cumulative transfer quotas.

## Distribution and operational hardening

Automate reproducible public release artifacts and registry publication after CI passes; verify real Linux systemd and Compose deployments plus supported desktop operating systems. Add upgrade rehearsal and restore exercises to release acceptance. Broaden observability based on measured needs.

## Future routing

Design node identity, region/line selection, placement and failover after the single-node service is stable. Do not claim automatic global optimal routing in the current product. Billing, cumulative traffic quotas and a separate Cloud desktop fork are outside the present scope.
