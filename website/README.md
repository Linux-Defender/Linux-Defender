# Linux Defender website

The marketing site and documentation for Linux Defender. It uses Astro, Tailwind CSS, and Starlight, and is configured for the SAFETY-CHAT repository's GitHub Pages address: `https://safety-chat.github.io/Linux-Defender/`.

## Work locally

```bash
cd website
bun install --frozen-lockfile
bun run dev
bun run check
bun run build
bun run preview
```

`prebuild` and `predev` copy the Linux Defender logo and its social-card image into `public/`. The older ClamUI screenshots remain in the repository as reference material and are not published as Linux Defender screenshots.

## Write documentation

Write guides in `src/content/docs/docs/`, add new pages to the sidebar in `astro.config.mjs`, and use `/Linux-Defender/docs/.../` links for repository-page deployment. The release reference pages import the root `CHANGELOG.md` and `RELEASE_NOTES.md`; keep those as their source of truth. The current branch is a development build and does not publish signed Linux Defender packages.

## Deployment

The GitHub Actions workflow builds `website/dist` and deploys it to GitHub Pages. Repository Pages must be enabled with GitHub Actions as the source. No custom domain is configured; do not point this project at `clamui.com`.

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
