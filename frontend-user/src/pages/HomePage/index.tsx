/**
 * HomePage — the single-page scan submission and report view.
 *
 * Layout:
 *   1. MetaTagGate    (blocks the form until acknowledged)
 *   2. ScanActionsBar (always visible once a scan has been submitted)
 *   3. ScanForm       (visible after acknowledgement; hidden while scanning)
 *   4. ScanSpinner    (shown while pending/running)
 *   5. ReportView     (shown on completed or failed)
 */

import { useState } from "react";
import MetaTagGate from "../../components/MetaTagGate";
import { useMetaTagGate } from "../../components/MetaTagGate/useMetaTagGate";
import ReportView from "../../components/ReportView";
import ScanActionsBar from "../../components/ScanActionsBar";
import ScanForm from "../../components/ScanForm";
import ScanSpinner from "../../components/ScanSpinner";
import { useScanPoller } from "../../hooks/useScanPoller";
import { submitScan } from "../../services/api";
import styles from "./HomePage.module.css";

/**
 * Renders the full scan workflow on a single page.
 */
export default function HomePage(): JSX.Element {
  const gate = useMetaTagGate();
  const [scanId, setScanId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [scannedUrl, setScannedUrl] = useState<string | null>(null);

  const { scan, isPolling } = useScanPoller(scanId);

  const isScanning = isPolling || (scan !== null && scan.status === "running");
  const isDone = scan !== null && (scan.status === "completed" || scan.status === "failed");

  /**
   * Submit a URL for scanning. Sets the scanId which triggers polling.
   *
   * @param url - The URL to scan.
   */
  async function handleSubmit(url: string, prompt: string = ""): Promise<void> {
    setSubmitError(null);
    try {
      const result = await submitScan(url, prompt);
      setScanId(result.scan_id);
      setScannedUrl(url);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed.");
    }
  }

  /** Reset state to allow a new scan. */
  function handleReset(): void {
    setScanId(null);
    setSubmitError(null);
    setScannedUrl(null);
  }

  /**
   * Reset state and immediately re-submit with a (possibly different) URL.
   *
   * @param url - The URL to scan next.
   */
  function handleRescan(url: string): void {
    setScanId(null);
    setSubmitError(null);
    setScannedUrl(null);
    void handleSubmit(url, "");
  }

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        {!isDone && (
          <div className={styles.hero}>
            <h1 className={styles.heroTitle}>Website Vulnerability Checker</h1>
            <p className={styles.heroSub}>
              Enter a URL to scan for common security issues.
            </p>
          </div>
        )}

        <MetaTagGate gate={gate} />

        {gate.acknowledged && scannedUrl !== null && (
          <ScanActionsBar
            currentUrl={scannedUrl}
            onScanAgain={() => handleRescan(scannedUrl)}
            onScanNew={handleRescan}
            isScanning={isScanning}
          />
        )}

        {gate.acknowledged && !isScanning && !isDone && (
          <>
            <ScanForm
              onSubmit={handleSubmit}
              isScanning={false}
              promptDisabled={scan?.prompt_service_down === true}
            />
            {submitError && (
              <p className={styles.submitError} role="alert">
                {submitError}
              </p>
            )}
          </>
        )}

        {isScanning && scan && <ScanSpinner status={scan.status} />}
        {isScanning && !scan && <ScanSpinner status="pending" />}

        {isDone && scan && (
          <ReportView scan={scan} onReset={handleReset} />
        )}
      </div>
    </div>
  );
}
