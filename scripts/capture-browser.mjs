// Browser-side capture for the Linux Defender visual review.
// Captures every app view from the visual harness plus the public site in both
// color schemes. Complements scripts/capture-app-window.sh, which captures the
// real Tauri/WebKitGTK window. Run from the repository root with Bun:
//
//   bun scripts/capture-browser.mjs [out-dir] [harness-url] [site-url]
//
// Prerequisites: website dependencies installed (Playwright) and the harness
// served by `bun run --cwd desktop dev`. The site URL is optional; when absent
// only harness captures are produced.
import { chromium } from "../website/node_modules/playwright/index.mjs";

const [outDir = "/tmp/opencode/captures", harnessUrl = "http://127.0.0.1:1420/visual-harness.html", siteUrl = ""] = process.argv.slice(2);

const views = [
  "overview", "scan", "database", "logs", "components", "quarantine",
  "statistics", "audit", "network", "profiles", "results", "preferences",
];

const browser = await chromium.launch();
try {
  for (const view of views) {
    const context = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await context.newPage();
    await page.goto(harnessUrl);
    await page.waitForTimeout(700);
    await page.evaluate((name) => {
      window.dispatchEvent(new CustomEvent("linux-defender-navigate", { detail: { page: name, args: {} } }));
    }, view);
    await page.waitForTimeout(350);
    await page.screenshot({ path: `${outDir}/app-${view}.png` });
    await context.close();
  }
  if (siteUrl) {
    const docs = new URL("docs/", siteUrl).toString();
    for (const scheme of ["light", "dark"]) {
      const context = await browser.newContext({ viewport: { width: 1024, height: 768 }, colorScheme: scheme });
      const page = await context.newPage();
      await page.goto(siteUrl);
      await page.waitForTimeout(600);
      await page.screenshot({ path: `${outDir}/site-home-${scheme}.png` });
      await page.goto(docs);
      await page.waitForTimeout(600);
      await page.screenshot({ path: `${outDir}/site-docs-${scheme}.png` });
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log(`Browser captures written to ${outDir}`);
