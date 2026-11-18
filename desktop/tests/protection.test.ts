import { describe, expect, mock, test } from "bun:test";

mock.module("../src/api", () => ({ request: async () => ({}) }));

const { parseStatistics, protectionLabel, protectionMessage, formatDuration } = await import("../src/protection");

const protection = { level: "protected", message: "System is protected", last_scan_timestamp: "2026-11-16T10:00:00Z", last_scan_age_hours: 5 };

describe("parseStatistics", () => {
  test("accepts a fresh profile whose totals are all zero", () => {
    const parsed = parseStatistics({
      total_scans: 0,
      files_scanned: 0,
      threats_detected: 0,
      clean_scans: 0,
      average_duration: 0,
      trends: [],
      protection_status: { level: "no_data", message: "No scans performed yet" },
    });

    expect(parsed).not.toBeNull();
    expect(parsed?.totalScans).toBe(0);
    expect(parsed?.averageDuration).toBe(0);
    expect(parsed?.protection.level).toBe("no_data");
    expect(parsed?.trends).toEqual([]);
  });

  test("accepts camelCase payloads and trend counts", () => {
    const parsed = parseStatistics({
      totalScans: 3,
      filesScanned: 120,
      threatsDetected: 1,
      cleanScans: 2,
      averageDuration: 12.5,
      trends: [{ label: "2026-11-16", scans: 2, threats: 1 }],
      protectionStatus: protection,
    });

    expect(parsed).toEqual({
      totalScans: 3,
      filesScanned: 120,
      threatsDetected: 1,
      cleanScans: 2,
      averageDuration: 12.5,
      trends: [{ label: "2026-11-16", scans: 2, threats: 1 }],
      protection: { level: "protected", message: "System is protected", lastScanTimestamp: "2026-11-16T10:00:00Z", lastScanAgeHours: 5 },
    });
  });

  test("keeps a dark protection message so the view can localize it", () => {
    const parsed = parseStatistics({
      total_scans: 1,
      files_scanned: 1,
      threats_detected: 0,
      clean_scans: 1,
      average_duration: 1,
      trends: [],
      protection_status: { level: "at_risk", message: "Virus definitions are over 7 days old" },
    });

    expect(protectionMessage(parsed?.protection.message ?? "")).toBe("Virus definitions are over 7 days old");
  });

  test("rejects payloads without a protection status or trend list", () => {
    const totals = { total_scans: 1, files_scanned: 1, threats_detected: 0, clean_scans: 1, average_duration: 1 };
    expect(parseStatistics(totals)).toBeNull();
    expect(parseStatistics({ ...totals, protection_status: protection })).toBeNull();
    expect(parseStatistics({ ...totals, protection_status: protection, trends: {} })).toBeNull();
    expect(parseStatistics(null)).toBeNull();
  });
});

describe("protection formatting", () => {
  test("labels known levels and falls back for unknown ones", () => {
    expect(protectionLabel("at_risk")).toBe("At Risk");
    expect(protectionLabel("no_data")).toBe("No Data");
    expect(protectionLabel("other")).toBe("Unknown");
  });

  test("leaves unknown core messages untranslated instead of dropping them", () => {
    expect(protectionMessage("Something new from the core")).toBe("Something new from the core");
  });

  test("formats durations without inventing a value for zero", () => {
    expect(formatDuration(0)).toBe("—");
    expect(formatDuration(1.25)).toBe("1.3s");
    expect(formatDuration(90)).toBe("1m 30s");
    expect(formatDuration(3660)).toBe("1h 1m");
  });
});
