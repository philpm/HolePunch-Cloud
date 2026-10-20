# Cloud 发布指南

[English](../RELEASE.md) | 简体中文 · [文档目录](README.md)

Cloud 是 Apache-2.0 开发版本，版本号定义在 `Cargo.toml`，共享核心通过 `vendor/holepunch` 固定。只有实际发布后，才能将归档和镜像描述为可下载。

## 构建与验证

从干净递归克隆开始，执行[测试](TESTING.md)、审查依赖通告和许可证，确认可从公开核心仓库取得固定提交。按[开发指南](DEVELOPMENT.md)准备补丁版 rathole 和 Caddy。

```sh
python3 scripts/build.py --release
python3 vendor/holepunch/scripts/build-rathole.py
# Example for binaries built on macOS ARM64:
python3 scripts/package.py --target aarch64-apple-darwin --bin-dir target/release --rathole vendor/holepunch/apps/desktop/src-tauri/binaries/holepunch-rathole-aarch64-apple-darwin --out dist
```

归档为 `holepunch-cloud-<version>-<target>.tar.gz`（Windows 为 ZIP），附相邻 `.sha256`。内容包括 Cloud、共享 CLI、补丁版 rathole、安装工具、通用文档、Apache-2.0/第三方声明、依赖清单和构建元数据。Caddy 另行提供或由安装器校验下载，兼容服务端安装名为 `holepunch-center`。

手动发布工作流为 Linux x64/ARM64、macOS ARM64、Windows x64 构建 Actions 归档，不创建 Release 或发布镜像。原生安装器需在各目标 OS 验证，本地构建成功不能证明跨平台支持。

## 发布经过测试的版本

验收后创建精确匹配 `v<Cargo version>` 的标签，保留生成文件名上传各归档和校验和。Cloud 安装器用 `--version` 定位 HolePunch-Cloud 的发布，再检查校验和、版本类型、版本号和平台。宣布可用前测试真实下载和新安装，产物未发布时保留源码及本地 `--archive` 步骤。

Cloud 和 rathole 镜像应从本仓库及固定核心构建，在 `deploy/compose.release.yml` 中使用测试过的前缀和不可变版本。用发布镜像验证新管理员初始化、租户隔离和真实流量；不能以 Self-hosted 镜像替换 Cloud。

## 验收

验证用户隔离、真实 SMTP、一次性接入、额度、转发恢复、两种 UI 语言、受保护副本上的升级回滚、公网 DNS/TLS 和持续负载。检查最终归档有无运维数据并保留许可证声明。除实际分发的共享核心、桌面和 rathole 外，还应审查 Cloud 锁文件；共享依赖脚本不会自动扫描 Cloud 锁文件。

分支与 GitHub 发布设置见[维护](MAINTAINING.md)。生产备份和详细运维证据不进入公开历史或发布产物。

<!-- translation-source: docs/RELEASE.md; source-sha256: f65c55af339583351e7a0550becbb824da15735852771e7733e07bbb561c18a3 -->
