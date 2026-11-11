use clamui_core::credentials::{attributes, Account, URLSCAN_API_KEY};
use clamui_core::urlscan::{
    validate_url, HttpResponse, HttpTransport, UrlscanClient, Visibility, URLSCAN_API_URL,
};
use std::sync::{Arc, Mutex};

type CapturedSubmissions = Arc<Mutex<Vec<(String, String, Visibility)>>>;

#[derive(Clone)]
struct FakeHttp {
    captured: CapturedSubmissions,
    response: HttpResponse,
}

impl HttpTransport for FakeHttp {
    fn submit(
        &self,
        api_key: &str,
        url: &str,
        visibility: Visibility,
    ) -> Result<HttpResponse, String> {
        self.captured
            .lock()
            .unwrap()
            .push((api_key.to_owned(), url.to_owned(), visibility));
        Ok(self.response.clone())
    }
}

fn fake(response: &str, status: u16) -> (FakeHttp, CapturedSubmissions) {
    let captured = Arc::new(Mutex::new(Vec::new()));
    (
        FakeHttp {
            captured: Arc::clone(&captured),
            response: HttpResponse {
                status,
                body: response.as_bytes().to_vec(),
            },
        },
        captured,
    )
}

#[test]
fn validates_http_urls_and_rejects_credentials_and_non_web_schemes() {
    assert_eq!(
        validate_url(" https://example.test/path?q=token ")
            .unwrap()
            .as_str(),
        "https://example.test/path?q=token"
    );
    for invalid in [
        "",
        "not a URL",
        "file:///etc/passwd",
        "https://user:password@example.test/",
        "https://example.test/\nmalformed",
    ] {
        assert!(validate_url(invalid).is_err(), "accepted {invalid:?}");
    }
}

#[test]
fn submission_sends_selected_visibility_and_builds_only_the_official_result_url() {
    let (transport, captured) = fake(
        r#"{"uuid":"68e26c59-2eae-437b-aeb1-cf750fafe7d7","visibility":"private"}"#,
        200,
    );
    let client = UrlscanClient::with_transport("test-api-key", Box::new(transport)).unwrap();
    let result = client
        .submit(
            "https://example.test/account?session=secret",
            Visibility::Private,
        )
        .unwrap();

    assert_eq!(
        URLSCAN_API_URL, "https://urlscan.io/api/v1/scan",
        "submissions must go to the official HTTPS API"
    );
    assert_eq!(result.visibility, Visibility::Private);
    assert_eq!(
        result.result_url,
        "https://urlscan.io/result/68e26c59-2eae-437b-aeb1-cf750fafe7d7/"
    );
    assert_eq!(
        *captured.lock().unwrap(),
        vec![(
            "test-api-key".into(),
            "https://example.test/account?session=secret".into(),
            Visibility::Private,
        )]
    );
}

#[test]
fn rejects_http_errors_and_malformed_scan_identifiers() {
    let (rate_limited, _) = fake("{}", 429);
    let client = UrlscanClient::with_transport("test-api-key", Box::new(rate_limited)).unwrap();
    assert!(client
        .submit("https://example.test", Visibility::Private)
        .unwrap_err()
        .contains("rate limit"));

    let (malformed, _) = fake(r#"{"uuid":"not-a-uuid"}"#, 200);
    let client = UrlscanClient::with_transport("test-api-key", Box::new(malformed)).unwrap();
    assert!(client
        .submit("https://example.test", Visibility::Private)
        .unwrap_err()
        .contains("invalid scan identifier"));
}

#[test]
fn empty_api_keys_are_rejected_and_secret_settings_are_never_returned_to_the_ui() {
    assert!(UrlscanClient::with_transport(" ", Box::new(fake("{}", 200).0)).is_err());
    assert_eq!(Account::UrlscanApiKey.username(), URLSCAN_API_KEY);
    assert_eq!(
        attributes(Account::UrlscanApiKey)["username"],
        URLSCAN_API_KEY
    );
    let settings = serde_json::json!({
        "urlscan_api_key": "never-return-this",
        "other_setting": true
    });
    let frontend = clamui_core::settings::frontend_settings(settings);
    assert!(frontend.get("urlscan_api_key").is_none());
    assert_eq!(frontend["other_setting"], true);
}
