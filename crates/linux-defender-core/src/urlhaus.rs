//! URLhaus ClamAV signature feed management.
//!
//! abuse.ch removed the anonymous `urlhaus.ndb` download and now requires a free
//! Auth-Key on its ClamAV export endpoint, so the key lives in the keyring and
//! the feed URL embeds it. The frontend builds the displayed URL from the
//! [`URLHAUS_FEED_PREFIX`] and [`URLHAUS_FEED_SUFFIX`] constants via
//! [`feed_url`]; [`dispatch`] exposes the keyring operations used by Preferences.

use crate::credentials::{Account, CredentialStore};
use crate::{AppResult, Context};
use serde_json::{json, Value};

pub const URLHAUS_FEED_PREFIX: &str = "https://urlhaus-api.abuse.ch/v2/files/exports/";
pub const URLHAUS_FEED_SUFFIX: &str = "/urlhaus_clamav.ndb";

/// The ClamAV signature export URL for a valid abuse.ch Auth-Key.
pub fn feed_url(auth_key: &str) -> AppResult<String> {
    crate::credentials::validate_urlhaus_auth_key(auth_key)?;
    Ok(format!(
        "{URLHAUS_FEED_PREFIX}{}{URLHAUS_FEED_SUFFIX}",
        auth_key.trim()
    ))
}

/// The ClamAV feed URL when an Auth-Key is saved in the keyring.
pub fn configured_feed_url(ctx: &Context) -> AppResult<Option<String>> {
    let Some(key) = CredentialStore::new(ctx).get(Account::UrlhausAuthKey)? else {
        return Ok(None);
    };
    Ok(feed_url(&key).ok())
}

pub fn dispatch(ctx: &Context, action: &str, args: Value) -> AppResult<Value> {
    match action {
        "key_status" => {
            serde_json::to_value(CredentialStore::new(ctx).status(Account::UrlhausAuthKey)?)
                .map_err(|_| "Unable to serialize URLhaus key status".into())
        }
        "feed_url" => Ok(json!({ "url": configured_feed_url(ctx)? })),
        "key_save" => {
            let key = required_string(&args, "key")?;
            let store = CredentialStore::new(ctx);
            let write = store.set(Account::UrlhausAuthKey, key)?;
            let info = store.status(Account::UrlhausAuthKey)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                "message": write.warning.unwrap_or_else(|| "URLhaus Auth-Key saved".into()),
            }))
        }
        "key_delete" => {
            let deleted = CredentialStore::new(ctx).delete(Account::UrlhausAuthKey)?;
            let info = CredentialStore::new(ctx).status(Account::UrlhausAuthKey)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                "message": if deleted { "URLhaus Auth-Key deleted" } else { "No URLhaus Auth-Key was configured" },
            }))
        }
        _ => Err(format!("Unknown urlhaus action: {action}")),
    }
}

fn required_string<'a>(args: &'a Value, key: &str) -> AppResult<&'a str> {
    args.get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| format!("{key} is required"))
}

#[cfg(test)]
mod tests {
    use super::feed_url;

    #[test]
    fn feed_url_embeds_the_auth_key_in_the_export_path() {
        assert_eq!(
            feed_url("  ab12cd34ef56-ABCD ").expect("valid key"),
            "https://urlhaus-api.abuse.ch/v2/files/exports/ab12cd34ef56-ABCD/urlhaus_clamav.ndb"
        );
    }

    #[test]
    fn feed_url_rejects_separators_and_short_keys() {
        for key in [
            "",
            "a",
            "ab",
            "  ",
            "ab/c",
            "ab cd",
            "ab..",
            &"a".repeat(129),
        ] {
            assert!(feed_url(key).is_err(), "key {key:?} must be rejected");
        }
    }
}
