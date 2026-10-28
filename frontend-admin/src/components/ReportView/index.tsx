/**
 * ReportView — renders a completed scan report with findings grouped by severity.
 * Used on the admin scan detail page.
 */
import type { Report } from "../../types/scan";
import FindingCard from "./FindingCard";
import styles from "./ReportView.module.css";

interface ReportViewProps {
  /** The report object from a completed scan. */
  report: Report;
}

/** Severity ordering for display — critical first. */
const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;

/**
 * Renders the report summary and all findings sorted by severity.
 * @param props.report - The Report to display.
 */
function ReportView({ report }: ReportViewProps): JSX.Element {
  const sorted = [...report.findings].sort((a, b) => {
    const ia = SEVERITY_ORDER.indexOf(a.severity as typeof SEVERITY_ORDER[number]);
    const ib = SEVERITY_ORDER.indexOf(b.severity as typeof SEVERITY_ORDER[number]);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  return (
    <section className={styles.container} aria-label="Scan report">
      {report.summary && (
        <div className={styles.summary}>
          <h2 className={styles.summaryTitle}>Summary</h2>
          <p className={styles.summaryText}>{report.summary}</p>
          <p className={styles.score}>Risk score: {report.risk_score}/100</p>
        </div>
      )}

      {report.recommendations?.length > 0 && (
        <>
          <h2 className={styles.findingsTitle}>Top Recommendations</h2>
          <ul className={styles.recommendations}>
            {report.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </>
      )}

      <h2 className={styles.findingsTitle}>
        Findings ({sorted.length})
      </h2>

      {sorted.length === 0 ? (
        <p className={styles.noFindings}>No findings detected.</p>
      ) : (
        <ul className={styles.list}>
          {sorted.map((f, i) => (
            <li key={`${f.category}-${i}`} className={styles.item}>
              <FindingCard finding={f} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default ReportView;
