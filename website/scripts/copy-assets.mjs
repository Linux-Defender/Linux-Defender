#!/usr/bin/env node
// Copies the website's Linux Defender brand assets and the shared screenshot
// reference set into website/public/ before Astro builds the static site.

import { mkdir, copyFile, access } from "node:fs/promises";
import { constants } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const websiteRoot = resolve(here, "..");
const tasks = [
  {
    from: resolve(websiteRoot, "src/assets/logo.svg"),
    to: resolve(websiteRoot, "public/favicon.svg"),
  },
  {
    from: resolve(websiteRoot, "src/assets/social-preview.png"),
    to: resolve(websiteRoot, "public/og-image.png"),
  },
];

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

for (const t of tasks) {
  if (!(await exists(t.from))) {
    console.warn(`[copy-assets] missing: ${t.from}`);
    continue;
  }
  await mkdir(dirname(t.to), { recursive: true });
  await copyFile(t.from, t.to);
  console.log(`[copy-assets] ${t.from} -> ${t.to}`);
}
