/**
 * api.ts — all HTTP calls for the admin frontend.
 *
 * The base URL is read from the VITE_ADMIN_API_URL env var at build time,
 * falling back to localhost for local development.
 */
import type { AdminStats, PaginatedScans, Scan } from "../types/scan";

const BASE = import.meta.env.VITE_ADMIN_API_URL ?? "http://localhost:8000";

/** Stored JWT token (in-module reference, set via setToken). */
let _token: string | null = sessionStorage.getItem("admin_token");

/**
 * Persist the JWT token for subsequent authenticated requests.
 * @param token - The JWT string received from /auth/admin/login.
 */
export function setToken(token: string): void {
  _token = token;
  sessionStorage.setItem("admin_token", token);
}

/** Clear the stored JWT (logout). */
export function clearToken(): void {
  _token = null;
  sessionStorage.removeItem("admin_token");
}

/** Return the currently stored token or null. */
export function getToken(): string | null {
  return _token;
}

/**
 * Build common fetch headers, injecting Authorization when a token is present.
 * @returns Headers object.
 */
function buildHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (_token) {
    headers["Authorization"] = `Bearer ${_token}`;
  }
  return headers;
}

/**
 * Authenticate against the admin login endpoint.
 * @param username - Admin username.
 * @param password - Admin password.
 * @returns JWT access token string.
 * @throws Error with message if credentials are invalid.
 */
export async function loginAdmin(
  username: string,
  password: string
): Promise<string> {
  const res = await fetch(`${BASE}/auth/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new Error("Invalid credentials");
  }
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

/**
 * Fetch paginated scan list with optional filters.
 * @param page - 1-based page number.
 * @param status - Optional status filter.
 * @param severity - Optional severity filter.
 */
export async function listScans(
  page = 1,
  status?: string,
  severity?: string
): Promise<PaginatedScans> {
  const params = new URLSearchParams({ page: String(page) });
  if (status) params.set("status", status);
  if (severity) params.set("severity", severity);

  const res = await fetch(`${BASE}/admin/scans?${params.toString()}`, {
    headers: buildHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch scans: ${res.status}`);
  return res.json() as Promise<PaginatedScans>;
}

/**
 * Fetch a single scan's full detail including report.
 * @param id - The scan UUID.
 */
export async function getScanDetail(id: string): Promise<Scan> {
  const res = await fetch(`${BASE}/admin/scans/${id}`, {
    headers: buildHeaders(),
  });
  if (!res.ok) throw new Error(`Scan not found: ${res.status}`);
  return res.json() as Promise<Scan>;
}

/**
 * Fetch aggregate dashboard stats.
 */
export async function getAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${BASE}/admin/stats`, {
    headers: buildHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json() as Promise<AdminStats>;
}

/**
 * Soft-delete a scan record.
 * @param id - The scan UUID.
 */
export async function deleteScan(id: string): Promise<void> {
  const res = await fetch(`${BASE}/admin/scans/${id}`, {
    method: "DELETE",
    headers: buildHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete scan: ${res.status}`);
}
