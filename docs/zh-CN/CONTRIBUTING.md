# 参与贡献

[English](../../CONTRIBUTING.md) | 简体中文 · [文档目录](README.md)

先阅读[文档](README.md)、[架构](ARCHITECTURE.md)和[行为准则](CODE_OF_CONDUCT.md)。提交聚焦单一问题的 issue 或 PR，提供可复现问题及期望行为。漏洞走[安全说明](SECURITY.md)中的私密流程。

## 配置与验证

递归克隆，或执行 `git submodule update --init --recursive`。使用 Rust 1.91.1+、Python 3.10+、Node.js 24 及本地构建工具，按[开发指南](DEVELOPMENT.md)执行：

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

认证、租户策略、数据库或数据平面变更还需相应[集成测试](TESTING.md)。保留所有权、令牌、额度、设置状态和已发布数据兼容性。PR 说明迁移/回滚影响和未测试平台。

## 共享核心与国际化

转发、CLI、控制台和翻译的共享修改先在 HolePunch 进行。发布经过审阅的提交，更新 Cloud 子模块到精确版本，再重新验证。不要复制共享模块或手工改生成词条。

文档原文、代码注释、标识符、CLI 帮助、诊断和示例使用英文。浏览器可见消息必须通过共享中英文词条翻译，保留插值、无障碍标签、用户内容和表单草稿，见[国际化](I18N.md)。更改文档行为时，维护对应 `README-zh.md` 和 `docs/zh-CN/`。欢迎用任何语言提问。

## PR 与许可

保持修改聚焦，更新现行文档、更新记录和行为测试。从功能分支提交到 `main`，遵循[维护指南](MAINTAINING.md)，不在提交/PR 中带入私密归档历史和运维文件。

除非明确另有说明，有意提交以纳入项目的贡献依照 [LICENSE](../../LICENSE) 第 5 节采用 Apache-2.0。保留第三方版权与许可证声明，本仓库不要求额外贡献者协议。

<!-- translation-source: CONTRIBUTING.md; source-sha256: 2926c4dc5ee849da84ec13782315f1574393d63a864043d14043ff698ee86bf7 -->
