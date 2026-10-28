/**
 * ScanDetailPage — full report view for a single scan, loaded by ID.
 * Accessible at /scans/:id.
 */
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import ReportView from "../../components/ReportView";
import { getScanDetail } from "../../services/api";
import type { Scan } from "../../types/scan";
import styles from "./ScanDetailPage.module.css";

/**
 * Loads a scan by its UUID from the route param and renders the report.
 */
function ScanDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getScanDetail(id)
      .then(setScan)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load scan");
      })
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className={styles.page}>
      <Link to="/dashboard" className={styles.back}>
        ← Back to Dashboard
      </Link>

      {loading && <p className={styles.loading}>Loading scan…</p>}
      {error && <p className={styles.error}>{error}</p>}

      {scan && (
        <>
          <h1 className={styles.heading}>Scan Report</h1>
          <p className={styles.meta}>
            <strong>URL:</strong> {scan.url}
          </p>
          <p className={styles.meta}>
            <strong>Status:</strong> {scan.status}
          </p>
          {scan.error_message && (
            <p className={styles.error}>{scan.error_message}</p>
          )}
          {scan.completed_at && (
            <p className={styles.meta}>
              <strong>Completed:</strong>{" "}
              {new Date(scan.completed_at).toLocaleString()}
            </p>
          )}

          {scan.report_json ? (
            <ReportView report={scan.report_json} />
          ) : (
            <p className={styles.pending}>
              Report not yet available — scan is {scan.status}.
            </p>
          )}
        </>
      )}
    </div>
  );
}

export default ScanDetailPage;
