/**
 * LoginForm.test.tsx — tests for the LoginForm component.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import LoginForm from "../components/LoginForm";

describe("LoginForm", () => {
  it("renders username and password inputs", () => {
    render(<LoginForm onLogin={vi.fn()} error={null} loading={false} />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders submit button", () => {
    render(<LoginForm onLogin={vi.fn()} error={null} loading={false} />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows error message when error prop is set", () => {
    render(
      <LoginForm onLogin={vi.fn()} error="Invalid credentials" loading={false} />
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials");
  });

  it("disables the button while loading", () => {
    render(<LoginForm onLogin={vi.fn()} error={null} loading={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onLogin with username and password on submit", async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onLogin={onLogin} error={null} loading={false} />);

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: "admin" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "secret" },
    });
    fireEvent.submit(screen.getByRole("form"));

    await waitFor(() => {
      expect(onLogin).toHaveBeenCalledWith("admin", "secret");
    });
  });
});
