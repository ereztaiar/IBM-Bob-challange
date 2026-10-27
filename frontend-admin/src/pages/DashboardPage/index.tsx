/**
 * DashboardPage — main admin dashboard.
 * Shows aggregate stats at the top and a sortable/filterable scan table below.
 */
import { useEffect, useState } from "react";
import StatCard from "../../components/StatCard";
import ScanTable from "../../components/ScanTable";
import { useScanTable } from "../../components/ScanTable/useScanTable";
import { getAdminStats } from "../../services/api";
import type { AdminStats } from "../../types/scan";
import styles from "./DashboardPage.module.css";

/**
 * Fetches and renders stats cards and the scan table.
 */
function DashboardPage(): JSX.Element {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const {
    scans,
    loading,
    error,
    page,
    total,
    statusFilter,
    sortColumn,
    sortDir,
    setPage,
    setStatusFilter,
    setSortColumn,
    setSortDir,
  } = useScanTable();

  /** Load aggregate stats once on mount. */
  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch(() => {
        /* Stats are non-critical; silently ignore on failure */
      });
  }, []);

  /**
   * Toggle sort column or direction.
   * @param col - Column clicked.
   */
  function handleSort(col: typeof sortColumn): void {
    if (col === sortColumn) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(col);
      setSortDir("desc");
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Dashboard</h1>

      {stats && (
        <div className={styles.statsRow}>
          <StatCard label="Total Scans" value={stats.total} />
          <StatCard
            label="Critical Findings"
            value={stats.by_severity.critical ?? 0}
            variant="critical"
          />
          <StatCard
            label="Scans Today"
            value={stats.today}
            variant="today"
          />
        </div>
      )}

      <ScanTable
        scans={scans}
        loading={loading}
        error={error}
        page={page}
        total={total}
        statusFilter={statusFilter}
        sortColumn={sortColumn}
        sortDir={sortDir}
        onPageChange={setPage}
        onStatusFilter={setStatusFilter}
        onSort={handleSort}
      />
    </div>
  );
}

export default DashboardPage;
