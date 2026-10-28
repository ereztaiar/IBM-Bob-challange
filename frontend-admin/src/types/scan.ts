/** Shared TypeScript types for the admin frontend — mirrors backend scan schemas. */

/** Possible states of a vulnerability scan. */
export type ScanStatus = "pending" | "running" | "completed" | "failed";

/** Severity levels for individual findings. */
export type Severity = "critical" | "high" | "medium" | "low" | "info";

/** A single finding produced by an agent check. */
export interface Finding {
  /** Check category, e.g. "headers", "ssl_tls". */
  category: string;
  /** Human-readable title. */
  title: string;
  /** Detailed description of the issue. */
  description: string;
  /** Severity level. */
  severity: Severity;
  /** Raw evidence supporting the finding. */
  evidence?: string;
  /** Remediation advice. */
  remediation?: string;
}

/** The full structured report attached to a completed scan. */
export interface Report {
  /** The URL that was scanned. */
  url: string;
  /** Summary paragraph written by the report-writer agent. */
  summary: string;
  /** Overall risk score, 0-100. */
  risk_score: number;
  /** All findings across all check agents. */
  findings: Finding[];
  /** Top recommendations. */
  recommendations: string[];
}

/** A scan record returned by the API. */
export interface Scan {
  scan_id: string;
  url: string;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  /** Present on GET /admin/scans/{id} once the scan has completed. */
  report_json?: Report | null;
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
