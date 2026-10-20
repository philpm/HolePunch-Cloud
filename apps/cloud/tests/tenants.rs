use async_trait::async_trait;
use axum::{body::Body, http::Request, Router};
use holepunch_cloud::router;
use holepunch_server_core::{
    model::{hash, now},
    node::{NodeConfig, NodeManager},
    App,
};
use http_body_util::BodyExt;
use serde_json::{json, Value};
use std::sync::Arc;
use tower::ServiceExt;
struct Node;
#[async_trait]
impl NodeManager for Node {
    async fn sync_config(&self, _: &str, _: NodeConfig) -> anyhow::Result<()> {
        Ok(())
    }
}
fn setup() -> (tempfile::TempDir, App, Router) {
    let d = tempfile::tempdir().unwrap();
    let a = App::new(
        d.path().join("test.db"),
        "legacy-admin-at-least-32-characters",
        Arc::new(Node),
    )
    .unwrap();
    {
        let s = a.store.lock().unwrap();
        s.set("domain_suffix", "t.example.test").unwrap();
        for (id, role) in [("alice", "user"), ("bob", "user"), ("admin", "admin")] {
            s.db.execute(
                "INSERT INTO users VALUES(?1,?2,'unused',?3,'active',1,?4)",
                rusqlite::params![id, format!("{id}@example.test"), role, now()],
            )
            .unwrap();
            s.db.execute(
                "INSERT INTO sessions VALUES(?,?,?,?)",
                rusqlite::params![hash(id), id, "csrf", now() + 3600],
            )
            .unwrap();
        }
    }
    let r = router(a.clone());
    (d, a, r)
}
async fn req(r: &Router, user: &str, method: &str, path: &str, body: Value) -> (u16, Value) {
    let request = Request::builder()
        .method(method)
        .uri(format!("/api/v1{path}"))
        .header("content-type", "application/json")
        .header("cookie", format!("hp_session={user}"))
        .header("x-csrf-token", "csrf")
        .body(Body::from(body.to_string()))
        .unwrap();
    let res = r.clone().oneshot(request).await.unwrap();
    let code = res.status().as_u16();
    let bytes = res.into_body().collect().await.unwrap().to_bytes();
    (code, serde_json::from_slice(&bytes).unwrap_or(Value::Null))
}
async fn device(r: &Router, user: &str) -> Value {
    let (c, v) = req(r, user, "POST", "/portal/clients", json!({"name":"device"})).await;
    assert_eq!(c, 200, "{v}");
    v
}
fn tunnel(c: &Value, bps: u64) -> Value {
    json!({"name":"api","client_id":c["id"],"protocol":"tcp","local_host":"127.0.0.1","local_port":8000,"enabled":true,"bandwidth_limit_bps":bps})
}
#[tokio::test]
async fn isolation_csrf_and_device_token_scope() {
    let (_d, _a, r) = setup();
    let a = device(&r, "alice").await;
    assert_eq!(
        req(&r, "bob", "POST", "/portal/tunnels", tunnel(&a, 100))
            .await
            .0,
        404
    );
    assert_eq!(
        req(
            &r,
            "bob",
            "POST",
            &format!("/portal/clients/{}/revoke", a["id"].as_str().unwrap()),
            json!({})
        )
        .await
        .0,
        404
    );
    assert_eq!(
        req(&r, "bob", "GET", "/portal/clients", Value::Null)
            .await
            .1,
        json!([])
    );
    assert_eq!(
        req(&r, "alice", "GET", "/admin/users", Value::Null).await.0,
        403
    );
    let res = r
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/portal/clients")
                .header("cookie", "hp_session=alice")
                .header("content-type", "application/json")
                .body(Body::from("{\"name\":\"csrf\"}"))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res.status(), 403);
    let (c, credential) = req(
        &r,
        "",
        "POST",
        "/enroll",
        json!({"token":a["enroll_token"]}),
    )
    .await;
    assert_eq!(c, 200);
    assert_eq!(
        req(
            &r,
            "",
            "POST",
            "/enroll",
            json!({"token":a["enroll_token"]})
        )
        .await
        .0,
        400
    );
    assert_eq!(
        req(
            &r,
            credential["token"].as_str().unwrap(),
            "GET",
            "/me",
            Value::Null
        )
        .await
        .0,
        401
    );
}
#[tokio::test]
async fn parallel_allocations_disabled_reservations_and_release() {
    let (_d, _a, r) = setup();
    let (c1, c2) = tokio::join!(
        req(&r, "alice", "POST", "/portal/clients", json!({"name":"a"})),
        req(&r, "alice", "POST", "/portal/clients", json!({"name":"b"}))
    );
    assert_eq!([c1.0, c2.0].iter().filter(|c| **c == 200).count(), 1);
    let c = if c1.0 == 200 { c1.1 } else { c2.1 };
    let (a, b) = tokio::join!(
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 600000)),
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 600000))
    );
    assert_eq!([a.0, b.0].iter().filter(|c| **c == 200).count(), 1);
    let t = if a.0 == 200 { a.1 } else { b.1 };
    let path = format!("/portal/tunnels/{}", t["id"].as_str().unwrap());
    let mut input = tunnel(&c, 600000);
    input["enabled"] = json!(false);
    assert_eq!(req(&r, "alice", "PUT", &path, input).await.0, 200);
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 500000))
            .await
            .0,
        409
    );
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 400000))
            .await
            .0,
        200
    );
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 0))
            .await
            .0,
        409
    );
    assert_eq!(req(&r, "alice", "DELETE", &path, Value::Null).await.0, 200);
    assert_eq!(
        req(&r, "alice", "GET", "/me", Value::Null).await.1["remaining_bps"],
        600000
    );
}
#[tokio::test]
async fn policy_inheritance_overrides_and_transactional_rejection() {
    let (_d, a, r) = setup();
    let c = device(&r, "alice").await;
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 600000))
            .await
            .0,
        200
    );
    let update =
        json!({"status":"active","role":"user","clients":null,"tunnels":null,"bps":500000});
    assert_eq!(
        req(&r, "admin", "PUT", "/admin/users/alice", update)
            .await
            .0,
        409
    );
    let p = json!({"clients":1,"tunnels":2,"bps":500000,"registration":false,"domain_suffix":"t.example.test"});
    assert_eq!(req(&r, "admin", "PUT", "/admin/policy", p).await.0, 409);
    assert_eq!(
        a.store.lock().unwrap().get("default_bps").unwrap().unwrap(),
        "1000000"
    );
    assert_eq!(
        req(
            &r,
            "admin",
            "PUT",
            "/admin/users/alice",
            json!({"status":"active","role":"user","clients":null,"tunnels":null,"bps":2000000})
        )
        .await
        .0,
        200
    );
    assert_eq!(req(&r,"admin","PUT","/admin/policy",json!({"clients":1,"tunnels":2,"bps":500000,"registration":false,"domain_suffix":"t.example.test"})).await.0,200);
    assert_eq!(
        req(&r, "alice", "GET", "/me", Value::Null).await.1["limits"]["bps"],
        2000000
    );
    assert_eq!(
        req(&r, "bob", "GET", "/me", Value::Null).await.1["limits"]["bps"],
        500000
    );
}
#[tokio::test]
async fn random_domains_cooldown_and_frozen_device() {
    let (_d, a, r) = setup();
    let c = device(&r, "alice").await;
    let mut input = tunnel(&c, 100000);
    input["protocol"] = json!("web");
    let (code, t) = req(&r, "alice", "POST", "/portal/tunnels", input.clone()).await;
    assert_eq!(code, 200, "{t}");
    assert!(t["domain"].as_str().unwrap().ends_with(".t.example.test"));
    req(
        &r,
        "alice",
        "DELETE",
        &format!("/portal/tunnels/{}", t["id"].as_str().unwrap()),
        Value::Null,
    )
    .await;
    input["domain"] = t["domain"].clone();
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", input).await.0,
        409
    );
    let (_, credential) = req(
        &r,
        "",
        "POST",
        "/enroll",
        json!({"token":c["enroll_token"]}),
    )
    .await;
    let update = json!({"status":"frozen","role":"user","clients":null,"tunnels":null,"bps":null});
    assert_eq!(
        req(&r, "admin", "PUT", "/admin/users/alice", update)
            .await
            .0,
        200
    );
    assert_eq!(req(&r, "alice", "GET", "/me", Value::Null).await.0, 401);
    assert!(a.store.lock().unwrap().active_tunnels().unwrap().is_empty());
    let res = r
        .oneshot(
            Request::builder()
                .uri("/api/v1/client/config")
                .header(
                    "authorization",
                    format!("Bearer {}", credential["token"].as_str().unwrap()),
                )
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res.status(), 403);
}
#[tokio::test]
async fn zero_bandwidth_draft_and_last_admin_protection() {
    let (_d, _a, r) = setup();
    let c = device(&r, "alice").await;
    let (code, t) = req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 0)).await;
    assert_eq!(code, 200);
    assert_eq!(t["enabled"], false);
    assert_eq!(
        req(
            &r,
            "admin",
            "PUT",
            "/admin/users/admin",
            json!({"status":"frozen","role":"user","clients":null,"tunnels":null,"bps":null})
        )
        .await
        .0,
        400
    );
}

#[tokio::test]
async fn atomic_reallocation_budget_decrease_and_legacy_guard() {
    let (_d, a, r) = setup();
    let c = device(&r, "alice").await;
    let (_, one) = req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 600_000)).await;
    let (_, two) = req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 400_000)).await;
    let items = json!({"allocations":[{"tunnel_id":one["id"],"bps":400_000},{"tunnel_id":two["id"],"bps":600_000}]});
    assert_eq!(
        req(&r, "bob", "POST", "/portal/bandwidth", items.clone())
            .await
            .0,
        404
    );
    assert_eq!(
        req(&r, "alice", "POST", "/portal/bandwidth", items).await.0,
        200
    );
    let update = json!({"status":"active","role":"user","bps":500_000,"allocations":[{"tunnel_id":one["id"],"bps":200_000},{"tunnel_id":two["id"],"bps":300_000}]});
    assert_eq!(
        req(&r, "admin", "PUT", "/admin/users/alice", update)
            .await
            .0,
        200
    );
    let (_, me) = req(&r, "alice", "GET", "/me", json!(null)).await;
    assert_eq!(me["allocated_bps"], 500_000);
    assert_eq!(me["limits"]["bps"], 500_000);
    let invalid = json!({"allocations":[{"tunnel_id":one["id"],"bps":400_000}]});
    assert_eq!(
        req(&r, "alice", "POST", "/portal/bandwidth", invalid)
            .await
            .0,
        409
    );
    assert_eq!(
        req(&r, "admin", "POST", "/clients", json!({"name":"unowned"}))
            .await
            .0,
        409
    );
    assert_eq!(a.store.lock().unwrap().clients().unwrap().len(), 1);
}

#[tokio::test]
async fn profile_sessions_deletion_and_backend_conflicts() {
    let (_d, a, r) = setup();
    let c = device(&r, "alice").await;
    req(&r, "alice", "POST", "/portal/tunnels", tunnel(&c, 500_000)).await;
    assert_eq!(
        req(
            &r,
            "alice",
            "PUT",
            "/me/profile",
            json!({"display_name":"Alice"})
        )
        .await
        .0,
        200
    );
    assert_eq!(
        req(&r, "alice", "GET", "/me", json!(null)).await.1["profile"],
        "Alice"
    );
    let (_, sessions) = req(&r, "alice", "GET", "/me/sessions", json!(null)).await;
    let path = format!("/me/sessions/{}", sessions[0]["id"].as_str().unwrap());
    assert_eq!(req(&r, "bob", "DELETE", &path, json!(null)).await.0, 200);
    assert_eq!(req(&r, "alice", "GET", "/me", json!(null)).await.0, 200);
    let update = json!({"status":"deleted","role":"user"});
    assert_eq!(
        req(&r, "admin", "PUT", "/admin/users/alice", update)
            .await
            .0,
        200
    );
    assert_eq!(req(&r, "alice", "GET", "/me", json!(null)).await.0, 401);
    let s = a.store.lock().unwrap();
    assert!(s.tunnels().unwrap().is_empty());
    assert!(!s.clients().unwrap()[0].active);
    assert_eq!(
        s.db.query_row("SELECT COUNT(*) FROM profiles", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        0
    );
}

#[tokio::test]
async fn cloud_rejects_unlimited_and_has_no_selfhost_domain_settings() {
    let (_d, _a, r) = setup();
    let client = device(&r, "alice").await;
    let mut input = tunnel(&client, 1000);
    input["bandwidth_limit_bps"] = Value::Null;
    assert_eq!(
        req(&r, "alice", "POST", "/portal/tunnels", input).await.0,
        400
    );
    assert_eq!(
        req(&r, "admin", "GET", "/domains", Value::Null).await.0,
        404
    );
    let (_, row) = req(
        &r,
        "alice",
        "POST",
        "/portal/tunnels",
        tunnel(&client, 1000),
    )
    .await;
    assert_eq!(
        req(
            &r,
            "alice",
            "POST",
            "/portal/bandwidth",
            json!({"allocations":[{"tunnel_id":row["id"],"bps":null}]})
        )
        .await
        .0,
        400
    );
}

#[tokio::test]
async fn administrator_setup_preserves_tenant_policy_and_member_isolation() {
    let (_dir, app, router) = setup();
    let alice = device(&router, "alice").await;
    assert_eq!(
        req(
            &router,
            "alice",
            "POST",
            "/portal/tunnels",
            tunnel(&alice, 500_000)
        )
        .await
        .0,
        200
    );
    let before = req(&router, "admin", "GET", "/admin/policy", Value::Null)
        .await
        .1;
    let input = json!({"display_name":"Cloud operator", "public_addr":"edge.example.test:2333", "domain_suffix":"t.example.test"});
    assert_eq!(
        req(&router, "alice", "GET", "/setup", Value::Null).await.0,
        403
    );
    assert_eq!(
        req(&router, "alice", "PUT", "/setup", input.clone())
            .await
            .0,
        403
    );
    assert!(req(&router, "alice", "GET", "/me", Value::Null)
        .await
        .1
        .get("setup_complete")
        .is_none());
    assert_eq!(
        req(&router, "admin", "GET", "/me", Value::Null).await.1["setup_complete"],
        false
    );
    assert_eq!(req(&router, "admin", "PUT", "/setup", input).await.0, 200);
    assert_eq!(
        req(&router, "admin", "GET", "/admin/policy", Value::Null)
            .await
            .1,
        before
    );
    let member = req(&router, "alice", "GET", "/me", Value::Null).await.1;
    assert_eq!(member["allocated_bps"], 500_000);
    assert_eq!(member["limits"]["bps"], 1_000_000);
    assert_eq!(member["tunnel_count"], 1);
    assert_eq!(
        req(&router, "bob", "GET", "/portal/tunnels", Value::Null)
            .await
            .1,
        json!([])
    );
    assert_eq!(
        app.store
            .lock()
            .unwrap()
            .get("setup_complete")
            .unwrap()
            .as_deref(),
        Some("true")
    );
}
