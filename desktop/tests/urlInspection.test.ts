import { describe, expect, test } from "bun:test";
import {
  activeProviders,
  combinedSummary,
  combinedVerdict,
  type UrlscanSubmission,
  type VirusTotalSubmission,
} from "../src/urlInspection";

const us: UrlscanSubmission = {
  uuid: "u", url: "https://example.org/", visibility: "private", result_url: "https://urlscan.io/result/u/",
};
const vt = (status: VirusTotalSubmission["status"], detections = 0): VirusTotalSubmission => ({
  status, url: "https://example.org/", detections, total_engines: 60,
});

describe("combined URL inspection", () => {
  test("both mode uses both services", () => {
    expect(activeProviders("both")).toEqual(["urlscan", "virustotal"]);
    expect(activeProviders("urlscan")).toEqual(["urlscan"]);
  });

  test("any detection wins", () => {
    expect(combinedVerdict(us, vt("detected", 2), ["urlscan", "virustotal"])).toBe("detected");
  });

  test("pending is never clean", () => {
    expect(combinedVerdict(us, vt("pending"), ["urlscan", "virustotal"])).toBe("pending");
  });

  test("one answered is partial, not complete", () => {
    expect(combinedVerdict(us, null, ["urlscan", "virustotal"])).toBe("partial");
    expect(combinedVerdict(null, vt("clean"), ["urlscan", "virustotal"])).toBe("partial");
  });

  test("both clean is clean", () => {
    expect(combinedVerdict(us, vt("clean"), ["urlscan", "virustotal"])).toBe("clean");
  });

  test("single service verdicts still work", () => {
    expect(combinedVerdict(null, vt("clean"), ["virustotal"])).toBe("clean");
    expect(combinedVerdict(null, null, ["virustotal"])).toBe("unavailable");
    expect(combinedVerdict(us, null, ["urlscan"])).toBe("clean");
  });

  test("summary is conservative", () => {
    expect(combinedSummary("partial", 0, 60)).toContain("Only one service");
    expect(combinedSummary("detected", 2, 60)).toContain("2 of 60");
    expect(combinedSummary("clean", 0, 60)).toContain("Both services");
  });
});
