import { useCallback, useEffect, useState } from "react";
import { navigate, notify, onEvent, request } from "../api";
import { Icon } from "../Icon";
import { _, ngettext } from "../i18n";
import {
  formatLastScan,
  parseStatistics,
  protectionLabel,
  protectionMessage,
  type Statistics,
} from "../protection";
import { useActivityRefresh } from "./useActivityRefresh";

type ScannerStatus = {
  available?: boolean;
  backend?: string;
  active_backend?: string;
  database_available?: boolean;
  database_error?: string;
  error?: string;
};

function readableError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function parseQuarantineCount(value: unknown): number | null {
  if (!value || typeof value !== "object") return null;
  const count = "entry_count" in value ? Reflect.get(value, "entry_count") : Reflect.get(value, "entryCount");
  return typeof count === "number" && Number.isFinite(count) ? count : null;
}

function availabilityBadge(available: boolean | undefined) {
  if (available === undefined) {
    return <span className="status-badge unknown">{_("Unknown")}</span>;
  }
  return <span className={`status-badge ${available ? "success" : "error"}`}>{available ? _("Available") : _("Unavailable")}</span>;
}

export default function Overview({ active }: { active: boolean }) {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [scanner, setScanner] = useState<ScannerStatus | null>(null);
  const [quarantineCount, setQuarantineCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [statisticsResult, scannerResult, quarantineResult] = await Promise.allSettled([
      request<unknown>("logs.statistics", { timeframe: "all" }),
      request<ScannerStatus>("scanner.status"),
      request<unknown>("quarantine.list", {
        schema: "ui",
        limit: 20,
        search: "",
        search_locale: Intl.DateTimeFormat().resolvedOptions().locale,
        cursor: null,
      }),
    ]);

    if (statisticsResult.status === "fulfilled") {
      const parsed = parseStatistics(statisticsResult.value);
      setStatistics(parsed);
      if (!parsed) setError(_("Linux Defender received invalid statistics data."));
    } else {
      setError(readableError(statisticsResult.reason));
    }

    setScanner(scannerResult.status === "fulfilled" ? scannerResult.value : null);
    setQuarantineCount(quarantineResult.status === "fulfilled" ? parseQuarantineCount(quarantineResult.value) : null);
    setLoading(false);
  }, []);

  const refreshOverview = useActivityRefresh(active, loadOverview);

  useEffect(() => {
    let dispose: (() => void) | undefined;
    let listening = true;
    void onEvent((event) => {
      if (event.event === "scan-complete") void refreshOverview(false);
    }).then((unlisten) => {
      if (listening) dispose = unlisten;
      else unlisten();
    }).catch((listenError: unknown) => notify(
      _("Statistics updates are unavailable: {error}", { error: readableError(listenError) }),
      "warning",
    ));
    return () => {
      listening = false;
      dispose?.();
    };
  }, [refreshOverview]);

  const protection = statistics?.protection ?? (error
    ? { level: "error", message: _("Unable to load statistics") }
    : { level: "checking", message: _("Checking protection status") });
  const protectionStatus = statistics || error ? protectionLabel(protection.level) : _("Loading…");
  const cards = statistics ? [
    { label: _("Total Scans"), value: statistics.totalScans.toLocaleString(), description: _("Number of scans performed"), alert: false },
    { label: _("Files Scanned"), value: statistics.filesScanned.toLocaleString(), description: _("Total files checked"), alert: false },
    { label: _("Threats Detected"), value: statistics.threatsDetected.toLocaleString(), description: _("Malware and suspicious files found"), alert: statistics.threatsDetected > 0 },
    { label: _("Clean Scans"), value: statistics.cleanScans.toLocaleString(), description: _("Scans with no threats found"), alert: false },
  ] : [];

  return <main className="page overview-page">
    <header className="page-header">
      <div><h1>{_("Overview")}</h1><p>{_("Your protection at a glance.")}</p></div>
      <button className="button" type="button" onClick={() => void refreshOverview()} disabled={loading}>
        <Icon name="refresh" />{_("Refresh")}
      </button>
    </header>

    {error && <p className="error-banner" role="alert">{_("Unable to load statistics")}: {error}</p>}

    <section className={`overview-hero ${protection.level}`} aria-labelledby="overview-protection-heading">
      <div className="overview-hero-mark" aria-hidden="true"><Icon name="shield" /></div>
      <div className="overview-hero-copy">
        <h2 id="overview-protection-heading">{_("Protection Status")}</h2>
        <p className="overview-hero-message">{protectionMessage(protection.message)}</p>
        <p className="overview-hero-meta">
          <span>{_("Last Scan")}</span>
          <span>{statistics ? formatLastScan(protection) : "—"}</span>
        </p>
      </div>
      <div className="overview-hero-actions">
        <span className={`status-badge ${protection.level}`}>
          {protectionStatus}
        </span>
        <div className="actions">
          <button className="button primary" type="button" onClick={() => navigate("scan", { quickScan: true })}>
            <Icon name="play" />{_("Start Scan")}
          </button>
          <button className="button" type="button" onClick={() => navigate("statistics")}>
            {_("Statistics")}
          </button>
        </div>
      </div>
    </section>

    <section aria-labelledby="overview-statistics-heading">
      <header className="section-header">
        <div><h2 id="overview-statistics-heading">{_("Scan Statistics")}</h2></div>
      </header>
      {statistics
        ? <div className="statistics-grid">
          {cards.map((card) => <article className={`metric-card${card.alert ? " error threat-detected" : ""}`} key={card.label}>
            <h3 className="row-title">{card.label}</h3>
            <strong>{card.value}</strong>
            <p className="row-description">{card.description}</p>
          </article>)}
        </div>
        : <p className="muted">{_("Loading…")}</p>}
    </section>

    <div className="overview-columns">
      <section aria-labelledby="overview-checks-heading">
        <header className="section-header">
          <div><h2 id="overview-checks-heading">{_("Protection checks")}</h2></div>
        </header>
        <div className="grouped-list overview-checks">
          <div className="group-row overview-check">
            <span className="overview-check-mark" aria-hidden="true"><Icon name="components" /></span>
            <div className="row-copy">
              <span className="row-title">{_("Scanner engine")}</span>
              <span className="row-description">{scanner?.backend || scanner?.active_backend || _("Unknown")}</span>
            </div>
            {availabilityBadge(scanner?.available)}
          </div>
          <div className="group-row overview-check">
            <span className="overview-check-mark" aria-hidden="true"><Icon name="database" /></span>
            <div className="row-copy">
              <span className="row-title">{_("Virus definitions")}</span>
              {scanner?.database_error && <span className="row-description">{scanner.database_error}</span>}
            </div>
            {availabilityBadge(scanner?.database_available)}
          </div>
          <div className="group-row overview-check">
            <span className="overview-check-mark" aria-hidden="true"><Icon name="logs" /></span>
            <div className="row-copy">
              <span className="row-title">{_("Last Scan")}</span>
              <span className="row-description">{statistics ? formatLastScan(protection) : "—"}</span>
            </div>
          </div>
          <div className="group-row overview-check">
            <span className="overview-check-mark" aria-hidden="true"><Icon name="shield" /></span>
            <div className="row-copy">
              <span className="row-title">{_("Quarantine")}</span>
              <span className="row-description">
                {quarantineCount === null
                  ? "—"
                  : ngettext("{count} file", "{count} files", quarantineCount, { count: quarantineCount })}
              </span>
            </div>
            <button className="button" type="button" onClick={() => navigate("quarantine")}>{_("Open")}</button>
          </div>
        </div>
      </section>

      <section aria-labelledby="overview-actions-heading">
        <header className="section-header">
          <div><h2 id="overview-actions-heading">{_("Quick Actions")}</h2></div>
        </header>
        <div className="quick-actions">
          <button className="group-row" type="button" onClick={() => navigate("scan", { quickScan: true })}>
            {_("Quick Scan")}<span>{_("Fast scan of the Downloads folder for quick threat detection")}</span>
          </button>
          <button className="group-row" type="button" onClick={() => navigate("database")}>
            {_("Update Database")}<span>{_("Keep virus definitions current")}</span>
          </button>
          <button className="group-row" type="button" onClick={() => navigate("logs")}>
            {_("View Scan Logs")}<span>{_("See detailed scan history")}</span>
          </button>
          <button className="group-row" type="button" onClick={() => navigate("quarantine")}>
            {_("Quarantine")}<span>{_("Manage quarantined files")}</span>
          </button>
        </div>
      </section>
    </div>
  </main>;
}
