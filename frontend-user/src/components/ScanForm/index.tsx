/**
 * ScanForm — URL input form that submits a scan to the backend.
 *
 * Only rendered after the MetaTagGate is acknowledged.
 */

import { useState, type FormEvent } from "react";
import styles from "./ScanForm.module.css";

interface ScanFormProps {
  /** Called with the submitted URL when the form is valid. */
  onSubmit: (url: string) => void;
  /** Whether a scan is currently in progress. */
  isScanning: boolean;
}

/**
 * Renders the URL input and submit button.
 *
 * @param props - Component props.
 */
export default function ScanForm({ onSubmit, isScanning }: ScanFormProps): JSX.Element {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  /**
   * Validate and submit the URL.
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

    onSubmit(trimmed);
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
    </form>
  );
}
