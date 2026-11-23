# Translations

Status and instructions for the **Linux Defender** gettext catalogs.

## TL;DR

- Catalogs: `po/linux-defender.pot` (template) + `po/*.po` for the 10 active locales
  `de en es fr hu it nb pt_BR vi zh_CN`.
- **Current status:** `check-translations.sh` passes; `update-pot.sh --check` fails —
  the POT is stale because the ClamUI audit refactor added ~32 new strings (see
  [`../../po/MISSING_TRANSLATIONS.txt`](../../po/MISSING_TRANSLATIONS.txt)).
- **Blocked on:** translations of those 32 new strings in all 10 catalogs.

## How to finish it

1. Regenerate the POT: `./scripts/update-pot.sh`
2. Merge each catalog: `msgmerge --update po/<loc>.po po/linux-defender.pot`
3. Fill the new entries with translations (see [the recipe](#polib-recipe)).
4. Verify each catalog: `msgcmp po/<loc>.po po/linux-defender.pot && msgfmt -c po/<loc>.po`
5. Verify everything: `./scripts/check-translations.sh && ./scripts/update-pot.sh --check`
6. Commit with message like: `Translate new ClamUI audit/firewall/opensnitch strings in all 10 catalogs`

## Polib recipe (recommended by the original author)

```sh
pip install polib
```

```python
import polib

def load(loc):
    """Return dict: msgid -> msgstr from /tmp/translations.json, extended per locale."""
    return polib.pofile(f"po/{loc}.po")

for loc in ["de", "en", "es", "fr", "hu", "it", "nb", "pt_BR", "vi", "zh_CN"]:
    po = polib.pofile(f"po/{loc}.po")
    for entry in po:
        if entry.msgid and not entry.msgstr:
            entry.msgstr = pick_translation(entry.msgid, loc)
    po.save()
```

Notes:
- For entries with `msgid_plural`, fill both `entry.msgstr[0]` and `entry.msgstr[1]` (or set both to the same string).
- `pick_translation(msgid, loc)` should return the locale's translation, or the msgid itself if none is available yet (English fallback is acceptable for the first pass).
- German translations for the 32 missing strings are documented in [`../../po/MISSING_TRANSLATIONS.txt`](../../po/MISSING_TRANSLATIONS.txt) (source: `/tmp/translations.json` → `translate_audit.py` `NEW` dict).

## Getting started on a new model

If you are an AI agent picking up this work:
1. Read [`../../po/MISSING_TRANSLATIONS.txt`](../../po/MISSING_TRANSLATIONS.txt) — it lists the exact msgids and German translations.
2. Re-run `./scripts/update-pot.sh` and `msgmerge` if the catalogs are behind, then
   `./scripts/check-translations.sh` to see the current gap (32 missing in all 10).
3. Translate the 32 strings into es, fr, hu, it, nb, pt_BR, vi, zh_CN (de is done; en is identity).
4. Verify: `msgcmp po/<loc>.po po/linux-defender.pot` for all 10, then `./scripts/check-translations.sh`.
5. Commit and push; verify the Translations CI workflow goes green (`gh run list`).

## What went wrong before (why a retry helps)

The attempts used hand-rolled PO parsers that corrupted files (duplicate msgids,
broken plurals, "do not both begin with \n" errors, "msgfmt: found N fatal errors").
Each attempt re-created the corruption. A real PO library (polib) or a full
regeneration from the POT avoids this.

## Related docs

- [Translator guide](../../website/src/content/docs/docs/contributing/translating.md) — project translation conventions.
- [`../clamui-fork/`](../clamui-fork/) — the fork: what was ported, rebrand state, parity matrix.
- [`../revival/RELATED-PROJECT-REVIEW.md`](../revival/RELATED-PROJECT-REVIEW.md) — the live upstream parity matrix.
