/**
 * useScanPoller — polls GET /scans/{id} every 3 seconds until terminal state.
 *
 * Stops polling when status is "completed" or "failed".
 * Also stops on unmount to avoid state updates after component destruction.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getScanStatus } from "../services/api";
import type { ScanResponse, ScanStatus } from "../types/scan";

const POLL_INTERVAL_MS = 3000;
const TERMINAL: Set<ScanStatus> = new Set(["completed", "failed"]);

/** Return value of useScanPoller. */
export interface ScanPollerState {
  scan: ScanResponse | null;
  isPolling: boolean;
  pollError: string | null;
}

/**
 * Begins polling for the given scanId immediately on mount.
 *
 * @param scanId - UUID of the scan to track, or null to idle.
 * @returns Current scan data, polling flag, and any poll error.
 */
export function useScanPoller(scanId: string | null): ScanPollerState {
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const poll = useCallback(async (id: string) => {
    try {
      const result = await getScanStatus(id);
      setScan(result);
      if (TERMINAL.has(result.status)) {
        stopPolling();
      }
    } catch (err) {
      setPollError(err instanceof Error ? err.message : "Unknown polling error");
      stopPolling();
    }
  }, [stopPolling]);

  useEffect(() => {
    if (!scanId) return;

    setScan(null);
    setPollError(null);
    setIsPolling(true);

    // Poll immediately then on interval
    void poll(scanId);
    intervalRef.current = setInterval(() => void poll(scanId), POLL_INTERVAL_MS);

    return stopPolling;
  }, [scanId, poll, stopPolling]);

  return { scan, isPolling, pollError };
}
