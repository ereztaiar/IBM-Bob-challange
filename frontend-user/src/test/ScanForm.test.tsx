/**
 * Tests for ScanForm component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ScanForm from "../components/ScanForm";

describe("ScanForm", () => {
  it("renders the URL input and submit button", () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={false} />);
    expect(screen.getByLabelText(/enter a website url/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /scan/i })).toBeInTheDocument();
  });

  it("shows an error when submitted with an empty value", async () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={false} />);
    await userEvent.click(screen.getByRole("button", { name: /scan/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/Please enter a URL/i);
  });

  it("shows an error for an invalid URL", async () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={false} />);
    await userEvent.type(screen.getByLabelText(/enter a website url/i), "not-a-url");
    await userEvent.click(screen.getByRole("button", { name: /scan/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/valid URL/i);
  });

  it("calls onSubmit with the URL and empty prompt when a valid URL is entered", async () => {
    const onSubmit = vi.fn();
    render(<ScanForm onSubmit={onSubmit} isScanning={false} />);
    await userEvent.type(screen.getByLabelText(/enter a website url/i), "https://example.com");
    await userEvent.click(screen.getByRole("button", { name: /scan/i }));
    expect(onSubmit).toHaveBeenCalledWith("https://example.com", "");
  });

  it("disables the URL input and submit button while scanning", () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={true} />);
    expect(screen.getByLabelText(/enter a website url/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /scanning/i })).toBeDisabled();
  });

  it("renders the focus area collapsible section", () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={false} />);
    expect(screen.getByText(/focus area/i)).toBeInTheDocument();
  });

  it("shows offline notice when promptDisabled is true", () => {
    render(<ScanForm onSubmit={vi.fn()} isScanning={false} promptDisabled={true} />);
    expect(screen.getByRole("status")).toHaveTextContent(/AI service is offline/i);
  });
});
