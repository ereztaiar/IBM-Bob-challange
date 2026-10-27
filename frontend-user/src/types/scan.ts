/**
 * Shared TypeScript types matching the backend scan schemas.
 */

/** Possible scan lifecycle states. */
export type ScanStatus = "pending" | "running" | "completed" | "failed";

/** Severity levels for a finding. */
export type Severity = "critical" | "high" | "medium" | "low" | "info";

/** A single vulnerability finding returned in the report. */
export interface Finding {
  category: string;
  severity: Severity;
  title: string;
  description: string;
  evidence: string;
  remediation: string;
}

/** Report JSON embedded in a completed scan. */
export interface Report {
  url: string;
  summary: string;
  risk_score: number;
  findings: Finding[];
  recommendations: string[];
}

/** Response from POST /scans and GET /scans/{id}. */
export interface ScanResponse {
  scan_id: string;
  url: string;
  status: ScanStatus;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  report_json: Report | null;
}
