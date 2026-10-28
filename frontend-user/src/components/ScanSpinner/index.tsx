/**
 * ScanSpinner — loading indicator shown while a scan is in progress.
 */

import type { ScanStatus } from "../../types/scan";
import styles from "./ScanSpinner.module.css";

interface ScanSpinnerProps {
  /** Current scan lifecycle status. */
  status: ScanStatus;
}

/**
 * Renders an animated spinner with the current scan status.
 *
 * @param props - Component props.
 */
export default function ScanSpinner({ status }: ScanSpinnerProps): JSX.Element {
  const messages: Record<ScanStatus, string> = {
    pending: "Queuing scan…",
    running: "Scanning — this may take a minute…",
    completed: "Finalising report…",
    failed: "Scan failed.",
  };

  return (
    <div className={styles.wrapper} role="status" aria-live="polite">
      <div className={styles.spinner} aria-hidden="true" />
      <p className={styles.message}>{messages[status]}</p>
      <span className={styles.status}>{status}</span>
    </div>
  );
}
