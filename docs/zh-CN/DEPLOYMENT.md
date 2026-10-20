# Cloud 部署与升级

[English](../DEPLOYMENT.md) | 简体中文 · [文档目录](README.md)

全新安装先看[安装指南](INSTALLATION.md)。生产使用 Cloud 二进制、固定共享核心、补丁版 rathole 和 Caddy，Docker 可选。控制台原始端口、Caddy Admin 和内部限速网关应保持私有，仅公开需要的 HTTPS、控制和隧道端口。

## 配置

必需初始化配置：`HP_ADMIN_TOKEN`（随机，至少 32 字节）、`HP_BOOTSTRAP_EMAIL`、`HP_BOOTSTRAP_PASSWORD`（至少 12 字节）、`HP_PUBLIC_ADDR`（公网控制主机:端口）及 `HP_DATA_DIR`。只有无管理员时才创建首个管理员，之后重启不重置密码。凭据保存在受保护环境文件或原生 `config.json`。

监听配置包括 `HP_BIND`、`HP_RATHOLE_BIND`、`HP_CADDY_URL`、`HP_CADDY_LISTEN`、`HP_TLS_ASK_URL`、`HP_PANEL_DOMAIN`、`HP_HTTP_PORT`、`HP_HTTPS_LISTEN`、`HP_PORT_START`、`HP_PORT_END`，含义见[共享部署参考](../../vendor/holepunch/docs/zh-CN/DEPLOYMENT.md)。启动器选择版本类型，`HP_EDITION` 不会转换已有数据库。

邮件配置为 `HP_SMTP_HOST`、`HP_SMTP_FROM`、可选 `HP_SMTP_USER` / `HP_SMTP_PASSWORD`、`HP_SMTP_PORT` 和 `HP_SMTP_TLS`（`starttls` 或 `tls`）。原生监督器从 `config.json` 的 `env` 读取，systemd 环境文件部署从服务环境读取，Compose 从 `.env` 读取，修改后重启。公网生产不能使用开发专用 `HP_MAIL_OUTBOX` 或 `HP_ALLOW_HTTP=1`。默认关闭注册；无 SMTP 时邀请、验证和密码重置不可用。

## 已有原生 systemd 部署

升级时保留现有服务拓扑和数据路径。旧安装常使用 `holepunch-center`、`rathole` 和 `holepunch-caddy` 三个单元，`holepunch-center` 是 Cloud 兼容可执行名称。新单单元安装器用于全新安装，不执行原地单元转换。

1. 在独立目录构建测试发布，检查可用磁盘/内存、当前版本、活动单元和就绪状态。
2. 用 `HP_DATA_DIR=DATA holepunch-center backup BACKUP.db` 创建一致在线数据库备份，同时备份环境文件、单元、Caddy 证书/状态目录和已安装二进制，保留加密或受控的异机副本。
3. 在数据库副本上，用隔离监听、本地证书和测试凭据演练迁移，不能让演练实例指向生产 Caddy Admin 或公网 ACME。
4. 切换前停止服务端和 rathole，制作最终一致数据目录快照，放入测试过的二进制，仅更新必需环境项，重启服务端和 rathole，保留 Caddy 配置/证书。
5. 检查 `/healthz`、`/readyz`、公网 HTTPS、管理员登录、能力、数据所有权及至少一次真实 TCP/UDP/Web 隧道访问，保留已有设备令牌和端点。

## schema 2 升级到 schema 4

Cloud 启动时迁移旧库，第一次启动前先配置初始化管理员。旧设备归其所有，ID、令牌、隧道名称、公网端口和 Noise 密钥保留。已有隧道各分配 1 Mbps，初始管理员获得独立较大额度，普通用户继承 1 客户端 / 2 隧道 / 1 Mbps。验证后通过控制台调整分配。已有部署不强制重新首次设置，侧栏仍可打开向导。

标记为 `self_hosted` 的数据库不能由 Cloud 打开，服务端会拒绝类型不匹配。此迁移用于旧的未标记部署或已有 Cloud 数据库。

## 回滚

停止新服务端和 rathole，恢复匹配旧版本的二进制、环境以及升级前最终数据库/数据快照，禁止旧二进制打开升级后的 schema。仅在切换修改了 Caddy 状态时恢复它，然后重启原单元，检查就绪和原隧道端点。快照之后的变更会丢失，应缩短验证窗口。

## 初始访问与运维

`python3 scripts/access.py --env-file /path/to/env --hide-secrets` 或 `--config PREFIX/config.json` 解释浏览器初始访问，但不声称服务就绪。只在私密终端省略 `--hide-secrets`。摘要含初始化凭据，不反映控制台中后来修改的密码，不能纳入版本控制。

systemd 用 journalctl，容器用 `docker compose logs`。`/readyz` 检查本地配置与控制就绪，不证明公网 DNS、云防火墙、SMTP 或远端应用可用。定期备份，在扩大使用前演练恢复。

<!-- translation-source: docs/DEPLOYMENT.md; source-sha256: 83be9b39b9a872a3d055f43ca35c65fcb710623e9e0fe98f0200da751077b8a7 -->
