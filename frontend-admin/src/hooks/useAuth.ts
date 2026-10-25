/**
 * useAuth.ts — authentication state hook for the admin frontend.
 *
 * Stores the JWT in sessionStorage (clears on tab close).
 * Exposes login(), logout(), and isAuthenticated.
 */
import { useState, useCallback } from "react";
import { loginAdmin, setToken, clearToken, getToken } from "../services/api";

/** Return type for useAuth. */
export interface UseAuthReturn {
  /** True when a JWT is present in sessionStorage. */
  isAuthenticated: boolean;
  /** Attempt to authenticate. Throws on invalid credentials. */
  login: (username: string, password: string) => Promise<void>;
  /** Clear the stored JWT and mark as unauthenticated. */
  logout: () => void;
  /** Non-null error message when the last login attempt failed. */
  error: string | null;
  /** True while a login request is in-flight. */
  loading: boolean;
}

/**
 * Hook providing authentication state and actions.
 * Initialises from sessionStorage so a page refresh keeps the admin logged in
 * for the duration of the browser session.
 */
export function useAuth(): UseAuthReturn {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => getToken() !== null
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  /**
   * Authenticate with the backend and persist the token.
   * @param username - Admin username.
   * @param password - Admin password.
   */
  const login = useCallback(
    async (username: string, password: string): Promise<void> => {
      setLoading(true);
      setError(null);
      try {
        const token = await loginAdmin(username, password);
        setToken(token);
        setIsAuthenticated(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /** Clear the token and update state. */
  const logout = useCallback((): void => {
    clearToken();
    setIsAuthenticated(false);
  }, []);

  return { isAuthenticated, login, logout, error, loading };
}
