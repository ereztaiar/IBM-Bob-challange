/**
 * Tests for MetaTagGate component.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import MetaTagGate from "../components/MetaTagGate";
import type { MetaTagGateState } from "../components/MetaTagGate/useMetaTagGate";

function makeGate(acknowledged: boolean, acknowledge = vi.fn()): MetaTagGateState {
  return { acknowledged, acknowledge };
}

describe("MetaTagGate", () => {
  it("renders the disclosure notice when not acknowledged", () => {
    render(<MetaTagGate gate={makeGate(false)} />);
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByText(/Before you scan/i)).toBeInTheDocument();
  });

  it("renders nothing when already acknowledged", () => {
    const { container } = render(<MetaTagGate gate={makeGate(true)} />);
    expect(container.firstChild).toBeNull();
  });

  it("calls acknowledge() when the button is clicked", async () => {
    const acknowledge = vi.fn();
    render(<MetaTagGate gate={makeGate(false, acknowledge)} />);
    await userEvent.click(screen.getByRole("button"));
    expect(acknowledge).toHaveBeenCalledOnce();
  });
});
