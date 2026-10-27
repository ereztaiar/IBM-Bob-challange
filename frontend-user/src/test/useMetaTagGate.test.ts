/**
 * Tests for useMetaTagGate — gate TTL logic.
 */

import { beforeEach, describe, expect, it } from "vitest";
import { useMetaTagGate } from "../components/MetaTagGate/useMetaTagGate";
import { renderHook, act } from "@testing-library/react";

const STORAGE_KEY = "meta_ack_at";

describe("useMetaTagGate", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("starts unacknowledged when sessionStorage is empty", () => {
    const { result } = renderHook(() => useMetaTagGate());
    expect(result.current.acknowledged).toBe(false);
  });

  it("becomes acknowledged after calling acknowledge()", () => {
    const { result } = renderHook(() => useMetaTagGate());
    act(() => result.current.acknowledge());
    expect(result.current.acknowledged).toBe(true);
  });

  it("starts acknowledged when a fresh timestamp exists in sessionStorage", () => {
    sessionStorage.setItem(STORAGE_KEY, String(Date.now()));
    const { result } = renderHook(() => useMetaTagGate());
    expect(result.current.acknowledged).toBe(true);
  });

  it("starts unacknowledged when timestamp is older than 30 minutes", () => {
    const expired = Date.now() - 31 * 60 * 1000;
    sessionStorage.setItem(STORAGE_KEY, String(expired));
    const { result } = renderHook(() => useMetaTagGate());
    expect(result.current.acknowledged).toBe(false);
  });
});
