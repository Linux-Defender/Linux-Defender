import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import { satteri } from "@astrojs/markdown-satteri";
import starlight from "@astrojs/starlight";
import tailwindcss from "@tailwindcss/vite";
import { mermaidSatteriPlugin } from "./scripts/mermaid-satteri.mjs";

export default defineConfig({
  site: "https://linux-defender.github.io",
  base: "/Linux-Defender",
  output: "static",
  compressHTML: true,
  markdown: {
    syntaxHighlight: {
      type: "shiki",
      excludeLangs: ["math", "mermaid"],
    },
    processor: satteri({
      hastPlugins: [mermaidSatteriPlugin],
    }),
  },
  integrations: [
    sitemap(),
    starlight({
      title: "Linux Defender Documentation",
      description: "Install, use, configure, and contribute to Linux Defender.",
      head: [
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: "https://linux-defender.github.io/Linux-Defender/og-image.png",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:image",
            content: "https://linux-defender.github.io/Linux-Defender/og-image.png",
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "og:image:alt",
            content: "Linux Defender security scanner preview",
          },
        },
        {
          tag: "meta",
          attrs: { property: "og:image:width", content: "1280" },
        },
        {
          tag: "meta",
          attrs: { property: "og:image:height", content: "640" },
        },
        {
          tag: "meta",
          attrs: { name: "twitter:card", content: "summary_large_image" },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:image:alt",
            content: "Linux Defender security scanner preview",
          },
        },
        {
          tag: "script",
          content: `(function(){function sync(){var b=document.querySelector('button[data-open-modal]');if(!b)return;Array.prototype.slice.call(b.querySelectorAll('kbd')).forEach(function(k){k.setAttribute('aria-hidden','true')});b.setAttribute('aria-label',b.textContent.replaceAll('\n',' ').replace(/ {2,}/g,' ').trim());}document.addEventListener('DOMContentLoaded',sync);document.addEventListener('astro:page-load',sync);if(document.readyState!=='loading')sync();})();`,
        },
      ],
      logo: {
        src: "./src/assets/logo.svg",
        alt: "Linux Defender",
      },
      social: [
        {
          icon: "github",
          label: "Linux Defender on GitHub",
          href: "https://github.com/Linux-Defender/Linux-Defender",
        },
      ],
      sidebar: [
        {
          label: "Start here",
          items: ["docs", "docs/installation", "docs/getting-started", "docs/troubleshooting"],
        },
        {
          label: "Guides",
          items: [
            "docs/guides/overview",
            "docs/guides/scanning",
            "docs/guides/profiles",
            "docs/guides/quarantine",
            "docs/guides/scheduling",
            "docs/guides/settings",
            "docs/guides/history",
            "docs/guides/statistics",
            "docs/guides/tray",
            "docs/guides/security-audit",
            "docs/guides/faq",
          ],
        },
        {
          label: "Reference",
          items: [
            "docs/reference/configuration",
            "docs/reference/scan-backends",
            "docs/reference/release-notes",
            "docs/reference/changelog",
          ],
        },
        {
          label: "Contributing",
          items: [
            "docs/contributing/development",
            "docs/contributing/translating",
            "docs/contributing/signing",
            "docs/contributing/architecture",
            "docs/contributing/code-of-conduct",
            "docs/contributing/security",
          ],
        },
      ],
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 3,
      },
      markdown: {
        processedDirs: [".."],
      },
      customCss: ["./src/styles/starlight.css"],
      routeMiddleware: "./src/starlight-route-data.ts",
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
  build: {
    inlineStylesheets: "auto",
  },
});
