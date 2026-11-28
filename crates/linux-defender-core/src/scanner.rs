use crate::common::{host_command, path_to_wire, Context, Job};
#[cfg(test)]
use crate::scan_parser::interpret_daemon;
use crate::scan_parser::{detection, wire_path, BackendEvidence, StreamEvidence};
use crate::AppResult;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, HashMap, HashSet};
#[cfg(test)]
use std::ffi::OsStr;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, Read, Write};
use std::os::unix::ffi::{OsStrExt, OsStringExt};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver};
use std::sync::{LazyLock, Mutex};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const OUTPUT_LIMIT: usize = 64 * 1024 * 1024;
/// User-supplied rules are bounded so a local directory cannot turn a scan
/// into an unbounded command line or a huge clamscan database load.
const MAX_LOCAL_YARA_FILES: usize = 1000;
const MAX_LOCAL_YARA_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_LOCAL_YARA_TOTAL_BYTES: u64 = 64 * 1024 * 1024;
const EICAR: &[u8] = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*";
static REQUEST_SEQUENCE: AtomicU64 = AtomicU64::new(0);

struct DaemonAvailability {
    checked_at: Instant,
    config_path: Option<String>,
    available: bool,
}

static DAEMON_AVAILABILITY: LazyLock<Mutex<Option<DaemonAvailability>>> =
    LazyLock::new(|| Mutex::new(None));

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ScanStatus {
    Clean,
    Infected,
    Error,
    Cancelled,
}

impl ScanStatus {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Clean => "clean",
            Self::Infected => "infected",
            Self::Error => "error",
            Self::Cancelled => "cancelled",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThreatDetail {
    pub file_path: String,
    pub threat_name: String,
    pub category: String,
    pub severity: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ScanProgress {
    pub current_file: String,
    pub files_scanned: u64,
    pub files_total: Option<u64>,
    /// Compatibility alias for consumers that adopted the UI wording.
    pub total_files: Option<u64>,
    pub infected_count: u64,
    pub new_threats: Vec<ThreatDetail>,
    pub bytes_scanned: u64,
    pub estimate_exceeded: bool,
    pub percentage: Option<f64>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ScanResult {
    pub status: ScanStatus,
    pub path: String,
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
    pub infected_files: Vec<String>,
    pub scanned_files: u64,
    pub scanned_dirs: u64,
    pub infected_count: u64,
    pub error_message: Option<String>,
    pub threat_details: Vec<ThreatDetail>,
    pub skipped_files: Vec<String>,
    pub skipped_count: u64,
    pub warning_message: Option<String>,
    pub nonfatal_warnings: Vec<String>,
    pub backend: String,
}

impl ScanResult {
    fn error(path: impl Into<String>, message: impl Into<String>, backend: &str) -> Self {
        let message = message.into();
        Self {
            status: ScanStatus::Error,
            path: path.into(),
            stdout: String::new(),
            stderr: message.clone(),
            exit_code: -1,
            infected_files: Vec::new(),
            scanned_files: 0,
            scanned_dirs: 0,
            infected_count: 0,
            error_message: Some(message),
            threat_details: Vec::new(),
            skipped_files: Vec::new(),
            skipped_count: 0,
            warning_message: None,
            nonfatal_warnings: Vec::new(),
            backend: backend.into(),
        }
    }

    fn cancelled(path: impl Into<String>, backend: &str) -> Self {
        Self {
            status: ScanStatus::Cancelled,
            path: path.into(),
            stdout: String::new(),
            stderr: String::new(),
            exit_code: -1,
            infected_files: Vec::new(),
            scanned_files: 0,
            scanned_dirs: 0,
            infected_count: 0,
            error_message: Some("Scan cancelled by user".into()),
            threat_details: Vec::new(),
            skipped_files: Vec::new(),
            skipped_count: 0,
            warning_message: None,
            nonfatal_warnings: Vec::new(),
            backend: backend.into(),
        }
    }
}

#[derive(Deserialize)]
struct ScanRequest {
    id: Option<String>,
    paths: Vec<String>,
    #[serde(default = "default_recursive")]
    recursive: bool,
    profile_id: Option<String>,
    profile_name: Option<String>,
    backend_override: Option<String>,
    #[serde(default)]
    force_stream: bool,
    exclusions: Option<Value>,
    #[serde(default)]
    scheduled: bool,
}

fn default_recursive() -> bool {
    true
}

#[derive(Default)]
struct Exclusions {
    directories: Vec<String>,
    patterns: Vec<String>,
    yara_rules: Vec<PathBuf>,
}

#[derive(Default)]
struct ScanOptions {
    limits: BTreeMap<&'static str, String>,
    pua: Option<bool>,
    alert_broken: Option<bool>,
    alert_macros: Option<bool>,
    heuristic_alerts: Option<bool>,
    follow_directory_symlinks: Option<bool>,
    follow_file_symlinks: Option<bool>,
    recursive: Option<bool>,
    exclude_hidden: bool,
}

struct ScanExecution<'a> {
    recursive: bool,
    backend: &'a str,
    force_stream: bool,
    exclusions: &'a Exclusions,
    options: &'a ScanOptions,
    database_directory: Option<&'a str>,
}

impl ScanOptions {
    fn requires_standalone(&self) -> bool {
        !self.limits.is_empty()
            || self.pua.is_some()
            || self.alert_broken.is_some()
            || self.alert_macros.is_some()
            || self.heuristic_alerts.is_some()
            || self.follow_directory_symlinks.is_some()
            || self.follow_file_symlinks.is_some()
            || self.recursive.is_some()
            || self.exclude_hidden
    }
}

#[derive(Default)]
struct TargetCount {
    files: u64,
    directories: u64,
    file_paths: Vec<PathBuf>,
    /// Files on FUSE mounts, which clamd cannot inspect through a passed
    /// descriptor; they are scanned in a separate `--stream` phase.
    stream_paths: Vec<PathBuf>,
    fuse: FuseDetector,
}

const FUSE_SUPER_MAGIC: u64 = 0x6573_5546;

fn is_fuse_magic(f_type: u64) -> bool {
    f_type == FUSE_SUPER_MAGIC
}

/// `statfs` probe for a single path. Filesystems are remembered per `st_dev`
/// by `FuseDetector` so large trees cost one probe per mount.
fn statfs_is_fuse(path: &Path) -> bool {
    let Ok(c_path) = std::ffi::CString::new(path.as_os_str().as_bytes()) else {
        return false;
    };
    let mut buffer = std::mem::MaybeUninit::<libc::statfs>::zeroed();
    // SAFETY: c_path is NUL-terminated and buffer is writable; it is read only
    // after the call reports success.
    if unsafe { libc::statfs(c_path.as_ptr(), buffer.as_mut_ptr()) } != 0 {
        return false;
    }
    // SAFETY: statfs returned 0, so the buffer is initialised.
    let buffer = unsafe { buffer.assume_init() };
    #[allow(clippy::unnecessary_cast, clippy::cast_sign_loss)]
    let f_type = buffer.f_type as u64;
    is_fuse_magic(f_type)
}

#[derive(Default)]
struct FuseDetector {
    devices: HashMap<u64, bool>,
    /// Injected probe for tests; no real FUSE mount is needed.
    probe: Option<fn(&Path) -> bool>,
}

impl FuseDetector {
    fn is_fuse(&mut self, path: &Path) -> bool {
        let Ok(metadata) = fs::metadata(path) else {
            return false;
        };
        let probe = self.probe.unwrap_or(statfs_is_fuse);
        *self
            .devices
            .entry(metadata.dev())
            .or_insert_with(|| probe(path))
    }
}

#[derive(Clone, Copy)]
enum TraversalMode {
    CountOnly,
    CollectPaths,
}

struct CapturedOutput {
    stdout_bytes: Vec<u8>,
    stdout_truncated: bool,
    stderr: String,
    exit_code: i32,
    cancelled: bool,
    evidence: StreamEvidence,
}

struct DaemonPhase<'a> {
    arguments: &'a [String],
    stdin: Option<File>,
    files: u64,
    directories: u64,
    stdin_path: Option<&'a str>,
}

struct DaemonPhaseEvidence<'a> {
    output: CapturedOutput,
    files: u64,
    directories: u64,
    stdin_path: Option<&'a str>,
    scanned_files: u64,
}

struct DaemonResultAccumulator {
    result: ScanResult,
    saw_infected: bool,
    saw_error: bool,
    saw_cancelled: bool,
    saw_incomplete_warning: bool,
    failure_exit_code: Option<i32>,
}

impl DaemonResultAccumulator {
    fn new(raw_path: &str) -> Self {
        Self {
            result: ScanResult {
                status: ScanStatus::Clean,
                path: raw_path.into(),
                stdout: String::new(),
                stderr: String::new(),
                exit_code: 0,
                infected_files: Vec::new(),
                scanned_files: 0,
                scanned_dirs: 0,
                infected_count: 0,
                error_message: None,
                threat_details: Vec::new(),
                skipped_files: Vec::new(),
                skipped_count: 0,
                warning_message: None,
                nonfatal_warnings: Vec::new(),
                backend: "daemon".into(),
            },
            saw_infected: false,
            saw_error: false,
            saw_cancelled: false,
            saw_incomplete_warning: false,
            failure_exit_code: None,
        }
    }

    fn add(&mut self, phase: ScanResult) {
        append_bounded_text(&mut self.result.stdout, &phase.stdout);
        append_bounded_text(&mut self.result.stderr, &phase.stderr);
        if phase.status == ScanStatus::Error && phase.exit_code != 0 {
            self.failure_exit_code.get_or_insert(phase.exit_code);
        } else if self.result.exit_code == 0 && phase.exit_code != 0 {
            self.result.exit_code = phase.exit_code;
        }
        self.result.scanned_files += phase.scanned_files;
        self.result.scanned_dirs += phase.scanned_dirs;
        self.result.infected_count += phase.infected_count;
        self.saw_infected |= phase.status == ScanStatus::Infected;
        self.saw_error |= phase.status == ScanStatus::Error;
        self.saw_cancelled |= phase.status == ScanStatus::Cancelled;
        if let Some(error) = phase.error_message {
            match &mut self.result.error_message {
                Some(current) => append_bounded_text(current, &error),
                None => self.result.error_message = Some(error),
            }
        }
        if !self.saw_incomplete_warning
            && phase.status == ScanStatus::Infected
            && phase.threat_details.is_empty()
            && phase.warning_message.is_some()
        {
            self.result.warning_message = phase.warning_message;
            self.saw_incomplete_warning = true;
        } else if self.result.warning_message.is_none() {
            self.result.warning_message = phase.warning_message;
        }
        self.result
            .nonfatal_warnings
            .extend(phase.nonfatal_warnings);
        self.result.threat_details.extend(phase.threat_details);
        self.result.skipped_files.extend(phase.skipped_files);
    }

    fn finish(mut self) -> ScanResult {
        self.result.infected_files = self
            .result
            .threat_details
            .iter()
            .map(|threat| threat.file_path.clone())
            .collect();
        self.result.skipped_count = self.result.skipped_files.len() as u64;
        self.result.status = if self.saw_cancelled {
            ScanStatus::Cancelled
        } else if self.saw_infected {
            ScanStatus::Infected
        } else if self.saw_error {
            ScanStatus::Error
        } else {
            ScanStatus::Clean
        };
        if let Some(exit_code) = self.failure_exit_code {
            self.result.exit_code = exit_code;
        }
        if self.saw_cancelled {
            self.result.exit_code = -1;
            self.result.error_message = Some("Scan cancelled by user".into());
        }
        self.result
    }
}

struct CapturedStream {
    bytes: Vec<u8>,
    truncated: bool,
    evidence: StreamEvidence,
}
#[derive(Default)]
struct ProgressState {
    files_scanned: u64,
    infected_paths: HashSet<String>,
    infected_count: u64,
}

pub fn dispatch(ctx: &Context, action: &str, args: Value) -> AppResult<Value> {
    match action {
        "status" => status(ctx),
        "scan" => scan(
            ctx,
            serde_json::from_value(args)
                .map_err(|error| format!("Invalid scanner.scan arguments: {error}"))?,
        ),
        "cancel" => {
            let id = args
                .get("id")
                .and_then(Value::as_str)
                .ok_or_else(|| "scanner.cancel requires id".to_owned())?;
            if id.is_empty()
                || id.len() > 128
                || !id
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_' || byte == b'-')
            {
                return Err("scanner.cancel has an invalid operation id".to_owned());
            }
            Ok(json!({"id": id, "cancelled": ctx.cancel(id)}))
        }
        "eicar" => eicar(ctx, args),
        _ => Err(format!("Unknown scanner action: {action}")),
    }
}

fn status(ctx: &Context) -> AppResult<Value> {
    let configured_backend = ctx
        .settings()?
        .get("scan_backend")
        .and_then(Value::as_str)
        .unwrap_or("auto")
        .to_owned();
    let clamscan = probe_program("clamscan", &["--version"]);
    let (user_yara_rules, yara_error) = match yara_database_paths(ctx) {
        Ok(rules) => (rules, None),
        Err(error) => (Vec::new(), Some(error)),
    };
    let default_yara = provision_default_yara(ctx);
    let mut all_yara_rules = user_yara_rules.clone();
    for path in default_yara {
        if !all_yara_rules.contains(&path) {
            all_yara_rules.push(path);
        }
    }
    let yara_rules = user_yara_rules;
    let clamdscan = probe_program("clamdscan", &["--version"]);
    let daemon_ping = if clamdscan.available {
        probe_clamd(ctx, &["--ping", "1"])
    } else {
        ProgramProbe::unavailable(
            clamdscan
                .error
                .clone()
                .unwrap_or_else(|| "clamdscan unavailable".into()),
        )
    };
    let daemon_available = clamdscan.available && daemon_ping.available;
    let (backend, available, error) = match configured_backend.as_str() {
        "clamscan" => ("clamscan", clamscan.available, clamscan.error.clone()),
        "daemon" => (
            if daemon_available {
                "daemon"
            } else {
                "unavailable"
            },
            daemon_available,
            if daemon_available {
                None
            } else {
                daemon_ping.error.clone().or(clamdscan.error.clone())
            },
        ),
        "auto" if !yara_rules.is_empty() => {
            ("clamscan", clamscan.available, clamscan.error.clone())
        }
        _ => {
            if daemon_available {
                ("daemon", true, None)
            } else {
                ("clamscan", clamscan.available, clamscan.error.clone())
            }
        }
    };
    let database = database_status(ctx);
    let local_database_available = database
        .get("available")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let database_available = if backend == "daemon" {
        daemon_available
    } else {
        local_database_available
    };
    let database_error = (!database_available).then(|| {
        crate::i18n::translate(
            ctx,
            "No ClamAV database files were found in standard host locations",
        )
    });
    Ok(json!({
        "available": available,
        "version": if backend == "daemon" { clamdscan.version.clone() } else { clamscan.version.clone() },
        "error": error,
        "backend": backend,
        "active_backend": backend,
        "configured_backend": configured_backend,
        "database_available": database_available,
        "database_error": database_error,
        "local_yara_rule_count": all_yara_rules.len(),
        "local_yara_error": yara_error,
        "daemon_status": {
            "available": daemon_available,
            "connected": daemon_ping.available,
            "clamdscan_available": clamdscan.available,
            "version": clamdscan.version.clone(),
            "message": daemon_ping.error.clone().or(clamdscan.error.clone()),
        },
        "clamscan": {"available": clamscan.available, "version": clamscan.version.clone(), "error": clamscan.error.clone()},
        "database": database,
    }))
}

fn scan(ctx: &Context, request: ScanRequest) -> AppResult<Value> {
    if request.paths.is_empty() {
        return Err("scanner.scan requires at least one path".into());
    }
    let (mut exclusions, options) = merged_scan_plan(ctx, &request)?;
    exclusions.yara_rules = yara_database_paths(ctx)?;
    let database_directory = clamscan_database_directory(ctx);
    if !exclusions.yara_rules.is_empty() && database_directory.is_none() {
        return Err(
            "Local YARA rules require a readable ClamAV signature database directory; refusing a YARA-only scan".to_owned()
        );
    }
    let id = request.id.unwrap_or_else(new_scan_id);
    if id.is_empty()
        || id.len() > 128
        || !id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_' || byte == b'-')
    {
        return Err("scanner.scan has an invalid operation id".into());
    }
    let job = ctx.job(&id)?;
    let started = Instant::now();
    let configured = request
        .backend_override
        .clone()
        .unwrap_or_else(|| configured_backend(ctx));
    if !matches!(configured.as_str(), "auto" | "daemon" | "clamscan") {
        return Err("backend_override must be auto, daemon, or clamscan".into());
    }
    let selected_backend = if configured == "auto"
        && (!exclusions.yara_rules.is_empty() || options.requires_standalone())
    {
        "clamscan".to_owned()
    } else {
        select_backend(ctx, &configured)
    };
    if selected_backend == "clamscan" {
        // One built-in, EICAR-only rule is active by default for standalone
        // scans. Daemon scans keep their original behavior.
        let default_rule = provision_default_yara(ctx);
        for path in default_rule {
            if !exclusions.yara_rules.contains(&path) {
                exclusions.yara_rules.push(path);
            }
        }
    }
    let mut results = Vec::with_capacity(request.paths.len());

    for (index, path) in request.paths.iter().enumerate() {
        if job.cancelled.load(Ordering::Acquire) {
            let mut result = ScanResult::cancelled(path, &selected_backend);
            localize_result(ctx, &mut result);
            results.push(result);
            continue;
        }
        let mut result = if selected_backend == "daemon"
            && (!exclusions.yara_rules.is_empty() || options.requires_standalone())
        {
            ScanResult::error(
                path,
                crate::i18n::translate(
                    ctx,
                    "This profile includes scan options that require standalone clamscan. Change the scan backend preference to automatic or clamscan.",
                ),
                &selected_backend,
            )
        } else {
            scan_target(
                ctx,
                &job,
                path,
                ScanExecution {
                    recursive: options.recursive.unwrap_or(request.recursive),
                    backend: &selected_backend,
                    force_stream: request.force_stream,
                    exclusions: &exclusions,
                    options: &options,
                    database_directory: database_directory.as_deref(),
                },
            )
        };
        localize_result(ctx, &mut result);
        results.push(result);
        if job.cancelled.load(Ordering::Acquire) {
            for skipped in request.paths.iter().skip(index + 1) {
                let mut result = ScanResult::cancelled(skipped, &selected_backend);
                localize_result(ctx, &mut result);
                results.push(result);
            }
            break;
        }
    }
    let aggregate = aggregate_result(&id, results, started.elapsed(), request.scheduled);
    // History persistence is best-effort: a full log directory or disk failure
    // must never erase a completed scan verdict from the caller.
    if let Err(error) = save_result(ctx, &id, &aggregate, request.scheduled) {
        let _ = crate::logs::write_debug(
            ctx,
            "WARNING",
            "scanner",
            &format!("scan result could not be saved to history: {error}"),
        );
    }
    let value = serde_json::to_value(&aggregate).map_err(|error| error.to_string())?;
    ctx.emit("scan-complete", json!({"id": id, "result": value}));
    Ok(value)
}

fn eicar(ctx: &Context, args: Value) -> AppResult<Value> {
    let id = args
        .get("id")
        .and_then(Value::as_str)
        .map(str::to_owned)
        .unwrap_or_else(new_scan_id);
    fs::create_dir_all(&ctx.paths.data_dir)
        .map_err(|error| format!("Unable to create EICAR temporary directory: {error}"))?;
    let unique = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|elapsed| elapsed.as_nanos())
        .unwrap_or(0);
    let filename = ctx.paths.data_dir.join(format!(
        ".linux-defender-eicar-{}-{}-{}",
        std::process::id(),
        unique,
        REQUEST_SEQUENCE.fetch_add(1, Ordering::Relaxed)
    ));
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .open(&filename)
        .map_err(|error| format!("Unable to create temporary EICAR file: {error}"))?;
    let scan = (|| {
        file.write_all(EICAR)
            .map_err(|error| format!("Unable to write temporary EICAR file: {error}"))?;
        file.sync_all()
            .map_err(|error| format!("Unable to sync temporary EICAR file: {error}"))?;
        drop(file);
        scan(
            ctx,
            ScanRequest {
                id: Some(id),
                paths: vec![filename.to_string_lossy().into_owned()],
                recursive: false,
                profile_id: None,
                profile_name: None,
                backend_override: args
                    .get("backend_override")
                    .and_then(Value::as_str)
                    .map(str::to_owned),
                force_stream: args
                    .get("force_stream")
                    .and_then(Value::as_bool)
                    .unwrap_or(false),
                exclusions: None,
                scheduled: false,
            },
        )
    })();
    let _ = fs::remove_file(&filename);
    scan
}

fn scan_target(
    ctx: &Context,
    job: &Job,
    raw_path: &str,
    execution: ScanExecution<'_>,
) -> ScanResult {
    let ScanExecution {
        recursive,
        backend,
        force_stream,
        exclusions,
        options,
        database_directory,
    } = execution;
    let path = match scan_path_from_wire(ctx, raw_path) {
        Ok(path) => path,
        Err(error) => return ScanResult::error(raw_path, error, backend),
    };
    if raw_path.contains('\0') || !path.exists() {
        return ScanResult::error(
            raw_path,
            "Scan target does not exist or contains an invalid NUL byte",
            backend,
        );
    }
    let traversal_mode = if backend == "daemon" {
        TraversalMode::CollectPaths
    } else {
        TraversalMode::CountOnly
    };
    let count = if backend != "daemon" && is_root_level(&path) {
        TargetCount::default()
    } else {
        match count_targets(&path, exclusions, &job.cancelled, traversal_mode) {
            Ok(count) => count,
            Err(error) => return ScanResult::error(raw_path, error, backend),
        }
    };
    if job.cancelled.load(Ordering::Acquire) {
        return ScanResult::cancelled(raw_path, backend);
    }

    if backend == "daemon" {
        if count.files == 0 {
            return ScanResult {
                status: ScanStatus::Clean,
                path: raw_path.into(),
                stdout: String::new(),
                stderr: String::new(),
                exit_code: 0,
                infected_files: Vec::new(),
                scanned_files: 0,
                scanned_dirs: count.directories,
                infected_count: 0,
                error_message: None,
                threat_details: Vec::new(),
                skipped_files: Vec::new(),
                skipped_count: 0,
                warning_message: None,
                nonfatal_warnings: Vec::new(),
                backend: backend.into(),
            };
        }
        return scan_daemon_target(ctx, job, raw_path, &count, force_stream);
    }

    let command = "clamscan".to_owned();
    let args = clamscan_arguments(
        ctx,
        &path,
        recursive,
        exclusions,
        options,
        database_directory,
    );
    let mut progress = ProgressState::default();
    let total = Some(count.files).filter(|total| *total > 0);
    let output = execute(&command, &args, None, &job.cancelled, |line| {
        update_progress(line, backend, None, &mut progress, total, |event| {
            emit_scan_progress(ctx, job, raw_path, backend, event);
        });
    });
    let output = match output {
        Ok(output) => output,
        Err(error) => return ScanResult::error(raw_path, error, backend),
    };
    finalize_clamscan(raw_path, output, progress.files_scanned)
}

fn finalize_clamscan(raw_path: &str, output: CapturedOutput, scanned_files: u64) -> ScanResult {
    let stdout = display_stdout(&output);
    let mut result = output.evidence.finish(
        BackendEvidence::Clamscan,
        raw_path,
        stdout,
        output.stderr,
        output.exit_code,
        (scanned_files, 0),
    );
    if output.cancelled {
        result.status = ScanStatus::Cancelled;
        result.error_message = Some("Scan cancelled by user".into());
    }
    result
}

/// Replace only the descriptor-passing flag. `force_stream` already emits
/// `--stream`, so this is a no-op in that mode and both flags never coexist.
fn stream_transport_arguments(arguments: &[String]) -> Vec<String> {
    let mut result = arguments.to_vec();
    if let Some(index) = result.iter().position(|argument| argument == "--fdpass") {
        result[index] = "--stream".into();
    }
    result
}

fn split_daemon_stdin_paths(paths: &[PathBuf]) -> (Vec<&PathBuf>, Vec<&PathBuf>) {
    paths.iter().partition(|path| !requires_daemon_stdin(path))
}

fn scan_daemon_target(
    ctx: &Context,
    job: &Job,
    raw_path: &str,
    count: &TargetCount,
    force_stream: bool,
) -> ScanResult {
    let base_arguments = match daemon_arguments(ctx, force_stream) {
        Ok(arguments) => arguments,
        Err(error) => return ScanResult::error(raw_path, error, "daemon"),
    };
    if job.cancelled.load(Ordering::Acquire) {
        return ScanResult::cancelled(raw_path, "daemon");
    }
    let stream_arguments = stream_transport_arguments(&base_arguments);
    let (fd_list, fd_stdin) = split_daemon_stdin_paths(&count.file_paths);
    let (stream_list, stream_stdin) = split_daemon_stdin_paths(&count.stream_paths);
    let stdin_count = (fd_stdin.len() + stream_stdin.len()) as u64;
    let safe_files = count.files.saturating_sub(stdin_count);
    let mut progress = ProgressState::default();

    if fd_stdin.is_empty() && stream_stdin.is_empty() {
        let mut accumulator = DaemonResultAccumulator::new(raw_path);
        let mut directories_left = count.directories;
        for (arguments, paths, files) in [
            (&base_arguments, &fd_list, fd_list.len() as u64),
            (&stream_arguments, &stream_list, stream_list.len() as u64),
        ] {
            if paths.is_empty() {
                continue;
            }
            let list = match write_private_file_list(ctx, paths.iter().copied()) {
                Ok(list) => list,
                Err(error) => {
                    accumulator.add(ScanResult::error(raw_path, error, "daemon"));
                    continue;
                }
            };
            let mut arguments = arguments.clone();
            arguments.extend(["--file-list".into(), list.to_string_lossy().into_owned()]);
            let phase = run_daemon_phase(
                ctx,
                job,
                raw_path,
                DaemonPhase {
                    arguments: &arguments,
                    stdin: None,
                    files,
                    directories: directories_left,
                    stdin_path: None,
                },
                count.files,
                &mut progress,
            );
            directories_left = 0;
            let _ = fs::remove_file(list);
            accumulator.add(phase);
        }
        return accumulator.finish();
    }

    let mut accumulator = DaemonResultAccumulator::new(raw_path);
    let mut stopped_for_cancellation = false;
    let mut directories_left = count.directories;
    let mut stdin_directories = if safe_files == 0 {
        count.directories
    } else {
        0
    };
    for (arguments, paths, files) in [
        (&base_arguments, &fd_list, fd_list.len() as u64),
        (&stream_arguments, &stream_list, stream_list.len() as u64),
    ] {
        if paths.is_empty() {
            continue;
        }
        if job.cancelled.load(Ordering::Acquire) {
            stopped_for_cancellation = true;
            break;
        }
        let list = match write_private_file_list(ctx, paths.iter().copied()) {
            Ok(list) => list,
            Err(error) => {
                accumulator.add(ScanResult::error(raw_path, error, "daemon"));
                continue;
            }
        };
        let mut arguments = arguments.clone();
        arguments.extend(["--file-list".into(), list.to_string_lossy().into_owned()]);
        let phase = run_daemon_phase(
            ctx,
            job,
            raw_path,
            DaemonPhase {
                arguments: &arguments,
                stdin: None,
                files,
                directories: directories_left,
                stdin_path: None,
            },
            count.files,
            &mut progress,
        );
        directories_left = 0;
        let _ = fs::remove_file(list);
        accumulator.add(phase);
    }

    for (arguments, paths) in [
        (&base_arguments, &fd_stdin),
        (&stream_arguments, &stream_stdin),
    ] {
        for path in paths {
            if job.cancelled.load(Ordering::Acquire) {
                stopped_for_cancellation = true;
                break;
            }
            let wire_path = path_to_wire(path);
            let file = match open_daemon_stdin_file(path) {
                Ok(file) => file,
                Err(error) => {
                    // One unreadable input must not poison the whole daemon
                    // verdict: clamd's own open failure is a skipped file.
                    let mut result = ScanResult {
                        status: ScanStatus::Clean,
                        path: raw_path.into(),
                        stdout: String::new(),
                        stderr: String::new(),
                        exit_code: 0,
                        infected_files: Vec::new(),
                        scanned_files: 0,
                        scanned_dirs: 0,
                        infected_count: 0,
                        error_message: None,
                        threat_details: Vec::new(),
                        skipped_files: Vec::new(),
                        skipped_count: 0,
                        warning_message: Some(format!("Skipped unreadable scan input: {error}")),
                        nonfatal_warnings: Vec::new(),
                        backend: "daemon".into(),
                    };
                    result.skipped_files.push(wire_path);
                    result.skipped_count = 1;
                    accumulator.add(result);
                    continue;
                }
            };
            let mut arguments = arguments.clone();
            arguments.push("-".into());
            let phase = run_daemon_phase(
                ctx,
                job,
                raw_path,
                DaemonPhase {
                    arguments: &arguments,
                    stdin: Some(file),
                    files: 1,
                    directories: stdin_directories,
                    stdin_path: Some(&wire_path),
                },
                count.files,
                &mut progress,
            );
            if phase.status != ScanStatus::Cancelled && phase.exit_code != -1 {
                stdin_directories = 0;
            }
            accumulator.add(phase);
            if job.cancelled.load(Ordering::Acquire) {
                stopped_for_cancellation = true;
                break;
            }
        }
        if stopped_for_cancellation {
            break;
        }
    }

    let mut result = accumulator.finish();
    if stopped_for_cancellation && result.status != ScanStatus::Cancelled {
        result.status = ScanStatus::Cancelled;
        result.exit_code = -1;
        result.error_message = Some("Scan cancelled by user".into());
    }
    result
}

fn run_daemon_phase(
    ctx: &Context,
    job: &Job,
    raw_path: &str,
    phase: DaemonPhase<'_>,
    total: u64,
    progress: &mut ProgressState,
) -> ScanResult {
    let DaemonPhase {
        arguments,
        stdin,
        files,
        directories,
        stdin_path,
    } = phase;
    let before_files = progress.files_scanned;
    let output = execute("clamdscan", arguments, stdin, &job.cancelled, |line| {
        update_progress(line, "daemon", stdin_path, progress, Some(total), |event| {
            emit_scan_progress(ctx, job, raw_path, "daemon", event)
        });
    });
    let output = match output {
        Ok(output) => output,
        Err(error) => return ScanResult::error(raw_path, error, "daemon"),
    };
    finalize_daemon_phase(
        raw_path,
        DaemonPhaseEvidence {
            output,
            files,
            directories,
            stdin_path,
            scanned_files: progress.files_scanned.saturating_sub(before_files),
        },
    )
}

fn finalize_daemon_phase(raw_path: &str, evidence: DaemonPhaseEvidence<'_>) -> ScanResult {
    let DaemonPhaseEvidence {
        output,
        files,
        directories,
        stdin_path,
        scanned_files,
    } = evidence;
    let stdout = display_stdout(&output);
    let mut evidence = output.evidence;
    evidence.attribute_anonymous_errors(stdin_path.unwrap_or(raw_path));
    let mut result = evidence.finish(
        BackendEvidence::Daemon { precounted: true },
        raw_path,
        stdout,
        output.stderr,
        output.exit_code,
        (
            if output.cancelled {
                scanned_files
            } else {
                files
            },
            if output.cancelled { 0 } else { directories },
        ),
    );
    if let Some(path) = stdin_path {
        restore_stdin_paths(&mut result, path);
    }
    if output.cancelled {
        result.status = ScanStatus::Cancelled;
        result.error_message = Some("Scan cancelled by user".into());
    }
    result
}

fn open_daemon_stdin_file(path: &Path) -> AppResult<File> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
        .map_err(|error| format!("Unable to safely open scan input: {error}"))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("Unable to inspect scan input: {error}"))?;
    if !metadata.is_file() {
        return Err("Scan input is not a regular file".into());
    }
    Ok(file)
}

fn restore_stdin_paths(result: &mut ScanResult, path: &str) {
    // clamd names the descriptor rather than the file for errors on stdin
    // paths. The evidence is attributed separately; rewrite the displayed
    // transcript as well so both surfaces name the real file.
    use crate::scan_parser::attribute_anonymous_error;
    result.stdout = result
        .stdout
        .split_inclusive('\n')
        .map(|line| attribute_anonymous_error(line.trim_end_matches('\n'), path))
        .collect::<Vec<_>>()
        .join("\n");
    for threat in &mut result.threat_details {
        threat.file_path = path.into();
    }
    result.infected_files = result
        .threat_details
        .iter()
        .map(|threat| threat.file_path.clone())
        .collect();
    for skipped in &mut result.skipped_files {
        *skipped = path.into();
    }
    result.skipped_count = result.skipped_files.len() as u64;
}

fn append_bounded_text(target: &mut String, value: &str) {
    if value.is_empty() || target.len() >= OUTPUT_LIMIT {
        return;
    }
    if !target.is_empty() {
        if target.len() + 1 >= OUTPUT_LIMIT {
            return;
        }
        target.push('\n');
    }
    let remaining = OUTPUT_LIMIT - target.len();
    if value.len() <= remaining {
        target.push_str(value);
        return;
    }
    let mut end = remaining;
    while !value.is_char_boundary(end) {
        end -= 1;
    }
    target.push_str(&value[..end]);
}

fn emit_scan_progress(
    ctx: &Context,
    job: &Job,
    raw_path: &str,
    backend: &str,
    event: ScanProgress,
) {
    let mut data = serde_json::to_value(event).unwrap_or(Value::Null);
    if let Some(object) = data.as_object_mut() {
        object.insert("id".into(), Value::String(job.id.clone()));
        object.insert("path".into(), Value::String(raw_path.into()));
        object.insert("backend".into(), Value::String(backend.into()));
    }
    ctx.emit("scan-progress", data);
}

fn configured_backend(ctx: &Context) -> String {
    ctx.settings()
        .ok()
        .and_then(|settings| {
            settings
                .get("scan_backend")
                .and_then(Value::as_str)
                .map(str::to_owned)
        })
        .unwrap_or_else(|| "auto".into())
}

fn select_backend(ctx: &Context, configured: &str) -> String {
    match configured {
        "clamscan" => "clamscan".into(),
        "daemon" => "daemon".into(),
        _ if daemon_usable(ctx) => "daemon".into(),
        _ => "clamscan".into(),
    }
}

fn clamd_config_path(ctx: &Context) -> Option<String> {
    crate::dispatch(ctx, "config.load", json!({"kind": "clamd"}))
        .ok()?
        .get("path")
        .and_then(Value::as_str)
        .filter(|path| !path.is_empty())
        .map(str::to_owned)
}

fn probe_clamd(ctx: &Context, arguments: &[&str]) -> ProgramProbe {
    let mut owned = Vec::new();
    if let Some(path) = clamd_config_path(ctx) {
        owned.extend(["--config-file".to_owned(), path]);
    }
    owned.extend(arguments.iter().map(|argument| (*argument).to_owned()));
    probe_program_owned("clamdscan", &owned)
}

fn daemon_usable(ctx: &Context) -> bool {
    let config = clamd_config_path(ctx);
    if let Ok(cache) = DAEMON_AVAILABILITY.lock() {
        if let Some(cache) = cache.as_ref() {
            if cache.config_path == config && cache.checked_at.elapsed() < Duration::from_secs(60) {
                return cache.available;
            }
        }
    }
    let available = probe_program("clamdscan", &["--version"]).available
        && probe_clamd(ctx, &["--ping", "1"]).available;
    if let Ok(mut cache) = DAEMON_AVAILABILITY.lock() {
        *cache = Some(DaemonAvailability {
            checked_at: Instant::now(),
            config_path: config,
            available,
        });
    }
    available
}

fn clamscan_arguments(
    ctx: &Context,
    path: &Path,
    recursive: bool,
    exclusions: &Exclusions,
    options: &ScanOptions,
    database_directory: Option<&str>,
) -> Vec<String> {
    let mut args = Vec::new();
    if recursive && path.is_dir() {
        args.push("-r".into());
    }
    args.push("-v".into());
    for (key, flag) in [
        ("MaxFileSize", "--max-filesize"),
        ("MaxScanSize", "--max-scansize"),
        ("MaxRecursion", "--max-recursion"),
        ("MaxFiles", "--max-files"),
    ] {
        if let Some(value) = options
            .limits
            .get(key)
            .cloned()
            .or_else(|| clamd_limit(ctx, key))
        {
            args.push(format!("{flag}={value}"));
        }
    }
    for (option, flag) in [
        (options.pua, "--detect-pua"),
        (options.alert_broken, "--alert-broken"),
        (options.alert_macros, "--alert-macros"),
    ] {
        if let Some(enabled) = option {
            args.push(format!("{flag}={}", if enabled { "yes" } else { "no" }));
        }
    }
    if let Some(enabled) = options.heuristic_alerts {
        args.push(format!(
            "--heuristic-alerts={}",
            if enabled { "yes" } else { "no" }
        ));
    }
    if let Some(enabled) = options.follow_directory_symlinks {
        args.push(format!("--follow-dir-symlinks={}", u8::from(enabled)));
    }
    if let Some(enabled) = options.follow_file_symlinks {
        args.push(format!("--follow-file-symlinks={}", u8::from(enabled)));
    }
    if options.exclude_hidden {
        args.extend(["--exclude".into(), "\\/\\.".into()]);
    }
    if let Some(directory) = database_directory {
        args.push(format!("--database={directory}"));
    }
    for directory in &exclusions.directories {
        args.extend(["--exclude-dir".into(), directory_regex(directory)]);
    }
    for pattern in &exclusions.patterns {
        args.extend(["--exclude".into(), glob_regex(pattern)]);
    }
    for rule in &exclusions.yara_rules {
        args.push(format!("--database={}", rule.display()));
    }
    args.push("--".into());
    args.push(path.to_string_lossy().into_owned());
    args
}

const DEFAULT_YARA_RULE: &str = include_str!("../assets/yara/linux-defender-default.yar");

/// Write the single built-in rule into the app data directory once. An
/// existing file is never overwritten, so a user can disable the rule by
/// replacing it with an empty file or by configuring their own folder.
fn provision_default_yara(ctx: &Context) -> Vec<PathBuf> {
    let directory = ctx.paths.data_dir.join("yara");
    let path = directory.join("linux-defender-default.yar");
    if path.exists() {
        return vec![path];
    }
    if fs::create_dir_all(&directory).is_err() {
        return Vec::new();
    }
    match crate::common::atomic_write(&path, DEFAULT_YARA_RULE.as_bytes(), 0o644) {
        Ok(()) => vec![path],
        Err(_) => Vec::new(),
    }
}

fn yara_database_paths(ctx: &Context) -> AppResult<Vec<PathBuf>> {
    let configured = ctx
        .settings()?
        .get("yara_rules_directory")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_owned();
    if configured.is_empty() {
        // No user folder: the built-in EICAR rule is added only for standalone
        // clamscan scans, never for daemon scans or backend selection.
        return Ok(Vec::new());
    }
    let directory = crate::common::expand_path(&configured);
    let metadata = fs::symlink_metadata(&directory).map_err(|error| {
        format!(
            "Unable to inspect configured local YARA rules directory {}: {error}",
            directory.display()
        )
    })?;
    if !metadata.is_dir() {
        return Err(format!(
            "Configured local YARA rules path is not a directory: {}",
            directory.display()
        ));
    }
    let entries = fs::read_dir(&directory).map_err(|error| {
        format!(
            "Unable to read configured local YARA rules directory {}: {error}",
            directory.display()
        )
    })?;
    let mut rules = Vec::new();
    let mut total_bytes = 0_u64;
    for entry in entries {
        let entry = entry.map_err(|error| error.to_string())?;
        let kind = entry.file_type().map_err(|error| error.to_string())?;
        if !kind.is_file() {
            continue;
        }
        let path = entry.path();
        // clamscan receives each rule as a UTF-8 --database argument; a
        // non-UTF-8 name would be silently corrupted by to_string_lossy.
        if path.to_str().is_none() {
            continue;
        }
        let extension = path
            .extension()
            .and_then(|extension| extension.to_str())
            .unwrap_or_default()
            .to_ascii_lowercase();
        if !matches!(extension.as_str(), "yar" | "yara") {
            continue;
        }
        if rules.len() >= MAX_LOCAL_YARA_FILES {
            return Err(format!(
                "Local YARA rules directory contains more than {MAX_LOCAL_YARA_FILES} rule files"
            ));
        }
        let size = entry.metadata().map_err(|error| error.to_string())?.len();
        if size > MAX_LOCAL_YARA_FILE_BYTES {
            return Err(format!(
                "Local YARA rule {} exceeds the {MAX_LOCAL_YARA_FILE_BYTES}-byte limit",
                path.display()
            ));
        }
        total_bytes = total_bytes.saturating_add(size);
        if total_bytes > MAX_LOCAL_YARA_TOTAL_BYTES {
            return Err(format!(
                "Local YARA rules exceed the {MAX_LOCAL_YARA_TOTAL_BYTES}-byte total limit"
            ));
        }
        rules.push(path);
    }
    rules.sort();
    Ok(rules)
}

fn daemon_arguments(ctx: &Context, force_stream: bool) -> AppResult<Vec<String>> {
    if !probe_program("clamdscan", &["--version"]).available {
        return Err("clamdscan is not installed".into());
    }
    if !probe_clamd(ctx, &["--ping", "1"]).available {
        return Err("clamd is not accessible".into());
    }
    let mut args = Vec::new();
    if let Some(path) = clamd_config_path(ctx) {
        args.extend(["--config-file".into(), path]);
    }
    if force_stream {
        args.push("--stream".into());
    } else {
        args.push("--fdpass".into());
    }
    args.push("-v".into());
    Ok(args)
}

// clamdscan's 1024-byte file-list line buffer must also hold LF and NUL.
const CLAMDSCAN_FILE_LIST_MAX_PATH_BYTES: usize = 1022;

fn requires_daemon_stdin(path: &Path) -> bool {
    let bytes = path.as_os_str().as_bytes();
    bytes.len() > CLAMDSCAN_FILE_LIST_MAX_PATH_BYTES
        || bytes.contains(&b'\n')
        || bytes.contains(&b'\r')
}

fn write_private_file_list<'a>(
    ctx: &Context,
    paths: impl IntoIterator<Item = &'a PathBuf>,
) -> AppResult<PathBuf> {
    fs::create_dir_all(&ctx.paths.data_dir)
        .map_err(|error| format!("Unable to create private scan-list directory: {error}"))?;
    let sequence = REQUEST_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let path = ctx.paths.data_dir.join(format!(
        ".linux-defender-clamdscan-{}-{sequence}.list",
        std::process::id()
    ));
    let result = (|| -> AppResult<()> {
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .mode(0o600)
            .open(&path)
            .map_err(|error| format!("Unable to create private clamd file list: {error}"))?;
        for target in paths {
            let bytes = target.as_os_str().as_bytes();
            if bytes.contains(&b'\n') || bytes.contains(&b'\r') || bytes.contains(&0) {
                return Err("Cannot scan paths containing newline, carriage return, or NUL with clamd file lists".into());
            }
            file.write_all(bytes)
                .and_then(|_| file.write_all(b"\n"))
                .map_err(|error| format!("Unable to write private clamd file list: {error}"))?;
        }
        file.sync_all()
            .map_err(|error| format!("Unable to sync private clamd file list: {error}"))
    })();
    if let Err(error) = result {
        let _ = fs::remove_file(&path);
        return Err(error);
    }
    Ok(path)
}

fn clamd_limit(ctx: &Context, key: &str) -> Option<String> {
    let loaded = crate::dispatch(ctx, "config.load", json!({"kind": "clamd"})).ok()?;
    loaded
        .get("values")?
        .get(key)?
        .as_array()?
        .first()?
        .as_str()
        .filter(|value| !value.trim().is_empty())
        .map(str::to_owned)
}

fn clamscan_database_directory(ctx: &Context) -> Option<String> {
    for kind in ["freshclam", "clamd"] {
        let config_path = crate::dispatch(ctx, "config.load", json!({"kind": kind}))
            .ok()
            .and_then(|config| {
                config
                    .get("path")
                    .and_then(Value::as_str)
                    .map(str::to_owned)
            });
        let probe = crate::host::database_available(config_path.as_deref(), true);
        if probe.available {
            return probe.path;
        }
    }
    let probe = crate::host::database_available(None, true);
    probe.available.then_some(probe.path).flatten()
}

fn merged_scan_plan(ctx: &Context, request: &ScanRequest) -> AppResult<(Exclusions, ScanOptions)> {
    let mut exclusions = Exclusions::default();
    append_exclusions(
        &mut exclusions,
        ctx.settings()?
            .get("exclusion_patterns")
            .unwrap_or(&Value::Null),
    );
    if let Some(extra) = &request.exclusions {
        append_exclusions(&mut exclusions, extra);
    }
    let mut options = ScanOptions::default();
    if request.profile_id.is_some() || request.profile_name.is_some() {
        let profiles = crate::dispatch(ctx, "profiles.list", json!({}))?;
        let records = profiles
            .as_array()
            .cloned()
            .or_else(|| profiles.get("profiles").and_then(Value::as_array).cloned())
            .unwrap_or_default();
        if let Some(profile) = records.into_iter().find(|profile| {
            request
                .profile_id
                .as_deref()
                .is_some_and(|id| profile.get("id").and_then(Value::as_str) == Some(id))
                || request
                    .profile_name
                    .as_deref()
                    .is_some_and(|name| profile.get("name").and_then(Value::as_str) == Some(name))
        }) {
            append_exclusions(
                &mut exclusions,
                profile.get("exclusions").unwrap_or(&Value::Null),
            );
            options = parse_profile_options(profile.get("options").unwrap_or(&Value::Null))?;
        } else {
            return Err("Requested scan profile was not found".into());
        }
    }
    Ok((exclusions, options))
}

fn parse_profile_options(value: &Value) -> AppResult<ScanOptions> {
    let Some(object) = value.as_object() else {
        return if value.is_null() {
            Ok(ScanOptions::default())
        } else {
            Err("Scan profile options must be a JSON object".into())
        };
    };
    if object.contains_key("SizeLimit") && object.contains_key("MaxFileSize") {
        return Err("Choose either SizeLimit or MaxFileSize in a scan profile, not both".into());
    }
    if object.contains_key("Thorough")
        && ["DetectPUA", "AlertBrokenExecutables", "AlertMacros"]
            .iter()
            .any(|key| object.contains_key(*key))
    {
        return Err(
            "Choose Thorough or its individual detection options in a scan profile, not both"
                .into(),
        );
    }
    if object.contains_key("Heuristic") && object.contains_key("HeuristicAlerts") {
        return Err(
            "Choose either Heuristic or HeuristicAlerts in a scan profile, not both".into(),
        );
    }
    let mut options = ScanOptions::default();
    for (key, value) in object {
        match key.as_str() {
            "MaxFileSize" | "MaxScanSize" | "MaxRecursion" | "MaxFiles" => {
                let raw = value
                    .as_str()
                    .map(str::to_owned)
                    .or_else(|| value.as_u64().map(|number| number.to_string()))
                    .ok_or_else(|| {
                        format!("Scan profile option {key} must be a string or unsigned integer")
                    })?;
                let parsed = raw.trim();
                let valid = if matches!(key.as_str(), "MaxFileSize" | "MaxScanSize") {
                    valid_clamav_size(parsed)
                } else {
                    parsed.parse::<u64>().is_ok_and(|number| {
                        if key == "MaxRecursion" {
                            (1..=100).contains(&number)
                        } else {
                            number <= u32::MAX as u64
                        }
                    })
                };
                if !valid {
                    return Err(format!(
                        "Invalid value for scan profile option {key}: {raw}"
                    ));
                }
                options.limits.insert(
                    match key.as_str() {
                        "MaxFileSize" => "MaxFileSize",
                        "MaxScanSize" => "MaxScanSize",
                        "MaxRecursion" => "MaxRecursion",
                        _ => "MaxFiles",
                    },
                    parsed.to_owned(),
                );
            }
            "DetectPUA"
            | "AlertBrokenExecutables"
            | "AlertMacros"
            | "Thorough"
            | "HeuristicAlerts"
            | "Heuristic"
            | "FollowDirectorySymlinks"
            | "FollowFileSymlinks"
            | "Recursive"
            | "ScanHidden" => {
                let enabled = value
                    .as_bool()
                    .ok_or_else(|| format!("Scan profile option {key} must be true or false"))?;
                match key.as_str() {
                    "DetectPUA" => options.pua = Some(enabled),
                    "AlertBrokenExecutables" => options.alert_broken = Some(enabled),
                    "AlertMacros" => options.alert_macros = Some(enabled),
                    "Thorough" => {
                        options.pua = Some(enabled);
                        options.alert_broken = Some(enabled);
                        options.alert_macros = Some(enabled);
                    }
                    "HeuristicAlerts" | "Heuristic" => options.heuristic_alerts = Some(enabled),
                    "FollowDirectorySymlinks" => options.follow_directory_symlinks = Some(enabled),
                    "FollowFileSymlinks" => options.follow_file_symlinks = Some(enabled),
                    "Recursive" => options.recursive = Some(enabled),
                    "ScanHidden" => options.exclude_hidden = !enabled,
                    _ => {}
                }
            }
            "SizeLimit" => {
                let enabled = value.as_bool().ok_or_else(|| {
                    "Scan profile option SizeLimit must be true or false".to_owned()
                })?;
                options
                    .limits
                    .insert("MaxFileSize", if enabled { "0" } else { "20M" }.into());
            }
            _ => return Err(format!("Unsupported scan profile option: {key}")),
        }
    }
    Ok(options)
}

fn valid_clamav_size(value: &str) -> bool {
    let upper = value.to_ascii_uppercase();
    let digits = if upper
        .chars()
        .last()
        .is_some_and(|suffix| matches!(suffix, 'K' | 'M' | 'G'))
    {
        &upper[..upper.len() - 1]
    } else {
        &upper
    };
    !digits.is_empty()
        && digits.bytes().all(|byte| byte.is_ascii_digit())
        && upper
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'K' | b'M' | b'G'))
}

fn append_exclusions(into: &mut Exclusions, value: &Value) {
    if let Some(records) = value.as_array() {
        for record in records {
            let enabled = record
                .get("enabled")
                .and_then(Value::as_bool)
                .unwrap_or(true);
            let pattern = record
                .get("pattern")
                .and_then(Value::as_str)
                .filter(|value| !value.is_empty());
            if !enabled {
                continue;
            }
            match (record.get("type").and_then(Value::as_str), pattern) {
                (Some("directory"), Some(pattern)) => into.directories.push(expand_home(pattern)),
                (_, Some(pattern)) => into.patterns.push(expand_home(pattern)),
                _ => {}
            }
        }
    }
    if let Some(paths) = value.get("paths").and_then(Value::as_array) {
        into.directories.extend(
            paths
                .iter()
                .filter_map(Value::as_str)
                .filter(|value| !value.is_empty())
                .map(expand_home),
        );
    }
    if let Some(patterns) = value.get("patterns").and_then(Value::as_array) {
        into.patterns.extend(
            patterns
                .iter()
                .filter_map(Value::as_str)
                .filter(|value| !value.is_empty())
                .map(expand_home),
        );
    }
}

fn count_targets(
    path: &Path,
    exclusions: &Exclusions,
    cancelled: &AtomicBool,
    mode: TraversalMode,
) -> AppResult<TargetCount> {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_default();
    if path.is_file() {
        if is_excluded(path, name, &exclusions.directories)
            || is_excluded(path, name, &exclusions.patterns)
        {
            return Ok(TargetCount::default());
        }
        let mut count = TargetCount {
            files: 1,
            ..TargetCount::default()
        };
        if matches!(mode, TraversalMode::CollectPaths) {
            if count.fuse.is_fuse(path) {
                count.stream_paths.push(path.to_path_buf());
            } else {
                count.file_paths.push(path.to_path_buf());
            }
        }
        return Ok(count);
    }
    if !path.is_dir() {
        return Err("Scan target is not a regular file or directory".into());
    }
    if is_excluded(path, name, &exclusions.directories) {
        return Ok(TargetCount::default());
    }
    let mut count = TargetCount::default();
    walk_targets(path, exclusions, cancelled, &mut count, mode, true)?;
    if count.files > 0 || count.directories > 0 {
        count.directories += 1;
    }
    Ok(count)
}

fn walk_targets(
    path: &Path,
    exclusions: &Exclusions,
    cancelled: &AtomicBool,
    count: &mut TargetCount,
    mode: TraversalMode,
    root: bool,
) -> AppResult<()> {
    if cancelled.load(Ordering::Acquire) {
        return Ok(());
    }
    let entries = match fs::read_dir(path) {
        Ok(entries) => entries,
        Err(error) if root => {
            return Err(format!(
                "Unable to enumerate scan target {}: {error}",
                path.display()
            ))
        }
        Err(_) => return Ok(()),
    };
    let on_fuse = matches!(mode, TraversalMode::CollectPaths) && count.fuse.is_fuse(path);
    for entry in entries {
        if cancelled.load(Ordering::Acquire) {
            return Ok(());
        }
        let entry = match entry {
            Ok(entry) => entry,
            Err(_) => continue,
        };
        let entry_path = entry.path();
        let name = entry.file_name().to_string_lossy().into_owned();
        let kind = match entry.file_type() {
            Ok(kind) => kind,
            Err(_) => continue,
        };
        if kind.is_dir() {
            if is_excluded(&entry_path, &name, &exclusions.directories) {
                continue;
            }
            count.directories += 1;
            let _ = walk_targets(&entry_path, exclusions, cancelled, count, mode, false);
        } else if kind.is_file() && !is_excluded(&entry_path, &name, &exclusions.patterns) {
            count.files += 1;
            if matches!(mode, TraversalMode::CollectPaths) {
                if on_fuse {
                    count.stream_paths.push(entry_path);
                } else {
                    count.file_paths.push(entry_path);
                }
            }
        }
    }
    Ok(())
}

fn is_excluded(path: &Path, name: &str, exclusions: &[String]) -> bool {
    let full = path.to_string_lossy();
    exclusions.iter().any(|pattern| {
        let expanded = expand_home(pattern);
        if expanded.starts_with('/') {
            full == expanded || full.starts_with(&(expanded.trim_end_matches('/').to_owned() + "/"))
        } else {
            glob_matches(name, &expanded) || glob_matches(&full, &expanded)
        }
    })
}

fn display_stdout(output: &CapturedOutput) -> String {
    let mut text = String::from_utf8_lossy(&output.stdout_bytes).into_owned();
    if output.stdout_truncated {
        text.push_str("\n[stdout truncated at 67108864 bytes]\n");
    }
    text
}

fn update_progress(
    raw: &[u8],
    backend: &str,
    stdin_path: Option<&str>,
    state: &mut ProgressState,
    total: Option<u64>,
    emit: impl FnOnce(ScanProgress),
) {
    let decoded = String::from_utf8_lossy(raw);
    let line = decoded.as_ref();
    let mut current = None;
    let mut threat = None;
    if backend == "daemon" {
        if let Some(path) = line
            .strip_suffix(": OK")
            .or_else(|| line.strip_suffix(": OK\r"))
        {
            current =
                Some(stdin_path.map_or_else(|| wire_path(raw, &decoded, path), str::to_owned));
        }
    } else if let Some(path) = line.strip_prefix("Scanning ") {
        current = Some(wire_path(raw, &decoded, path));
    }
    if let Some(mut detail) =
        detection(raw).filter(|_| backend == "daemon" || !line.starts_with("Scanning "))
    {
        if let Some(path) = stdin_path {
            detail.file_path = path.to_owned();
        }
        current = Some(detail.file_path.clone());
        if state.infected_paths.insert(detail.file_path.clone()) {
            state.files_scanned += 1;
        }
        state.infected_count += 1;
        threat = Some(detail);
    } else if let Some(path) = current.as_ref() {
        if state.infected_paths.insert(path.clone()) {
            state.files_scanned += 1;
        }
    } else {
        return;
    }
    let percentage = total
        .filter(|total| *total > 0)
        .map(|total| ((state.files_scanned as f64 / total as f64) * 100.0).clamp(0.0, 100.0));
    emit(ScanProgress {
        current_file: current.unwrap_or_default(),
        files_scanned: state.files_scanned,
        files_total: total,
        total_files: total,
        infected_count: state.infected_count,
        new_threats: threat.into_iter().collect(),
        bytes_scanned: 0,
        estimate_exceeded: total.is_some_and(|total| state.files_scanned > total),
        percentage,
    });
}

fn execute(
    program: &str,
    args: &[String],
    stdin: Option<File>,
    cancelled: &AtomicBool,
    mut line: impl FnMut(&[u8]),
) -> AppResult<CapturedOutput> {
    let mut command = host_command(program, args);
    command
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .process_group(0);
    if let Some(stdin) = stdin {
        command.stdin(Stdio::from(stdin));
    }
    let mut child = command
        .spawn()
        .map_err(|error| format!("Unable to start {program}: {error}"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "Unable to capture scanner stdout".to_owned())?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| "Unable to capture scanner stderr".to_owned())?;
    let (sender, receiver) = mpsc::sync_channel(128);
    let stdout_reader = spawn_reader(stdout, true, program == "clamdscan", sender.clone());
    let stderr_reader = spawn_reader(stderr, false, program == "clamdscan", sender);
    let cancelled_process = wait_with_cancel(&mut child, cancelled, &receiver, &mut line)?;
    while !stdout_reader.is_finished() || !stderr_reader.is_finished() {
        if let Ok(value) = receiver.recv_timeout(Duration::from_millis(10)) {
            line(&value);
        }
    }
    let stdout = stdout_reader
        .join()
        .map_err(|_| "Scanner stdout reader panicked".to_owned())?;
    let stderr = stderr_reader
        .join()
        .map_err(|_| "Scanner stderr reader panicked".to_owned())?;
    while let Ok(value) = receiver.try_recv() {
        line(&value);
    }
    let mut stderr_text = String::from_utf8_lossy(&stderr.bytes).into_owned();
    if stderr.truncated {
        stderr_text.push_str("\n[stderr truncated at 67108864 bytes]\n");
    }
    Ok(CapturedOutput {
        stdout_bytes: stdout.bytes,
        stdout_truncated: stdout.truncated,
        stderr: stderr_text,
        evidence: {
            let mut evidence = stdout.evidence;
            evidence.merge_stderr(stderr.evidence);
            evidence
        },
        exit_code: child
            .try_wait()
            .ok()
            .flatten()
            .and_then(|status| status.code())
            .unwrap_or(-1),
        cancelled: cancelled_process,
    })
}

fn spawn_reader<R: Read + Send + 'static>(
    reader: R,
    is_stdout: bool,
    daemon: bool,
    sender: mpsc::SyncSender<Vec<u8>>,
) -> thread::JoinHandle<CapturedStream> {
    spawn_reader_with_limit(reader, is_stdout, daemon, sender, OUTPUT_LIMIT)
}

fn spawn_reader_with_limit<R: Read + Send + 'static>(
    reader: R,
    is_stdout: bool,
    daemon: bool,
    sender: mpsc::SyncSender<Vec<u8>>,
    limit: usize,
) -> thread::JoinHandle<CapturedStream> {
    thread::spawn(move || {
        let mut reader = BufReader::new(reader);
        let mut bytes = Vec::new();
        let mut truncated = false;
        let mut buffer = [0_u8; 8192];
        let mut pending = Vec::new();
        let mut line_start = 0_usize;
        let mut evidence = StreamEvidence::new(daemon);
        loop {
            let read = match reader.read(&mut buffer) {
                Ok(0) | Err(_) => break,
                Ok(read) => read,
            };
            if bytes.len() < limit {
                let remaining = limit - bytes.len();
                let retained = read.min(remaining);
                bytes.extend_from_slice(&buffer[..retained]);
                truncated |= retained < read;
            } else {
                truncated = true;
            }
            let previous_len = pending.len();
            pending.extend_from_slice(&buffer[..read]);
            let mut start = 0;
            for (index, byte) in pending.iter().enumerate().skip(previous_len) {
                if *byte == b'\n' {
                    let raw = &pending[start..index];
                    let line_end = line_start.saturating_add(raw.len());
                    evidence.observe(raw, is_stdout, line_end <= limit);
                    line_start = line_end.saturating_add(1);
                    if is_stdout {
                        let _ = sender.send(raw.to_vec());
                    }
                    start = index + 1;
                }
            }
            pending.drain(..start);
        }
        if !pending.is_empty() {
            evidence.observe(
                &pending,
                is_stdout,
                line_start.saturating_add(pending.len()) <= limit,
            );
            if is_stdout {
                let _ = sender.send(pending);
            }
        }
        CapturedStream {
            bytes,
            truncated,
            evidence,
        }
    })
}

fn wait_with_cancel(
    child: &mut Child,
    cancelled: &AtomicBool,
    receiver: &Receiver<Vec<u8>>,
    line: &mut impl FnMut(&[u8]),
) -> AppResult<bool> {
    let mut terminated = false;
    loop {
        let mut received = false;
        for _ in 0..128 {
            match receiver.try_recv() {
                Ok(value) => {
                    received = true;
                    line(&value);
                }
                Err(_) => break,
            }
        }
        if child
            .try_wait()
            .map_err(|error| format!("Unable to wait for scanner: {error}"))?
            .is_some()
        {
            // A cancel arriving between child exit and this check must win.
            if cancelled.load(Ordering::Acquire) && !terminated {
                return Ok(true);
            }
            return Ok(terminated);
        }
        if cancelled.load(Ordering::Acquire) && !terminated {
            terminate_group(child);
            terminated = true;
        }
        if !received {
            match receiver.recv_timeout(Duration::from_millis(100)) {
                Ok(value) => line(&value),
                Err(mpsc::RecvTimeoutError::Timeout) => {}
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    thread::sleep(Duration::from_millis(100));
                }
            }
        }
    }
}

fn terminate_group(child: &mut Child) {
    #[cfg(target_family = "unix")]
    {
        let group = -(child.id() as i32);
        unsafe {
            let _ = libc::kill(group, libc::SIGTERM);
        }
        let deadline = Instant::now() + Duration::from_secs(5);
        while Instant::now() < deadline {
            // Reap the leader so its zombie cannot keep an otherwise empty group alive.
            let _ = child.try_wait();
            if !process_group_alive(group) {
                return;
            }
            thread::sleep(Duration::from_millis(25));
        }
        if process_group_alive(group) {
            unsafe {
                let _ = libc::kill(group, libc::SIGKILL);
            }
        }
    }
    #[cfg(not(target_family = "unix"))]
    {
        let _ = child.kill();
    }
}

#[cfg(target_family = "unix")]
fn process_group_alive(group: i32) -> bool {
    (unsafe { libc::kill(group, 0) == 0 })
        || std::io::Error::last_os_error().raw_os_error() == Some(libc::EPERM)
}

fn bounded_join<'a>(values: impl Iterator<Item = &'a str>) -> String {
    let mut joined = String::new();
    for value in values {
        append_bounded_text(&mut joined, value);
    }
    joined
}

fn aggregate_result(
    id: &str,
    results: Vec<ScanResult>,
    duration: Duration,
    scheduled: bool,
) -> Value {
    let status = if results
        .iter()
        .any(|result| result.status == ScanStatus::Infected)
    {
        ScanStatus::Infected
    } else if results
        .iter()
        .any(|result| result.status == ScanStatus::Error)
    {
        ScanStatus::Error
    } else if results
        .iter()
        .any(|result| result.status == ScanStatus::Cancelled)
    {
        ScanStatus::Cancelled
    } else {
        ScanStatus::Clean
    };
    let threats = results
        .iter()
        .flat_map(|result| result.threat_details.clone())
        .collect::<Vec<_>>();
    let errors = results
        .iter()
        .filter_map(|result| result.error_message.clone())
        .collect::<Vec<_>>();
    json!({
        "id": id,
        "status": status.as_str(),
        "scanned_files": results.iter().map(|result| result.scanned_files).sum::<u64>(),
        "scanned_dirs": results.iter().map(|result| result.scanned_dirs).sum::<u64>(),
        "infected_count": results.iter().map(|result| result.infected_count).sum::<u64>(),
        "threat_details": threats,
        "infected_files": results.iter().flat_map(|result| result.infected_files.clone()).collect::<Vec<_>>(),
        "stdout": bounded_join(results.iter().map(|result| result.stdout.as_str())),
        "stderr": bounded_join(results.iter().map(|result| result.stderr.as_str())),
        "error_message": errors.first(),
        "errors": errors,
        "skipped_files": results.iter().flat_map(|result| result.skipped_files.clone()).collect::<Vec<_>>(),
        "skipped_count": results.iter().map(|result| result.skipped_count).sum::<u64>(),
        "warning_message": results.iter()
            .filter(|result| result.status == ScanStatus::Infected && result.threat_details.is_empty())
            .find_map(|result| result.warning_message.as_ref())
            .or_else(|| results.iter().find_map(|result| result.warning_message.as_ref())),
        "nonfatal_warnings": results.iter().flat_map(|result| result.nonfatal_warnings.clone()).collect::<Vec<_>>(),
        "duration_seconds": duration.as_secs_f64(),
        "scheduled": scheduled,
        "per_target_results": results,
    })
}

fn save_result(ctx: &Context, id: &str, aggregate: &Value, scheduled: bool) -> AppResult<()> {
    crate::dispatch(
        ctx,
        "logs.save",
        json!({
            "type": "scan", "id": id, "status": aggregate["status"], "path": Value::Null,
            "scanned_files": aggregate["scanned_files"], "scanned_dirs": aggregate["scanned_dirs"],
            "infected_count": aggregate["infected_count"], "threat_details": aggregate["threat_details"],
            "error_message": aggregate["error_message"], "duration": aggregate["duration_seconds"],
            "scheduled": scheduled,
            "backend_suffix": aggregate["per_target_results"].as_array().and_then(|results| results.first()).and_then(|result| result.get("backend")).and_then(Value::as_str).map(|backend| format!("({backend})")),
        }),
    )?;
    Ok(())
}

#[derive(Default)]
struct ProgramProbe {
    available: bool,
    version: Option<String>,
    error: Option<String>,
}
impl ProgramProbe {
    fn unavailable(error: String) -> Self {
        Self {
            available: false,
            version: None,
            error: Some(error),
        }
    }
}
fn bounded_command_output(
    command: &mut std::process::Command,
    timeout: Duration,
) -> std::io::Result<std::process::Output> {
    command.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = command.spawn()?;
    let deadline = Instant::now() + timeout;
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    let out = stdout.map(|mut pipe| {
        std::thread::spawn(move || {
            let mut bytes = Vec::new();
            let _ = pipe.read_to_end(&mut bytes);
            bytes
        })
    });
    let err = stderr.map(|mut pipe| {
        std::thread::spawn(move || {
            let mut bytes = Vec::new();
            let _ = pipe.read_to_end(&mut bytes);
            bytes
        })
    });
    loop {
        if let Some(status) = child.try_wait()? {
            return Ok(std::process::Output {
                status,
                stdout: out.and_then(|h| h.join().ok()).unwrap_or_default(),
                stderr: err.and_then(|h| h.join().ok()).unwrap_or_default(),
            });
        }
        if Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            return Err(std::io::Error::new(
                std::io::ErrorKind::TimedOut,
                "command timed out",
            ));
        }
        std::thread::sleep(Duration::from_millis(10));
    }
}

fn probe_program(program: &str, arguments: &[&str]) -> ProgramProbe {
    let args = arguments
        .iter()
        .map(|argument| (*argument).to_owned())
        .collect::<Vec<_>>();
    probe_program_owned(program, &args)
}

fn probe_program_owned(program: &str, arguments: &[String]) -> ProgramProbe {
    // A wedged clamdscan must not freeze scanner.status or backend selection.
    let mut command = host_command(program, arguments);
    match bounded_command_output(&mut command, Duration::from_secs(10)) {
        Ok(output) if output.status.success() => ProgramProbe {
            available: true,
            version: String::from_utf8_lossy(&output.stdout)
                .lines()
                .next()
                .map(str::to_owned),
            error: None,
        },
        Ok(output) => {
            ProgramProbe::unavailable(String::from_utf8_lossy(&output.stderr).trim().to_owned())
        }
        Err(error) => ProgramProbe::unavailable(format!("{program}: {error}")),
    }
}

fn database_status(ctx: &Context) -> Value {
    let mut locations = vec!["/var/lib/clamav".to_owned(), "/var/lib/ClamAV".to_owned()];
    for kind in ["clamd", "freshclam"] {
        if let Ok(config) = crate::dispatch(ctx, "config.load", json!({"kind": kind})) {
            if let Some(directory) = config
                .get("values")
                .and_then(|values| values.get("DatabaseDirectory"))
                .and_then(Value::as_array)
                .and_then(|values| values.first())
                .and_then(Value::as_str)
                .filter(|directory| !directory.is_empty())
            {
                let directory = expand_home(directory);
                if !locations.contains(&directory) {
                    locations.push(directory);
                }
            }
        }
    }

    let mut newest = None;
    let mut selected = None;
    let mut files = 0_u64;
    for location in locations {
        let Ok(inventory) = crate::host::database_directory_inventory(&location) else {
            continue;
        };
        selected = Some(location);
        files += inventory.files;
        if let Some(modified) = inventory.latest_modified_unix {
            newest = Some(newest.map_or(modified, |current: u64| current.max(modified)));
        }
    }
    json!({"available": clamscan_database_directory(ctx).is_some(), "path": selected, "files": files, "latest_modified_unix": newest})
}

fn new_scan_id() -> String {
    let sequence = REQUEST_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let high = (nanos >> 64) as u64 ^ (std::process::id() as u64);
    let low = nanos as u64 ^ sequence;
    format!(
        "{:08x}-{:04x}-4{:03x}-a{:03x}-{:012x}",
        high as u32,
        (high >> 32) as u16,
        (low >> 48) as u16 & 0x0fff,
        (low >> 36) as u16 & 0x0fff,
        low & 0x0000_0fff_ffff_ffff
    )
}

fn is_root_level(path: &Path) -> bool {
    matches!(
        path.to_string_lossy().as_ref(),
        "/" | "/home" | "/usr" | "/var" | "/opt" | "/etc" | "/tmp" | "/root"
    )
}

fn expand_home(value: &str) -> String {
    value
        .strip_prefix("~/")
        .and_then(|tail| {
            std::env::var_os("HOME").map(|home| {
                PathBuf::from(home)
                    .join(tail)
                    .to_string_lossy()
                    .into_owned()
            })
        })
        .unwrap_or_else(|| value.to_owned())
}

fn scan_path_from_wire(ctx: &Context, wire: &str) -> AppResult<PathBuf> {
    let path = crate::common::path_from_wire(wire)?;
    let bytes = path.as_os_str().as_bytes();
    if bytes == b"~" {
        return Ok(ctx.paths.home.clone());
    }
    if let Some(rest) = bytes.strip_prefix(b"~/") {
        return Ok(ctx
            .paths
            .home
            .join(std::ffi::OsString::from_vec(rest.to_vec())));
    }
    Ok(path)
}

fn trn(ctx: &Context, singular: &str, plural: &str, count: u64) -> String {
    crate::i18n::translate_plural(ctx, singular, plural, count)
}

fn trnf(
    ctx: &Context,
    singular: &str,
    plural: &str,
    count: u64,
    replacements: &[(&str, &str)],
) -> String {
    let mut rendered = trn(ctx, singular, plural, count);
    for (placeholder, value) in replacements {
        rendered = rendered.replace(placeholder, value);
    }
    rendered
}

fn localize_result(ctx: &Context, result: &mut ScanResult) {
    if result.error_message.as_deref() == Some("Scan cancelled by user") {
        result.error_message = Some(crate::i18n::translate(ctx, "Scan cancelled by user"));
    } else if let Some(suffix) = result
        .error_message
        .as_deref()
        .and_then(|message| message.strip_prefix("No files could be scanned"))
        .filter(|suffix| suffix.is_empty() || suffix.starts_with('\n'))
    {
        let mut translated = crate::i18n::translate(ctx, "No files could be scanned");
        translated.push_str(suffix);
        result.error_message = Some(translated);
    } else if result.error_message.as_deref()
        == Some("Scan target does not exist or contains an invalid NUL byte")
    {
        result.error_message = Some(crate::i18n::translate(
            ctx,
            "Scan target does not exist or contains an invalid NUL byte",
        ));
    } else if result.error_message.as_deref()
        == Some("Scan target is not a regular file or directory")
    {
        result.error_message = Some(crate::i18n::translate(
            ctx,
            "Scan target is not a regular file or directory",
        ));
    }
    let Some(warning) = result.warning_message.as_deref() else {
        return;
    };
    if warning == "Threats were detected, but details are unavailable." {
        result.warning_message = Some(crate::i18n::translate(
            ctx,
            "Threats were detected, but details are unavailable.",
        ));
        return;
    }
    if let Some(count) = warning
        .strip_suffix(" file could not be accessed")
        .or_else(|| warning.strip_suffix(" files could not be accessed"))
        .and_then(|count| count.parse::<u64>().ok())
    {
        let rendered_count = count.to_string();
        result.warning_message = Some(trnf(
            ctx,
            "{count} file could not be accessed",
            "{count} files could not be accessed",
            count,
            &[("{count}", &rendered_count)],
        ));
    } else if let Some(count) = warning
        .strip_suffix(" file could not be read")
        .or_else(|| warning.strip_suffix(" files could not be read"))
        .and_then(|count| count.parse::<u64>().ok())
    {
        let rendered_count = count.to_string();
        result.warning_message = Some(trnf(
            ctx,
            "{count} file could not be read",
            "{count} files could not be read",
            count,
            &[("{count}", &rendered_count)],
        ));
    } else if let Some(count) = warning
        .strip_suffix(
            " non-fatal warning during scan; some files may have been only partially scanned",
        )
        .or_else(|| {
            warning.strip_suffix(
                " non-fatal warnings during scan; some files may have been only partially scanned",
            )
        })
        .and_then(|count| count.parse::<u64>().ok())
    {
        let rendered_count = count.to_string();
        result.warning_message = Some(trnf(
            ctx,
            "{count} non-fatal warning during scan; some files may have been only partially scanned",
            "{count} non-fatal warnings during scan; some files may have been only partially scanned",
            count,
            &[("{count}", &rendered_count)],
        ));
    }
}

fn glob_matches(value: &str, pattern: &str) -> bool {
    // Memoized so a pattern such as `*a*a*a*...` cannot explode exponentially
    // while exclusion rules are evaluated for every scanned path.
    fn matches(
        value: &[char],
        pattern: &[char],
        value_index: usize,
        pattern_index: usize,
        memo: &mut [Vec<Option<bool>>],
    ) -> bool {
        if let Some(cached) = memo[value_index][pattern_index] {
            return cached;
        }
        let result = if pattern_index == pattern.len() {
            value_index == value.len()
        } else {
            match pattern[pattern_index] {
                '*' => {
                    let mut next = pattern_index + 1;
                    while next < pattern.len() && pattern[next] == '*' {
                        next += 1;
                    }
                    let mut found = false;
                    for index in value_index..=value.len() {
                        if matches(value, pattern, index, next, memo) {
                            found = true;
                            break;
                        }
                    }
                    found
                }
                '?' => {
                    value_index < value.len()
                        && matches(value, pattern, value_index + 1, pattern_index + 1, memo)
                }
                '[' => match class_match(pattern, pattern_index, value.get(value_index).copied()) {
                    Some((next, true)) => matches(value, pattern, value_index + 1, next, memo),
                    Some((_, false)) => false,
                    None => {
                        value.get(value_index) == Some(&'[')
                            && matches(value, pattern, value_index + 1, pattern_index + 1, memo)
                    }
                },
                literal => {
                    value.get(value_index) == Some(&literal)
                        && matches(value, pattern, value_index + 1, pattern_index + 1, memo)
                }
            }
        };
        memo[value_index][pattern_index] = Some(result);
        result
    }

    let chars = value.chars().collect::<Vec<_>>();
    let pattern = pattern.chars().collect::<Vec<_>>();
    let mut memo = vec![vec![None; pattern.len() + 1]; chars.len() + 1];
    matches(&chars, &pattern, 0, 0, &mut memo)
}

fn class_end(pattern: &[char], open: usize) -> Option<usize> {
    let mut index = open + 1;
    if matches!(pattern.get(index), Some('!')) {
        index += 1;
    }
    if matches!(pattern.get(index), Some(']')) {
        index += 1;
    }
    while index < pattern.len() {
        if pattern[index] == ']' {
            return Some(index);
        }
        index += 1;
    }
    None
}

fn class_match(pattern: &[char], open: usize, value: Option<char>) -> Option<(usize, bool)> {
    let end = class_end(pattern, open)?;
    let value = value?;
    let mut index = open + 1;
    let negated = if pattern.get(index) == Some(&'!') {
        index += 1;
        true
    } else {
        false
    };
    let mut matched = false;
    while index < end {
        let start = pattern[index];
        if index + 2 < end && pattern[index + 1] == '-' {
            matched |= start <= value && value <= pattern[index + 2];
            index += 3;
        } else {
            matched |= start == value;
            index += 1;
        }
    }
    Some((end + 1, if negated { !matched } else { matched }))
}

fn glob_regex(pattern: &str) -> String {
    let characters = pattern.chars().collect::<Vec<_>>();
    let mut output = String::from("^");
    let mut index = 0;
    while index < characters.len() {
        match characters[index] {
            '*' => output.push_str(".*"),
            '?' => output.push('.'),
            '[' if class_end(&characters, index).is_some() => {
                let end = class_end(&characters, index).expect("checked class end");
                output.push('[');
                let mut class_index = index + 1;
                if characters.get(class_index) == Some(&'!') {
                    output.push('^');
                    class_index += 1;
                }
                for (offset, character) in characters[class_index..=end].iter().enumerate() {
                    if *character == '\\' || (*character == '^' && offset == 0) {
                        output.push('\\');
                    }
                    output.push(*character);
                }
                index = end;
            }
            '\\' | '.' | '+' | '(' | ')' | '|' | '^' | '$' | '{' | '}' | '[' | ']' => {
                output.push('\\');
                output.push(characters[index]);
            }
            character => output.push(character),
        }
        index += 1;
    }
    output.push('$');
    output
}
fn directory_regex(pattern: &str) -> String {
    if pattern.contains('/') || pattern.contains('\\') {
        glob_regex(pattern)
    } else {
        format!(
            "(^|.*/){}(/|$)",
            glob_regex(pattern)
                .trim_start_matches('^')
                .trim_end_matches('$')
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scan_parser::interpret_clamscan;

    #[test]
    fn local_yara_loading_uses_only_sorted_regular_rule_files() {
        let root = tempfile::tempdir().expect("rules workspace");
        let rules = root.path().join("rules");
        fs::create_dir(&rules).expect("create rules folder");
        fs::write(rules.join("z-last.YARA"), "rule z { condition: true }")
            .expect("write YARA file");
        fs::write(rules.join("a-first.yar"), "rule a { condition: true }")
            .expect("write YARA file");
        fs::write(rules.join("ignored.txt"), "not a rule").expect("write unrelated file");
        fs::create_dir(rules.join("nested.yar")).expect("create nested directory");
        std::os::unix::fs::symlink(rules.join("a-first.yar"), rules.join("linked.yar"))
            .expect("create symlink");
        let ctx = Context::with_paths(crate::common::Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        ctx.update_settings(json!({
            "yara_rules_directory": rules.to_string_lossy()
        }))
        .expect("configure YARA folder");

        let found = yara_database_paths(&ctx).expect("load rule paths");

        assert_eq!(
            found,
            [rules.join("a-first.yar"), rules.join("z-last.YARA")]
        );
    }

    #[test]
    fn clamscan_arguments_pass_yara_files_as_individual_database_arguments() {
        let root = tempfile::tempdir().expect("scan workspace");
        let ctx = Context::with_paths(crate::common::Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        let target = root.path().join("a file to scan");
        let rule = root.path().join("rules with spaces.yar");

        let arguments = clamscan_arguments(
            &ctx,
            &target,
            false,
            &Exclusions {
                yara_rules: vec![rule.clone()],
                ..Exclusions::default()
            },
            &ScanOptions::default(),
            Some("/var/lib/clamav"),
        );

        let separator = arguments
            .iter()
            .position(|argument| argument == "--")
            .expect("scan option terminator");
        assert_eq!(
            arguments[separator - 1],
            format!("--database={}", rule.display())
        );
        assert!(arguments.contains(&"--database=/var/lib/clamav".into()));
        assert_eq!(
            arguments.last(),
            Some(&target.to_string_lossy().into_owned())
        );
    }

    #[test]
    fn supported_profile_options_are_applied_as_safe_clamscan_arguments() {
        let options = parse_profile_options(&json!({
            "MaxFileSize": "40M",
            "MaxRecursion": 25,
            "Thorough": true,
            "Heuristic": false,
            "ScanHidden": false,
            "Recursive": false,
            "FollowFileSymlinks": true
        }))
        .expect("parse profile options");
        assert!(options.requires_standalone());
        assert_eq!(options.recursive, Some(false));

        let root = tempfile::tempdir().expect("scan workspace");
        let ctx = Context::with_paths(crate::common::Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        let target = root.path().join("scan target");
        let arguments = clamscan_arguments(
            &ctx,
            &target,
            options.recursive.unwrap_or(true),
            &Exclusions::default(),
            &options,
            None,
        );

        assert!(arguments.contains(&"--max-filesize=40M".into()));
        assert!(arguments.contains(&"--max-recursion=25".into()));
        assert!(arguments.contains(&"--detect-pua=yes".into()));
        assert!(arguments.contains(&"--alert-broken=yes".into()));
        assert!(arguments.contains(&"--alert-macros=yes".into()));
        assert!(arguments.contains(&"--heuristic-alerts=no".into()));
        assert!(arguments.contains(&"--follow-file-symlinks=1".into()));
        assert!(arguments.contains(&"--exclude".into()));
        assert!(arguments.contains(&"\\/\\.".into()));
        assert!(!arguments.contains(&"-r".into()));
    }

    #[test]
    fn invalid_or_unknown_profile_scan_options_fail_closed() {
        assert!(parse_profile_options(&json!({"MaxFileSize": "20MG"})).is_err());
        assert!(parse_profile_options(&json!({"MaxRecursion": 0})).is_err());
        assert!(parse_profile_options(&json!({"--remove": true})).is_err());
        assert!(parse_profile_options(&json!({"DetectPUA": "yes"})).is_err());
        assert!(parse_profile_options(&json!({"SizeLimit": false, "MaxFileSize": "40M"})).is_err());
        assert!(parse_profile_options(&json!({"Thorough": true, "DetectPUA": false})).is_err());
    }

    #[test]
    fn scan_uses_engine_options_saved_in_the_selected_profile() {
        let root = tempfile::tempdir().expect("profile workspace");
        let ctx = Context::with_paths(crate::common::Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        let profile = crate::dispatch(
            &ctx,
            "profiles.create",
            json!({"name":"Deep scan", "options":{"DetectPUA":false, "MaxFileSize":"60M"}}),
        )
        .expect("create profile");
        let request = ScanRequest {
            id: None,
            paths: vec!["/tmp/example".into()],
            recursive: true,
            profile_id: profile.get("id").and_then(Value::as_str).map(str::to_owned),
            profile_name: None,
            backend_override: None,
            force_stream: false,
            exclusions: None,
            scheduled: false,
        };

        let (_, options) = merged_scan_plan(&ctx, &request).expect("load profile scan plan");

        assert!(options.requires_standalone());
        assert_eq!(options.pua, Some(false));
        assert_eq!(
            options.limits.get("MaxFileSize").map(String::as_str),
            Some("60M")
        );
    }

    #[test]
    fn missing_configured_yara_folder_fails_closed() {
        let root = tempfile::tempdir().expect("rules workspace");
        let ctx = Context::with_paths(crate::common::Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        ctx.update_settings(json!({
            "yara_rules_directory": root.path().join("missing").to_string_lossy()
        }))
        .expect("configure missing YARA folder");

        assert!(yara_database_paths(&ctx)
            .expect_err("missing configured directory must not look like no rules")
            .contains("Unable to inspect configured local YARA rules directory"));
    }

    #[test]
    fn caret_is_literal_in_fnmatch_character_classes_for_daemon_and_clamscan() {
        let expression = regex::Regex::new(&glob_regex("sample[^a].txt")).expect("regex");
        for (name, expected) in [
            ("samplea.txt", true),
            ("sample^.txt", true),
            ("sampleb.txt", false),
        ] {
            assert_eq!(
                glob_matches(name, "sample[^a].txt"),
                expected,
                "daemon: {name}"
            );
            assert_eq!(expression.is_match(name), expected, "clamscan: {name}");
        }
    }

    #[test]
    fn adversarial_glob_pattern_does_not_need_exponential_work() {
        let value = "a".repeat(80);
        let pattern = format!("{}b", "*a".repeat(14));
        assert!(!glob_matches(&value, &pattern));
        assert!(glob_matches("aaaaaaaaaaaaaaaaaaaa", "*a*a*a*a*a*a"));
    }

    fn capture_fixture(
        stdout: Vec<u8>,
        stderr: Vec<u8>,
        daemon: bool,
        cancelled: bool,
        exit_code: i32,
        stdin_path: Option<&str>,
    ) -> (CapturedOutput, ProgressState, Vec<ScanProgress>) {
        let (sender, receiver) = mpsc::sync_channel(128);
        let stdout = spawn_reader_with_limit(
            std::io::Cursor::new(stdout),
            true,
            daemon,
            sender.clone(),
            32,
        );
        let stderr =
            spawn_reader_with_limit(std::io::Cursor::new(stderr), false, daemon, sender, 32);
        let stdout = stdout.join().expect("stdout reader");
        let stderr = stderr.join().expect("stderr reader");
        let mut progress = ProgressState::default();
        let mut events = Vec::new();
        while let Ok(line) = receiver.try_recv() {
            update_progress(
                &line,
                if daemon { "daemon" } else { "clamscan" },
                stdin_path,
                &mut progress,
                None,
                |event| events.push(event),
            );
        }
        let mut evidence = stdout.evidence;
        evidence.merge_stderr(stderr.evidence);
        let mut stderr_text = String::from_utf8_lossy(&stderr.bytes).into_owned();
        if stderr.truncated {
            stderr_text.push_str("\n[stderr truncated at 67108864 bytes]\n");
        }
        (
            CapturedOutput {
                stdout_bytes: stdout.bytes,
                stdout_truncated: stdout.truncated,
                stderr: stderr_text,
                exit_code,
                cancelled,
                evidence,
            },
            progress,
            events,
        )
    }

    #[test]
    fn final_results_keep_late_threats_skips_and_warnings_for_both_backends() {
        let stdout = b"Scanning /filler...........................\n/tmp/late: Eicar FOUND\n/tmp/missing: Failed to open file\nScanned files: 7\nScanned directories: 3\nTotal errors: 1\n".to_vec();
        let stderr = b"unimportant filler beyond display cap...........\nLibClamAV Warning: file truncated\n".to_vec();
        for daemon in [false, true] {
            let (output, progress, _) =
                capture_fixture(stdout.clone(), stderr.clone(), daemon, false, 2, None);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 7,
                        directories: 3,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert!(result.stdout.contains("[stdout truncated"));
            assert!(!result.stdout.contains("Eicar FOUND"));
            assert!(result.stderr.contains("[stderr truncated"));
            assert_eq!(result.status, ScanStatus::Infected);
            assert_eq!(result.infected_count, 1);
            assert_eq!(result.infected_files, ["/tmp/late"]);
            assert_eq!(result.scanned_files, 7);
            assert_eq!(result.scanned_dirs, 3);
            assert_eq!(result.skipped_files, ["/tmp/missing"]);
            assert_eq!(
                result.warning_message.as_deref(),
                Some("1 file could not be accessed")
            );
            assert_eq!(
                result.nonfatal_warnings,
                ["LibClamAV Warning: file truncated"]
            );
        }
    }

    #[test]
    fn late_hard_errors_and_total_error_summary_affect_final_verdict() {
        for daemon in [false, true] {
            let stdout = b"ordinary filler beyond display limit........\nScanned files: 4\nTotal errors: 1\n".to_vec();
            let stderr =
                b"ordinary filler beyond display limit........\nERROR: database failure\n".to_vec();
            let (output, progress, _) =
                capture_fixture(stdout.clone(), stderr, daemon, false, 2, None);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 4,
                        directories: 0,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert_eq!(result.status, ScanStatus::Error);
            assert!(result
                .error_message
                .as_deref()
                .unwrap()
                .contains("ERROR: database failure"));

            let (output, progress, _) = capture_fixture(stdout, Vec::new(), daemon, false, 2, None);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 4,
                        directories: 0,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert_eq!(result.status, ScanStatus::Clean);
            assert_eq!(
                result.warning_message.as_deref(),
                Some("1 file could not be read")
            );
        }
    }

    #[test]
    fn hard_errors_crossing_display_boundary_are_retained_without_duplicates() {
        for daemon in [false, true] {
            let stdout = b"Scanned files: 4\nERROR: early\nERROR: late\n".to_vec();
            let (output, progress, _) = capture_fixture(stdout, Vec::new(), daemon, false, 2, None);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 4,
                        directories: 0,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert_eq!(result.status, ScanStatus::Error);
            assert_eq!(
                result.error_message.as_deref(),
                Some("ERROR: early\nERROR: late")
            );
        }
    }

    #[test]
    fn localizes_all_failed_heading_without_translating_appended_diagnostics() {
        let temp = tempfile::tempdir().expect("temporary workspace");
        let context = Context::with_paths(crate::common::Paths {
            home: temp.path().join("home"),
            config_dir: temp.path().join("config/linux-defender"),
            data_dir: temp.path().join("data/linux-defender"),
        })
        .expect("context");
        context
            .update_settings(json!({"language": "de"}))
            .expect("language");

        let stdout = b"ordinary filler beyond display limit........\nScanned files: 0\nERROR: engine unavailable\n".to_vec();
        let (output, progress, _) = capture_fixture(stdout, Vec::new(), false, false, 2, None);
        let mut result = finalize_clamscan("/tmp", output, progress.files_scanned);
        assert_eq!(
            result.error_message.as_deref(),
            Some("No files could be scanned\nERROR: engine unavailable")
        );
        localize_result(&context, &mut result);
        assert_eq!(
            result.error_message.as_deref(),
            Some("Keine Dateien konnten gescannt werden\nERROR: engine unavailable")
        );
    }

    #[test]
    fn explicit_zero_summary_after_truncation_overrides_progress_hint() {
        let stdout = b"Scanning /filler...........................\nScanned files: 0\nScanned directories: 0\n".to_vec();
        let (output, progress, _) = capture_fixture(stdout, Vec::new(), false, false, 0, None);
        assert!(progress.files_scanned > 0);
        let result = finalize_clamscan("/tmp", output, progress.files_scanned);
        assert_eq!((result.scanned_files, result.scanned_dirs), (0, 0));
    }

    #[test]
    fn cancellation_preserves_late_raw_paths_and_daemon_stdin_mapping() {
        let stdout = b"filler beyond display limit................\n/tmp/raw-\xff: First FOUND\n/tmp/other: Second FOUND".to_vec();
        let expected = path_to_wire(Path::new(OsStr::from_bytes(b"/tmp/raw-\xff")));
        for daemon in [false, true] {
            let (output, progress, events) =
                capture_fixture(stdout.clone(), Vec::new(), daemon, true, -1, None);
            assert_eq!(events[0].new_threats[0].file_path, expected);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 2,
                        directories: 0,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert_eq!(result.status, ScanStatus::Cancelled);
            assert_eq!(result.infected_count, 2);
            assert_eq!(result.infected_files[0], expected);
            assert_eq!(result.infected_files[1], "/tmp/other");
        }
        let path = "file:///tmp/raw%FF";
        let (output, progress, _) = capture_fixture(
            b"filler beyond display limit................\nfd[0]: First FOUND\nfd[0]: Second FOUND"
                .to_vec(),
            Vec::new(),
            true,
            true,
            -1,
            Some(path),
        );
        let result = finalize_daemon_phase(
            "/tmp",
            DaemonPhaseEvidence {
                output,
                files: 1,
                directories: 0,
                stdin_path: Some(path),
                scanned_files: progress.files_scanned,
            },
        );
        assert_eq!(result.status, ScanStatus::Cancelled);
        assert_eq!(result.infected_count, 2);
        assert!(result.infected_files.iter().all(|actual| actual == path));
    }

    #[test]
    fn cancelled_daemon_phase_keeps_prior_phase_findings_without_remapping_them() {
        let (first, progress, _) = capture_fixture(
            b"filler beyond display limit................\n/tmp/first: First FOUND\n".to_vec(),
            Vec::new(),
            true,
            false,
            1,
            None,
        );
        let first = finalize_daemon_phase(
            "/tmp",
            DaemonPhaseEvidence {
                output: first,
                files: 1,
                directories: 2,
                stdin_path: None,
                scanned_files: progress.files_scanned,
            },
        );
        let path = "file:///tmp/raw%FF";
        let (second, progress, _) = capture_fixture(
            b"filler beyond display limit................\nfd[0]: Second FOUND".to_vec(),
            Vec::new(),
            true,
            true,
            -1,
            Some(path),
        );
        let second = finalize_daemon_phase(
            "/tmp",
            DaemonPhaseEvidence {
                output: second,
                files: 1,
                directories: 0,
                stdin_path: Some(path),
                scanned_files: progress.files_scanned,
            },
        );
        let mut accumulator = DaemonResultAccumulator::new("/tmp");
        accumulator.add(first);
        accumulator.add(second);
        let result = accumulator.finish();
        assert_eq!(result.status, ScanStatus::Cancelled);
        assert_eq!(result.infected_files, ["/tmp/first", path]);
        assert_eq!(result.infected_count, 2);
        assert_eq!(result.scanned_dirs, 2);
    }

    #[test]
    fn split_utf8_and_non_utf8_paths_survive_reader_and_finalization() {
        let mut stdout = vec![b'x'; 8182];
        stdout.push(b'\n');
        stdout.extend_from_slice("/tmp/café: First FOUND\n".as_bytes());
        stdout.extend_from_slice(b"/tmp/raw-\xff: Second FOUND");
        let stderr = b"filler beyond display limit................\nWARNING: Can't open file /tmp/skip-\xff: Permission denied".to_vec();
        let (output, progress, events) = capture_fixture(stdout, stderr, false, false, 1, None);
        let result = finalize_clamscan("/tmp", output, progress.files_scanned);
        assert_eq!(result.infected_files[0], "/tmp/café");
        assert_eq!(events[0].new_threats[0].file_path, "/tmp/café");
        assert_eq!(
            result.infected_files[1],
            path_to_wire(Path::new(OsStr::from_bytes(b"/tmp/raw-\xff")))
        );
        assert_eq!(
            result.skipped_files[0],
            path_to_wire(Path::new(OsStr::from_bytes(b"/tmp/skip-\xff")))
        );
    }

    #[test]
    fn live_and_final_paths_preserve_unicode_whitespace_and_raw_byte_boundaries() {
        let directory = tempfile::tempdir().expect("temporary directory");
        let clean = directory.path().join("item");
        let infected = directory.path().join("item\u{a0}");
        let infected_space = directory.path().join("item ");
        let skipped_space = directory.path().join("skip ");
        let raw = directory
            .path()
            .join(std::ffi::OsString::from_vec(b"raw-\xff\xc2\xa0".to_vec()));
        let skipped = directory
            .path()
            .join(std::ffi::OsString::from_vec(b"skip-\xff\xc2\xa0".to_vec()));
        fs::write(&clean, b"clean sibling").expect("write clean file");
        fs::write(&infected, b"infected").expect("write infected file");
        fs::write(&infected_space, b"space infected").expect("write space infected file");
        fs::write(&raw, b"raw infected").expect("write raw infected file");
        let expected = path_to_wire(&infected);
        let expected_space = path_to_wire(&infected_space);
        let expected_skipped_space = path_to_wire(&skipped_space);
        let expected_raw = path_to_wire(&raw);
        let expected_skipped = path_to_wire(&skipped);

        for daemon in [false, true] {
            for cancelled in [false, true] {
                let mut stdout = b"filler beyond display limit................\n".to_vec();
                if !daemon {
                    stdout.extend_from_slice(b"Scanning ");
                }
                stdout.extend_from_slice(infected.as_os_str().as_bytes());
                stdout.extend_from_slice(if daemon { b": OK\n" } else { b"\n" });
                stdout.extend_from_slice(infected.as_os_str().as_bytes());
                stdout.extend_from_slice(b": First FOUND\n");
                if !daemon {
                    stdout.extend_from_slice(b"Scanning ");
                }
                stdout.extend_from_slice(infected_space.as_os_str().as_bytes());
                stdout.extend_from_slice(if daemon { b": OK\n" } else { b"\n" });
                stdout.extend_from_slice(infected_space.as_os_str().as_bytes());
                stdout.extend_from_slice(b": Space FOUND\n");
                stdout.extend_from_slice(raw.as_os_str().as_bytes());
                stdout.extend_from_slice(b": Second FOUND");
                let mut stderr = b"filler beyond display limit................\n".to_vec();
                stderr.extend_from_slice(skipped.as_os_str().as_bytes());
                stderr.extend_from_slice(b": Failed to open file\n");
                stderr.extend_from_slice(b"ERROR: Can't access file ");
                stderr.extend_from_slice(skipped_space.as_os_str().as_bytes());
                stderr.push(b'\n');
                let (output, progress, events) = capture_fixture(
                    stdout,
                    stderr,
                    daemon,
                    cancelled,
                    if cancelled { -1 } else { 1 },
                    None,
                );
                assert_eq!(events[0].current_file, expected);
                assert_eq!(events[1].new_threats[0].file_path, expected);
                assert_eq!(events[2].current_file, expected_space);
                assert_eq!(events[3].new_threats[0].file_path, expected_space);
                assert_eq!(events[4].new_threats[0].file_path, expected_raw);
                assert_eq!(events[4].infected_count, 3);
                let result = if daemon {
                    finalize_daemon_phase(
                        "/tmp",
                        DaemonPhaseEvidence {
                            output,
                            files: 3,
                            directories: 0,
                            stdin_path: None,
                            scanned_files: progress.files_scanned,
                        },
                    )
                } else {
                    finalize_clamscan("/tmp", output, progress.files_scanned)
                };
                assert_eq!(
                    result.infected_files,
                    [
                        expected.as_str(),
                        expected_space.as_str(),
                        expected_raw.as_str()
                    ]
                );
                assert_eq!(
                    result.skipped_files,
                    [expected_skipped.as_str(), expected_skipped_space.as_str()]
                );
                let selected =
                    crate::common::path_from_wire(&result.infected_files[0]).expect("wire path");
                assert_eq!(fs::read(selected).expect("selected file"), b"infected");
                let selected =
                    crate::common::path_from_wire(&result.infected_files[1]).expect("wire path");
                assert_eq!(
                    fs::read(selected).expect("selected file"),
                    b"space infected"
                );
                assert_eq!(fs::read(&clean).expect("clean sibling"), b"clean sibling");
            }
        }
    }

    #[test]
    fn exit_one_without_details_has_incomplete_details_warning() {
        for daemon in [false, true] {
            let (output, progress, _) =
                capture_fixture(Vec::new(), Vec::new(), daemon, false, 1, None);
            let result = if daemon {
                finalize_daemon_phase(
                    "/tmp",
                    DaemonPhaseEvidence {
                        output,
                        files: 1,
                        directories: 0,
                        stdin_path: None,
                        scanned_files: progress.files_scanned,
                    },
                )
            } else {
                finalize_clamscan("/tmp", output, progress.files_scanned)
            };
            assert_eq!(result.status, ScanStatus::Infected);
            assert_eq!(result.infected_count, 1);
            assert_eq!(
                result.warning_message.as_deref(),
                Some("Threats were detected, but details are unavailable.")
            );
        }
    }

    #[test]
    fn infection_summary_count_survives_missing_threat_details() {
        let summary = interpret_clamscan("/tmp", "Infected files: 3\n", "", 1, 0);
        assert_eq!(summary.status, ScanStatus::Infected);
        assert_eq!(summary.infected_count, 3);
        assert!(summary.threat_details.is_empty());

        let detailed =
            interpret_clamscan("/tmp", "/tmp/a: Eicar FOUND\nInfected files: 4\n", "", 1, 1);
        assert_eq!(detailed.status, ScanStatus::Infected);
        assert_eq!(detailed.infected_count, 4);
        assert_eq!(detailed.threat_details.len(), 1);
    }

    #[test]
    fn daemon_incomplete_detection_warning_takes_priority_over_access_warnings() {
        let benign = interpret_daemon("/tmp", "/tmp/missing: Failed to open file\n", "", 2, 2, 0);
        let incomplete = interpret_daemon("/tmp", "", "", 1, 1, 0);
        for (first, second) in [
            (benign.clone(), incomplete.clone()),
            (incomplete.clone(), benign.clone()),
        ] {
            let mut accumulator = DaemonResultAccumulator::new("/tmp");
            accumulator.add(first);
            accumulator.add(second);
            let result = accumulator.finish();
            assert_eq!(result.status, ScanStatus::Infected);
            assert_eq!(result.infected_count, 1);
            assert_eq!(result.scanned_files, 3);
            assert_eq!(result.skipped_count, 1);
            assert_eq!(
                result.warning_message.as_deref(),
                Some("Threats were detected, but details are unavailable.")
            );
        }
    }

    #[test]
    fn aggregate_prioritizes_localized_incomplete_detection_warning() {
        let temp = tempfile::tempdir().expect("temporary workspace");
        let context = Context::with_paths(crate::common::Paths {
            home: temp.path().join("home"),
            config_dir: temp.path().join("config/linux-defender"),
            data_dir: temp.path().join("data/linux-defender"),
        })
        .expect("context");
        context
            .update_settings(json!({"language": "de"}))
            .expect("language");
        let mut benign =
            interpret_daemon("/tmp", "/tmp/missing: Failed to open file\n", "", 2, 2, 0);
        let mut incomplete = interpret_daemon("/tmp", "", "", 1, 1, 0);
        localize_result(&context, &mut benign);
        localize_result(&context, &mut incomplete);
        let result = aggregate_result("test", vec![benign, incomplete], Duration::ZERO, false);
        assert_eq!(result["status"], "infected");
        assert_eq!(result["infected_count"], 1);
        assert_eq!(result["scanned_files"], 3);
        assert_eq!(result["skipped_count"], 1);
        assert_eq!(
            result["warning_message"],
            "Bedrohungen wurden erkannt, aber es sind keine Details verfügbar."
        );
    }

    #[test]
    fn daemon_accumulator_preserves_error_exit_codes() {
        let mut accumulator = DaemonResultAccumulator::new("/tmp");
        accumulator.add(ScanResult::error("/tmp", "open failed", "daemon"));
        assert_eq!(accumulator.finish().exit_code, -1);

        let mut accumulator = DaemonResultAccumulator::new("/tmp");
        accumulator.add(interpret_daemon(
            "/tmp",
            "/tmp/infected: Signature FOUND\n",
            "",
            1,
            1,
            0,
        ));
        accumulator.add(ScanResult::error("/tmp", "open failed", "daemon"));
        let result = accumulator.finish();
        assert_eq!(result.status, ScanStatus::Infected);
        assert_eq!(result.exit_code, -1);
    }

    #[test]
    fn fuse_magic_is_recognised() {
        assert!(is_fuse_magic(FUSE_SUPER_MAGIC));
        // ext4, tmpfs, btrfs, overlayfs and nfs magic values.
        for other in [0xEF53, 0x858458F6, 0x9123683E, 0x794C7630, 0x6969] {
            assert!(!is_fuse_magic(other));
        }
    }

    #[test]
    fn fuse_detector_caches_one_probe_per_device() {
        use std::sync::atomic::{AtomicUsize, Ordering};
        static PROBES: AtomicUsize = AtomicUsize::new(0);
        fn counting_probe(_: &Path) -> bool {
            PROBES.fetch_add(1, Ordering::AcqRel);
            true
        }
        let root = tempfile::tempdir().expect("temp dir");
        let file = root.path().join("payload");
        std::fs::write(&file, b"payload").expect("write payload");
        let mut detector = FuseDetector {
            probe: Some(counting_probe),
            ..FuseDetector::default()
        };
        assert!(detector.is_fuse(&file));
        assert!(detector.is_fuse(&file));
        assert_eq!(PROBES.load(Ordering::Acquire), 1);
    }

    #[test]
    fn stream_transport_arguments_replaces_only_fdpass() {
        let args = vec![
            "--scan-daemon".into(),
            "--fdpass".into(),
            "--no-summary".into(),
        ];
        assert_eq!(
            stream_transport_arguments(&args),
            vec!["--scan-daemon", "--stream", "--no-summary"]
        );
        let already = vec!["--stream".into()];
        assert_eq!(stream_transport_arguments(&already), already);
    }

    #[test]
    fn daemon_stdin_paths_are_partitioned() {
        let long = std::path::PathBuf::from(format!("/tmp/{}", "x".repeat(1100)));
        let short = std::path::PathBuf::from("/tmp/short");
        let paths = [short.clone(), long.clone()];
        let (safe, stdin) = split_daemon_stdin_paths(&paths);
        assert_eq!(safe, vec![&short]);
        assert_eq!(stdin, vec![&long]);
    }

    #[test]
    fn stdin_transcript_errors_name_the_real_file() {
        let mut result = ScanResult::error("/tmp", "ok", "daemon");
        result.stdout = "fd[10]: Not a regular file ERROR\n/tmp/ok: OK\n".into();
        restore_stdin_paths(&mut result, "/tmp/fuse-file");
        assert!(result
            .stdout
            .contains("/tmp/fuse-file: Not a regular file ERROR"));
    }
}
