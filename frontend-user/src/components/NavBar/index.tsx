/**
 * NavBar — thin wrapper around the shared NavBar for the user frontend.
 */

import { NavBar as SharedNavBar } from "ui-shared/components/NavBar";

/**
 * Renders the user-facing navigation bar.
 */
export default function NavBar(): JSX.Element {
  return (
    <SharedNavBar
      brand="VulnChecker"
      tagline="Website Vulnerability Scanner"
    />
  );
}
