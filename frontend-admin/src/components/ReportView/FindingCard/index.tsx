/**
 * FindingCard — displays a single vulnerability finding with severity colouring.
 * Shared across the user and admin frontends (re-implemented independently).
 */
import type { Finding } from "../../types/scan";
import styles from "./FindingCard.module.css";

interface FindingCardProps {
  /** The finding to display. */
  finding: Finding;
}

/** CSS class suffix per severity level. */
const SEVERITY_CLASS: Record<string, string> = {
  critical: styles.critical,
  high: styles.high,
  medium: styles.medium,
  low: styles.low,
  info: styles.info,
};

/**
 * Renders a finding card with severity badge, title, description, and remediation.
 * @param props.finding - The Finding object to render.
 */
function FindingCard({ finding }: FindingCardProps): JSX.Element {
  const severityClass = SEVERITY_CLASS[finding.severity] ?? "";

  return (
    <article
      className={`${styles.card} ${severityClass}`}
      aria-label={`Finding: ${finding.title}`}
    >
      <header className={styles.header}>
        <span className={`${styles.badge} ${severityClass}`}>
          {finding.severity.toUpperCase()}
        </span>
        <h3 className={styles.title}>{finding.title}</h3>
      </header>

      <p className={styles.description}>{finding.description}</p>

      {finding.remediation && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Remediation</h4>
          <p className={styles.sectionBody}>{finding.remediation}</p>
        </div>
      )}

      {finding.references && finding.references.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>References</h4>
          <ul className={styles.refList}>
            {finding.references.map((ref) => (
              <li key={ref}>
                <a href={ref} target="_blank" rel="noopener noreferrer">
                  {ref}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

export default FindingCard;
