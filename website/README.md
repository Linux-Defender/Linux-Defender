# Linux Defender website

The marketing site and documentation for Linux Defender. It uses Astro, Tailwind CSS, and Starlight, and is configured for the Linux-Defender repository's GitHub Pages address: `https://linux-defender.github.io/Linux-Defender/`.

## Work locally

Install Bun and Node.js 22.23.4 or newer before running the site locally.

```bash
cd website
bun install --frozen-lockfile
bun run dev
bun run check
bun run build
bun run preview
```

`prebuild` and `predev` copy the Linux Defender logo and its social-card image into `public/`. Do not edit those generated copies. The home page shows a labelled illustrative preview of the Overview rather than a screenshot, so the site never presents a stale capture as the current interface. Older upstream screenshots remain in the repository only as reference material and are not published as Linux Defender screenshots.

## Write documentation

Write published guides in `src/content/docs/docs/` with concise, task-focused Markdown/MDX and repository-page `/Linux-Defender/docs/.../` links; add a sidebar entry in `astro.config.mjs`. The release reference pages import the root `CHANGELOG.md` and `RELEASE_NOTES.md`; keep those as their source of truth and do not duplicate their content. Root `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` are GitHub discoverability pointers, not a second documentation tree. The current branch is a development build and does not publish signed Linux Defender packages.

The `/docs/` site uses Starlight for navigation, full-text search, and copyable code blocks without a separate CMS, server, or search service.

## Deployment

The GitHub Actions workflow builds `website/dist` and deploys it to GitHub Pages. Repository Pages must be enabled with GitHub Actions as the source. No custom domain is configured.

## Structure

```text
website/
├── astro.config.mjs
├── scripts/copy-assets.mjs
├── public/
└── src/
    ├── assets/
    ├── components/
    ├── content/docs/docs/
    ├── layouts/
    ├── pages/
    └── styles/
```
