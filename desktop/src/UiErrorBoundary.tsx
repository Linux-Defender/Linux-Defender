import { Component, type ErrorInfo, type ReactNode } from "react";

import { _ } from "./i18n";

type Props = { children: ReactNode };
type State = { message: string | null; detail: string };

/**
 * Keep an unexpected render failure from leaving an empty window. The fallback
 * shows the error text locally and offers a reload; it never reports anything
 * over the network.
 */
export class UiErrorBoundary extends Component<Props, State> {
  state: State = { message: null, detail: "" };

  static getDerivedStateFromError(error: unknown): Partial<State> {
    return { message: error instanceof Error ? error.message : String(error) };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Linux Defender interface error", error, info.componentStack);
    this.setState({ detail: info.componentStack ?? "" });
  }

  render(): ReactNode {
    if (this.state.message === null) {
      return this.props.children;
    }
    const detail = [this.state.message, this.state.detail].filter(Boolean).join("\n");
    return (
      <main className="startup-error" role="alert">
        <section className="card" aria-labelledby="ui-error-title">
          <h1 id="ui-error-title">{_("Error")}</h1>
          <p className="error">{_("Error: {error}", { error: this.state.message })}</p>
          <details className="ui-error-details">
            <summary>{_("Technical details")}</summary>
            <pre>{detail}</pre>
          </details>
          <button className="button primary" type="button" onClick={() => window.location.reload()}>
            {_("Retry")}
          </button>
        </section>
      </main>
    );
  }
}
