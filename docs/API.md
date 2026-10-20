# Cloud API

[English](API.md) | [简体中文](zh-CN/API.md)

The [shared API reference](../vendor/holepunch/docs/API.md) covers sessions, setup, clients, tunnels, enrollment, sites, diagnostics and native clients. `/api/v1/capabilities` returns `edition: cloud`, multi-user, quotas and email authentication enabled. Administrator `/api/v1/me` includes `setup_complete`; members do not receive this administrator state.

Cloud adds these routes under `/api/v1`:

| Method | Path | Access |
| --- | --- | --- |
| POST | `/auth/register` | Public, registration policy and rate limits |
| POST | `/auth/verify`, `/auth/resend`, `/auth/request-reset`, `/auth/reset` | Public, one-time challenges and rate limits |
| GET / POST | `/admin/users` | Administrator session; POST sends invitation |
| PUT | `/admin/users/{id}` | Administrator session and CSRF |
| POST | `/admin/users/{id}/invitation` | Administrator session and CSRF |
| GET / PUT | `/admin/policy` | Administrator; PUT requires CSRF |

Policy fields are `clients`, `tunnels`, `bps`, `registration`, `domain_suffix`. PUT validates aggregate allocations transactionally. Individual user limits may be null to inherit defaults; Cloud tunnel `bandwidth_limit_bps` must be an explicit allocation. Missing email configuration prevents opening registration.

`GET/PUT /setup` are shared administrator routes and preserve tenant policy and user resources. Setup changes profile, public control address and domain suffix; use `/admin/policy` for quotas and registration. `GET/PUT /domains` remains a Self-hosted-only route.

Errors use English developer messages; the console localizes known errors. Never include real credentials in examples or API evidence.
