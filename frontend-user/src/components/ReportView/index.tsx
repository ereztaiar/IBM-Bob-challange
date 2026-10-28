/**
 * ReportView — renders a completed vulnerability scan report.
 *
 * Handles the error / failed state locally, then delegates to the shared
 * ReportView component for the actual report layout.
 */

import type { ScanResponse } from "../../types/scan";
import { ReportView as SharedReportView } from "ui-shared/components/ReportView";
import { useReportView } from "./useReportView";
import styles from "./ReportView.module.css";

interface ReportViewProps {
  /** The completed or failed scan. */
  scan: ScanResponse;
  /** Called when the user clicks "Scan another URL". */
  onReset: () => void;
}

/**
 * Renders the full report or an error message.
 *
 * @param props - Component props.
 */
export default function ReportView({ scan, onReset }: ReportViewProps): JSX.Element {
  const { report, hasError, errorMessage } = useReportView(scan);

  if (hasError) {
    return (
      <div className={styles.errorWrapper}>
        <div className={styles.errorBox} role="alert">
          <strong>Scan failed:</strong> {errorMessage}
        </div>
        <button className={styles.resetButton} onClick={onReset}>
          ← Try another URL
        </button>
      </div>
    );
  }

  if (!report) return <></>;

  return <SharedReportView report={report} onReset={onReset} />;
}
