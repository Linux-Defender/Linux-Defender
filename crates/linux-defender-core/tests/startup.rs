use linux_defender_core::common::{Context, Paths};
use linux_defender_core::dispatch;
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use uuid::Uuid;

fn test_context() -> (Context, PathBuf) {
    let root = std::env::temp_dir().join(format!("linux-defender-startup-{}", Uuid::new_v4()));
    let paths = Paths {
        home: root.join("home"),
        config_dir: root.join("config/linux-defender"),
        data_dir: root.join("data/linux-defender"),
    };
    let context = Context::with_paths(paths).expect("test context");
    (context, root)
}

#[test]
fn frontend_can_report_a_successful_mount() {
    let (context, root) = test_context();
    let result = dispatch(&context, "app.startup_ready", json!({})).expect("startup_ready");
    assert_eq!(result["ready"], true);
    assert!(dispatch(&context, "app.startup_ready", json!({"unexpected": 1})).is_err());
    let _ = fs::remove_dir_all(root);
}

#[test]
fn startup_report_does_not_expose_general_dispatch() {
    let (context, root) = test_context();
    assert!(dispatch(&context, "app.startup_ready_extra", json!({})).is_err());
    let _ = fs::remove_dir_all(root);
}

#[test]
fn debug_log_path_respects_sandbox_data_dir() {
    let (ctx, _root) = test_context();
    let path = linux_defender_core::logs::debug_log_path(&ctx);
    assert_eq!(path, ctx.paths.data_dir.join("debug/linux-defender.log"));
}
