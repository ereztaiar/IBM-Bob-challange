/**
 * ScanForm — URL input form that submits a scan to the backend.
 *
 * Only rendered after the MetaTagGate is acknowledged.
 */

import { useState, type FormEvent } from "react";
import styles from "./ScanForm.module.css";

/** Maximum length of the optional user prompt. */
const MAX_PROMPT_LENGTH = 300;

/** Props for the ScanForm component. */
interface ScanFormProps {
  /** Called with the submitted URL and optional focus prompt when the form is valid. */
  onSubmit: (url: string, prompt: string) => void;
  /** Whether a scan is currently in progress. */
  isScanning: boolean;
  /**
   * When true the focus-area textarea is disabled, and an inline notice is shown
   * to inform the user that the AI service is unavailable.
   */
  promptDisabled?: boolean;
}

/**
 * Renders the URL input, submit button, and optional collapsible focus-area textarea.
 *
 * @param props - Component props.
 */
export default function ScanForm({
  onSubmit,
  isScanning,
  promptDisabled = false,
}: ScanFormProps): JSX.Element {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");

  /**
   * Validate and submit the URL together with the optional focus prompt.
   *
   * @param e - Form submit event.
   */
  function handleSubmit(e: FormEvent<HTMLFormElement>): void {
    e.preventDefault();
    setError(null);

    const trimmed = value.trim();
    if (!trimmed) {
      setError("Please enter a URL.");
      return;
    }

    try {
      const parsed = new URL(trimmed);
      if (!["http:", "https:"].includes(parsed.protocol)) {
        setError("Only http:// and https:// URLs are supported.");
        return;
      }
    } catch {
      setError("Please enter a valid URL (e.g. https://example.com).");
      return;
    }

    onSubmit(trimmed, prompt.trim());
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <label className={styles.label} htmlFor="scan-url">
        Enter a website URL to scan
      </label>
      <div className={styles.inputRow}>
        <input
          id="scan-url"
          className={styles.input}
          type="url"
          placeholder="https://example.com"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isScanning}
          aria-describedby={error ? "scan-url-error" : undefined}
        />
        <button
          className={styles.submitButton}
          type="submit"
          disabled={isScanning}
        >
          {isScanning ? "Scanning…" : "Scan"}
        </button>
      </div>
      {error && (
        <p id="scan-url-error" className={styles.error} role="alert">
          {error}
        </p>
      )}

      <details className={styles.focusDetails}>
        <summary className={styles.focusSummary}>Focus area (optional)</summary>
        <div className={styles.focusBody}>
          {promptDisabled ? (
            <p className={styles.offlineNotice} role="status">
              Focus area unavailable — AI service is offline.
            </p>
          ) : (
            <>
              <textarea
                id="scan-prompt"
                className={styles.focusTextarea}
                placeholder="e.g. check the payment page for injection issues"
                maxLength={MAX_PROMPT_LENGTH}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isScanning}
                rows={3}
              />
              <span className={styles.charCounter} aria-live="polite">
                {MAX_PROMPT_LENGTH - prompt.length} / {MAX_PROMPT_LENGTH}
              </span>
            </>
          )}
        </div>
      </details>
    </form>
  );
}
