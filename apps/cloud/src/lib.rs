use std::path::PathBuf;
// Private Cloud application: registration, SMTP and tenant administration.
use axum::{
    extract::{Path, State},
    http::{HeaderMap, StatusCode},
    routing::{get, post, put},
    Json, Router,
};
use holepunch_server_core::{bad, dirty, model::*, node, tenant::*, ApiResult, App, Error};
use rusqlite::{params, OptionalExtension};
use serde::Deserialize;
use serde_json::{json, Value};
async fn register(State(a): State<App>, Json(i): Json<Credentials>) -> ApiResult<Json<Value>> {
    let e = email(&i.email)?;
    {
        let s = a.store.lock().unwrap();
        if s.get("registration")?.as_deref() != Some("true") {
            return Err(Error(
                StatusCode::FORBIDDEN,
                "Registration is currently closed".into(),
            ));
        }
        throttle(&s, "register-global", 30)?;
        throttle(&s, &format!("register:{e}"), 3)?;
    }
    let p = password_async(i.password).await?;
    let id = secret();
    let token = secret();
    {
        let s = a.store.lock().unwrap();
        let exists: bool = s.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM users WHERE email=?)",
            [&e],
            |r| r.get(0),
        )?;
        if exists {
            return Ok(Json(json!({"status":"check_email"})));
        }
        s.change("user.register", &id, |s| {
            s.db.execute(
                "INSERT INTO users VALUES(?,?,?,'user','active',0,?)",
                params![id, e, p, now()],
            )?;
            s.db.execute(
                "INSERT INTO challenges VALUES(?,?,'verify',?)",
                params![hash(&token), id, now() + 1800],
            )?;
            Ok(())
        })?;
    }
    send_mail(&a, &e, "verify", &token).await?;
    Ok(Json(json!({"status":"check_email"})))
}
async fn send_mail(a: &App, to: &str, purpose: &str, token: &str) -> ApiResult<()> {
    let result = deliver_mail(to, purpose, token).await;
    a.store.lock().unwrap().db.execute("INSERT INTO mail_delivery VALUES(?,?,?,?) ON CONFLICT(email,purpose) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at",params![to,purpose,if result.is_ok(){"sent"}else{"failed"},now()])?;
    result
}
async fn deliver_mail(to: &str, purpose: &str, token: &str) -> ApiResult<()> {
    let text=format!("HolePunch {purpose}\nOne-time code (valid for 30 minutes): {token}\nEnter this code in the HolePunch console.\n");
    if let Some(dir) = std::env::var("HP_MAIL_OUTBOX")
        .ok()
        .filter(|v| !v.trim().is_empty())
    {
        let path = PathBuf::from(dir);
        std::fs::create_dir_all(&path).map_err(anyhow::Error::from)?;
        node::private_write(
            &path.join(format!("{}.txt", secret())),
            &format!("To: {to}\n{text}"),
        )
        .map_err(Error::from)?;
        return Ok(());
    }
    use lettre::{
        transport::smtp::authentication::Credentials, AsyncSmtpTransport, AsyncTransport, Message,
        Tokio1Executor,
    };
    let host = std::env::var("HP_SMTP_HOST")
        .map_err(|_| bad("Email is not configured; contact the administrator"))?;
    let from = std::env::var("HP_SMTP_FROM").map_err(|_| bad("Email sender is not configured"))?;
    let msg = Message::builder()
        .from(from.parse().map_err(|_| bad("Invalid sender address"))?)
        .to(to.parse().map_err(|_| bad("Enter a valid email address"))?)
        .subject("HolePunch account verification")
        .body(text)
        .map_err(|e| anyhow::anyhow!(e))?;
    let mut transport = match std::env::var("HP_SMTP_TLS")
        .as_deref()
        .unwrap_or("starttls")
    {
        "starttls" => AsyncSmtpTransport::<Tokio1Executor>::starttls_relay(&host),
        "tls" => AsyncSmtpTransport::<Tokio1Executor>::relay(&host),
        _ => return Err(bad("SMTP TLS mode must be starttls or tls")),
    }
    .map_err(|e| anyhow::anyhow!(e))?;
    if let Some(port) = std::env::var("HP_SMTP_PORT").ok().filter(|v| !v.is_empty()) {
        transport = transport.port(port.parse().map_err(|_| bad("Invalid SMTP port"))?);
    }
    transport = transport.timeout(Some(std::time::Duration::from_secs(15)));
    if let (Ok(user), Ok(pass)) = (
        std::env::var("HP_SMTP_USER"),
        std::env::var("HP_SMTP_PASSWORD"),
    ) {
        if !user.is_empty() {
            transport = transport.credentials(Credentials::new(user, pass));
        }
    }
    transport.build().send(msg).await.map_err(|_| {
        Error(
            StatusCode::BAD_GATEWAY,
            "Email delivery failed; try again later".into(),
        )
    })?;
    Ok(())
}
#[derive(Deserialize)]
struct Challenge {
    token: String,
    password: Option<String>,
}
async fn verify(State(a): State<App>, Json(i): Json<Challenge>) -> ApiResult<Json<Value>> {
    consume(&a, &i, "verify", None)?;
    Ok(Json(json!({"status":"verified"})))
}
fn consume(a: &App, i: &Challenge, purpose: &str, new_password: Option<String>) -> ApiResult<()> {
    let s = a.store.lock().unwrap();
    throttle(&s, "challenge-global", 60)?;
    let id: Option<String> =
        s.db.query_row(
            "SELECT user_id FROM challenges WHERE token_hash=? AND purpose=? AND expires>?",
            params![hash(&i.token), purpose, now()],
            |r| r.get(0),
        )
        .optional()?;
    let id = id.ok_or_else(|| bad("Code is invalid or expired"))?;
    s.change("user.verify_or_reset", &id, |s| {
        s.db.execute(
            "DELETE FROM challenges WHERE token_hash=?",
            [hash(&i.token)],
        )?;
        if let Some(p) = new_password {
            s.db.execute(
                "UPDATE users SET password=?,verified=1 WHERE id=?",
                params![p, id],
            )?;
            s.db.execute("DELETE FROM sessions WHERE user_id=?", [&id])?;
        } else {
            s.db.execute("UPDATE users SET verified=1 WHERE id=?", [&id])?;
        }
        Ok(())
    })?;
    Ok(())
}
#[derive(Deserialize)]
struct EmailInput {
    email: String,
}
async fn request_reset(State(a): State<App>, Json(i): Json<EmailInput>) -> ApiResult<Json<Value>> {
    request_challenge(a, i, "reset").await
}
async fn resend(State(a): State<App>, Json(i): Json<EmailInput>) -> ApiResult<Json<Value>> {
    request_challenge(a, i, "verify").await
}
async fn request_challenge(a: App, i: EmailInput, purpose: &str) -> ApiResult<Json<Value>> {
    let e = email(&i.email)?;
    let token = secret();
    let found = {
        let s = a.store.lock().unwrap();
        throttle(&s, "mail-global", 30)?;
        throttle(&s, &format!("mail:{e}"), 3)?;
        let id: Option<String> =
            s.db.query_row(
                "SELECT id FROM users WHERE email=? AND status='active'",
                [&e],
                |r| r.get(0),
            )
            .optional()?;
        if let Some(id) = id {
            s.db.execute(
                "DELETE FROM challenges WHERE user_id=? AND purpose=?",
                params![id, purpose],
            )?;
            s.db.execute(
                "INSERT INTO challenges VALUES(?,?,?,?)",
                params![hash(&token), id, purpose, now() + 1800],
            )?;
            true
        } else {
            false
        }
    };
    if found {
        send_mail(&a, &e, purpose, &token).await?;
    }
    Ok(Json(json!({"status":"check_email"})))
}
async fn reset(State(a): State<App>, Json(i): Json<Challenge>) -> ApiResult<Json<Value>> {
    let raw = i.password.clone().unwrap_or_default();
    {
        let s = a.store.lock().unwrap();
        throttle(&s, "reset-global", 30)?;
    }
    let p = password_async(raw).await?;
    consume(&a, &i, "reset", Some(p))?;
    Ok(Json(json!({"status":"password_updated"})))
}
async fn users(State(a): State<App>, h: HeaderMap) -> ApiResult<Json<Value>> {
    manager(&a, &h, false)?;
    let s = a.store.lock().unwrap();
    let mut q = s.db.prepare("SELECT id FROM users ORDER BY created_at")?;
    let ids = q
        .query_map([], |r| r.get::<_, String>(0))?
        .collect::<rusqlite::Result<Vec<_>>>()?;
    let mut rows = vec![];
    for id in ids {
        let overrides: Option<(Option<u64>, Option<u64>, Option<u64>)> =
            s.db.query_row(
                "SELECT clients,tunnels,bps FROM user_limits WHERE user_id=?",
                [&id],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
            )
            .optional()?;
        let u = read_user(&s, &id)?;
        let mail: Option<String> =
            s.db.query_row(
                "SELECT status FROM mail_delivery WHERE email=? ORDER BY updated_at DESC LIMIT 1",
                [&u.email],
                |r| r.get(0),
            )
            .optional()?;
        rows.push(json!({"mail_status":mail,"user":u,"limits":limits(&s,&id)?,"overrides":overrides.map(|(c,t,b)|json!({"clients":c,"tunnels":t,"bps":b})),"allocated_bps":allocated(&s,&id,"")?,"client_count":count(&s,&id,"clients")?,"tunnel_count":count(&s,&id,"tunnels")?}));
    }
    Ok(Json(json!(rows)))
}
#[derive(Deserialize)]
struct AddUser {
    email: String,
}
async fn add_user(
    State(a): State<App>,
    h: HeaderMap,
    Json(i): Json<AddUser>,
) -> ApiResult<Json<Value>> {
    let actor = manager(&a, &h, true)?;
    let e = email(&i.email)?;
    let id = secret();
    let code = secret();
    let p = password_async(secret()).await?;
    {
        let s = a.store.lock().unwrap();
        let exists: bool = s.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM users WHERE email=?)",
            [&e],
            |r| r.get(0),
        )?;
        if exists {
            return Err(Error(StatusCode::CONFLICT, "Email already exists".into()));
        }
        s.change("user.invite", &format!("{}:{id}", actor.id), |s| {
            s.db.execute(
                "INSERT INTO users VALUES(?,?,?,'user','active',0,?)",
                params![id, e, p, now()],
            )?;
            s.db.execute(
                "INSERT INTO challenges VALUES(?,?,'reset',?)",
                params![hash(&code), id, now() + 1800],
            )?;
            Ok(())
        })?;
    }
    send_mail(&a, &e, "reset", &code).await?;
    Ok(Json(json!({"id":id,"status":"invited"})))
}
#[derive(Deserialize)]
struct UserUpdate {
    status: String,
    role: String,
    clients: Option<u64>,
    tunnels: Option<u64>,
    bps: Option<u64>,
    #[serde(default)]
    allocations: Vec<Allocation>,
}
async fn update_user(
    State(a): State<App>,
    h: HeaderMap,
    Path(id): Path<String>,
    Json(i): Json<UserUpdate>,
) -> ApiResult<Json<Value>> {
    let actor = manager(&a, &h, true)?;
    if !["active", "frozen", "deleted"].contains(&i.status.as_str())
        || !["admin", "user"].contains(&i.role.as_str())
    {
        return Err(bad("Invalid role or status"));
    }
    let s = a.store.lock().unwrap();
    let old = read_user(&s, &id)?;
    if old.status == "deleted" {
        return Err(bad("Deleted accounts cannot be restored"));
    }
    if old.role == "admin" && (i.role != "admin" || i.status != "active") {
        let n: i64 = s.db.query_row(
            "SELECT COUNT(*) FROM users WHERE role='admin' AND status='active'",
            [],
            |r| r.get(0),
        )?;
        if n <= 1 {
            return Err(bad("Cannot deactivate the last administrator"));
        }
    }
    for (value, max) in [
        (i.clients, 10000),
        (i.tunnels, 10000),
        (i.bps, 1_000_000_000_000),
    ] {
        if value.is_some_and(|v| v > max) {
            return Err(bad("Limits exceed the supported range"));
        }
    }
    let new_bps = i
        .bps
        .unwrap_or(s.get("default_bps")?.unwrap().parse().unwrap());
    if allocation_total(&s, &old, &i.allocations)? > new_bps {
        return Err(Error(
            StatusCode::CONFLICT,
            "Reduce tunnel allocations before reducing the user limit".into(),
        ));
    }
    s.change("user.update",&format!("{}:{id}",actor.id),|s|{
 s.db.execute("UPDATE users SET status=?,role=? WHERE id=?",params![i.status,i.role,id])?;s.db.execute("INSERT INTO user_limits VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET clients=excluded.clients,tunnels=excluded.tunnels,bps=excluded.bps",params![id,i.clients,i.tunnels,i.bps])?;
 write_allocations(s,&i.allocations)?;
 if i.status=="deleted" {
  s.db.execute("INSERT INTO domain_cooldown SELECT domain,? FROM tunnels WHERE domain IS NOT NULL AND client_id IN(SELECT client_id FROM client_owners WHERE user_id=?) ON CONFLICT(domain) DO UPDATE SET expires=excluded.expires",params![now()+7*86400,id])?;
  s.db.execute("DELETE FROM tunnels WHERE client_id IN(SELECT client_id FROM client_owners WHERE user_id=?)",[&id])?;
  s.db.execute("UPDATE clients SET active=0,running=0 WHERE id IN(SELECT client_id FROM client_owners WHERE user_id=?)",[&id])?;
  s.db.execute("DELETE FROM challenges WHERE user_id=?",[&id])?;
  s.db.execute("DELETE FROM profiles WHERE user_id=?",[&id])?;
  s.db.execute("DELETE FROM mail_delivery WHERE email=?",[&old.email])?;
  s.db.execute("UPDATE users SET email=?,password='',verified=0 WHERE id=?",params![format!("deleted+{id}@invalid.example"),id])?;
 }

 if old.status!=i.status||old.role!=i.role{s.db.execute("DELETE FROM sessions WHERE user_id=?",[&id])?;}
 Ok(())})?;
    Ok(Json(json!({"status":"pending"})))
}
async fn policy(State(a): State<App>, h: HeaderMap) -> ApiResult<Json<Value>> {
    manager(&a, &h, false)?;
    let s = a.store.lock().unwrap();
    Ok(Json(
        json!({"clients":s.get("default_clients")?,"tunnels":s.get("default_tunnels")?,"bps":s.get("default_bps")?,"registration":s.get("registration")?.as_deref()==Some("true"),"domain_suffix":s.get("domain_suffix")?}),
    ))
}
#[derive(Deserialize)]
struct Policy {
    clients: u64,
    tunnels: u64,
    bps: u64,
    registration: bool,
    domain_suffix: String,
}
async fn update_policy(
    State(a): State<App>,
    h: HeaderMap,
    Json(i): Json<Policy>,
) -> ApiResult<Json<Value>> {
    let actor = manager(&a, &h, true)?;
    if i.clients > 10000 || i.tunnels > 10000 || i.bps > 1_000_000_000_000 {
        return Err(bad("Limits exceed the supported range"));
    }
    let suffix = if i.domain_suffix.is_empty() {
        String::new()
    } else {
        domain(&i.domain_suffix).map_err(bad)?
    };
    let configured = |key| {
        std::env::var(key)
            .ok()
            .is_some_and(|v| !v.trim().is_empty())
    };
    if i.registration
        && !configured("HP_MAIL_OUTBOX")
        && !(configured("HP_SMTP_HOST") && configured("HP_SMTP_FROM"))
    {
        return Err(bad("Configure email delivery first"));
    }
    let s = a.store.lock().unwrap();
    let tx = s.db.unchecked_transaction()?;
    for (k, v) in [
        ("default_clients", i.clients.to_string()),
        ("default_tunnels", i.tunnels.to_string()),
        ("default_bps", i.bps.to_string()),
    ] {
        s.set(k, &v)?;
    }
    let ids = {
        let mut q = s.db.prepare("SELECT id FROM users")?;
        let rows = q
            .query_map([], |r| r.get::<_, String>(0))?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        rows
    };
    for id in ids {
        let l = limits(&s, &id)?;
        if allocated(&s, &id, "")? > l.bps {
            return Err(Error(
                StatusCode::CONFLICT,
                "Default limit is below existing allocations; adjust affected users first".into(),
            ));
        }
    }
    s.set(
        "registration",
        if i.registration { "true" } else { "false" },
    )?;
    s.set("domain_suffix", &suffix)?;
    dirty(&s)?;
    s.db.execute(
        "INSERT INTO audit(created_at,action,target) VALUES(?,'policy.update',?)",
        params![now(), actor.id],
    )?;
    tx.commit()?;
    Ok(Json(json!({"status":"pending"})))
}
async fn reinvite(
    State(a): State<App>,
    h: HeaderMap,
    Path(id): Path<String>,
) -> ApiResult<Json<Value>> {
    let actor = manager(&a, &h, true)?;
    let e = {
        let s = a.store.lock().unwrap();
        let u = read_user(&s, &id)?;
        if u.status != "active" {
            return Err(bad("Account is not active"));
        }
        s.change("user.reinvite", &format!("{}:{id}", actor.id), |_| Ok(()))?;
        u.email
    };
    request_challenge(a, EmailInput { email: e }, "reset").await
}

pub fn router(app: App) -> Router {
    assert_eq!(app.edition, holepunch_server_core::edition::Edition::Cloud);
    holepunch_server_core::router_with_routes(
        app,
        Router::new()
            .route("/api/v1/admin/users/{id}/invitation", post(reinvite))
            .route("/api/v1/auth/register", post(register))
            .route("/api/v1/auth/verify", post(verify))
            .route("/api/v1/auth/resend", post(resend))
            .route("/api/v1/auth/request-reset", post(request_reset))
            .route("/api/v1/auth/reset", post(reset))
            .route("/api/v1/admin/users", get(users).post(add_user))
            .route("/api/v1/admin/users/{id}", put(update_user))
            .route("/api/v1/admin/policy", get(policy).put(update_policy)),
    )
}
