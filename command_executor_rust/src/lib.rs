use pyo3::prelude::*;
use std::collections::HashMap;
use std::process::Stdio; // For TokioCommand setup
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::process::{Child, Command as TokioCommand}; // Ensure Child is imported
use log::{info, warn, error};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CommandExecutorError {
    #[error("Failed to parse command: {0}")]
    ParseError(String),

    #[error("Failed to spawn command '{command}': {source}")]
    SpawnError {
        command: String,
        #[source]
        source: std::io::Error,
    },

    #[error("Command '{command}' timed out after {duration_secs} seconds")]
    TimeoutError {
        command: String,
        duration_secs: u64,
    },

    #[error("I/O error during command execution: {source}")]
    IoError {
        #[from] // Automatically convert std::io::Error
        source: std::io::Error,
    },

    #[error("Task join error during command execution: {source}")]
    JoinError {
        #[from] // Automatically convert tokio::task::JoinError
        source: tokio::task::JoinError,
    },
    
    #[error("Failed to write to stdin: {0}")]
    StdinWriteError(String),

    #[error("Empty command string provided")]
    EmptyCommandError,
}

impl From<CommandExecutorError> for PyErr {
    fn from(err: CommandExecutorError) -> PyErr {
        match err {
            CommandExecutorError::ParseError(_) | CommandExecutorError::EmptyCommandError => {
                pyo3::exceptions::PyValueError::new_err(err.to_string())
            }
            CommandExecutorError::SpawnError { .. } => {
                pyo3::exceptions::PyOSError::new_err(err.to_string())
            }
            CommandExecutorError::TimeoutError { .. } => {
                pyo3::exceptions::PyTimeoutError::new_err(err.to_string())
            }
            CommandExecutorError::IoError { .. } | CommandExecutorError::StdinWriteError(_) => {
                pyo3::exceptions::PyIOError::new_err(err.to_string())
            }
            CommandExecutorError::JoinError { .. } => {
                pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
            }
        }
    }
}


#[pyclass]
#[derive(Debug, Clone)]
struct CommandOutput {
    #[pyo3(get)]
    stdout: String,
    #[pyo3(get)]
    stderr: String,
    #[pyo3(get)]
    exit_code: Option<i32>,
}

// Helper async function to manage the actual execution and I/O
async fn run_and_capture_output(
    mut child: Child, // Takes ownership of the child process
    stdin_str: Option<String>,
) -> Result<CommandOutput, CommandExecutorError> {
    let child_stdin_opt = child.stdin.take();
    let child_stdout_opt = child.stdout.take();
    let child_stderr_opt = child.stderr.take();

    // Spawn a task to write to stdin if data is provided
    let stdin_writer_task = tokio::spawn(async move {
        if let (Some(mut child_stdin), Some(data)) = (child_stdin_opt, stdin_str) {
            child_stdin.write_all(data.as_bytes()).await
                .map_err(|e| CommandExecutorError::StdinWriteError(format!("Failed to write to child stdin: {}", e)))?;
            child_stdin.shutdown().await
                .map_err(|e| CommandExecutorError::StdinWriteError(format!("Error shutting down child stdin: {}", e)))?;
        }
        Ok::<(), CommandExecutorError>(())
    });

    // Spawn tasks to read stdout and stderr concurrently
    let stdout_reader_task = tokio::spawn(async move {
        let mut buffer = Vec::new();
        if let Some(mut child_stdout) = child_stdout_opt {
            child_stdout.read_to_end(&mut buffer).await?;
        }
        Ok::<_, std::io::Error>(buffer)
    });

    let stderr_reader_task = tokio::spawn(async move {
        let mut buffer = Vec::new();
        if let Some(mut child_stderr) = child_stderr_opt {
            child_stderr.read_to_end(&mut buffer).await?;
        }
        Ok::<_, std::io::Error>(buffer)
    });

    // Wait for all I/O tasks and the child process to complete
    let (stdin_result, stdout_result, stderr_result, status_result) = tokio::join!(
        stdin_writer_task,
        stdout_reader_task,
        stderr_reader_task,
        child.wait() // Wait for the child process to exit
    );

    // Process results from tokio::join, handling potential errors
    // Outer `?` for JoinError, inner `?` for task-specific error (CommandExecutorError or std::io::Error)
    stdin_result??; // Result<Result<(), CommandExecutorError>, JoinError>

    let stdout_buf = stdout_result??; // Result<Result<Vec<u8>, std::io::Error>, JoinError>
    let stderr_buf = stderr_result??; // Result<Result<Vec<u8>, std::io::Error>, JoinError>
    let status = status_result?;      // Result<std::process::ExitStatus, std::io::Error>

    let stdout = String::from_utf8_lossy(&stdout_buf).into_owned();
    let stderr = String::from_utf8_lossy(&stderr_buf).into_owned();
    let exit_code = status.code();

    Ok(CommandOutput {
        stdout,
        stderr,
        exit_code,
    })
}


#[pyfunction]
fn execute_command_rust_async<'a>(
    py: Python<'a>,
    command_str: String,
    cwd: Option<String>,
    env_vars: Option<HashMap<String, String>>,
    timeout_seconds: Option<u64>,
    stdin_str: Option<String>,
) -> PyResult<Bound<'a, PyAny>> {
    pyo3_async_runtimes::tokio::future_into_py(py, async move {
        let result: Result<CommandOutput, CommandExecutorError> = async {
            let original_command_str = command_str.clone(); // For error reporting
            let parts = shlex::split(&command_str)
                .ok_or_else(|| CommandExecutorError::ParseError(original_command_str.clone()))?;

            if parts.is_empty() {
                return Err(CommandExecutorError::EmptyCommandError);
            }

        let mut cmd_builder = TokioCommand::new(&parts[0]);
        if parts.len() > 1 {
            cmd_builder.args(&parts[1..]);
        }
        if let Some(current_dir) = cwd {
            cmd_builder.current_dir(current_dir);
        }
        if let Some(env_map) = env_vars {
            cmd_builder.envs(env_map);
        }

        cmd_builder.stdin(Stdio::piped());
        cmd_builder.stdout(Stdio::piped());
        cmd_builder.stderr(Stdio::piped());

        let child = match cmd_builder.spawn() {
            Ok(child_process) => child_process,
            Err(e) => {
                return Err(CommandExecutorError::SpawnError {
                    command: parts[0].to_string(),
                    source: e,
                });
            }
        };

        let child_pid_str = child.id().map(|id| id.to_string()).unwrap_or_else(|| "unknown".to_string());
        info!("Spawned child process (PID: {}) for command: {}", child_pid_str, command_str);

        if let Some(secs) = timeout_seconds {
            let timeout_duration = std::time::Duration::from_secs(secs);
            tokio::select! {
                biased;
                _ = tokio::time::sleep(timeout_duration) => {
                    warn!("Command (PID: {}) timed out after {}s.", child_pid_str, secs);
                    Err(CommandExecutorError::TimeoutError {
                        command: original_command_str, // Use the cloned original command string
                        duration_secs: secs,
                    })
                }
                res = run_and_capture_output(child, stdin_str.clone()) => {
                    info!("Command (PID: {}) finished before timeout.", child_pid_str);
                    res // This is Result<CommandOutput, CommandExecutorError>
                }
            }
        } else {
            info!("Command (PID: {}) running without timeout.", child_pid_str);
            run_and_capture_output(child, stdin_str.clone()).await
        }
    }.await; // End of inner async block
    result.map_err(|e| e.into()) // Convert CommandExecutorError to PyErr
    })
}

#[pymodule]
fn agent_lifecycle_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();
    m.add_function(pyo3::wrap_pyfunction!(execute_command_rust_async, m)?)?;
    m.add_class::<CommandOutput>()?;
    Ok(())
}
