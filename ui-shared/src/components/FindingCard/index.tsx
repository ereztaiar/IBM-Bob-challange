/**
 * FindingCard — displays a single vulnerability finding.
 *
 * Colour-coded by severity using a left-border accent and badge.
 * Shared across the user and admin frontends via ui-shared.
 */

import type { Finding } from "./types";
import styles from "./FindingCard.module.css";

export interface FindingCardProps {
  /** The finding to render. */
  finding: Finding;
}

/**
 * Renders severity badge, title, description, evidence, and remediation.
 *
 * @param props - Component props.
 */
export function FindingCard({ finding }: FindingCardProps): JSX.Element {
  return (
    <article
      className={`${styles.card} ${styles[finding.severity] ?? ""}`}
      aria-label={`Finding: ${finding.title}`}
    >
      <header className={styles.header}>
        <span className={`${styles.badge} ${styles[finding.severity] ?? ""}`}>
          {finding.severity.toUpperCase()}
        </span>
        <h3 className={styles.title}>{finding.title}</h3>
      </header>

      <p className={styles.category}>{finding.category}</p>

      <p className={styles.description}>{finding.description}</p>

      {finding.remediation && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Remediation</h4>
          <p className={styles.sectionBody}>{finding.remediation}</p>
        </div>
      )}

      {finding.evidence && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Evidence</h4>
          <pre className={styles.evidence}>{finding.evidence}</pre>
        </div>
      )}
    </article>
  );
}

export default FindingCard;
