/**
 * StatCard — displays a single aggregate metric on the dashboard.
 */
import styles from "./StatCard.module.css";

interface StatCardProps {
  /** Short label, e.g. "Total Scans". */
  label: string;
  /** The numeric value to display prominently. */
  value: number;
  /** Optional accent colour class suffix: "default" | "critical" | "today". */
  variant?: "default" | "critical" | "today";
}

/**
 * Renders a labelled metric card.
 * @param props.label - Descriptive label shown below the value.
 * @param props.value - Numeric metric.
 * @param props.variant - Visual accent variant.
 */
function StatCard({
  label,
  value,
  variant = "default",
}: StatCardProps): JSX.Element {
  return (
    <div className={`${styles.card} ${styles[variant]}`} role="region" aria-label={label}>
      <span className={styles.value}>{value.toLocaleString()}</span>
      <span className={styles.label}>{label}</span>
    </div>
  );
}

export default StatCard;
