//! Native-only startup diagnostics for blank-window reports (upstream ClamUI #361/#366).
//!
//! No new Tauri command, capability, permission, or boot JavaScript is involved:
//! this only records milestones in-process and classifies a stuck startup so the
//! existing 10-second watchdog can write one actionable debug line.
use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};

pub const WATCHDOG_DELAY: Duration = Duration::from_secs(10);
pub const MAIN_THREAD_PROBE: Duration = Duration::from_secs(3);
const MAX_MILESTONES: usize = 64;

#[derive(Clone)]
pub struct StartupTrace {
    inner: Arc<Inner>,
}

struct Inner {
    started: Instant,
    milestones: Mutex<Vec<(Duration, String)>>,
    setup_finished: AtomicBool,
    first_request: AtomicBool,
    first_response: AtomicBool,
}

impl Default for StartupTrace {
    fn default() -> Self {
        Self::new()
    }
}

impl StartupTrace {
    pub fn new() -> Self {
        let trace = Self {
            inner: Arc::new(Inner {
                started: Instant::now(),
                milestones: Mutex::new(Vec::new()),
                setup_finished: AtomicBool::new(false),
                first_request: AtomicBool::new(false),
                first_response: AtomicBool::new(false),
            }),
        };
        trace.mark("native runtime started");
        trace
    }

    pub fn mark(&self, label: impl Into<String>) {
        let elapsed = self.inner.started.elapsed();
        if let Ok(mut milestones) = self.inner.milestones.lock() {
            if milestones.len() >= MAX_MILESTONES {
                milestones.remove(0);
            }
            milestones.push((elapsed, label.into()));
        }
    }

    pub fn setup_finished(&self) {
        self.inner.setup_finished.store(true, Ordering::Release);
        self.mark("setup finished");
    }

    pub fn is_setup_finished(&self) -> bool {
        self.inner.setup_finished.load(Ordering::Acquire)
    }

    /// Record only the first IPC request/response so a busy session cannot
    /// grow the timeline without bound.
    pub fn note_request(&self, action: &str) -> bool {
        if self.inner.first_request.swap(true, Ordering::AcqRel) {
            return false;
        }
        self.mark(format!("first IPC request: {action}"));
        true
    }

    pub fn note_response(&self, action: &str, succeeded: bool) -> bool {
        if self.inner.first_response.swap(true, Ordering::AcqRel) {
            return false;
        }
        self.mark(format!(
            "first IPC response: {action} ({})",
            if succeeded { "ok" } else { "failed" }
        ));
        true
    }

    pub fn summary(&self) -> String {
        let milestones = self
            .inner
            .milestones
            .lock()
            .map(|g| g.clone())
            .unwrap_or_default();
        milestones
            .iter()
            .map(|(at, label)| format!("+{}ms {label}", at.as_millis()))
            .collect::<Vec<_>>()
            .join(" | ")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProbeResult {
    Responded,
    TimedOut,
    Failed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Verdict {
    SetupUnfinished,
    MainThreadBlocked,
    FrontendMissing,
    Unknown,
}

/// A hang before setup completes cannot be distinguished from a blocked main
/// thread by probing, so report the earlier stage instead.
pub fn pick_verdict(setup_finished: bool, probe: ProbeResult) -> Verdict {
    if !setup_finished {
        return Verdict::SetupUnfinished;
    }
    match probe {
        ProbeResult::Responded => Verdict::FrontendMissing,
        ProbeResult::TimedOut => Verdict::MainThreadBlocked,
        ProbeResult::Failed => Verdict::Unknown,
    }
}

pub fn describe(verdict: Verdict, summary: &str) -> String {
    let stage = match verdict {
        Verdict::SetupUnfinished => "native setup did not finish",
        Verdict::MainThreadBlocked => "main thread is blocked",
        Verdict::FrontendMissing => "page never mounted",
        Verdict::Unknown => "startup stage is unknown",
    };
    format!("startup watchdog: {stage}; timeline: {summary}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn timeline_is_bounded_and_ordered() {
        let trace = StartupTrace::new();
        for index in 0..MAX_MILESTONES + 10 {
            trace.mark(format!("step {index}"));
        }
        let summary = trace.summary();
        // The oldest milestones are intentionally dropped once bounded.
        assert!(!summary.contains("native runtime started"));
        assert!(summary.contains("step 73"));
        assert!(summary.matches(" | ").count() < MAX_MILESTONES);
    }

    #[test]
    fn request_and_response_are_recorded_once() {
        let trace = StartupTrace::new();
        assert!(trace.note_request("status"));
        assert!(!trace.note_request("status"));
        assert!(trace.note_response("status", true));
        assert!(!trace.note_response("status", false));
        let summary = trace.summary();
        assert_eq!(summary.matches("first IPC request").count(), 1);
        assert_eq!(summary.matches("first IPC response").count(), 1);
    }

    #[test]
    fn setup_finished_is_recorded_as_a_milestone() {
        let trace = StartupTrace::new();
        assert!(!trace.is_setup_finished());
        trace.setup_finished();
        assert!(trace.is_setup_finished());
        assert!(trace.summary().contains("setup finished"));
    }

    #[test]
    fn verdicts_name_the_stuck_stage() {
        assert_eq!(
            pick_verdict(false, ProbeResult::Responded),
            Verdict::SetupUnfinished
        );
        assert_eq!(
            pick_verdict(true, ProbeResult::Responded),
            Verdict::FrontendMissing
        );
        assert_eq!(
            pick_verdict(true, ProbeResult::TimedOut),
            Verdict::MainThreadBlocked
        );
        assert_eq!(pick_verdict(true, ProbeResult::Failed), Verdict::Unknown);
        assert!(describe(Verdict::MainThreadBlocked, "t").contains("main thread"));
        assert!(describe(Verdict::FrontendMissing, "t").contains("page never mounted"));
    }
}
