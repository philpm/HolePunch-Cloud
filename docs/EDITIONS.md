# Repository and product boundaries

[HolePunch](https://github.com/philpm/HolePunch) and [HolePunch Cloud](https://github.com/philpm/HolePunch-Cloud) are Apache-2.0 projects that build and release independently.

HolePunch owns server/client cores, the single-administrator Self-hosted server, CLI, optional desktop app, and localized web console. Cloud owns multi-user registration, SMTP delivery, invitations, user administration, resource policy, and their tests. Generic operator documentation is public; production credentials, customer information, and internal operational evidence stay outside both repositories.

`vendor/holepunch` is a Git submodule pinned to a full commit. Commit and publish shared changes upstream first, fetch that exact commit here, test Cloud, and commit the updated gitlink. Do not deploy a floating branch or leave local modifications in the submodule. A new clone and CI must be able to fetch the pinned commit without a private repository token.

The Cloud build wrapper compiles the Cloud server and shared CLI. Packaging uses shared extension points with Cloud-specific inputs. Archives validate edition and target before installation. Self-hosted builds remain independent of Cloud source.

The products share schema primitives but mark database ownership. Neither server may open the other's data directory; automatic edition conversion is not supported. Both share English/Simplified Chinese UI catalogs. See [Architecture](ARCHITECTURE.md), [Localization](I18N.md), and [Deployment](DEPLOYMENT.md).
