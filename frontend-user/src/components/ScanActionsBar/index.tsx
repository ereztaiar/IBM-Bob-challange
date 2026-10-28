/**
 * ScanActionsBar — always-visible bar shown above the spinner/report
 * after the first successful scan submission.
 *
 * Provides two actions:
 *  - "Scan again" — re-scans the same URL with one click.
 *  - New-URL input — allows scanning a different URL.
 *
 * All controls are disabled while a scan is in progress.
 */

import { useState, type FormEvent } from "react";
import styles from "./ScanActionsBar.module.css";

/** Props for the ScanActionsBar component. */
export interface ScanActionsBarProps {
  /** The URL that was most recently scanned, shown on the "Scan again" button. */
  currentUrl: string;
  /** Called when the user clicks "Scan again" to re-submit the same URL. */
  onScanAgain: () => void;
  /** Called when the user submits a new URL via the input field. */
  onScanNew: (url: string) => void;
  /** When true all controls are disabled (a scan is currently in progress). */
  isScanning: boolean;
}

/**
 * Renders the always-visible scan actions bar above the report/spinner.
 *
 * @param props - Component props.
 */
export default function ScanActionsBar({
  currentUrl,
  onScanAgain,
  onScanNew,
  isScanning,
}: ScanActionsBarProps): JSX.Element {
  const [newUrl, setNewUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  /**
   * Validate and submit the new URL.
   *
   * @param e - Form submit event.
   */
  function handleNewUrlSubmit(e: FormEvent<HTMLFormElement>): void {
    e.preventDefault();
    setError(null);

    const trimmed = newUrl.trim();
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

    setNewUrl("");
    onScanNew(trimmed);
  }

  return (
    <div className={styles.bar} role="region" aria-label="Scan actions">
      <button
        className={styles.rescanButton}
        type="button"
        onClick={onScanAgain}
        disabled={isScanning}
        title={`Re-scan ${currentUrl}`}
      >
        ↺ Scan again
      </button>

      <form className={styles.newUrlForm} onSubmit={handleNewUrlSubmit} noValidate>
        <input
          className={styles.newUrlInput}
          type="url"
          placeholder="Scan a different URL…"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          disabled={isScanning}
          aria-label="New URL to scan"
          aria-describedby={error ? "scan-actions-error" : undefined}
        />
        <button
          className={styles.newUrlButton}
          type="submit"
          disabled={isScanning}
        >
          Scan
        </button>
      </form>

      {error && (
        <p id="scan-actions-error" className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
