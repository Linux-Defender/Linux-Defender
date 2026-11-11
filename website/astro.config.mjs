import { defineConfig } from "astro/config";
import { satteri } from "@astrojs/markdown-satteri";
import starlight from "@astrojs/starlight";
import tailwindcss from "@tailwindcss/vite";
import { mermaidSatteriPlugin } from "./scripts/mermaid-satteri.mjs";

export default defineConfig({
  site: "https://safety-chat.github.io",
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
    starlight({
      title: "Linux Defender Documentation",
      description: "Install, use, configure, and contribute to Linux Defender.",
      logo: {
        src: "./src/assets/logo.svg",
        alt: "Linux Defender",
      },
      social: [
        {
          icon: "github",
          label: "Linux Defender on GitHub",
          href: "https://github.com/SAFETY-CHAT/Linux-Defender",
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
