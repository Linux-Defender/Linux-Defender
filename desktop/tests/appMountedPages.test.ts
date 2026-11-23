import { describe, expect, test } from "bun:test";
import { INITIAL_MOUNTED_PAGES } from "../src/initialMountedPages";

describe("initial mounted pages", () => {
  test("mounts Scan alongside Overview from the start", () => {
    // selectPage() dispatches linux-defender-page-selected/linux-defender-quick-scan and
    // open-targets synchronously; Scan must already be mounted so its
    // window listeners exist before the first navigation/quick-scan event.
    expect(INITIAL_MOUNTED_PAGES).toContain("overview");
    expect(INITIAL_MOUNTED_PAGES).toContain("scan");
  });
});
