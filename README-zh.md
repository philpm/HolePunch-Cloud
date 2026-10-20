# HolePunch Cloud

<img src="docs/assets/logo.svg" alt="HolePunch 标志" width="96">

[![许可证：Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![Rust 1.91.1+](https://img.shields.io/badge/Rust-1.91.1%2B-orange.svg)

[English](README.md) | [简体中文](README-zh.md)

使用 Rust 编写、可自行部署的开源多用户内网穿透平台。

HolePunch Cloud 让你在自己的基础设施上运营隧道服务。它基于 [HolePunch](https://github.com/philpm/HolePunch) 核心，增加用户账户、邮件邀请和资源配额。用户通过共享 CLI 接入设备，在浏览器中配置 TCP、UDP 和 HTTPS/WebSocket 隧道。

> **开发版本：0.4.0-dev.1。** 目前采用单节点部署。可从源码安装；版本下载和预构建镜像需要相应版本实际发布后才能使用。

- [特性](#特性)
- [快速开始](#快速开始)
- [配置](#配置)
- [文档](#文档)
- [从源码构建](#从源码构建)
- [开发计划](#开发计划)
- [参与贡献](#参与贡献)
- [开源协议](#开源协议)

## 特性

- **独立用户空间。** 设备和隧道归各自用户所有，管理员和成员的权限由服务端强制校验。
- **邮件账户与邀请。** 通过 SMTP 支持可选注册、邮箱验证、密码重置和管理员邀请。
- **按用户分配资源。** 设置默认和个别用户的客户端、隧道、带宽上限，各隧道在所属用户的带宽额度内分配。
- **共享转发核心。** 复用 HolePunch CLI、一次性设备接入、rathole 连接、Caddy HTTPS 路由及故障恢复能力。
- **按角色组织控制台。** 管理员可管理用户、策略、本机网站、诊断和设置；成员管理自己的资源。
- **中英文界面。** 共用离线翻译目录，切换语言时保留表单草稿。
- **独立部署。** 使用 SQLite 和固定提交版本的核心，支持原生或 Docker Compose 部署；不进行累计流量统计，也没有月流量配额。

只需要一个管理员、不需要用户管理和账户配额时，可使用 [HolePunch Self-hosted](https://github.com/philpm/HolePunch)。两个版本均采用 Apache-2.0。

## 快速开始

准备一台公网 Linux 服务器、指向它的域名，以及运行本地应用的设备。下面以通过 `nas.t.example.com` 发布用户 NAS 上的 Web 应用为例。

### 1. 启动平台

在服务器上安装 Git、Python 3.10+、Docker Engine 和 Compose v2：

```sh
git clone --recurse-submodules https://github.com/philpm/HolePunch-Cloud.git
cd HolePunch-Cloud
python3 scripts/setup.py --public-host edge.example.com \
  --panel-domain panel.example.com --admin-email admin@example.com
python3 scripts/compose.py up
```

替换为自己的域名，将控制台和设备连接域名解析到服务器，并为 Web 隧道配置 `*.t.example.com`。放行 TCP 80/443、控制端口（默认 TCP 2333）和所选 TCP/UDP 隧道端口。使用普通 HTTP CDN 时，设备连接域名应使用仅 DNS 解析。

就绪检查成功后，命令会输出管理地址和初始凭据。妥善保存 `.env` 与 `.env.access.txt`，采集日志时使用 `--hide-secrets`。原生安装与源码安装步骤见[安装指南](docs/zh-CN/INSTALLATION.md)。

### 2. 配置账户和策略

打开 `https://panel.example.com`，登录并完成**设置向导**，将 `t.example.com` 设为域名后缀。在**默认策略**中设置额度，并在开放注册或发送邀请前配置 SMTP。

普通用户初始额度为 1 个客户端、2 条隧道和 1 Mbps 可分配带宽。管理员可修改默认值或为个别用户设置覆盖值，详见[管理员指南](docs/zh-CN/ADMIN_MULTI_USER.md)。

### 3. 接入设备并发布服务

已验证的用户在**客户端**页面创建设备。在用户设备上，将共享 `holepunch-client` 与打过补丁的 `rathole` 二进制文件放在同一个 `bin/` 目录中，将它加入 `PATH`，再执行：

```sh
holepunch-client connect --server https://panel.example.com
```

输入一次性接入码并保持客户端运行。可使用适配设备平台的原生包，或按[共享核心开发指南](vendor/holepunch/docs/zh-CN/DEVELOPMENT.md)构建客户端。

在控制台中创建 Web 隧道：

| 字段 | 值 |
|---|---|
| 名称 | `nas-web` |
| 协议 | Web |
| 本地地址 | `127.0.0.1` |
| 本地端口 | `8080` |
| 域名 | `nas.t.example.com` |
| 带宽分配 | `1 Mbps`，需在用户剩余额度之内 |

配置同步后，访问 `https://nas.t.example.com`。本地应用需持续运行。TCP/UDP 隧道使用控制台显示的公网端点。

## 配置

部署配置保存在 `.env` 或原生安装的受保护 `config.json` 中。SMTP 配置包括 `HP_SMTP_HOST`、`HP_SMTP_FROM`、可选的 `HP_SMTP_USER` / `HP_SMTP_PASSWORD`、`HP_SMTP_PORT` 和 `HP_SMTP_TLS`。修改部署配置后重启服务，并在开放注册前验证邮件确实送达。

在**默认策略**和**用户管理**中管理用户额度及注册策略。每条隧道都会预留带宽，包括已禁用的隧道；用户的分配总和不得超过其额度。限速由双向流量和全部连接共享。详见[管理指南](docs/zh-CN/ADMIN_MULTI_USER.md)和[部署指南](docs/zh-CN/DEPLOYMENT.md)。

### 日志与排障

```sh
docker compose logs -f center rathole caddy
holepunch-client status
holepunch-client doctor
holepunch-client logs --follow
```

本地就绪状态不能证明公网 DNS、SMTP 送达或应用可达。请实际访问隧道，并按部署指南执行备份、升级和回滚。

## 文档

| 指南 | 内容 |
|---|---|
| [安装](docs/zh-CN/INSTALLATION.md) | 原生、源码及 Docker Compose 安装 |
| [管理员指南](docs/zh-CN/ADMIN_MULTI_USER.md) | 用户、邮件、角色和带宽额度 |
| [部署与运维](docs/zh-CN/DEPLOYMENT.md) | 配置、升级、备份及回滚 |
| [架构](docs/zh-CN/ARCHITECTURE.md) | 租户隔离与共享核心边界 |
| [API](docs/zh-CN/API.md) | Cloud 路由和共享 API 约定 |
| [国际化](docs/zh-CN/I18N.md) | 共享界面词条与文档翻译 |

[完整中文文档](docs/zh-CN/README.md) · [English documentation](docs/README.md) · [安全说明](docs/zh-CN/SECURITY.md)

## 从源码构建

需要 Rust 1.91.1+、Python 3.10+ 和本地构建工具。UI 测试使用 Node.js 24。

```sh
git submodule update --init --recursive
python3 scripts/build.py
cargo test --workspace --locked
```

按[开发指南](docs/zh-CN/DEVELOPMENT.md)准备 Caddy 和打过补丁的 rathole，再执行 `python3 scripts/dev-local.py start`。本地控制台为 `http://127.0.0.1:13011`，凭据保存在 `output/local-dev/ACCESS.md`；开发邮件只写入本地发件箱。

`apps/cloud/` 存放 Cloud 应用，`vendor/holepunch/` 固定共享核心版本；`deploy/`、`scripts/`、`tests/` 和 `docs/` 分别存放部署模板、工具、测试和文档。共享修改先在 HolePunch 中审阅，再由 Cloud 更新依赖提交。

## 开发计划

当前重点是经过验证的公开发布、目标平台部署、SMTP 用户接入，以及升级和恢复演练。远程节点调度与故障切换属于后续工作。计费、累计流量配额和独立的 Cloud 桌面分支不在当前范围内，详见[路线图](docs/zh-CN/ROADMAP.md)和[测试指南](docs/zh-CN/TESTING.md)。

## 参与贡献

欢迎问题报告、PR 和翻译。请先阅读[贡献指南](docs/zh-CN/CONTRIBUTING.md)、[支持说明](docs/zh-CN/SUPPORT.md)与[行为准则](docs/zh-CN/CODE_OF_CONDUCT.md)。安全漏洞请通过[安全说明](docs/zh-CN/SECURITY.md)中的私密渠道报告。

## 开源协议

HolePunch Cloud 采用 [Apache-2.0](LICENSE)。固定版本的 HolePunch 核心及第三方组件保留各自的许可证声明，详见[第三方声明](docs/zh-CN/NOTICE.md)。

<!-- translation-source: README.md; source-sha256: f833e98f3165b2d510b447e74051ee820a0b1e36ccb67558d43856a1fd94d72a -->
