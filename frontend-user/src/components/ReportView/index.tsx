/**
 * ReportView — renders a completed vulnerability scan report.
 *
 * Shows risk score, executive summary, severity-coloured finding cards,
 * and top recommendations. Handles the "failed" scan state with an error box.
 */

import type { ScanResponse } from "../../types/scan";
import FindingCard from "./FindingCard";
import styles from "./ReportView.module.css";
import { useReportView } from "./useReportView";

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
  const { report, hasError, errorMessage, scoreLevel } = useReportView(scan);

  if (hasError) {
    return (
      <div className={styles.report}>
        <div className={styles.errorBox} role="alert">
          <strong>Scan failed:</strong> {errorMessage}
        </div>
        <button className={styles.newScanButton} onClick={onReset}>
          ← Try another URL
        </button>
      </div>
    );
  }

  if (!report) return <></>;

  const severityOrder = ["critical", "high", "medium", "low", "info"];
  const sorted = [...report.findings].sort(
    (a, b) => severityOrder.indexOf(a.severity) - severityOrder.indexOf(b.severity)
  );

  return (
    <div className={styles.report}>
      <div className={styles.header}>
        <h2 className={styles.title}>Scan Report</h2>
        <p className={styles.url}>{report.url}</p>
        <p className={styles.summary}>{report.summary}</p>
        <div className={styles.scoreRow}>
          <span className={styles.scoreLabel}>Risk Score</span>
          <span className={styles.score} data-level={scoreLevel}>
            {report.risk_score}/100
          </span>
        </div>
      </div>

      <hr className={styles.divider} />

      {report.recommendations.length > 0 && (
        <>
          <p className={styles.sectionTitle}>Top Recommendations</p>
          <ul className={styles.recommendations}>
            {report.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
          <hr className={styles.divider} />
        </>
      )}

      <p className={styles.sectionTitle}>
        Findings ({sorted.length})
      </p>
      <div className={styles.findings}>
        {sorted.map((finding, i) => (
          <FindingCard key={i} finding={finding} />
        ))}
      </div>

      <button className={styles.newScanButton} onClick={onReset}>
        ← Scan another URL
      </button>
    </div>
  );
}
