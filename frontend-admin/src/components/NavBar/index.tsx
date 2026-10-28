/**
 * NavBar — thin wrapper around the shared NavBar for the admin frontend.
 * Shows the app title, an "Admin" badge, and a Logout button.
 */

import { NavBar as SharedNavBar } from "ui-shared/components/NavBar";

interface NavBarProps {
  /** Callback invoked when the user clicks Logout. */
  onLogout: () => void;
}

/**
 * Renders the persistent admin navigation bar.
 * @param props.onLogout - Handler for the logout button.
 */
function NavBar({ onLogout }: NavBarProps): JSX.Element {
  return (
    <SharedNavBar
      brand="Vulnerability Checker"
      badge="Admin"
      onLogout={onLogout}
    />
  );
}

export default NavBar;
