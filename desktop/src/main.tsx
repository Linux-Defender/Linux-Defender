import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { UiErrorBoundary } from "./UiErrorBoundary";
import { _, loadCatalog } from "./i18n";
import { startupState } from "./api";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Linux Defender could not find its application root");
}

void startupState()
  .then((state) => {
    (window as Window & { __linuxDefenderStartup?: unknown }).__linuxDefenderStartup = state;
  })
  .catch(() => undefined);

const root = createRoot(rootElement);
void loadCatalog()
  .then(() => {
    root.render(
      <StrictMode>
        <UiErrorBoundary>
          <App />
        </UiErrorBoundary>
      </StrictMode>,
    );
  })
  .catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    root.render(
      <main className="startup-error">
        <section className="card" aria-labelledby="startup-error-title">
          <h1 id="startup-error-title">{_("Linux Defender could not start")}</h1>
          <p className="error">{message}</p>
          <button className="button primary" type="button" onClick={() => window.location.reload()}>
            {_("Retry")}
          </button>
        </section>
      </main>,
    );
  });
