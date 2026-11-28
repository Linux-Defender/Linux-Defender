// Runs before the React bundle. Classic script (CSP forbids inline code).
// If the app fails before React mounts, show what is known instead of a blank
// window. Never runs after mount, makes no network requests, and uses only
// textContent for untrusted error text.
(function () {
  "use strict";
  var STALL_MS = 8000;
  var started = Date.now();
  var events = [];

  function mark(text) {
    if (events.length < 50) {
      events.push("+" + (Date.now() - started) + "ms " + text);
    }
  }

  function placeholder() {
    return document.querySelector("[data-boot-placeholder]");
  }

  function mounted() {
    return placeholder() === null;
  }

  function debugLogPath() {
    try {
      var state = window.__linuxDefenderStartup;
      if (state && typeof state.debug_log === "string" && state.debug_log) {
        return state.debug_log;
      }
    } catch (ignored) {}
    return "~/.local/share/linux-defender/debug/linux-defender.log";
  }

  function snapshot() {
    return [
      "readyState=" + document.readyState,
      "tauriInternals=" + typeof window.__TAURI_INTERNALS__,
      "url=" + location.href,
      "events: " + (events.length ? events.join(" | ") : "none"),
    ].join("\n");
  }

  function show(headline, detail) {
    var box = placeholder();
    if (!box) return;
    box.hidden = false;
    box.querySelector("[data-boot-status]").textContent = headline;
    var pre = box.querySelector("[data-boot-detail]");
    pre.hidden = false;
    pre.textContent = detail;
  }

  function failed(headline, detail) {
    if (mounted()) return;
    show("Linux Defender could not start: " + headline, detail + "\n\n" + snapshot());
  }

  window.__linuxDefenderBoot = { mark: mark, events: events };
  mark("boot script ran");

  window.addEventListener("error", function (event) {
    var target = event.target;
    if (target && target !== window && (target.src || target.href)) {
      failed("could not load " + (target.src || target.href), "");
      return;
    }
    failed(
      String(event.message || "script error"),
      (event.filename || "") + ":" + (event.lineno || 0) + ":" + (event.colno || 0)
    );
  }, true);
  window.addEventListener("unhandledrejection", function (event) {
    var reason = event.reason;
    failed("unhandled promise rejection", String((reason && reason.message) || reason));
  });
  document.addEventListener("securitypolicyviolation", function (event) {
    mark("CSP blocked " + event.violatedDirective + " " + event.blockedURI);
  });
  document.addEventListener("DOMContentLoaded", function () { mark("DOM ready"); });

  setTimeout(function () {
    if (mounted()) return;
    mark("still not mounted");
    show(
      "Linux Defender is still starting after " + STALL_MS / 1000 + " seconds",
      "The window opened but the interface has not appeared. Check the debug log at " +
        debugLogPath() + " and include this text in a report.\n\n" +
        snapshot()
    );
  }, STALL_MS);
})();
