import { describe, expect, test } from "bun:test";
import {
  activeProviders, combinedMessageId, combinedVerdict,
  type UrlscanSubmission, type VirusTotalSubmission,
} from "../src/urlInspection";

const us: UrlscanSubmission = {
  uuid: "u", url: "https://example.org/", visibility: "private", result_url: "https://urlscan.io/result/u/",
};
const vt = (status: VirusTotalSubmission["status"], detections = 0): VirusTotalSubmission => ({
  status, url: "https://example.org/", detections, total_engines: 60,
});
const both = ["urlscan", "virustotal"] as const;

describe("combined URL inspection", () => {
  test("both mode uses both services", () => {
    expect(activeProviders("both")).toEqual(["urlscan", "virustotal"]);
    expect(activeProviders("urlscan")).toEqual(["urlscan"]);
  });

  test("any detection wins", () => {
    expect(combinedVerdict(us, vt("detected", 2), both)).toBe("detected");
  });

  test("pending is never clean", () => {
    expect(combinedVerdict(us, vt("pending"), both)).toBe("pending");
  });

  test("errors and rate limits are never clean", () => {
    expect(combinedVerdict(us, vt("error"), both)).toBe("partial");
    expect(combinedVerdict(us, vt("rate_limited"), both)).toBe("partial");
    expect(combinedVerdict(null, vt("error"), ["virustotal"])).toBe("partial");
  });

  test("urlscan alone is only a receipt, never a verdict", () => {
    expect(combinedVerdict(us, null, ["urlscan"])).toBe("partial");
    expect(combinedVerdict(null, null, ["urlscan"])).toBe("unavailable");
  });

  test("clean requires VirusTotal clean and both services answering", () => {
    expect(combinedVerdict(us, vt("clean"), both)).toBe("clean");
    expect(combinedVerdict(null, vt("clean"), both)).toBe("partial");
    expect(combinedVerdict(null, vt("clean"), ["virustotal"])).toBe("clean");
  });

  test("messages are static translation ids", () => {
    expect(combinedMessageId("clean")).toContain("urlscan");
    expect(combinedMessageId("partial")).toContain("not checked successfully");
    expect(combinedMessageId("detected")).toContain("suspicious");
  });
});
