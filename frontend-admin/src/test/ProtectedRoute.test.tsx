/**
 * ProtectedRoute.test.tsx — tests for the ProtectedRoute component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";

/** Wraps a ProtectedRoute inside a MemoryRouter for testing. */
function renderRoute(isAuthenticated: boolean) {
  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route path="/login" element={<p>Login Page</p>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <p>Protected Content</p>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("renders children when authenticated", () => {
    renderRoute(true);
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("redirects to /login when not authenticated", () => {
    renderRoute(false);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });
});
