/**
 * api.ts — all backend API calls in one place.
 *
 * Uses the `VITE_API_URL` env var (default: http://localhost:8000) as the
 * base URL so the same build works with different backends.
 */

import type { ScanResponse } from "../types/scan";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Submit a URL for vulnerability scanning.
 *
 * @param url - The URL to scan.
 * @returns The initial ScanResponse with status "pending".
 * @throws Error if the request fails or the server returns a non-2xx status.
 */
export async function submitScan(url: string): Promise<ScanResponse> {
  const response = await fetch(`${BASE_URL}/scans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Server error: ${response.status}`);
  }

  return response.json() as Promise<ScanResponse>;
}

/**
 * Poll the status of an existing scan.
 *
 * @param scanId - The UUID string returned by submitScan.
 * @returns The current ScanResponse, including report_json when completed.
 * @throws Error if the request fails or the scan is not found.
 */
export async function getScanStatus(scanId: string): Promise<ScanResponse> {
  const response = await fetch(`${BASE_URL}/scans/${scanId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch scan status: ${response.status}`);
  }

  return response.json() as Promise<ScanResponse>;
}
