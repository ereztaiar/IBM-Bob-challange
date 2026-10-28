/**
 * useReportView — derives display state from a completed ScanResponse.
 */

import type { Report, ScanResponse } from "../../types/scan";

/** Severity level bucket used for the risk-score colour. */
type ScoreLevel = "low" | "medium" | "high";

/** Return value of useReportView. */
export interface ReportViewState {
  report: Report | null;
  hasError: boolean;
  errorMessage: string;
  scoreLevel: ScoreLevel;
}

/**
 * Derives display values from a ScanResponse.
 *
 * @param scan - The completed (or failed) scan.
 * @returns Derived display state for ReportView.
 */
export function useReportView(scan: ScanResponse): ReportViewState {
  if (scan.status === "failed") {
    return {
      report: null,
      hasError: true,
      errorMessage: scan.error_message ?? "The scan failed for an unknown reason.",
      scoreLevel: "low",
    };
  }

  const report = scan.report_json ?? null;
  const score = report?.risk_score ?? 0;

  const scoreLevel: ScoreLevel =
    score >= 70 ? "high" : score >= 35 ? "medium" : "low";

  return { report, hasError: false, errorMessage: "", scoreLevel };
}
