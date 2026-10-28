/**
 * MetaTagGate — disclosure notice that must be acknowledged before scanning.
 *
 * Renders a notice explaining that the tool uses meta-tag based detection
 * techniques. The user must click "I Understand" to proceed. The gate uses
 * {@link useMetaTagGate} to persist acknowledgement for 30 minutes.
 */

import styles from "./MetaTagGate.module.css";
import type { MetaTagGateState } from "./useMetaTagGate";

interface MetaTagGateProps {
  /** Acknowledgement state and callback from useMetaTagGate. */
  gate: MetaTagGateState;
}

/**
 * Renders the disclosure gate or nothing if already acknowledged.
 *
 * @param props - Component props.
 */
export default function MetaTagGate({ gate }: MetaTagGateProps): JSX.Element | null {
  if (gate.acknowledged) return null;

  return (
    <div className={styles.gate} role="alertdialog" aria-labelledby="gate-title">
      <h2 id="gate-title">⚠ Before you scan</h2>
      <p>
        This tool performs automated security checks against the URL you provide.
        Please read and acknowledge the following before proceeding:
      </p>
      <ul>
        <li>Only scan websites you own or have explicit permission to test.</li>
        <li>Scans send HTTP requests to the target URL and may appear in its logs.</li>
        <li>
          Some checks (e.g. XSS probe, env-file probing) send modified requests
          to the server — these are benign but may trigger security monitoring.
        </li>
        <li>Results are informational only and do not constitute a full penetration test.</li>
      </ul>
      <button className={styles.ackButton} onClick={gate.acknowledge}>
        I Understand — Continue
      </button>
    </div>
  );
}
