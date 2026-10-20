# 安全报告与运维

[English](../../SECURITY.md) | 简体中文 · [文档目录](README.md)

Cloud 源码以 Apache-2.0 公开，运维凭据和用户数据保持私密。涉及共享核心的漏洞，应在披露前与 HolePunch 安全流程协调。

公网控制台使用 HTTPS，SMTP 使用 TLS，设备身份独立，会话启用 CSRF，服务账户遵循最小权限。控制台原始端口、Caddy Admin 和内部网关不公开。真实邮件送达验证前关闭注册，生产不使用开发发件箱或不安全 HTTP 设置。

升级前备份，保留匹配的二进制/配置/数据快照用于回滚。凭据泄露后轮换并撤销受影响会话/设备。安装摘要含初始化秘密，不能进入版本控制或公开日志，运维流程见[部署](DEPLOYMENT.md)。

## 支持版本与报告

安全修复目前面向 `main` 和最新开发版本，旧预览无维护保证，尚无稳定支持周期。

使用 [GitHub 私密漏洞报告](https://github.com/philpm/HolePunch-Cloud/security/advisories/new)，提供受影响提交、影响、最小复现与脱敏诊断。不要在公开 issue 发布利用细节、令牌、数据库或客户信息。

若私密渠道不可用，通过[所有者主页](https://github.com/philpm)提供的私密联系方式安排报告渠道，不在公开求助中披露漏洞。维护者应在公开发布前启用并验证渠道。修复与披露会和报告者协调，目前不承诺响应时间。

<!-- translation-source: SECURITY.md; source-sha256: e950dd185e895bfee167b90421f5aa8d0f16980187a119529b79a2c37231f8eb -->
