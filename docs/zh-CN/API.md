# Cloud API

[English](../API.md) | 简体中文 · [文档目录](README.md)

[共享 API 参考](../../vendor/holepunch/docs/zh-CN/API.md)介绍会话、设置、客户端、隧道、接入、本机网站、诊断和原生客户端。`/api/v1/capabilities` 返回 `edition: cloud`，启用多用户、额度和邮箱认证。管理员 `/api/v1/me` 含 `setup_complete`，成员不会得到此管理员状态。

Cloud 在 `/api/v1` 下增加：

| 方法 | 路径 | 权限 |
|---|---|---|
| POST | `/auth/register` | 公开，受注册策略和限流约束 |
| POST | `/auth/verify`、`/auth/resend`、`/auth/request-reset`、`/auth/reset` | 公开，使用一次性验证与限流 |
| GET / POST | `/admin/users` | 管理员会话，POST 发送邀请 |
| PUT | `/admin/users/{id}` | 管理员会话和 CSRF |
| POST | `/admin/users/{id}/invitation` | 管理员会话和 CSRF |
| GET / PUT | `/admin/policy` | 管理员，PUT 需要 CSRF |

策略字段为 `clients`、`tunnels`、`bps`、`registration`、`domain_suffix`。PUT 在事务中验证总分配。个别用户限制可为 null 以继承默认值，Cloud 隧道 `bandwidth_limit_bps` 必须显式分配。缺少邮件配置时不能开放注册。

`GET/PUT /setup` 是共享管理员接口，保留租户策略与用户资源；设置修改资料、公网控制地址和域名后缀，额度/注册使用 `/admin/policy`。`GET/PUT /domains` 仍仅属于 Self-hosted。

错误消息使用英文开发者诊断，控制台翻译已知错误。示例和 API 证据不能包含真实凭据。

<!-- translation-source: docs/API.md; source-sha256: f0a8ea11a323cf7b293b2f0bdf76e1ba9bba2c7fe236b0791f1f48641f6701dc -->
