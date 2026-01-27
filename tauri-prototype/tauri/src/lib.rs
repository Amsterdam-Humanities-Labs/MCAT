use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::State;

struct BackendState {
    process: Option<Child>,
    port: u16,
    backend_dir: PathBuf,
}

struct Backend(Mutex<BackendState>);

const DEFAULT_PORT: u16 = 9876;

fn find_backend_dir() -> Option<PathBuf> {
    let current_dir = std::env::current_dir().ok()?;

    let possible_paths = [
        // From monorepo root
        current_dir.join("backend"),
        // From apps/desktop
        current_dir
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.join("backend"))
            .unwrap_or_default(),
    ];

    possible_paths
        .into_iter()
        .find(|p| p.join("mcat").join("server.py").exists())
}

fn find_python(backend_dir: &PathBuf) -> String {
    let venv_python = backend_dir.join(".venv").join("bin").join("python");
    if venv_python.exists() {
        return venv_python.to_string_lossy().to_string();
    }
    "python".to_string()
}

fn read_port_file(backend_dir: &PathBuf) -> Option<u16> {
    let port_file = backend_dir.join(".port");
    std::fs::read_to_string(&port_file)
        .ok()
        .and_then(|s| s.trim().parse().ok())
}

fn spawn_python_backend(backend_dir: &PathBuf) -> Option<Child> {
    let server_path = backend_dir.join("mcat").join("server.py");
    let python = find_python(backend_dir);

    // Remove old port file
    let _ = std::fs::remove_file(backend_dir.join(".port"));

    match Command::new(&python).arg(&server_path).spawn() {
        Ok(child) => Some(child),
        Err(e) => {
            eprintln!("Failed to start Python backend: {}", e);
            None
        }
    }
}

fn wait_for_port(backend_dir: &PathBuf, timeout_ms: u64) -> u16 {
    let start = std::time::Instant::now();
    let timeout = Duration::from_millis(timeout_ms);

    while start.elapsed() < timeout {
        if let Some(port) = read_port_file(backend_dir) {
            return port;
        }
        std::thread::sleep(Duration::from_millis(100));
    }

    DEFAULT_PORT
}

#[tauri::command]
async fn call_backend(
    endpoint: String,
    method: Option<String>,
    body: Option<String>,
    backend: State<'_, Backend>,
) -> Result<String, String> {
    let port = backend.0.lock().unwrap().port;
    let url = format!("http://127.0.0.1:{}{}", port, endpoint);
    let client = reqwest::Client::new();

    let method = method.unwrap_or_else(|| "GET".to_string());

    let response = match method.as_str() {
        "POST" => {
            let req = client
                .post(&url)
                .header("Content-Type", "application/json");

            let req = if let Some(b) = body {
                req.body(b)
            } else {
                req.body("{}")
            };

            req.send().await
        }
        _ => client.get(&url).send().await,
    };

    let response = response.map_err(|e| format!("Request failed: {}", e))?;

    let body = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;

    Ok(body)
}

#[tauri::command]
fn get_backend_status(backend: State<Backend>) -> String {
    let guard = backend.0.lock().unwrap();
    match &guard.process {
        Some(_) => format!("running on port {}", guard.port),
        None => "not started".to_string(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let backend_dir = find_backend_dir().expect("Could not find backend directory");
    let python_process = spawn_python_backend(&backend_dir);
    let port = wait_for_port(&backend_dir, 5000);

    let backend_state = BackendState {
        process: python_process,
        port,
        backend_dir: backend_dir.clone(),
    };

    tauri::Builder::default()
        .manage(Backend(Mutex::new(backend_state)))
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![call_backend, get_backend_status])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

impl Drop for Backend {
    fn drop(&mut self) {
        let mut guard = self.0.lock().unwrap();
        if let Some(mut child) = guard.process.take() {
            let _ = child.kill();
        }
        let _ = std::fs::remove_file(guard.backend_dir.join(".port"));
    }
}
