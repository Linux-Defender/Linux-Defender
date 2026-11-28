/** Pure helpers for combined website URL inspection. No network or side effects. */
export type UrlProvider = "urlscan" | "virustotal";
export type InspectionMode = UrlProvider | "both";

export type UrlscanSubmission = {
  uuid: string;
  url: string;
  visibility: "private" | "unlisted" | "public";
  result_url: string;
};
export type VirusTotalSubmission = {
  status: "clean" | "detected" | "pending" | "rate_limited" | "error";
  url: string;
  analysis_id?: string;
  detections: number;
  total_engines: number;
  analysis_url?: string;
  error_message?: string;
};

export type CombinedVerdict = "clean" | "detected" | "pending" | "partial" | "unavailable";

/** Services that can actually be used in the current mode. */
export function activeProviders(mode: InspectionMode): UrlProvider[] {
  return mode === "both" ? ["urlscan", "virustotal"] : [mode];
}

/**
 * Merge two independent reputation results conservatively.
 *
 * A urlscan submission only proves the URL was accepted for later review —
 * it carries no verdict. Only VirusTotal provides a machine-readable verdict,
 * so a "clean" combined result requires a VirusTotal clean verdict and no
 * failure from any active service. Errors, rate limits and pending results
 * are never clean.
 */
export function combinedVerdict(
  urlscan: UrlscanSubmission | null,
  virustotal: VirusTotalSubmission | null,
  providers: readonly UrlProvider[],
): CombinedVerdict {
  if (providers.length === 0) return "unavailable";
  if (!providers.includes("virustotal")) {
    // urlscan alone has only a submission receipt, never a verdict.
    return urlscan ? "partial" : "unavailable";
  }
  if (!virustotal) return urlscan ? "partial" : "unavailable";
  if (virustotal.status === "detected") return "detected";
  if (virustotal.status === "pending") return "pending";
  if (virustotal.status === "error" || virustotal.status === "rate_limited") return "partial";
  // A clean VirusTotal verdict is downgraded when the other active service
  // failed to answer, so two-service mode never overclaims completeness.
  if (providers.includes("urlscan") && !urlscan) return "partial";
  return "clean";
}

/** Static message IDs; the caller wraps them with _() and interpolates values. */
export function combinedMessageId(verdict: CombinedVerdict): string {
  switch (verdict) {
    case "detected": return "A service reported a suspicious URL; review both reports.";
    case "pending": return "The URL analysis is still processing; this is not a clean verdict.";
    case "partial": return "The URL was not checked successfully by every selected service; review the available report.";
    case "unavailable": return "No URL inspection service returned a result.";
    default: return "VirusTotal reported no detections; the urlscan result is available for review.";
  }
}
