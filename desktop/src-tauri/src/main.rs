#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

#[cfg(target_os = "macos")]
#[macro_use]
extern crate objc;

mod action_logs;
mod commands;
mod community_contributions;
mod custom_protocol;
mod daemon;
mod file_exists;
mod fix_env;
mod get_env;
mod install_cli;
mod logging;
mod providers;
mod resource_watcher;
mod server;
mod settings;
mod spacetime_server;
mod system_tray;
mod ui_messages;
mod ui_ready;
mod updates;
mod util;
mod window;

use community_contributions::CommunityContributions;
use custom_protocol::CustomProtocol;
use log::{error, info};
use resource_watcher::{ProState, WorkspacesState};
use std::sync::{Arc, Mutex};
use system_tray::{SystemTray, SYSTEM_TRAY_ICON_BYTES};
use tauri::{image::Image, tray::TrayIconBuilder, Manager};
use tokio::sync::{
    mpsc::{self, Sender},
    RwLock,
};
use ui_messages::UiMessage;
use util::{kill_child_processes, QUIT_EXIT_CODE};

pub type AppHandle = tauri::AppHandle;

pub struct AppState {
    workspaces: Arc<RwLock<WorkspacesState>>,
    pro: Arc<RwLock<ProState>>,
    community_contributions: Arc<Mutex<CommunityContributions>>,
    ui_messages: Sender<UiMessage>,
    releases: Arc<Mutex<updates::Releases>>,
    pending_update: Arc<Mutex<Option<updates::Release>>>,
    #[allow(dead_code)]
    update_installed: Arc<Mutex<bool>>,
    resources_handles: Arc<Mutex<Vec<tauri::async_runtime::JoinHandle<()>>>>,
}
fn main() -> anyhow::Result<()> {
    // https://unix.stackexchange.com/questions/82620/gui-apps-dont-inherit-path-from-parent-console-apps
    fix_env::fix_env("PATH")?;

    let contributions = community_contributions::init()?;

    let ctx = tauri::generate_context!();
    let app_name = ctx.package_info().name.to_string();

    CustomProtocol::forward_deep_link();

    let (tx, rx) = mpsc::channel::<UiMessage>(10);

    let mut app_builder = tauri::Builder::default();
    // this case is handled by macos itself + tauri::RunEvent::Reopen
    #[cfg(not(target_os = "macos"))]
    {
        app_builder = app_builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let app_state = app.state::<AppState>();

            tauri::async_runtime::block_on(async move {
                if let Err(err) = app_state.ui_messages.send(UiMessage::ShowDashboard).await {
                    error!("Failed to broadcast show dashboard message: {}", err);
                };
            });
        }));
    }
    app_builder = app_builder
        .manage(AppState {
            workspaces: Arc::new(RwLock::new(WorkspacesState::default())),
            pro: Arc::new(RwLock::new(ProState::default())),
            community_contributions: Arc::new(Mutex::new(contributions)),
            ui_messages: tx.clone(),
            releases: Arc::new(Mutex::new(updates::Releases::default())),
            pending_update: Arc::new(Mutex::new(None)),
            update_installed: Arc::new(Mutex::new(false)),
            resources_handles: Arc::new(Mutex::new(vec![])),
        })
        .plugin(logging::build_plugin())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(move |app| {
            info!("Setup application");

            providers::check_dangling_provider(&app.handle());
            let window_helper = window::WindowHelper::new(app.handle().clone());

            let window = app.get_webview_window("main").unwrap();
            window_helper.setup(&window);

            let app_handle = app.handle().clone();
            resource_watcher::setup(&app_handle);

            action_logs::setup(&app.handle())?;

            let custom_protocol = CustomProtocol::init();
            custom_protocol.setup(app.handle().clone());

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let update_helper = updates::UpdateHelper::new(&app_handle);
                if let Ok(releases) = update_helper.fetch_releases().await {
                    let state = app_handle.state::<AppState>();
                    let mut releases_state = state.releases.lock().unwrap();
                    *releases_state = releases;
                }

                update_helper.poll().await;
            });

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(err) = server::setup(&app_handle).await {
                    error!("Failed to start server: {}", err);
                }
            });

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(err) = spacetime_server::setup(&app_handle).await {
                    error!("Failed to start SpacetimeDB server: {}", err);
                }
            });

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                ui_messages::UiMessageHelper::new(app_handle, app_name, window_helper)
                    .listen(rx)
                    .await;
            });

            let system_tray = SystemTray::new();
            let app_handle = app.handle().clone();
            tauri::async_runtime::block_on(async move {
                if let Ok(menu) = system_tray.init(&app_handle).await {
                    let _tray = TrayIconBuilder::with_id("main")
                        .icon(Image::new(SYSTEM_TRAY_ICON_BYTES, 16, 16),)
                        .icon_as_template(true)
                        .menu(&menu)
                        .show_menu_on_left_click(true)
                        .on_menu_event(system_tray.get_menu_event_handler())
                        .on_tray_icon_event(system_tray.get_tray_icon_event_handler())
                        .build(&app_handle);
                }
            });

            info!("Setup done");
            Ok(())
        });

    app_builder = app_builder.invoke_handler(tauri::generate_handler![
        ui_ready::ui_ready,
        action_logs::write_action_log,
        action_logs::get_action_logs,
        action_logs::get_action_log_file,
        install_cli::install_cli,
        get_env::get_env,
        file_exists::file_exists,
        community_contributions::get_contributions,
        updates::get_pending_update,
        updates::check_updates
    ]);

    let app = app_builder
        .build(ctx)
        .expect("error while building tauri application");

    app.run(move |app_handle, event| {
        let exit_requested_tx = tx.clone();
        #[cfg(target_os = "macos")]
        let reopen_tx = tx.clone();

        #[cfg(target_os = "macos")]
        {
            if let tauri::RunEvent::Reopen { .. } = event {
                tauri::async_runtime::block_on(async move {
                    if let Err(err) = reopen_tx.send(UiMessage::ShowDashboard).await {
                        error!("Failed to broadcast show dashboard message: {}", err);
                    };
                });

                return;
            }
        }

        match event {
            // Prevents app from exiting when last window is closed, leaving the system tray active
            tauri::RunEvent::ExitRequested { api, code, .. } => {
                info!("Handling ExitRequested event.");

                // On windows, we want to kill all existing child processes to prevent dangling processes later down the line.

                tauri::async_runtime::block_on(async move {
                    if let Err(err) = exit_requested_tx.send(UiMessage::ExitRequested).await {
                        error!("Failed to broadcast UI ready message: {:?}", err);
                    }
                });

                // Check if the user clicked "Quit" in the system tray, in which case we have to actually close.
                if let Some(code) = code {
                    if code == QUIT_EXIT_CODE {
                        return;
                    }
                }

                // Otherwise, we stay alive in the system tray.
                api.prevent_exit();
            }
            tauri::RunEvent::WindowEvent { event, label: _, .. } => {
                if let tauri::WindowEvent::Destroyed = event {
                    providers::check_dangling_provider(app_handle);
                    #[cfg(target_os = "macos")]
                    {
                        let window_helper = window::WindowHelper::new(app_handle.clone());
                        let window_count = app_handle.windows().len();
                        info!("Window destroyed, {} remaining", window_count);
                        if window_count == 0 {
                            window_helper.set_dock_icon_visibility(false);
                        }
                    }
                }
            }
            tauri::RunEvent::Exit => {
                kill_child_processes(std::process::id());
                providers::check_dangling_provider(app_handle);
                tauri::async_runtime::block_on(async move {
                    resource_watcher::shutdown(app_handle).await;
                });
            }
            _ => {}
        }
    });

    Ok(())
}
