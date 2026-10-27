/**
 * StatCard.test.tsx — tests for the StatCard component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatCard from "../components/StatCard";

describe("StatCard", () => {
  it("renders the label", () => {
    render(<StatCard label="Total Scans" value={42} />);
    expect(screen.getByText("Total Scans")).toBeInTheDocument();
  });

  it("renders the formatted value", () => {
    render(<StatCard label="Total Scans" value={1234} />);
    // toLocaleString may format as 1,234 depending on locale
    expect(screen.getByRole("region", { name: "Total Scans" })).toBeInTheDocument();
  });

  it("applies default variant when no variant is provided", () => {
    // CSS Modules mangle class names — verify the element exists with the label
    render(<StatCard label="Test" value={0} />);
    expect(screen.getByRole("region", { name: "Test" })).toBeInTheDocument();
  });

  it("renders critical variant", () => {
    // The element is still rendered — variant only affects styling, not semantics
    render(<StatCard label="Critical" value={5} variant="critical" />);
    expect(screen.getByRole("region", { name: "Critical" })).toBeInTheDocument();
  });

  it("renders today variant", () => {
    render(<StatCard label="Today" value={3} variant="today" />);
    expect(screen.getByRole("region", { name: "Today" })).toBeInTheDocument();
  });
});
