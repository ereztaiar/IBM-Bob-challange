/**
 * NavBar — top navigation bar shared by both frontends.
 *
 * Props control the branding text, optional badge, tagline (user frontend),
 * and an optional logout button (admin frontend). Both frontends use an
 * identical visual shell — only the content differs.
 */

import styles from "./NavBar.module.css";

export interface NavBarProps {
  /**
   * Primary brand name shown on the left.
   * @default "VulnChecker"
   */
  brand?: string;
  /**
   * Small badge rendered next to the brand (e.g. "Admin").
   * Not shown when omitted.
   */
  badge?: string;
  /**
   * Muted tagline shown next to the brand (e.g. "Website Vulnerability Scanner").
   * Not shown when omitted or when badge is set.
   */
  tagline?: string;
  /**
   * When provided, renders a Logout button and calls this on click.
   * Admin frontend passes `logout` here; user frontend omits it.
   */
  onLogout?: () => void;
}

/**
 * Renders the persistent top navigation bar.
 *
 * @param props - Component props.
 */
export function NavBar({
  brand = "VulnChecker",
  badge,
  tagline,
  onLogout,
}: NavBarProps): JSX.Element {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
      <div className={styles.left}>
        <span className={styles.brand}>{brand}</span>
        {badge && (
          <span className={styles.badge}>{badge}</span>
        )}
        {!badge && tagline && (
          <span className={styles.tagline}>{tagline}</span>
        )}
      </div>

      {onLogout && (
        <button
          className={styles.logoutBtn}
          onClick={onLogout}
          aria-label="Log out"
        >
          Logout
        </button>
      )}
    </nav>
  );
}

export default NavBar;
