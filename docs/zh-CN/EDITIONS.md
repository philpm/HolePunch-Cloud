# 仓库与产品边界

[English](../EDITIONS.md) | 简体中文 · [文档目录](README.md)

[HolePunch](https://github.com/philpm/HolePunch) 和 [HolePunch Cloud](https://github.com/philpm/HolePunch-Cloud) 均为 Apache-2.0 项目，独立构建和发布。

HolePunch 维护服务端/客户端核心、单管理员 Self-hosted、CLI、可选桌面和国际化控制台。Cloud 维护多用户注册、SMTP、邀请、用户管理、资源策略与测试。通用运维文档公开，生产凭据、客户信息和内部证据放在两个仓库之外。

`vendor/holepunch` 是固定完整提交的 Git 子模块。共享修改先提交并发布到上游，再在这里获取精确提交、测试 Cloud 并更新 gitlink。不部署浮动分支，也不保留子模块未提交修改。新克隆和 CI 必须能在无私有仓库令牌的情况下获取依赖。

Cloud 构建包装器编译 Cloud 服务端与共享 CLI，打包通过共享扩展点传入特定版本参数。安装前检查归档类型和目标平台。Self-hosted 构建始终不依赖 Cloud 源码。

两个产品共享 schema 基础，但标记数据库所有权，均不能打开对方的数据目录，不支持自动转换。共用中英文 UI 目录，详见[架构](ARCHITECTURE.md)、[国际化](I18N.md)和[部署](DEPLOYMENT.md)。

<!-- translation-source: docs/EDITIONS.md; source-sha256: 6a6bde7632c036327c496a72657540cf192740f596057d5491bb3c669b035295 -->
