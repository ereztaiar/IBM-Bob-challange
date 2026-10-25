/** Shared TypeScript types for the admin frontend — mirrors backend scan schemas. */

/** Possible states of a vulnerability scan. */
export type ScanStatus = "pending" | "running" | "completed" | "failed";

/** Severity levels for individual findings. */
export type Severity = "critical" | "high" | "medium" | "low" | "info";

/** A single finding produced by an agent check. */
export interface Finding {
  /** Machine-readable check identifier, e.g. "xss", "ssl_tls". */
  check: string;
  /** Human-readable title. */
  title: string;
  /** Detailed description of the issue. */
  description: string;
  /** Severity level. */
  severity: Severity;
  /** Optional remediation advice. */
  remediation?: string;
  /** Optional reference URLs. */
  references?: string[];
}

/** The full structured report attached to a completed scan. */
export interface Report {
  /** Summary paragraph written by the report-writer agent. */
  summary: string;
  /** All findings across all check agents. */
  findings: Finding[];
}

/** A scan record returned by the API. */
export interface Scan {
  id: string;
  url: string;
  status: ScanStatus;
  created_at: string;
  completed_at?: string;
  report?: Report;
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
  by_severity: Record<Severity, number>;
  today: number;
}
