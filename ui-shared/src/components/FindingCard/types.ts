/** Severity levels for a vulnerability finding. */
export type Severity = "critical" | "high" | "medium" | "low" | "info";

/** A single vulnerability finding. */
export interface Finding {
  category: string;
  severity: Severity;
  title: string;
  description: string;
  evidence?: string;
  remediation?: string;
}

/** A full scan report. */
export interface Report {
  url: string;
  summary: string;
  risk_score: number;
  findings: Finding[];
  recommendations: string[];
}
