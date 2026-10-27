/**
 * FindingCard — displays a single vulnerability finding.
 *
 * Colour-coded by severity using CSS data attributes.
 */

import type { Finding } from "../../../types/scan";
import styles from "./FindingCard.module.css";

interface FindingCardProps {
  /** The finding to render. */
  finding: Finding;
}

/**
 * Renders severity badge, title, description, evidence, and remediation.
 *
 * @param props - Component props.
 */
export default function FindingCard({ finding }: FindingCardProps): JSX.Element {
  return (
    <article className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.badge} data-severity={finding.severity}>
          {finding.severity}
        </span>
        <h3 className={styles.title}>{finding.title}</h3>
      </div>

      <p className={styles.category}>{finding.category}</p>

      <div className={styles.section}>
        <p className={styles.sectionLabel}>Description</p>
        <p className={styles.sectionText}>{finding.description}</p>
      </div>

      {finding.evidence && (
        <div className={styles.section}>
          <p className={styles.sectionLabel}>Evidence</p>
          <pre className={styles.evidence}>{finding.evidence}</pre>
        </div>
      )}

      {finding.remediation && (
        <div className={styles.section}>
          <p className={styles.sectionLabel}>Remediation</p>
          <p className={styles.sectionText}>{finding.remediation}</p>
        </div>
      )}
    </article>
  );
}
