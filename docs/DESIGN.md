# Linux Defender design system — Guardian

Linux Defender uses one visual identity across the desktop app and the website:
**Guardian** — ink surfaces, paper text, and a single safety-green accent.

It replaces the teal/navy palette inherited from ClamUI. If you add a screen, pull
colors, spacing, and shapes from the tokens below instead of hard-coding values.

## Principles

- **One accent.** Safety green marks the live, healthy, and actionable path. Nothing
  else competes with it; secondary emphasis uses neutral ink, not a second hue.
- **Ink and paper.** The dark shell reads as a control surface; the light theme reads
  as paper. Both share the same green and the same geometry.
- **Quiet destructive actions.** Destructive controls are tonal (outlined, danger
  text) and only fill with color on hover, so they never dominate a screen.
- **Status is honest.** Border and text color carry state; tinted backgrounds stay
  low-saturation so notices never shout.

## Color tokens

The app defines these in `desktop/src/styles.css` (`:root` for light,
`@media (prefers-color-scheme: dark)` for the ink theme). The website mirrors them as
Tailwind theme variables `--color-guard-*` in `website/src/styles/global.css`, and
Starlight docs map them to `--sl-color-*` in `website/src/styles/starlight.css`.

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--bg` | `#f5f8f5` | `#0a0c0b` | Window / page background |
| `--sidebar-bg` | `#edf2ed` | `#0d1210` | Navigation rail |
| `--surface` | `#ffffff` | `#111614` | Cards, tables, dialogs |
| `--group-bg` | `#f1f5f0` | `#141b17` | Grouped rows, progress track |
| `--control-bg` | `#ffffff` | `#151c19` | Inputs, secondary buttons |
| `--fg` | `#14201a` | `#e6ede9` | Primary text |
| `--muted` | `#56655d` | `#93a39b` | Secondary text, paths |
| `--border` | `#d9e2da` | `#1f2a25` | Hairlines, card outlines |
| `--control-border` | `#a3b5a9` | `#2c3a33` | Input and button outlines |
| `--accent` | `#157f3d` | `#7ce38b` | The safety-green accent |
| `--accent-soft` | `#e4f3e8` | `#14261b` | Active nav, accent chips |
| `--accent-line` | `#2f9a55` | `#2f6b45` | Accent outlines and gradients |
| `--accent-fg` | `#ffffff` | `#06110a` | Text on an accent fill |
| `--danger` | `#b52330` | `#f0707a` | Destructive text and outlines |
| `--warning` | `#805b00` | `#f4b740` | Warnings |
| `--notice-bg` / `--ok-bg` / `--warn-bg` / `--error-bg` | pale tints | ink tints | Banner backgrounds |

Contrast: body text and the accent both clear WCAG AA against their own surface in
both themes. Never place `--accent` (#7ce38b) text on a light surface or `--accent-fg`
on a mid-tone; use `--accent` in light as `--accent` (#157f3d) already is.

## Type and shape

- Family: Cantarell / Noto Sans / system UI for the app, the same stack for the site.
- Headings use tight tracking (`-0.02em` at page level, `-0.01em` for section titles).
- Radii: `--radius-group: 10px` for cards and panels, `--radius-control: 6px` for
  inputs and buttons, `999px` for progress and pills.
- Elevation: one shadow token, `--shadow-pop`, for menus, toasts, and dialogs.

## Components

- **Brand mark:** shield glyph in `--accent` on an `--accent-soft` tile with an
  `--accent-line` border. The app header renders it from `Icon name="shield"`; the
  site and packages use `icons/io.github.linuxdefender.linuxdefender.svg`.
- **Navigation:** active item uses `--accent-soft` background, an inset 3px accent
  rule, and an accent-tinted icon.
- **Primary button:** accent fill with `--accent-fg` text.
- **Danger button:** transparent fill, danger outline and text; fills on hover.
- **Progress:** custom-styled `<progress>` with an accent gradient value on a
  `--group-bg` track.
- **Banners:** `.notice` / `.warning` / `.error` / `.success` use the tinted tokens
  rather than fixed hex values.
- **Overview hero:** the only surface that tints a whole band. Protected uses an
  `--accent-soft` wash, at-risk/unprotected/error use `--error-bg`, and
  no-data/unknown/checking stay on plain `--surface`; the mark tile follows the
  same level.
- **Metric cards:** `--surface` cards in a two-up grid. Only the threat card takes
  the danger tint, and only while its count is above zero.

## Brand assets

- `icons/io.github.linuxdefender.linuxdefender.svg` — canonical app icon (ink tile,
  green shield, ink check). `..png` is rendered from it with
  `rsvg-convert -w 128 -h 128 …`.
- `desktop/src-tauri/icons/io.github.linuxdefender.linuxdefender.svg` — copy for the
  Tauri bundle.
- `website/src/assets/logo.svg` — copied to `website/public/favicon.svg` by
  `website/scripts/copy-assets.mjs`.
- `screenshots/social-preview.svg` and `website/src/assets/social-preview.svg` —
  1280×640 social card; `..png` rendered from the SVG.

When the mark changes, update the SVG sources and regenerate every PNG so the app
icon, favicon, and social card stay in step.

### UI screenshots

`screenshots/*.png` are 900×700 captures of the **current Linux Defender UI**,
not inherited ClamUI material. Regenerate them from `desktop/visual-harness.html`
served by `bun run --cwd desktop dev`: dispatch a
`linux-defender-navigate` window event with `{ page, args }`, capture at width
900, and pad to 900×700. The results capture additionally dispatches
`linux-defender-scan-result` after navigation; the "with scan result" overview
uses the harness `?threats` flag. The two social-preview PNGs are copies of
`website/src/assets/social-preview.png` (the branded card), not upstream art.

For a one-command visual review of every surface, run `./scripts/capture-all.sh` (see the development guide); it combines the native WebKitGTK window, all twelve React views, and the site in both color schemes into one output directory.

`scripts/check-screenshot-branding.py` refuses any pixel change until it has
been reviewed: every image is pinned by SHA-256 in
`scripts/screenshot-manifest.json`, and Tesseract OCR additionally rejects the
old `ClamUI` / `Dashboard` branding when available. Refresh the manifest only
after inspecting the regenerated images.
