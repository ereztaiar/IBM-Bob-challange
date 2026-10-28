/**
 * ScanSpinner — loading indicator shown while a scan is in progress.
 * Shared across frontends via ui-shared.
 */

export type ScanStatus = "pending" | "running" | "completed" | "failed";

import styles from "./ScanSpinner.module.css";

export interface ScanSpinnerProps {
  /** Current scan lifecycle status. */
  status: ScanStatus;
}

const MESSAGES: Record<ScanStatus, string> = {
  pending: "Queuing scan…",
  running: "Scanning — this may take a minute…",
  completed: "Finalising report…",
  failed: "Scan failed.",
};

/**
 * Renders an animated spinner with the current scan status.
 *
 * @param props - Component props.
 */
export function ScanSpinner({ status }: ScanSpinnerProps): JSX.Element {
  return (
    <div className={styles.wrapper} role="status" aria-live="polite">
      <div className={styles.spinner} aria-hidden="true" />
      <p className={styles.message}>{MESSAGES[status]}</p>
      <span className={styles.statusLabel}>{status}</span>
    </div>
  );
}

export default ScanSpinner;
