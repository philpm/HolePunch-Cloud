# Documentation

These guides describe the current Cloud development build. English documentation is authoritative; the interface supports English and Simplified Chinese.

| Task | Guide |
|---|---|
| Understand features and limitations | [Product overview](OVERVIEW.md) |
| Install natively, from source, or with Compose | [Installation](INSTALLATION.md) |
| Manage users, email, and bandwidth allowances | [Administrator guide](ADMIN_MULTI_USER.md) |
| Configure, upgrade, back up, and restore | [Deployment](DEPLOYMENT.md) |
| Connect a device | [Shared CLI guide](../vendor/holepunch/docs/CLI.md) |
| Build and develop locally | [Development](DEVELOPMENT.md) |
| Understand modules and tenant isolation | [Architecture](ARCHITECTURE.md) |
| Use the HTTP API | [API](API.md) |
| Maintain translations | [Localization](I18N.md) |
| Run validation | [Testing](TESTING.md) |
| Build and publish artifacts | [Release](RELEASE.md) |
| Review repository dependencies | [Repository boundaries](EDITIONS.md) |
| See planned work | [Roadmap](ROADMAP.md) |
| Maintain public branches and releases | [Maintaining](MAINTAINING.md) |

[Contributing](../CONTRIBUTING.md) · [Support](../SUPPORT.md) · [Security](../SECURITY.md) · [Code of conduct](../CODE_OF_CONDUCT.md) · [Third-party notices](../NOTICE.md)

Initialize `vendor/holepunch` before following shared documentation links. `target/` and `dist/` are generated output. `output/` also contains local databases, credentials, mail, and test evidence; stop running development services and back up data before cleanup. None of these directories belongs in a public commit.
