# Translations

Status and instructions for the **Linux Defender** gettext catalogs.

## TL;DR

- Catalogs: `po/linux-defender.pot` (template) + `po/*.po` for the 10 active
  locales `de en es fr hu it nb pt_BR vi zh_CN`.
- **Automated status: green.** `update-pot.sh --check`, `check-potfiles.sh`,
  `check-translations.sh`, `msgfmt -c`, and `msgcmp` all pass. Every active
  catalog contains all 1,459 source messages.
- **Human status: still open.** The generated
  [`po/TRANSLATION-REVIEW.md`](../../po/TRANSLATION-REVIEW.md) lists long English
  strings that remain identical in non-English catalogs. Some are legitimate
  protected literals; a translator must decide each case.
- `po/MISSING_TRANSLATIONS.txt` is a historical snapshot from the audit refactor,
  not a current gap list.

## How to validate a catalog change

1. Edit the source literal(s) and precise translator note in Rust/TypeScript.
2. Regenerate and merge with `python3 scripts/merge-catalogs.py` (it runs `update-pot.sh`, `msgmerge` for every active locale, and fills only newly added entries with the English fallback).
3. Merge each catalog with `msgmerge --update po/<loc>.po po/linux-defender.pot`.
4. Fill the affected entries, preserving placeholders, markup, whitespace, and
   every required `msgstr[N]` form for plurals.
5. Run `./scripts/check-translations.sh`, `./scripts/check-potfiles.sh`, and
   `./scripts/update-pot.sh --check`.
6. Regenerate the review report with
   `python3 scripts/generate-translation-review.py` and commit it with the
   catalog changes. The Translations CI workflow verifies it.

Use a real PO library (for example `polib`) or a full regeneration from the POT
if you need to script catalog edits. Hand-rolled PO parsers previously corrupted
duplicate msgids, plurals, and multiline strings.

## Translator conventions

- Keep gettext arguments static literals; select conditional branches around
  each translated literal, then interpolate after lookup.
- Use the existing plural API and keep every form meaningful; never introduce
  pseudo-plurals.
- Preserve Unicode `—`, `–`, and `…` unless a translator note says otherwise.
- Protected literals (commands, packages, file names, app IDs) stay unchanged;
  a `// Translators:` note must say so.

## Related docs

- [Translator guide](../../website/src/content/docs/docs/contributing/translating.md) — published conventions and language-specific notes.
- [`../clamui-fork/`](../clamui-fork/) — fork status and porting record.
- [`../revival/RELATED-PROJECT-REVIEW.md`](../revival/RELATED-PROJECT-REVIEW.md) — upstream parity matrix.
