import { describe, expect, test } from "bun:test";

import { helperTrustFailure, isHelperTrustError } from "../src/helperTrustError";

describe("helperTrustFailure", () => {
  test("classifies current, legacy, and unavailable helper diagnostics", () => {
    expect(helperTrustFailure("the privileged helper /usr/bin/linux-defender-apply-preferences is missing")).toBe("missing");
    expect(helperTrustFailure("Error: the host privileged helper /usr/bin/linux-defender-apply-preferences is unavailable")).toBe("missing");
    expect(helperTrustFailure("the privileged helper /usr/bin/linux-defender-apply-preferences is not a root-owned immutable executable")).toBe("untrusted");
    expect(helperTrustFailure("legacy privileged helper libraries are not root-owned and immutable")).toBe("untrusted");
    // Backwards-compatible wording.
    expect(helperTrustFailure("the canonical privileged helper is missing")).toBe("missing");
    expect(helperTrustFailure("the canonical host privileged helper is unavailable")).toBe("missing");
    expect(helperTrustFailure("the canonical privileged helper is not a root-owned immutable executable")).toBe("untrusted");
  });

  test("does not misclassify unrelated diagnostics", () => {
    expect(isHelperTrustError("freshclam (/etc/freshclam.conf): the canonical privileged helper is missing")).toBe(false);
    expect(isHelperTrustError("the canonical privileged helper was repaired")).toBe(false);
    expect(isHelperTrustError("constructor")).toBe(false);
    expect(isHelperTrustError("toString")).toBe(false);
    expect(isHelperTrustError("__proto__")).toBe(false);
    expect(isHelperTrustError("the file is missing")).toBe(false);
  });
});
