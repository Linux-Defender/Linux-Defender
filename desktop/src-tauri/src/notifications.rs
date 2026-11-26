use linux_defender_core::{
    common::Context,
    i18n::{translate, translate_plural},
};
use serde_json::Value;
use std::sync::atomic::{AtomicI32, Ordering};
use tauri::AppHandle;
use tauri_plugin_notification::NotificationExt;

pub struct Notifications {
    next_native_id: AtomicI32,
}

impl Notifications {
    pub fn new() -> Self {
        Self {
            next_native_id: AtomicI32::new(1),
        }
    }

    pub fn dispatch(&self, ctx: &Context, app: &AppHandle, event: &str, data: &Value) {
        let Some((_id, title, body, action, device_only)) = notification_for(ctx, event, data)
        else {
            return;
        };
        let settings = match ctx.settings() {
            Ok(value) => value,
            Err(_) => return,
        };
        if !settings
            .get("notifications_enabled")
            .and_then(Value::as_bool)
            .unwrap_or(true)
        {
            return;
        }
        if device_only
            && !settings
                .get("device_auto_scan_notify")
                .and_then(Value::as_bool)
                .unwrap_or(true)
        {
            return;
        }
        let native_id = self.next_native_id.fetch_add(1, Ordering::Relaxed);
        let identity = notification_identity(event, data);
        let _ = app
            .notification()
            .builder()
            .id(native_id)
            .title(title)
            .body(body)
            .action_type_id(action)
            .extra("linux-defender-action", action)
            .extra("linux-defender-identity", identity)
            .show();
    }
}

fn notification_identity(event: &str, data: &Value) -> Value {
    let result = data.get("result").unwrap_or(data);
    let mut identity = serde_json::Map::new();
    identity.insert("event".into(), Value::String(event.to_owned()));
    if let Some(id) = data
        .get("id")
        .or_else(|| result.get("id"))
        .and_then(Value::as_str)
    {
        identity.insert("id".into(), Value::String(id.to_owned()));
    }
    Value::Object(identity)
}

fn trn(ctx: &Context, singular: &str, plural: &str, count: u64) -> String {
    translate_plural(ctx, singular, plural, count)
}

fn notification_for(
    ctx: &Context,
    event: &str,
    data: &Value,
) -> Option<(&'static str, String, String, &'static str, bool)> {
    let tr = |message| translate(ctx, message);
    match event {
        "scan-complete" => {
            let result = data.get("result").unwrap_or(data);
            let status = result
                .get("status")
                .and_then(Value::as_str)
                .unwrap_or("error");
            let (title, body) = match status {
                "clean" => (tr("Scan Complete"), tr("No threats found")),
                "infected" => (tr("Threats Detected!"), String::new()),
                "cancelled" => (tr("Scan Cancelled"), String::new()),
                _ => (
                    tr("Scan Error"),
                    // Host process text is untrusted: sanitize before showing it
                    // in a native notification, as the persistence path does.
                    linux_defender_core::common::sanitize_line(
                        result
                            .get("error_message")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    ),
                ),
            };
            Some(("scan-complete", title, body, "show-scan", false))
        }
        "update-complete" => {
            let result = data.get("result").unwrap_or(data);
            let status = result
                .get("status")
                .and_then(Value::as_str)
                .unwrap_or("error");
            let method = result
                .get("update_method")
                .and_then(Value::as_str)
                .unwrap_or("manual");
            let count = result
                .get("databases_updated")
                .and_then(Value::as_u64)
                .unwrap_or(0);
            let (title, body) = match (status, method, count) {
                ("success", "service_signal", _) => (
                    tr("Database Update Requested"),
                    tr("Freshclam service was signalled to check for updates"),
                ),
                ("success", _, updated) if updated > 0 => (
                    tr("Database Updated"),
                    trn(
                        ctx,
                        "{count} virus database was updated",
                        "{count} virus databases were updated",
                        updated,
                    )
                    .replace("{count}", &updated.to_string()),
                ),
                ("up_to_date", _, _) => (
                    tr("Database Up to Date"),
                    tr("Virus definitions are already current"),
                ),
                ("cancelled", _, _) => (
                    tr("Database Update Cancelled"),
                    linux_defender_core::common::sanitize_line(
                        result
                            .get("error_message")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    ),
                ),
                _ => (
                    tr("Database Update Failed"),
                    linux_defender_core::common::sanitize_line(
                        result
                            .get("error_message")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    ),
                ),
            };
            Some(("update-complete", title, body, "show-update", false))
        }
        "virustotal-complete" => Some((
            "virustotal-scan-complete",
            tr("VirusTotal Analysis Complete"),
            String::new(),
            "show-scan",
            false,
        )),
        "device-scan-start" => Some((
            "device-scan-started",
            tr("Scanning Device"),
            String::new(),
            "show-scan",
            true,
        )),
        "device-scan-complete" => Some((
            "device-scan-complete",
            tr("Device Scan Complete"),
            String::new(),
            "show-scan",
            true,
        )),
        _ => None,
    }
}
