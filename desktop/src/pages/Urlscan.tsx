import { useCallback, useEffect, useState, type JSX } from "react";

import { isOpaqueApiToken, isPublicHttpUrl, notify, openExternal, request } from "../api";
import { Icon } from "../Icon";
import { _ } from "../i18n";
import { Modal } from "../Modal";

type Visibility = "private" | "unlisted" | "public";
type Provider = "urlscan" | "virustotal";
type KeyStatus = {
  present: boolean;
  backend: "keyring" | "plaintext_fallback" | "none";
  status: "configured" | "not_configured" | "locked" | "unavailable";
  masked?: string;
  message?: string;
};
type UrlscanSubmission = { uuid: string; url: string; visibility: Visibility; result_url: string };
type VirusTotalSubmission = {
  status: "clean" | "detected" | "pending" | "rate_limited" | "error";
  url: string;
  analysis_id?: string;
  detections: number;
  total_engines: number;
  analysis_url?: string;
  error_message?: string;
};

const URLSCAN_WEBSITE = "https://urlscan.io/";
const VIRUSTOTAL_UPLOAD_URL = "https://www.virustotal.com/gui/home/upload";

const VISIBILITIES: Array<{ id: Visibility; label: () => string }> = [
  { id: "private", label: () => _("Private — visible only to you") },
  { id: "unlisted", label: () => _("Unlisted — visible to urlscan Pro researchers") },
  { id: "public", label: () => _("Public — visible in urlscan search") },
];

function keyStatusLabel(status: KeyStatus | null): string {
  if (status?.present) {
    return _("Configured ({masked}) using {backend}", {
      masked: status.masked ?? _("masked"),
      backend: status.backend.replaceAll("_", " "),
    });
  }
  if (status?.status === "locked") return _("System keyring is locked");
  if (status?.status === "unavailable") return _("System keyring is unavailable");
  return _("Not configured");
}

export default function Urlscan({ active }: { active: boolean }): JSX.Element {
  const [provider, setProvider] = useState<Provider>("urlscan");
  const [urlscanStatus, setUrlscanStatus] = useState<KeyStatus | null>(null);
  const [virusTotalStatus, setVirusTotalStatus] = useState<KeyStatus | null>(null);
  const [urlscanKey, setUrlscanKey] = useState("");
  const [virusTotalKey, setVirusTotalKey] = useState("");
  const [url, setUrl] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("private");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [urlscanResult, setUrlscanResult] = useState<UrlscanSubmission | null>(null);
  const [virusTotalResult, setVirusTotalResult] = useState<VirusTotalSubmission | null>(null);
  const [noKeyActions, setNoKeyActions] = useState<Record<Provider, string>>({ urlscan: "none", virustotal: "none" });
  const [error, setError] = useState<string | null>(null);

  const refreshKeys = useCallback(async () => {
    const [urlscan, virusTotal, settings] = await Promise.allSettled([
      request<KeyStatus>("urlscan.key_status"),
      request<KeyStatus>("virustotal.key_status"),
      request<Record<string, unknown>>("settings.get"),
    ]);
    setUrlscanStatus(urlscan.status === "fulfilled"
      ? urlscan.value
      : { present: false, backend: "none", status: "unavailable" });
    setVirusTotalStatus(virusTotal.status === "fulfilled"
      ? virusTotal.value
      : { present: false, backend: "none", status: "unavailable" });
    if (settings.status === "fulfilled") {
      const value = settings.value;
      setNoKeyActions({
        urlscan: typeof value.urlscan_remember_no_key_action === "string" ? value.urlscan_remember_no_key_action : "none",
        virustotal: typeof value.virustotal_remember_no_key_action === "string" ? value.virustotal_remember_no_key_action : "none",
      });
    }
  }, []);

  useEffect(() => {
    if (active) void refreshKeys();
  }, [active, refreshKeys]);

  const saveKey = async (service: Provider): Promise<void> => {
    const key = service === "urlscan" ? urlscanKey.trim() : virusTotalKey.trim();
    if (!key) {
      notify(service === "urlscan" ? _("Enter your urlscan API key.") : _("Enter your VirusTotal API key."), "error");
      return;
    }
    if (service === "urlscan" && !isOpaqueApiToken(key)) {
      notify(_("The urlscan API key must be at least 16 characters and contain no spaces."), "error");
      return;
    }
    setBusy(true);
    try {
      const saved = await request<KeyStatus>(`${service}.key_save`, { key });
      if (service === "urlscan") setUrlscanStatus(saved);
      else setVirusTotalStatus(saved);
      if (service === "urlscan") setUrlscanKey("");
      else setVirusTotalKey("");
      const savedTone = saved.status === "locked" || saved.status === "unavailable" || saved.backend === "plaintext_fallback" ? "warning" : "success";
      notify(saved.message ?? _("API key saved"), savedTone);
    } catch (reason) {
      notify(_("Unable to save the API key: {error}", { error: String(reason) }), "error");
    } finally {
      setBusy(false);
    }
  };

  const deleteKey = async (service: Provider): Promise<void> => {
    setBusy(true);
    try {
      const deleted = await request<KeyStatus>(`${service}.key_delete`);
      if (service === "urlscan") {
        setUrlscanStatus(deleted);
        setUrlscanResult(null);
      } else {
        setVirusTotalStatus(deleted);
        setVirusTotalResult(null);
      }
      const deletedTone = deleted.status === "locked" || deleted.status === "unavailable" ? "warning" : "success";
      notify(deleted.message ?? _("API key deleted"), deletedTone);
    } catch (reason) {
      notify(_("Unable to delete the API key: {error}", { error: String(reason) }), "error");
    } finally {
      setBusy(false);
    }
  };

  const submit = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    setConfirm(false);
    try {
      if (provider === "urlscan") {
        const result = await request<UrlscanSubmission>("urlscan.submit", { url: url.trim(), visibility });
        setUrlscanResult(result);
        notify(_("URL submitted to urlscan"), "success");
      } else {
        const result = await request<VirusTotalSubmission>("virustotal.url_scan", {
          id: `vt-url-${crypto.randomUUID()}`,
          url: url.trim(),
        });
        setVirusTotalResult(result);
        if (result.error_message && result.status !== "pending") setError(result.error_message);
        else notify(_("URL analysis submitted to VirusTotal"), "success");
      }
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  };

  const visibilityDescription = visibility === "private"
    ? _("Private scans are visible only to you unless you share the result; urlscan retains them for a limited period.")
    : visibility === "unlisted"
      ? _("Unlisted scans are not in public search, but vetted urlscan Pro researchers can see them.")
      : _("Public scans are visible in urlscan search and may expose the submitted URL to others.");
  const currentStatus = provider === "urlscan" ? urlscanStatus : virusTotalStatus;
  const hasKey = currentStatus?.present === true;

  const review = (): void => {
    setError(null);
    if (hasKey) {
      setConfirm(true);
      return;
    }
    if (currentStatus?.status !== "not_configured") {
      setError(provider === "urlscan"
        ? _("Enter your urlscan API key before submitting a URL.")
        : _("Enter your VirusTotal API key before submitting a URL."));
      return;
    }
    const action = provider === "urlscan" ? noKeyActions.urlscan : noKeyActions.virustotal;
    if (action === "open_website") {
      void openExternal(provider === "urlscan" ? URLSCAN_WEBSITE : VIRUSTOTAL_UPLOAD_URL)
        .then(() => notify(provider === "urlscan"
          ? _("Opened the urlscan.io website in your browser")
          : _("Opened the VirusTotal upload page in your browser"), "info"))
        .catch((reason: unknown) => setError(String(reason)));
      return;
    }
    if (action === "prompt") {
      notify(provider === "urlscan"
        ? _("Configure a urlscan API key in Preferences before submitting a URL.")
        : _("Configure a VirusTotal API key in Preferences before starting this scan."), "error");
      return;
    }
    setError(provider === "urlscan"
      ? _("Enter your urlscan API key before submitting a URL.")
      : _("Enter your VirusTotal API key before submitting a URL."));
  };

  return <div className="settings-preferences urlscan-page">
    <h2>{_("Website URL inspection")}</h2>
    <div className="segmented-control" role="group" aria-label={_("URL scan service")}>
      <button type="button" aria-pressed={provider === "urlscan"} onClick={() => { setProvider("urlscan"); setError(null); }}>{_("urlscan.io")}</button>
      <button type="button" aria-pressed={provider === "virustotal"} onClick={() => { setProvider("virustotal"); setError(null); }}>{_("VirusTotal")}</button>
    </div>

    <section className="preference-section form-section">
      <h3 className="section-heading">{provider === "urlscan" ? _("urlscan.io account") : _("VirusTotal account")}</h3>
      <p>{_("API keys are stored in the operating system keyring when available and are never sent to the interface.")}</p>
      <div className="preference-row setting-row"><span className="row-copy"><strong>{_("Key status")}</strong><small>{keyStatusLabel(currentStatus)}</small></span><button className="button" type="button" onClick={() => void refreshKeys()}>{_("Refresh")}</button></div>
      {!hasKey && <label className="field"><span>{_("Personal API key")}</span><input type="password" autoComplete="off" spellCheck={false} value={provider === "urlscan" ? urlscanKey : virusTotalKey} onChange={(event) => provider === "urlscan" ? setUrlscanKey(event.currentTarget.value) : setVirusTotalKey(event.currentTarget.value)} placeholder={provider === "urlscan" ? _("Paste your urlscan API key") : _("Paste your VirusTotal API key")} /></label>}
      <div className="button-row">
        {!hasKey ? <button className="button primary" type="button" disabled={busy || !(provider === "urlscan" ? urlscanKey.trim() : virusTotalKey.trim())} onClick={() => void saveKey(provider)}>{_("Save key")}</button> : <button className="button" type="button" disabled={busy} onClick={() => void deleteKey(provider)}>{_("Delete key")}</button>}
        <button className="button" type="button" onClick={() => void openExternal(provider === "urlscan" ? "https://urlscan.io/user/signup" : "https://www.virustotal.com/gui/my-apikey")}>{_("Get an API key")}</button>
      </div>
    </section>

    <section className="preference-section form-section">
      <h3 className="section-heading">{_("Submit a website for inspection")}</h3>
      <p>{provider === "urlscan"
        ? _("urlscan visits the website in a remote browser and records its page activity. This is not a local file scan or an antivirus verdict.")
        : _("VirusTotal checks the URL with multiple security engines and blocklists. This is a remote reputation analysis, not a local file scan.")}</p>
      <label className="field"><span>{_("Website URL")}</span><input type="url" autoComplete="url" spellCheck={false} value={url} onChange={(event) => setUrl(event.currentTarget.value)} placeholder="https://example.org/" /></label>
      {provider === "urlscan" && <><label className="field"><span>{_("Result visibility")}</span><select value={visibility} onChange={(event) => setVisibility(event.currentTarget.value as Visibility)}>{VISIBILITIES.map((option) => <option value={option.id} key={option.id}>{option.label()}</option>)}</select></label><p className="muted">{visibilityDescription}</p></>}
      <div className="privacy-notice notice warning" role="note"><Icon name="warning" /><span>{provider === "urlscan"
        ? _("urlscan receives the complete URL, including its query string, and visits it. Never submit login links, session tokens, private/internal URLs, or confidential information.")
        : _("VirusTotal adds submitted and queried URLs to its dataset, where they may be shared with its community and security partners. Never submit login links, session tokens, private/internal URLs, or confidential information.")}</span></div>
      {error ? <p className="notice error" role="alert">{error}</p> : null}
      {provider === "urlscan" && urlscanResult ? <div className="notice success" role="status"><div><strong>{_("Submission accepted")}</strong><p>{_("Visibility: {visibility}", { visibility: urlscanResult.visibility })}</p></div><button className="button" type="button" onClick={() => void openExternal(urlscanResult.result_url)}><Icon name="external-link" />{_("Open urlscan result")}</button></div> : null}
      {provider === "virustotal" && virusTotalResult ? <div className={`notice ${virusTotalResult.status === "detected" ? "warning" : virusTotalResult.status === "error" || virusTotalResult.status === "rate_limited" ? "error" : "success"}`} role="status"><div><strong>{virusTotalResult.status === "detected" ? _("VirusTotal reported detections") : virusTotalResult.status === "clean" ? _("Analysis complete — no detections reported") : virusTotalResult.status === "pending" ? _("Analysis is still processing") : virusTotalResult.status === "rate_limited" ? _("VirusTotal rate limit reached") : _("VirusTotal analysis failed")}</strong>{virusTotalResult.status === "clean" || virusTotalResult.status === "detected" ? <p>{_("{detections} of {total} URL engines reported suspicious or malicious", { detections: virusTotalResult.detections, total: virusTotalResult.total_engines })}</p> : null}{virusTotalResult.error_message ? <p>{virusTotalResult.error_message}</p> : null}</div>{virusTotalResult.analysis_url ? <button className="button" type="button" onClick={() => void openExternal(virusTotalResult.analysis_url!)}><Icon name="external-link" />{_("Open VirusTotal analysis")}</button> : null}</div> : null}
      <div className="button-row"><button className="button primary" type="button" disabled={busy || !isPublicHttpUrl(url)} onClick={review}>{busy ? _("Submitting…") : _("Review submission")}</button></div>
    </section>
    {confirm ? <Modal title={provider === "urlscan" ? _("Confirm urlscan submission") : _("Confirm VirusTotal URL submission")} busy={busy} onClose={() => { if (!busy) setConfirm(false); }}>
      <p>{provider === "urlscan"
        ? _("urlscan will visit this URL and store page activity. The service receives the full URL, including its query string.")
        : _("VirusTotal will submit this URL for analysis and add it to its dataset, where it may be shared with its community and security partners.")}</p>
      <dl className="about-details"><dt>{_("URL")}</dt><dd><code className="path-value">{url.trim()}</code></dd>{provider === "urlscan" ? <><dt>{_("Visibility")}</dt><dd>{visibility}</dd></> : null}</dl>
      {provider === "urlscan" ? <p>{visibilityDescription}</p> : null}
      <div className="dialog-actions"><button className="button" type="button" disabled={busy} onClick={() => setConfirm(false)}>{_("Cancel")}</button><button className="button primary" type="button" disabled={busy} onClick={() => void submit()}>{busy ? _("Submitting…") : _("Submit URL")}</button></div>
    </Modal> : null}
  </div>;
}
