# Cloud 测试

[English](../TESTING.md) | 简体中文 · [文档目录](README.md)

## 必需本地检查

```sh
python3 vendor/holepunch/scripts/check-repository.py --root .
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 vendor/holepunch/scripts/sync-i18n.py --check
node --test vendor/holepunch/tests/i18n.test.cjs
python3 scripts/build.py
```

Rust 测试覆盖租户隔离、CSRF、限定权限令牌、原子分配、策略继承、资料/会话生命周期，以及管理员设置保留成员资源。部署测试覆盖私密凭据、拒绝覆盖、归档类型、独立工具加载和 Cloud 诊断翻译。核心仓库另行执行核心与可移植安装测试。

## 真实本地集成

先停止本地开发环境，避免内部网关端口冲突，再执行：

```sh
python3 scripts/e2e-multi-user.py --caddy output/tools/caddy --rathole output/tools/rathole --rate-seconds 60
python3 scripts/e2e.py --caddy output/tools/caddy --rathole output/tools/rathole
```

套件启动真实子进程，检查 CLI 接入、隔离、TCP/UDP/HTTPS、重连/重载/撤销和采样限速，并清理进程。使用本地证书，不使用公网 ACME。完成后以 `python3 scripts/dev-local.py start` 恢复开发环境。

通过 `docker compose --env-file tests/compose.env config --quiet` 验证两种 Compose 配置，发布配置显式提供占位镜像前缀和标签。配置检查不是容器运行测试，CI 会构建 Linux 镜像并执行实际集成。

## 浏览器验收

检查登录页与控制台英文默认、手动语言选择及持久化、管理员/成员导航、设置开始/跳过/重开/保存、改密、切换语言保留草稿、策略/用户管理和移动布局。脱敏证据放在忽略的 `output/playwright/`。

## 生产升级验收

先备份并在副本演练，验证 schema、版本类型、客户端/令牌/Noise 保留、所有权与原隧道端点。检查公网 TLS、登录、就绪、实际流量和服务重启。开放注册前需使用真实提供商测试 SMTP，见[部署](DEPLOYMENT.md)。

每个 PR 记录测试提交、平台、命令和限制。生产验收日记与原始证据留在公开 Git 历史之外，详见[发布](RELEASE.md)和[维护](MAINTAINING.md)。

<!-- translation-source: docs/TESTING.md; source-sha256: 035d13ec60e439731ad90d8313b64607e51eb714df041af8d0985b76c3deaf4a -->
