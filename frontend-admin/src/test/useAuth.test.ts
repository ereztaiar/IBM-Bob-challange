/**
 * useAuth.test.ts — unit tests for the useAuth hook.
 */
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAuth } from "../hooks/useAuth";
import * as api from "../services/api";

describe("useAuth", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("initialises as unauthenticated when no token in sessionStorage", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("sets isAuthenticated to true on successful login", async () => {
    vi.spyOn(api, "loginAdmin").mockResolvedValue("fake-jwt");
    vi.spyOn(api, "setToken").mockImplementation(() => {});

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.login("admin", "password");
    });
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("sets error on failed login", async () => {
    vi.spyOn(api, "loginAdmin").mockRejectedValue(new Error("Invalid credentials"));

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.login("admin", "wrong");
    });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe("Invalid credentials");
  });

  it("clears isAuthenticated on logout", async () => {
    vi.spyOn(api, "loginAdmin").mockResolvedValue("fake-jwt");
    vi.spyOn(api, "setToken").mockImplementation(() => {});
    vi.spyOn(api, "clearToken").mockImplementation(() => {});

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.login("admin", "password");
    });
    act(() => result.current.logout());
    expect(result.current.isAuthenticated).toBe(false);
  });
});
