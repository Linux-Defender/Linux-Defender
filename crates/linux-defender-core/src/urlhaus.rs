//! URLhaus ClamAV signature feed management.
//!
//! abuse.ch removed the anonymous `urlhaus.ndb` download and now requires a free
//! Auth-Key on its ClamAV export endpoint, so the key lives in the keyring and
//! the feed URL embeds it. Linux Defender ships a product-default key, which
//! [`configured_feed_url`] resolves so the frontend can pre-add the feed. The
//! [`dispatch`] actions remain the native API for reporting status and for
//! saving or disabling a user-supplied key.

use crate::credentials::{
    mask_api_key, Account, CredentialBackend, CredentialInfo, CredentialStatus, CredentialStore,
};
use crate::i18n::translate as tr;
use crate::{AppResult, Context};
use serde_json::{json, Value};

pub const URLHAUS_FEED_PREFIX: &str = "https://urlhaus-api.abuse.ch/v2/files/exports/";
pub const URLHAUS_FEED_SUFFIX: &str = "/urlhaus_clamav.ndb";
/// The abuse.ch Auth-Key supplied to Linux Defender. It is the product
/// default: the URLhaus feed is enabled automatically for every install. A key
/// saved through `urlhaus.key_save` replaces it, and `urlhaus.key_delete`
/// disables it until a new key is saved.
pub const URLHAUS_DEFAULT_AUTH_KEY: &str = "4bf8c78f1e2c86892a179019b21653d9c6f8469596e87501";
/// Set by `urlhaus.key_delete` so the product default does not come back on the
/// next start.
const URLHAUS_DEFAULT_KEY_DISABLED_SETTING: &str = "urlhaus_default_key_disabled";

/// The ClamAV signature export URL for a valid abuse.ch Auth-Key.
pub fn feed_url(auth_key: &str) -> AppResult<String> {
    crate::credentials::validate_urlhaus_auth_key(auth_key)?;
    Ok(format!(
        "{URLHAUS_FEED_PREFIX}{}{URLHAUS_FEED_SUFFIX}",
        auth_key.trim()
    ))
}

fn default_key_disabled(ctx: &Context) -> AppResult<bool> {
    Ok(ctx
        .settings()?
        .get(URLHAUS_DEFAULT_KEY_DISABLED_SETTING)
        .and_then(Value::as_bool)
        .unwrap_or(false))
}

/// The Auth-Key in use: the keyring key when one is saved, otherwise the
/// product-default key unless the user disabled it.
fn configured_auth_key(ctx: &Context) -> AppResult<Option<String>> {
    if let Some(key) = CredentialStore::new(ctx).get(Account::UrlhausAuthKey)? {
        return Ok(Some(key));
    }
    Ok((!default_key_disabled(ctx)?).then(|| URLHAUS_DEFAULT_AUTH_KEY.to_owned()))
}

/// The ClamAV feed URL when an Auth-Key is in use.
pub fn configured_feed_url(ctx: &Context) -> AppResult<Option<String>> {
    Ok(configured_auth_key(ctx)?.and_then(|key| feed_url(&key).ok()))
}

/// The key status reported by the native API. When no key is saved the product
/// default counts as saved (the feed is enabled by default).
fn status_info(ctx: &Context) -> AppResult<CredentialInfo> {
    let store = CredentialStore::new(ctx);
    if store.get(Account::UrlhausAuthKey)?.is_some() {
        return store.status(Account::UrlhausAuthKey);
    }
    let available = !default_key_disabled(ctx)?;
    Ok(CredentialInfo {
        present: available,
        backend: CredentialBackend::None,
        status: if available {
            CredentialStatus::Configured
        } else {
            CredentialStatus::NotConfigured
        },
        masked: available.then(|| mask_api_key(Some(URLHAUS_DEFAULT_AUTH_KEY))),
    })
}

pub fn dispatch(ctx: &Context, action: &str, args: Value) -> AppResult<Value> {
    match action {
        "key_status" => serde_json::to_value(status_info(ctx)?)
            .map_err(|_| "Unable to serialize URLhaus key status".into()),
        "feed_url" => Ok(json!({ "url": configured_feed_url(ctx)? })),
        "key_save" => {
            let key = required_string(&args, "key")?;
            let store = CredentialStore::new(ctx);
            let write = store.set(Account::UrlhausAuthKey, key)?;
            // A saved key replaces the product default.
            ctx.update_settings(json!({ URLHAUS_DEFAULT_KEY_DISABLED_SETTING: false }))?;
            let info = status_info(ctx)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                                // Translators: Keep `URLhaus` and `Auth-Key` unchanged; they are product/protocol names.
                "message": write.warning.unwrap_or_else(|| tr(ctx, "URLhaus Auth-Key saved")),
            }))
        }
        "key_delete" => {
            let deleted = CredentialStore::new(ctx).delete(Account::UrlhausAuthKey)?;
            // Disabling the product default so it does not come back.
            ctx.update_settings(json!({ URLHAUS_DEFAULT_KEY_DISABLED_SETTING: true }))?;
            let info = status_info(ctx)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                                "message": if deleted {
                    // Translators: Keep `URLhaus` and `Auth-Key` unchanged; they are product/protocol names.
                    tr(ctx, "URLhaus Auth-Key deleted")
                } else {
                    tr(ctx, "No URLhaus Auth-Key was configured")
                },
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
    use super::{
        configured_feed_url, dispatch, feed_url, URLHAUS_DEFAULT_AUTH_KEY, URLHAUS_FEED_PREFIX,
        URLHAUS_FEED_SUFFIX,
    };
    use crate::common::{Context, Paths};
    use serde_json::{json, Value};

    #[test]
    fn product_default_auth_key_is_valid_and_builds_the_feed_url() {
        crate::credentials::validate_urlhaus_auth_key(URLHAUS_DEFAULT_AUTH_KEY)
            .expect("the product default key must pass validation");
        assert_eq!(
            feed_url(URLHAUS_DEFAULT_AUTH_KEY).expect("valid key"),
            format!("{URLHAUS_FEED_PREFIX}{URLHAUS_DEFAULT_AUTH_KEY}{URLHAUS_FEED_SUFFIX}")
        );
    }

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

    fn test_context() -> (tempfile::TempDir, Context) {
        let root = tempfile::tempdir().expect("temp dir");
        let context = Context::with_paths(Paths {
            home: root.path().join("home"),
            config_dir: root.path().join("config"),
            data_dir: root.path().join("data"),
        })
        .expect("context");
        (root, context)
    }

    #[test]
    fn the_product_default_is_used_when_no_key_is_saved() {
        let (_root, ctx) = test_context();
        let status = dispatch(&ctx, "key_status", json!({})).expect("key_status");
        assert_eq!(status["present"], true);
        let expected = feed_url(URLHAUS_DEFAULT_AUTH_KEY).expect("default feed url");
        assert_eq!(
            dispatch(&ctx, "feed_url", json!({})).expect("feed_url")["url"],
            Value::String(expected.clone())
        );
        assert_eq!(
            configured_feed_url(&ctx).expect("configured feed url"),
            Some(expected)
        );
    }

    #[test]
    fn key_delete_disables_the_product_default() {
        let (_root, ctx) = test_context();
        let deleted = dispatch(&ctx, "key_delete", json!({})).expect("key_delete");
        assert_eq!(deleted["present"], false);
        assert_eq!(
            dispatch(&ctx, "feed_url", json!({})).expect("feed_url")["url"],
            Value::Null
        );
    }
}
