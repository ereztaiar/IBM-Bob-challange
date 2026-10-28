/**
 * ReportView — renders a completed vulnerability scan report.
 *
 * Accepts a `Report` object directly.
 *
 * Shared across the user and admin frontends via ui-shared.
 */

import type { Report } from "../FindingCard/types";
import FindingCard from "../FindingCard";
import styles from "./ReportView.module.css";

/** Severity ordering for display — critical first. */
const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;

/** Colour bucket for the risk score. */
type ScoreLevel = "low" | "medium" | "high";

function scoreLevel(score: number): ScoreLevel {
  if (score >= 70) return "high";
  if (score >= 35) return "medium";
  return "low";
}

export interface ReportViewProps {
  /** The report to display. */
  report: Report;
}

/**
 * Renders the report summary, risk score, recommendations, and findings.
 *
 * @param props - Component props.
 */
export function ReportView({ report }: ReportViewProps): JSX.Element {
  const sorted = [...report.findings].sort((a, b) => {
    const ia = SEVERITY_ORDER.indexOf(a.severity as typeof SEVERITY_ORDER[number]);
    const ib = SEVERITY_ORDER.indexOf(b.severity as typeof SEVERITY_ORDER[number]);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  const level = scoreLevel(report.risk_score);

  return (
    <section className={styles.container} aria-label="Scan report">
      <div className={styles.summary}>
        <div className={styles.summaryHeader}>
          <div>
            <h2 className={styles.summaryTitle}>Scan Report</h2>
            <p className={styles.url}>{report.url}</p>
          </div>
          <div className={styles.scoreBox}>
            <span className={styles.scoreLabel}>Risk Score</span>
            <span className={styles.score} data-level={level}>
              {report.risk_score}/100
            </span>
          </div>
        </div>
        {report.summary && (
          <p className={styles.summaryText}>{report.summary}</p>
        )}
      </div>

      {report.recommendations.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Top Recommendations</h2>
          <ul className={styles.recommendations}>
            {report.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>
          Findings ({sorted.length})
        </h2>
        {sorted.length === 0 ? (
          <p className={styles.noFindings}>No findings detected.</p>
        ) : (
          <ul className={styles.findingsList}>
            {sorted.map((f, i) => (
              <li key={`${f.category}-${i}`}>
                <FindingCard finding={f} />
              </li>
            ))}
          </ul>
        )}
      </div>

    </section>
  );
}

export default ReportView;
