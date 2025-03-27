use serde::{Deserialize, Serialize};
use spacetimedb::spacetimedb;

#[spacetimedb(table)]
#[derive(Serialize, Deserialize)]
pub struct User {
    #[primarykey]
    pub id: String,
    pub name: String,
    pub email: Option<String>,
    pub avatar_url: Option<String>,
    pub slack_id: String,
    pub created_at: u64,
}

#[spacetimedb(table)]
#[derive(Serialize, Deserialize)]
pub struct AuthToken {
    #[primarykey]
    pub token: String,
    pub user_id: String,
    pub created_at: u64,
    pub expires_at: u64,
}

#[spacetimedb(reducer)]
pub fn create_user(
    _ctx: spacetimedb::ReducerContext,
    name: String,
    email: Option<String>,
    avatar_url: Option<String>,
    slack_id: String,
) -> () {
    let user_id = generate_id();
    let current_time = get_current_time();

    let _ = User::insert(User {
        id: user_id,
        name,
        email,
        avatar_url,
        slack_id,
        created_at: current_time,
    });
}

#[spacetimedb(reducer)]
pub fn create_auth_token(_ctx: spacetimedb::ReducerContext, user_id: String) -> () {
    if User::filter_by_id(&user_id).is_none() {
        return;
    }

    let token = generate_id();
    let current_time = get_current_time();
    let expires_at = current_time + 30 * 24 * 60 * 60; // 30 days

    let _ = AuthToken::insert(AuthToken {
        token,
        user_id,
        created_at: current_time,
        expires_at,
    });
}

#[spacetimedb(reducer)]
pub fn verify_token(_ctx: spacetimedb::ReducerContext, _token: String) -> () {
}

fn generate_id() -> String {
    use rand::{thread_rng, Rng};
    let mut rng = thread_rng();
    let random_bytes: [u8; 16] = rng.gen();

    random_bytes
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>()
}

fn get_current_time() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
