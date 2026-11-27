mod accent_color;
mod clipboard;
mod model;
mod notifications;
mod policy;
mod runtime;
mod scan_progress;
mod startup_trace;
mod tray;

use linux_defender_core::common::path_to_wire;
use std::{
    env,
    ffi::OsString,
    path::{Path, PathBuf},
};

const NORMALIZED_GUI_ARGS: &str = "LINUX_DEFENDER_NORMALIZED_GUI_ARGS";

/// Helper entry points this executable answers to. The pre-rename names stay
/// accepted so a symlink installed by an earlier release keeps working.
const HELPER_NAMES: [&str; 2] = [
    "linux-defender-apply-preferences",
    "clamui-apply-preferences",
];
const SCHEDULER_NAMES: [&str; 2] = ["linux-defender-scheduled-scan", "clamui-scheduled-scan"];

fn main() {
    let mut raw = env::args_os();
    let executable = PathBuf::from(
        raw.next()
            .unwrap_or_else(|| OsString::from("linux-defender")),
    );
    let raw_args: Vec<OsString> = raw.collect();
    let name = executable
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("linux-defender");

    let exit_code = if HELPER_NAMES.contains(&name) {
        unicode_args(&raw_args)
            .map(|args| linux_defender_core::privileged::run_helper(&args))
            .unwrap_or_else(report_non_unicode_cli_argument)
    } else if SCHEDULER_NAMES.contains(&name) {
        unicode_args(&raw_args)
            .map(|args| linux_defender_core::scheduler::run_scheduled(&args))
            .unwrap_or_else(report_non_unicode_cli_argument)
    } else {
        route_main(&executable, &raw_args)
    };
    if exit_code != 0 {
        std::process::exit(exit_code);
    }
}

fn route_main(executable: &Path, raw_args: &[OsString]) -> i32 {
    if let Ok(args) = unicode_args(raw_args) {
        if args
            .first()
            .is_some_and(|argument| argument == "--scheduled-scan")
        {
            return linux_defender_core::scheduler::run_scheduled(&args[1..]);
        }
        if linux_defender_core::cli::is_cli(&args) {
            return linux_defender_core::cli::run(&args);
        }
        return run_gui(args);
    }

    let Some(first) = raw_args.first().and_then(|argument| argument.to_str()) else {
        return normalize_and_reexec_gui(executable, raw_args);
    };
    if first == "--scheduled-scan" || linux_defender_core::cli::is_cli(&[first.to_owned()]) {
        return report_non_unicode_cli_argument(());
    }
    normalize_and_reexec_gui(executable, raw_args)
}

fn run_gui(args: Vec<String>) -> i32 {
    // Core reports this optional metadata in platform.system_info without
    // importing Tauri into the headless library.
    env::set_var("LINUX_DEFENDER_TAURI_VERSION", "2");
    apply_webkit_renderer_workaround();
    match runtime::run(args) {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("Linux Defender could not start: {error}");
            1
        }
    }
}

/// WebKitGTK's DMA-BUF renderer can leave a blank or non-rendering window with
/// the NVIDIA proprietary driver. Fall back to the software renderer before the
/// webview is created, matching the Flatpak runtime's existing workaround. An
/// explicit user choice in the environment always wins.
fn apply_webkit_renderer_workaround() {
    if env::var_os("WEBKIT_DISABLE_DMABUF_RENDERER").is_some() {
        return;
    }
    if nvidia_proprietary_driver_present() {
        env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }
}

fn nvidia_proprietary_driver_present() -> bool {
    Path::new("/proc/driver/nvidia/version").exists()
        || std::fs::read_to_string("/proc/modules")
            .is_ok_and(|modules| modules.lines().any(|line| line.starts_with("nvidia ")))
}

fn unicode_args(raw_args: &[OsString]) -> Result<Vec<String>, ()> {
    raw_args
        .iter()
        .map(|argument| argument.to_str().map(str::to_owned).ok_or(()))
        .collect()
}

fn report_non_unicode_cli_argument(_: ()) -> i32 {
    eprintln!("Linux Defender arguments must be valid Unicode; use the GUI file-selection route for arbitrary filesystem names.");
    2
}

#[cfg(unix)]
fn normalize_and_reexec_gui(executable: &Path, raw_args: &[OsString]) -> i32 {
    use std::os::unix::process::CommandExt;

    if env::var_os(NORMALIZED_GUI_ARGS).is_some() {
        eprintln!("Linux Defender could not normalize a non-Unicode GUI argument");
        return 2;
    }
    let cwd = match env::current_dir() {
        Ok(cwd) => cwd,
        Err(error) => {
            eprintln!("Linux Defender could not determine the current directory: {error}");
            return 1;
        }
    };
    let normalized = raw_args.iter().map(|argument| match argument.to_str() {
        Some(value) => value.to_owned(),
        None => {
            let path = PathBuf::from(argument);
            let absolute = if path.is_absolute() {
                path
            } else {
                cwd.join(path)
            };
            path_to_wire(&absolute)
        }
    });
    let error = std::process::Command::new(executable)
        .args(normalized)
        .env(NORMALIZED_GUI_ARGS, "1")
        .exec();
    eprintln!("Linux Defender could not restart with normalized GUI arguments: {error}");
    1
}

#[cfg(not(unix))]
fn normalize_and_reexec_gui(_executable: &Path, _raw_args: &[OsString]) -> i32 {
    eprintln!("Linux Defender cannot preserve a non-Unicode GUI argument on this platform");
    2
}
