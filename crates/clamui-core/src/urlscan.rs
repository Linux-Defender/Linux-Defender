use crate::credentials::{Account, CredentialStore};
use crate::{AppResult, Context};
use reqwest::blocking::Client;
use reqwest::redirect::Policy;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::time::Duration;
use url::Url;
use uuid::Uuid;

pub const URLSCAN_API_URL: &str = "https://urlscan.io/api/v1/scan";
const URLSCAN_TIMEOUT: Duration = Duration::from_secs(30);
const URLSCAN_MAX_URL_BYTES: usize = 8192;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Visibility {
    Private,
    Unlisted,
    Public,
}

impl Visibility {
    fn as_str(self) -> &'static str {
        match self {
            Self::Private => "private",
            Self::Unlisted => "unlisted",
            Self::Public => "public",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Submission {
    pub uuid: String,
    pub url: String,
    pub visibility: Visibility,
    pub result_url: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HttpResponse {
    pub status: u16,
    pub body: Vec<u8>,
}

pub trait HttpTransport: Send + Sync {
    fn submit(
        &self,
        api_key: &str,
        url: &str,
        visibility: Visibility,
    ) -> Result<HttpResponse, String>;
}

struct ReqwestTransport {
    client: Client,
}

impl ReqwestTransport {
    fn new() -> AppResult<Self> {
        let client = Client::builder()
            .timeout(URLSCAN_TIMEOUT)
            .no_proxy()
            .redirect(Policy::none())
            .user_agent(concat!("LinuxDefender/", env!("CARGO_PKG_VERSION")))
            .build()
            .map_err(|_| "Unable to initialize urlscan connection")?;
        Ok(Self { client })
    }
}

impl HttpTransport for ReqwestTransport {
    fn submit(
        &self,
        api_key: &str,
        url: &str,
        visibility: Visibility,
    ) -> Result<HttpResponse, String> {
        let response = self
            .client
            .post(URLSCAN_API_URL)
            .header("API-Key", api_key)
            .json(&json!({ "url": url, "visibility": visibility.as_str() }))
            .send()
            .map_err(|error| {
                if error.is_timeout() {
                    "urlscan request timed out".to_owned()
                } else {
                    "Unable to connect to urlscan".to_owned()
                }
            })?;
        let status = response.status().as_u16();
        let body = response
            .bytes()
            .map_err(|_| "Unable to read urlscan response")?
            .to_vec();
        Ok(HttpResponse { status, body })
    }
}

pub struct UrlscanClient {
    api_key: String,
    transport: Box<dyn HttpTransport>,
}

impl UrlscanClient {
    pub fn new(api_key: &str) -> AppResult<Self> {
        if api_key.trim().is_empty() {
            return Err("urlscan API key is not configured".into());
        }
        Ok(Self {
            api_key: api_key.to_owned(),
            transport: Box::new(ReqwestTransport::new()?),
        })
    }

    pub fn with_transport(api_key: &str, transport: Box<dyn HttpTransport>) -> AppResult<Self> {
        if api_key.trim().is_empty() {
            return Err("urlscan API key is not configured".into());
        }
        Ok(Self {
            api_key: api_key.to_owned(),
            transport,
        })
    }

    pub fn submit(&self, input: &str, visibility: Visibility) -> AppResult<Submission> {
        let url = validate_url(input)?;
        let response = self
            .transport
            .submit(&self.api_key, url.as_str(), visibility)?;
        if !(200..300).contains(&response.status) {
            return Err(match response.status {
                401 | 403 => "urlscan rejected the API key or its permissions".into(),
                429 => "urlscan rate limit reached; try again later".into(),
                status => format!("urlscan returned HTTP {status}"),
            });
        }
        let accepted: AcceptedResponse = serde_json::from_slice(&response.body)
            .map_err(|_| "urlscan returned an invalid response")?;
        let uuid = Uuid::parse_str(&accepted.uuid)
            .map_err(|_| "urlscan returned an invalid scan identifier")?
            .to_string();
        let visibility = accepted.visibility.unwrap_or(visibility);
        Ok(Submission {
            result_url: format!("https://urlscan.io/result/{uuid}/"),
            uuid,
            url: url.to_string(),
            visibility,
        })
    }
}

#[derive(Deserialize)]
struct AcceptedResponse {
    uuid: String,
    visibility: Option<Visibility>,
}

pub fn validate_url(input: &str) -> AppResult<Url> {
    let input = input.trim();
    if input.is_empty()
        || input.len() > URLSCAN_MAX_URL_BYTES
        || input.chars().any(char::is_control)
    {
        return Err("Enter a valid HTTP or HTTPS URL".into());
    }
    let url = Url::parse(input).map_err(|_| "Enter a valid HTTP or HTTPS URL")?;
    if !matches!(url.scheme(), "http" | "https")
        || url.host_str().is_none()
        || !url.username().is_empty()
        || url.password().is_some()
    {
        return Err("URL must use HTTP or HTTPS and cannot contain login credentials".into());
    }
    Ok(url)
}

pub fn dispatch(ctx: &Context, action: &str, args: Value) -> AppResult<Value> {
    match action {
        "key_status" => {
            serde_json::to_value(CredentialStore::new(ctx).status(Account::UrlscanApiKey)?)
                .map_err(|_| "Unable to serialize urlscan key status".into())
        }
        "key_save" => {
            let key = required_string(&args, "key")?;
            let store = CredentialStore::new(ctx);
            let write = store.set(Account::UrlscanApiKey, key)?;
            let info = store.status(Account::UrlscanApiKey)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                "message": write.warning.unwrap_or_else(|| "urlscan API key saved".into()),
            }))
        }
        "key_delete" => {
            let deleted = CredentialStore::new(ctx).delete(Account::UrlscanApiKey)?;
            let info = CredentialStore::new(ctx).status(Account::UrlscanApiKey)?;
            Ok(json!({
                "present": info.present,
                "backend": info.backend,
                "status": info.status,
                "masked": info.masked,
                "message": if deleted { "urlscan API key deleted" } else { "No urlscan API key was configured" },
            }))
        }
        "submit" => {
            let url = required_string(&args, "url")?;
            let visibility = args
                .get("visibility")
                .and_then(Value::as_str)
                .and_then(|value| serde_json::from_value(json!(value)).ok())
                .ok_or_else(|| "Choose a valid urlscan visibility".to_owned())?;
            let key = CredentialStore::new(ctx)
                .get(Account::UrlscanApiKey)?
                .ok_or_else(|| {
                    "Set a personal urlscan API key before submitting a URL".to_owned()
                })?;
            let result = UrlscanClient::new(&key)?.submit(url, visibility)?;
            serde_json::to_value(result).map_err(|_| "Unable to serialize urlscan result".into())
        }
        _ => Err(format!("Unknown urlscan action: {action}")),
    }
}

fn required_string<'a>(args: &'a Value, key: &str) -> AppResult<&'a str> {
    args.get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| format!("{key} is required"))
}
