use serde::{Deserialize, Serialize};
use spacetimedb::{reducer, table, Identity, ReducerContext, Table, Timestamp, TableType};

// ========== Table Definitions ==========

#[table]
#[derive(Serialize, Deserialize)]
pub struct Workspace {
    #[primary_key]
    pub id: String,
    pub name: String,
    pub created_at: Timestamp,
    pub last_activity: Timestamp,
    pub owner: Identity,
}

#[table]
#[derive(Serialize, Deserialize)]
pub struct ResourceAllocation {
    #[primary_key]
    pub workspace_id: String,
    pub cpu_count: u8,
    pub memory_mb: u32,
    pub gpu_enabled: bool,
    pub gpu_memory_mb: Option<u32>,
    pub apple_silicon: bool,
}

#[table]
#[derive(Serialize, Deserialize)]
pub struct CodeInterpreterSession {
    #[primary_key]
    pub id: String,
    pub workspace_id: String,
    pub created_at: Timestamp,
    pub last_activity: Timestamp,
    pub total_execution_count: u32,
}

#[table]
#[derive(Serialize, Deserialize)]
pub struct CodeExecution {
    #[primary_key]
    pub id: String,
    pub session_id: String,
    pub code: String,
    pub language: String,
    pub executed_at: Timestamp,
    pub execution_time_ms: u64,
    pub result: Option<String>,
    pub error: Option<String>,
    pub cpu_usage_percent: f32,
    pub memory_usage_mb: f32,
    pub gpu_usage_percent: Option<f32>,
}

// ========== Reducers ==========

#[reducer]
pub fn create_workspace(
    ctx: ReducerContext,
    name: String,
    cpu_count: u8,
    memory_mb: u32,
    gpu_enabled: bool,
    gpu_memory_mb: Option<u32>,
    apple_silicon: bool,
) -> String {
    // Generate a new unique ID for the workspace
    let workspace_id = generate_id();

    // Insert workspace data
    Workspace::insert(&Workspace {
        id: workspace_id.clone(),
        name,
        created_at: ctx.timestamp,
        last_activity: ctx.timestamp,
        owner: ctx.sender,
    });

    // Insert resource allocation data
    ResourceAllocation::insert(&ResourceAllocation {
        workspace_id: workspace_id.clone(),
        cpu_count,
        memory_mb,
        gpu_enabled,
        gpu_memory_mb,
        apple_silicon,
    });

    // Return the workspace ID
    workspace_id
}

#[reducer]
pub fn update_workspace_activity(ctx: ReducerContext, workspace_id: String) -> bool {
    // Find the workspace
    let workspace = match Workspace::get(&workspace_id) {
        Some(w) => w,
        None => return false,
    };

    // Update the last activity timestamp
    Workspace::update(
        &workspace_id,
        &Workspace {
            id: workspace.id,
            name: workspace.name,
            created_at: workspace.created_at,
            last_activity: ctx.timestamp,
            owner: workspace.owner,
        },
    );

    true
}

#[reducer]
pub fn create_code_interpreter_session(ctx: ReducerContext, workspace_id: String) -> String {
    // Find the workspace
    if Workspace::get(&workspace_id).is_none() {
        return "error: workspace not found".to_string();
    }

    // Generate a new unique ID for the session
    let session_id = generate_id();

    // Insert session data
    CodeInterpreterSession::insert(&CodeInterpreterSession {
        id: session_id.clone(),
        workspace_id,
        created_at: ctx.timestamp,
        last_activity: ctx.timestamp,
        total_execution_count: 0,
    });

    session_id
}

#[reducer]
pub fn record_code_execution(
    ctx: ReducerContext,
    session_id: String,
    code: String,
    language: String,
    execution_time_ms: u64,
    result: Option<String>,
    error: Option<String>,
    cpu_usage_percent: f32,
    memory_usage_mb: f32,
    gpu_usage_percent: Option<f32>,
) -> String {
    // Find the session
    let session = match CodeInterpreterSession::get(&session_id) {
        Some(s) => s,
        None => return "error: session not found".to_string(),
    };

    // Generate a new unique ID for the execution record
    let execution_id = generate_id();

    // Insert execution data
    CodeExecution::insert(&CodeExecution {
        id: execution_id.clone(),
        session_id: session_id.clone(),
        code,
        language,
        executed_at: ctx.timestamp,
        execution_time_ms,
        result,
        error,
        cpu_usage_percent,
        memory_usage_mb,
        gpu_usage_percent,
    });

    // Update session data
    CodeInterpreterSession::update(
        &session_id,
        &CodeInterpreterSession {
            id: session.id,
            workspace_id: session.workspace_id,
            created_at: session.created_at,
            last_activity: ctx.timestamp,
            total_execution_count: session.total_execution_count + 1,
        },
    );

    // Update workspace activity
    update_workspace_activity(ctx, session.workspace_id);

    execution_id
}

// ========== Helper Functions ==========

fn generate_id() -> String {
    use rand::{thread_rng, Rng};
    let mut rng = thread_rng();
    let random_bytes: [u8; 16] = rng.gen();

    random_bytes
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>()
}
