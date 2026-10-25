/**
 * useScanTable.ts — state and sort/filter logic for the ScanTable component.
 */
import { useState, useCallback, useEffect } from "react";
import { listScans } from "../../services/api";
import type { Scan, ScanStatus } from "../../types/scan";

/** Sort directions. */
export type SortDirection = "asc" | "desc";

/** Columns that can be sorted. */
export type SortColumn = "created_at" | "status" | "url";

/** Return type for useScanTable. */
export interface UseScanTableReturn {
  scans: Scan[];
  loading: boolean;
  error: string | null;
  page: number;
  total: number;
  statusFilter: string;
  sortColumn: SortColumn;
  sortDir: SortDirection;
  setPage: (p: number) => void;
  setStatusFilter: (s: string) => void;
  setSortColumn: (c: SortColumn) => void;
  setSortDir: (d: SortDirection) => void;
  refresh: () => void;
}

/**
 * Manages fetching, sorting, and filtering the scan table.
 * Calls the API whenever page or filter changes.
 */
export function useScanTable(): UseScanTableReturn {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sortColumn, setSortColumn] = useState<SortColumn>("created_at");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");

  /** Fetch the current page from the API. */
  const fetch_ = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listScans(
        page,
        statusFilter as ScanStatus | undefined || undefined
      );
      // Client-side sort (server returns unsorted within page)
      const sorted = [...result.items].sort((a, b) => {
        const valA = a[sortColumn] ?? "";
        const valB = b[sortColumn] ?? "";
        const cmp = String(valA).localeCompare(String(valB));
        return sortDir === "asc" ? cmp : -cmp;
      });
      setScans(sorted);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scans");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, sortColumn, sortDir]);

  useEffect(() => {
    void fetch_();
  }, [fetch_]);

  return {
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
    refresh: fetch_,
  };
}
