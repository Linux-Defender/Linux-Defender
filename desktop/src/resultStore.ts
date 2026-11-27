/** Keeps the latest scan and VirusTotal results where the lazily mounted
 * Results page can always find them. A full-system scan can produce more raw
 * output than sessionStorage's ~5 MB quota, so the in-memory copy is canonical
 * and sessionStorage is only a trimmed copy for page reloads.
 *
 * Adapted from upstream ClamUI (MIT) `desktop/src/resultStore.ts`, with
 * Linux Defender storage keys. */
export type ResultKind = "scan" | "virustotal";

type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

const STORAGE_KEYS: Record<ResultKind, string> = {
  scan: "linux-defender-last-scan-result",
  virustotal: "linux-defender-last-vt-result",
};

export const STORED_OUTPUT_LIMIT = 256 * 1024;
const OUTPUT_FIELDS = ["stdout", "stderr"] as const;

function tail(text: string, limit: number): string {
  if (text.length <= limit) return text;
  return `[output truncated, last ${limit} characters kept]\n${text.slice(text.length - limit)}`;
}

export function trimmedForStorage(value: unknown, limit: number = STORED_OUTPUT_LIMIT): unknown {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return value;
  const trimmed: Record<string, unknown> = { ...(value as Record<string, unknown>) };
  for (const field of OUTPUT_FIELDS) {
    const output = trimmed[field];
    if (typeof output === "string") trimmed[field] = tail(output, limit);
  }
  if (Array.isArray(trimmed.per_target_results)) {
    trimmed.per_target_results = trimmed.per_target_results.map((entry) => trimmedForStorage(entry, limit));
  }
  return trimmed;
}

export function createResultStore(storage: () => StorageLike | null) {
  const memory = new Map<ResultKind, unknown>();
  const persist = (kind: ResultKind, value: unknown): void => {
    const target = storage();
    if (!target) return;
    const key = STORAGE_KEYS[kind];
    for (const candidate of [value, trimmedForStorage(value), trimmedForStorage(value, 0)]) {
      try {
        target.setItem(key, JSON.stringify(candidate));
        return;
      } catch {
        // Quota exceeded: retry with less output; memory stays complete.
      }
    }
    try { target.removeItem(key); } catch { /* nothing to clean up */ }
  };
  return {
    remember(kind: ResultKind, value: unknown): void {
      memory.set(kind, value);
      persist(kind, value);
    },
    recall<T>(kind: ResultKind, guard: (value: unknown) => value is T): T | null {
      const live = memory.get(kind);
      if (guard(live)) return live;
      try {
        const serialized = storage()?.getItem(STORAGE_KEYS[kind]);
        if (!serialized) return null;
        const parsed: unknown = JSON.parse(serialized);
        return guard(parsed) ? parsed : null;
      } catch {
        return null;
      }
    },
  };
}

export const resultStore = createResultStore(() => {
  try {
    return typeof sessionStorage === "undefined" ? null : sessionStorage;
  } catch {
    return null;
  }
});
