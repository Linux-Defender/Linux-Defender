export type HelperTrustFailure = "missing" | "untrusted";

/**
 * Classifies native helper failures. The Rust side embeds the helper path in
 * most messages, so matching is by the stable phrase rather than the full
 * string. The "canonical" wording used by older tests is still accepted for
 * backwards compatibility.
 */
export function helperTrustFailure(message: string): HelperTrustFailure | null {
  const normalized = message.trim().toLowerCase();
  if (
    /the (host )?privileged helper\b/.test(normalized) &&
    (normalized.endsWith(" is missing") || normalized.endsWith(" is unavailable"))
  ) {
    return "missing";
  }
  if (
    /the (host )?privileged helper\b/.test(normalized) &&
    normalized.endsWith(" is not a root-owned immutable executable")
  ) {
    return "untrusted";
  }
  if (normalized === "legacy privileged helper libraries are not root-owned and immutable") {
    return "untrusted";
  }
  if (normalized === "the privileged helper is unavailable") {
    return "missing";
  }
  // Backwards-compatible exact wording.
  if (normalized === "the canonical privileged helper is missing") return "missing";
  if (normalized === "the canonical host privileged helper is unavailable") return "missing";
  if (normalized === "the canonical privileged helper is not a root-owned immutable executable") return "untrusted";
  if (normalized === "legacy privileged helper libraries are not root-owned and immutable") return "untrusted";
  return null;
}

/** Recognizes native helper failures without changing their fail-closed behavior. */
export function isHelperTrustError(message: string): boolean {
  return helperTrustFailure(message) !== null;
}
