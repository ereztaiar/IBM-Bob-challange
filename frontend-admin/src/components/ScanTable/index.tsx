/**
 * ScanTable — sortable, filterable table of all vulnerability scans.
 * Used on the dashboard page.
 */
import { useNavigate } from "react-router-dom";
import type { Scan } from "../../types/scan";
import type { SortColumn, SortDirection } from "./useScanTable";
import styles from "./ScanTable.module.css";

interface ScanTableProps {
  scans: Scan[];
  loading: boolean;
  error: string | null;
  page: number;
  total: number;
  statusFilter: string;
  sortColumn: SortColumn;
  sortDir: SortDirection;
  onPageChange: (p: number) => void;
  onStatusFilter: (s: string) => void;
  onSort: (col: SortColumn) => void;
}

/** Severity badge colours. */
const STATUS_CLASSES: Record<string, string> = {
  completed: styles.statusCompleted,
  running: styles.statusRunning,
  pending: styles.statusPending,
  failed: styles.statusFailed,
};

/**
 * Format an ISO date string to a readable local date-time.
 * @param iso - ISO 8601 string.
 */
function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

/**
 * Renders the scan history table with sort controls and status filter.
 */
function ScanTable({
  scans,
  loading,
  error,
  page,
  total,
  statusFilter,
  sortColumn,
  sortDir,
  onPageChange,
  onStatusFilter,
  onSort,
}: ScanTableProps): JSX.Element {
  const navigate = useNavigate();
  const pageSize = 20;
  const totalPages = Math.ceil(total / pageSize);

  /**
   * Toggle sort direction or switch sort column.
   * @param col - Column to sort by.
   */
  function handleSort(col: SortColumn): void {
    onSort(col);
  }

  /** Arrow indicator for the active sort column. */
  function ariaSort(col: SortColumn): "none" | "ascending" | "descending" {
    if (sortColumn !== col) return "none";
    return sortDir === "asc" ? "ascending" : "descending";
  }

  function sortIndicator(col: SortColumn): string {
    if (sortColumn !== col) return "";
    return sortDir === "asc" ? " ↑" : " ↓";
  }

  return (
    <div className={styles.wrapper}>
      {/* Filters */}
      <div className={styles.toolbar}>
        <label htmlFor="status-filter" className={styles.filterLabel}>
          Status:
        </label>
        <select
          id="status-filter"
          className={styles.select}
          value={statusFilter}
          onChange={(e) => onStatusFilter(e.target.value)}
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {loading ? (
        <p className={styles.loading}>Loading…</p>
      ) : (
        <table className={styles.table} aria-label="Scan history">
          <thead>
            <tr>
              <th
                className={styles.th}
                onClick={() => handleSort("url")}
                aria-sort={ariaSort("url")}
              >
                URL{sortIndicator("url")}
              </th>
              <th
                className={styles.th}
                onClick={() => handleSort("status")}
                aria-sort={ariaSort("status")}
              >
                Status{sortIndicator("status")}
              </th>
              <th
                className={styles.th}
                onClick={() => handleSort("created_at")}
                aria-sort={ariaSort("created_at")}
              >
                Created{sortIndicator("created_at")}
              </th>
              <th className={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {scans.length === 0 && (
              <tr>
                <td colSpan={4} className={styles.empty}>
                  No scans found.
                </td>
              </tr>
            )}
            {scans.map((scan) => (
              <tr key={scan.scan_id} className={styles.row}>
                <td className={styles.td}>{scan.url}</td>
                <td className={styles.td}>
                  <span
                    className={`${styles.status} ${STATUS_CLASSES[scan.status] ?? ""}`}
                  >
                    {scan.status}
                  </span>
                </td>
                <td className={styles.td}>{formatDate(scan.created_at)}</td>
                <td className={styles.td}>
                  <button
                    className={styles.viewBtn}
                    onClick={() => navigate(`/scans/${scan.scan_id}`)}
                    aria-label={`View scan for ${scan.url}`}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button
            className={styles.pageBtn}
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            ← Prev
          </button>
          <span className={styles.pageInfo}>
            Page {page} of {totalPages}
          </span>
          <button
            className={styles.pageBtn}
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

export default ScanTable;
