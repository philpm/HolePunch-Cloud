# Cloud 本地开发

[English](../DEVELOPMENT.md) | 简体中文 · [文档目录](README.md)

执行 `git submodule update --init --recursive` 初始化固定子模块。安装 Rust 1.91.1+、Python 3.10+、用于 UI 测试的 Node.js 24 及本地构建工具。执行 `python3 scripts/build.py`，再把 Caddy 2.11.4 和补丁版 rathole 放到 `output/tools/`。rathole 使用 `python3 vendor/holepunch/scripts/build-rathole.py` 构建，再复制生成的 sidecar。

`python3 scripts/dev-local.py start` 启动隔离原生环境，控制台 `http://127.0.0.1:13011`，私密凭据位于 `output/local-dev/ACCESS.md`。`stop` 停止进程并保留数据。开发邮件写入 `output/local-dev/mail/`，不实际发送。此配置允许 HTTP Cookie，使用 Caddy 本地 CA，不全局安装信任。

端口：控制台 13011、Caddy Admin 12039、Noise 控制 12353、HTTP 18100、HTTPS 18463、隧道池 25000–25020；内部转发从 30000 开始。端到端测试前停止冲突的测试环境。这些不是生产默认值。

按[测试指南](TESTING.md)验证。共享代码先在原 HolePunch 仓库修改、测试和提交，再更新这里的 gitlink。本地数据和证据放在被忽略且受保护的 `output/`，提交的截图/日志不能包含密码、接入码或令牌。

<!-- translation-source: docs/DEVELOPMENT.md; source-sha256: 7714f4796ed6fc6ddc547096185d1a735811cf87e21457a297379236f12b215a -->
