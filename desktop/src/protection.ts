import { _, ngettext } from "./i18n";

export type TrendPoint = { label: string; scans: number; threats: number };
export type Protection = { level: string; message: string; lastScanTimestamp?: string; lastScanAgeHours?: number };
export type Statistics = {
  totalScans: number;
  filesScanned: number;
  threatsDetected: number;
  cleanScans: number;
  averageDuration: number;
  startDate?: string;
  endDate?: string;
  trends: TrendPoint[];
  protection: Protection;
};

function fieldValue(object: object, snake: string, camel: string): unknown {
  if (Object.prototype.hasOwnProperty.call(object, snake)) return Reflect.get(object, snake);
  if (Object.prototype.hasOwnProperty.call(object, camel)) return Reflect.get(object, camel);
  return undefined;
}

function optionalNumber(record: object, snake: string, camel: string): { value: number } | null {
  const value = fieldValue(record, snake, camel);
  return typeof value === "number" && Number.isFinite(value) ? { value } : null;
}

function readNumber(record: object, snake: string, camel: string): number {
  return optionalNumber(record, snake, camel)?.value ?? 0;
}

function readText(record: object, snake: string, camel: string): string | undefined {
  const value = fieldValue(record, snake, camel);
  return typeof value === "string" ? value : undefined;
}

function parseTrend(value: unknown): TrendPoint[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((point) => {
    if (!point || typeof point !== "object") return [];
    const label = readText(point, "label", "label") ?? readText(point, "date", "date");
    if (!label) return [];
    return [{ label, scans: readNumber(point, "scans", "scanCount"), threats: readNumber(point, "threats", "threatCount") }];
  });
}

/** Parse the `logs.statistics` payload, tolerating both snake_case and camelCase keys. */
export function parseStatistics(value: unknown): Statistics | null {
  if (!value || typeof value !== "object") return null;
  const protectionValue = fieldValue(value, "protection_status", "protectionStatus");
  if (!protectionValue || typeof protectionValue !== "object") return null;
  const totalScans = optionalNumber(value, "total_scans", "totalScans");
  const filesScanned = optionalNumber(value, "files_scanned", "filesScanned");
  const threatsDetected = optionalNumber(value, "threats_detected", "threatsDetected");
  const cleanScans = optionalNumber(value, "clean_scans", "cleanScans");
  const averageDuration = optionalNumber(value, "average_duration", "averageDuration");
  const level = readText(protectionValue, "level", "level");
  const message = readText(protectionValue, "message", "message");
  const trends = fieldValue(value, "trends", "trends");
  if (!level || message === undefined || !Array.isArray(trends)) return null;
  const startDate = readText(value, "start_date", "startDate");
  const endDate = readText(value, "end_date", "endDate");
  const lastScanTimestamp = readText(protectionValue, "last_scan_timestamp", "lastScanTimestamp");
  const lastScanAgeHours = optionalNumber(protectionValue, "last_scan_age_hours", "lastScanAgeHours");
  return {
    totalScans: totalScans?.value ?? 0,
    filesScanned: filesScanned?.value ?? 0,
    threatsDetected: threatsDetected?.value ?? 0,
    cleanScans: cleanScans?.value ?? 0,
    averageDuration: averageDuration?.value ?? 0,
    ...(startDate ? { startDate } : {}),
    ...(endDate ? { endDate } : {}),
    trends: parseTrend(trends),
    protection: {
      level,
      message,
      ...(lastScanTimestamp ? { lastScanTimestamp } : {}),
      ...(lastScanAgeHours !== null ? { lastScanAgeHours: lastScanAgeHours.value } : {}),
    },
  };
}

export function formatDuration(seconds: number): string {
  if (seconds <= 0) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function normalizedTimestamp(value: string): string {
  return value.replace(/(\.\d{3})\d+(?=(?:Z|[+-]\d{2}:?\d{2})?$)/, "$1");
}

export function formatDateTime(value: string): string {
  const date = new Date(normalizedTimestamp(value));
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function formatDate(value: string): string {
  const dateOnly = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateOnly) {
    return new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3])).toLocaleDateString();
  }
  const date = new Date(normalizedTimestamp(value));
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

export function formatLastScan(protection: Protection): string {
  if (!protection.lastScanTimestamp) return _("No scans recorded");
  const formatted = formatDateTime(protection.lastScanTimestamp);
  if (protection.lastScanAgeHours === undefined) return formatted;
  if (protection.lastScanAgeHours < 1) return `${formatted} (${_("less than an hour ago")})`;
  if (protection.lastScanAgeHours < 24) {
    const hours = Math.floor(protection.lastScanAgeHours);
    return `${formatted} (${ngettext("{count} hour ago", "{count} hours ago", hours, { count: hours })})`;
  }
  if (protection.lastScanAgeHours < 168) {
    const days = Math.floor(protection.lastScanAgeHours / 24);
    return `${formatted} (${ngettext("{count} day ago", "{count} days ago", days, { count: days })})`;
  }
  const weeks = Math.floor(protection.lastScanAgeHours / 168);
  return `${formatted} (${ngettext("{count} week ago", "{count} weeks ago", weeks, { count: weeks })})`;
}

export function protectionLabel(level: string): string {
  if (level === "protected") return _("Protected");
  if (level === "at_risk") return _("At Risk");
  if (level === "unprotected") return _("Unprotected");
  if (level === "no_data") return _("No Data");
  if (level === "error") return _("Error");
  return _("Unknown");
}

export function protectionMessage(message: string): string {
  if (message === "No scans performed yet") return _("No scans performed yet");
  if (message === "Last scan was over 30 days ago") return _("Last scan was over 30 days ago");
  if (message === "Last scan was over a week ago") return _("Last scan was over a week ago");
  if (message === "Virus definitions are over 7 days old") return _("Virus definitions are over 7 days old");
  if (message === "Virus definitions are over 1 day old") return _("Virus definitions are over 1 day old");
  if (message === "System is protected") return _("System is protected");
  return message;
}
