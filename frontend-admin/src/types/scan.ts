/**
 * Shared TypeScript types for the admin frontend — mirrors backend scan schemas.
 *
 * Finding, Report, and Severity are authoritative in ui-shared and
 * re-exported here so existing imports within this app continue to work.
 */

export type { Finding, Report, Severity } from "ui-shared/components/FindingCard/types";

/** Possible states of a vulnerability scan. */
export type ScanStatus = "pending" | "running" | "completed" | "failed";

/** A scan record returned by the API. */
export interface Scan {
  scan_id: string;
  url: string;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  /** Present on GET /admin/scans/{id} once the scan has completed. */
  report_json?: import("ui-shared/components/FindingCard/types").Report | null;
}

/** Paginated list response from GET /admin/scans. */
export interface PaginatedScans {
  items: Scan[];
  total: number;
  page: number;
  page_size: number;
}

/** Dashboard aggregate stats from GET /admin/stats. */
export interface AdminStats {
  total: number;
  by_severity: Record<import("ui-shared/components/FindingCard/types").Severity, number>;
  today: number;
}
