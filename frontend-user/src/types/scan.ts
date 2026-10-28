/**
 * Shared TypeScript types matching the backend scan schemas.
 *
 * Finding, Report, and Severity are authoritative in ui-shared and
 * re-exported here so existing imports within this app continue to work.
 */

export type { Finding, Report, Severity } from "ui-shared/components/FindingCard/types";

/** Possible scan lifecycle states. */
export type ScanStatus = "pending" | "running" | "completed" | "failed";

/** Response from POST /scans and GET /scans/{id}. */
export interface ScanResponse {
  scan_id: string;
  url: string;
  status: ScanStatus;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  report_json: import("ui-shared/components/FindingCard/types").Report | null;
  prompt_service_down: boolean;
}
