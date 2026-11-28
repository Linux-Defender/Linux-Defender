"""Regression tests for the boot-diagnostics and website-a11y guards.

These prove the guards are fail-closed: they accept the real repository and
reject a copy with the protected behavior removed.
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


boot = load("check_boot_diagnostics", ROOT / "scripts/check-boot-diagnostics.py")
a11y = load("check_website_a11y", ROOT / "scripts/check-website-a11y.py")

BOOT_FILES = (
    "desktop/index.html",
    "desktop/public/boot-diagnostics.js",
    "desktop/tests/bootDiagnostics.test.ts",
    "desktop/src-tauri/src/model.rs",
    "desktop/src/api.ts",
    "desktop/src-tauri/src/runtime.rs",
    "scripts/inspect-blank-window.py",
    "docs/documentation/SCRIPTS.md",
    "website/src/content/docs/docs/troubleshooting.md",
)
A11Y_FILES = (
    "website/astro.config.mjs",
    "website/src/styles/global.css",
    "website/src/layouts/Base.astro",
)


def fixture(test: unittest.TestCase, files: tuple[str, ...]) -> Path:
    tmp = tempfile.TemporaryDirectory(prefix="ld-ui-guard-")
    test.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    for rel in files:
        src = ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    return root


class UIGuardTests(unittest.TestCase):
    def test_real_repository_passes(self) -> None:
        self.assertEqual(boot.check(), [])
        self.assertEqual(a11y.check(), [])

    def test_empty_repository_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(boot.check(root))
            self.assertTrue(a11y.check(root))

    def test_boot_guard_rejects_early_error_regression(self) -> None:
        root = fixture(self, BOOT_FILES)
        self.assertEqual(boot.check(root), [])
        script = root / "desktop/public/boot-diagnostics.js"
        script.write_text(script.read_text(encoding="utf-8").replace("sawPlaceholder", "placeholderFlag"))
        failures = boot.check(root)
        self.assertTrue(any("sawPlaceholder" in failure for failure in failures))

    def test_boot_guard_rejects_unsafe_dom_write(self) -> None:
        root = fixture(self, BOOT_FILES)
        script = root / "desktop/public/boot-diagnostics.js"
        script.write_text(script.read_text(encoding="utf-8") + "\n// innerHTML\n")
        failures = boot.check(root)
        self.assertTrue(any("innerHTML" in failure for failure in failures))

    def test_boot_guard_rejects_hardcoded_native_log_path_in_js(self) -> None:
        root = fixture(self, BOOT_FILES)
        script = root / "desktop/public/boot-diagnostics.js"
        script.write_text(
            script.read_text(encoding="utf-8").replace("debugLogPath()", "NATIVE_LOG_PATH")
        )
        failures = boot.check(root)
        self.assertTrue(any("debugLogPath()" in failure for failure in failures))

    def test_a11y_guard_rejects_search_label_regression(self) -> None:
        root = fixture(self, A11Y_FILES)
        self.assertEqual(a11y.check(root), [])
        config = root / "website/astro.config.mjs"
        config.write_text(config.read_text(encoding="utf-8").replace("astro:page-load", "page-load"))
        failures = a11y.check(root)
        self.assertTrue(any("astro:page-load" in failure for failure in failures))

    def test_a11y_guard_rejects_light_mode_contrast_regression(self) -> None:
        root = fixture(self, A11Y_FILES)
        css = root / "website/src/styles/global.css"
        css.write_text(
            css.read_text(encoding="utf-8").replace(
                'html.light .product-preview [class~="text-guard-sage"]',
                "html.light .product-preview [class~=unused]",
            )
        )
        failures = a11y.check(root)
        self.assertTrue(any("text-guard-sage" in failure for failure in failures))

    def test_a11y_guard_rejects_duplicate_base_script(self) -> None:
        root = fixture(self, A11Y_FILES)
        base = root / "website/src/layouts/Base.astro"
        base.write_text(base.read_text(encoding="utf-8") + "\n// syncSearchLabel\n")
        failures = a11y.check(root)
        self.assertTrue(any("Base.astro duplicates" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
