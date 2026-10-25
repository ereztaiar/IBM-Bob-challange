/**
 * NavBar — top navigation bar for the admin frontend.
 * Shows the app title and a Logout button.
 */
import { Link } from "react-router-dom";
import styles from "./NavBar.module.css";

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
    <nav className={styles.nav} aria-label="Admin navigation">
      <Link to="/dashboard" className={styles.brand}>
        Vulnerability Checker <span className={styles.adminBadge}>Admin</span>
      </Link>
      <button
        className={styles.logoutBtn}
        onClick={onLogout}
        aria-label="Log out"
      >
        Logout
      </button>
    </nav>
  );
}

export default NavBar;
