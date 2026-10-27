/**
 * useMetaTagGate — manages the 30-minute meta-tag disclosure acknowledgement.
 *
 * Acknowledgement timestamp is stored in sessionStorage under the key
 * `meta_ack_at`. The gate reappears when the session ends or the TTL expires.
 */

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "meta_ack_at";
const TTL_MS = 30 * 60 * 1000; // 30 minutes

/** Return value of useMetaTagGate. */
export interface MetaTagGateState {
  /** Whether the user has acknowledged and the TTL has not expired. */
  acknowledged: boolean;
  /** Record the acknowledgement at the current timestamp. */
  acknowledge: () => void;
}

/**
 * Custom hook for the meta-tag disclosure gate.
 *
 * @returns acknowledged flag and the acknowledge() callback.
 */
export function useMetaTagGate(): MetaTagGateState {
  const [acknowledged, setAcknowledged] = useState<boolean>(() =>
    _isValid()
  );

  // Re-check every minute in case the TTL expires mid-session.
  useEffect(() => {
    const id = setInterval(() => {
      setAcknowledged(_isValid());
    }, 60_000);
    return () => clearInterval(id);
  }, []);

  const acknowledge = useCallback(() => {
    sessionStorage.setItem(STORAGE_KEY, String(Date.now()));
    setAcknowledged(true);
  }, []);

  return { acknowledged, acknowledge };
}

/** Return true if a stored ack timestamp exists and is within the TTL. */
function _isValid(): boolean {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return false;
  const ts = Number(raw);
  return !isNaN(ts) && Date.now() - ts < TTL_MS;
}
