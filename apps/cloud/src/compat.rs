#[tokio::main]
async fn main() -> anyhow::Result<()> {
    holepunch_server_core::service::run(
        holepunch_server_core::edition::Edition::Cloud,
        holepunch_cloud::router,
        "holepunch-center",
    )
    .await
}
