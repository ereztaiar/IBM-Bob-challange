/**
 * Tests for FindingCard component.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FindingCard from "../components/ReportView/FindingCard";
import type { Finding } from "../types/scan";

const baseFinding: Finding = {
  category: "headers",
  severity: "high",
  title: "Missing HSTS",
  description: "HSTS header is absent.",
  evidence: "Header 'strict-transport-security' not present",
  remediation: "Add the HSTS header.",
};

describe("FindingCard", () => {
  it("renders the finding title", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText("Missing HSTS")).toBeInTheDocument();
  });

  it("renders the severity badge", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders evidence text", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText(/strict-transport-security/i)).toBeInTheDocument();
  });

  it("renders remediation text", () => {
    render(<FindingCard finding={baseFinding} />);
    expect(screen.getByText(/Add the HSTS header/i)).toBeInTheDocument();
  });

  it("applies the correct data-severity attribute for colour coding", () => {
    const { container } = render(<FindingCard finding={baseFinding} />);
    const badge = container.querySelector("[data-severity='high']");
    expect(badge).toBeInTheDocument();
  });
});
