/**
 * FindingCard.test.tsx — tests for the admin ReportView FindingCard.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import FindingCard from "../components/ReportView/FindingCard";
import type { Finding } from "../types/scan";

const baseFinding: Finding = {
  check: "xss",
  title: "Cross-Site Scripting",
  description: "Reflected XSS vulnerability detected.",
  severity: "high",
  remediation: "Sanitise user input.",
  references: ["https://owasp.org/xss"],
};

describe("FindingCard", () => {
  it("renders the title", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText("Cross-Site Scripting")).toBeInTheDocument();
  });

  it("renders the severity badge", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("renders the description", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(
      screen.getByText("Reflected XSS vulnerability detected.")
    ).toBeInTheDocument();
  });

  it("renders the remediation section", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText("Sanitise user input.")).toBeInTheDocument();
  });

  it("renders references as links", () => {
    render(<FindingCard finding={baseFinding} />);
    const link = screen.getByRole("link", { name: /owasp.org/i });
    expect(link).toHaveAttribute("href", "https://owasp.org/xss");
  });

  it("omits remediation section when not provided", () => {
    render(
      <FindingCard finding={{ ...baseFinding, remediation: undefined }} />
    );
    expect(screen.queryByText("Sanitise user input.")).not.toBeInTheDocument();
  });
});
