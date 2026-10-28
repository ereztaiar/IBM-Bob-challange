/**
 * NavBar — top navigation bar displayed on every page.
 */

import styles from "./NavBar.module.css";

/**
 * Renders the application top navigation bar.
 */
export default function NavBar(): JSX.Element {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
      <span className={styles.brand}>VulnChecker</span>
      <span className={styles.tagline}>Website Vulnerability Scanner</span>
    </nav>
  );
}
