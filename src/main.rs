// Welcome to the imoog rust re-write
mod routes;

use axum::{
    routing::{get},
    body::Body,
    Router
};
use routes::fetch_image;
use std::net::SocketAddr;


#[tokio::main]
async fn main() {
    let app: Router<Body> = Router::new()
        .route("/", get(fetch_image));

    let addr = SocketAddr::from(([127, 0, 0, 1], 8000));
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}
