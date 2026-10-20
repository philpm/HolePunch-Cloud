# Cloud administrator guide

[English](ADMIN_MULTI_USER.md) | [简体中文](zh-CN/ADMIN_MULTI_USER.md)

Sign in with an email and password. Use Language in the header to switch English/Simplified Chinese. The sidebar separates Overview, Clients, Tunnels, Bandwidth allocation and Account settings; administrators also see User management, Default policy, Local websites, Node settings, Audit log and Setup guide.

## First setup

Fresh administrators enter the four-step Setup guide. Confirm the account, optionally replace its password, set a public control host and platform domain suffix, run local service checks, then save and add a client. The guide preserves form drafts when switching languages. Existing deployments can reopen it without resetting their data.

For Web tunnels, point `*.t.example.com` to the server and configure `t.example.com`. Cloud users can choose names inside that suffix or request random assignment. A normal HTTP CDN proxy cannot carry the Noise control connection: use a public IP or DNS-only hostname for `HP_PUBLIC_ADDR`.

## Users and registration

Configure SMTP in the deployment environment and restart before enabling registration in Default policy. A registered account is an ordinary member; verification is required before creating resources. User management sends invitations to set a password, resends invitations, changes role/status, and manages user resources. Email delivery status is recorded; successful queuing is not proof that a message reached the inbox.

Default ordinary-user allowances are 1 client, 2 tunnels and 1 Mbps. A blank individual limit inherits the default; zero means no capacity. The final active administrator cannot be removed. Freezing an account disconnects access; deletion removes its profile and resources and releases domains after a cooldown. Review destructive changes in the confirmation dialog.

## Bandwidth

Every tunnel has a bandwidth allocation, including disabled tunnels. Its owner's total allocations must not exceed the user allowance. Limits aggregate both directions and all connections; 1 Mbps is 1,000,000 bit/s. Zero disables a tunnel. Allocate several tunnels atomically in Bandwidth allocation, or adjust a user's allowance and allocations together in User management. Lowering defaults below existing allocations is rejected until affected users are adjusted. Runtime limit changes disconnect existing connections. There is no total-transfer, daily or monthly traffic quota.

## Clients

Create a device to receive a one-time code, then run `holepunch-client connect --server https://panel.example.com` on the user's computer. Enter the code when prompted. Configure local addresses, protocols, ports and domains in the console. The optional desktop app is a convenience for status/logs; it is not required. Use one identity per device and revoke lost devices.

## Coexisting websites

Local websites routes approved domains to loopback applications through the managed edge. Avoid editing Caddy's generated routes manually. Node settings controls server addresses and diagnostics. Public ports, firewall forwarding and DNS still require deployment configuration; the setup wizard does not modify the provider firewall.
