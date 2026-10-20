# 安装 Cloud

[English](../INSTALLATION.md) | 简体中文 · [文档目录](README.md)

使用 `--recurse-submodules` 克隆 `https://github.com/philpm/HolePunch-Cloud.git`，核心固定到具体提交。部署工具需要 Python 3.10+，源码构建还需要 Rust 1.91.1+ 和平台构建工具。Cloud 发布包和镜像单独发布，下列命令不假设未发布产物已经存在。

## 1. 交互式原生安装

在 Cloud 仓库中执行：

```sh
sh scripts/install.sh --source . --prefix "$HOME/.local/share/holepunch-cloud"
```

安装器询问公网控制主机、控制台域名、管理员邮箱和端口，构建 Cloud、共享 CLI/sidecar，验证 Caddy，创建受保护配置，并输出管理地址和初始邮箱/密码/API 令牌。共享安装器支持 Linux、macOS 和 Windows x64，以及 Linux/macOS ARM64。Windows 使用 `scripts/install.ps1`，通过 `--prefix` 指定可写目录。原生前台模式需要持续运行的终端或进程监督器。

全新的 Linux systemd 安装需以 root 运行，指定 `--service systemd --prefix /opt/holepunch-cloud`；不要覆盖已有部署。服务以非特权账户监督三个进程，检查已有监听，不修改 DNS 或防火墙。

使用已发布原生包时，从项目 Releases 页面下载归档及对应 `.sha256`，解压后执行：

```sh
python3 deploy.py install --archive /path/to/holepunch-cloud-VERSION-TARGET.tar.gz --prefix /opt/holepunch-cloud --service systemd
```

`--archive` 拒绝 Self-hosted 或错误平台的归档。实际发布版本可用 `python3 scripts/deploy.py install --version VERSION` 下载 Cloud 包，并检查校验和、版本类型、版本号及平台；发布必须包含约定命名的归档与校验文件。安装器不覆盖已有目录，采集终端日志时使用 `--hide-secrets`。

## 2. 克隆、构建并运行

```sh
python3 scripts/build.py --release
python3 vendor/holepunch/scripts/build-rathole.py
```

服务端为 `target/release/holepunch-cloud`，兼容二进制 `holepunch-center` 运行同一 Cloud 应用。安装 Caddy 和固定补丁版 rathole，按[部署指南](DEPLOYMENT.md)配置环境变量并监督三个进程。若希望简化监督配置，可使用上文 `--source .` 原生安装。

## 3. Linux Docker Compose

```sh
python3 scripts/setup.py --interactive
python3 scripts/compose.py up
```

辅助命令启动源码构建、等待实际就绪，再输出浏览器访问信息。`.env` 和 `.env.access.txt` 含随机初始凭据，必须保密。预构建镜像使用 `deploy/compose.release.yml`，将 `HP_IMAGE_PREFIX` 设为验证过的仓库前缀，`HP_VERSION` 设为精确标签，必要时先登录镜像仓库，再传入 `--file deploy/compose.release.yml --pull`。镜像名为 `PREFIX-center:TAG` 和 `PREFIX-rathole:TAG`，必须由本 Cloud 仓库及固定核心构建，不能替换为 Self-hosted 镜像。

Compose 需要 Linux 主机网络，Docker Desktop 不是经过验证的生产替代方案。

## 首次浏览器访问

使用显示的初始管理员邮箱和密码登录。四步设置向导涵盖账户、控制地址/域名后缀、本地服务检查及 CLI 接入。登录页和控制台顶部的语言选择按浏览器保存。修改密码需要当前密码，保存后注销已有会话。

完成服务端设置后，在**默认策略**配置用户额度和注册。注册或邀请前先配置 SMTP。普通用户默认 1 个客户端、2 条隧道、1 Mbps，管理员可单独覆盖。管理员 API 令牌不是 Web 密码，也不是客户端接入令牌。

无控制台域名时，面板监听回环地址，使用显示的 SSH 转发命令。有域名时，DNS 指向 VPS，并允许 HTTPS/ACME 到达 Caddy。已有 Nginx/宝塔的服务器，在分配 80/443 前应阅读[共存指南](../../vendor/holepunch/docs/zh-CN/COEXISTENCE.md)。

<!-- translation-source: docs/INSTALLATION.md; source-sha256: a279a7a506f91075a1907849c571f128566245601790b063a2e433e2d973e861 -->
