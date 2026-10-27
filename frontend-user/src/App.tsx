/**
 * App — root component. Mounts NavBar and the single HomePage.
 */

import NavBar from "./components/NavBar";
import HomePage from "./pages/HomePage";

/**
 * Renders the top-level application shell.
 */
export default function App(): JSX.Element {
  return (
    <>
      <NavBar />
      <HomePage />
    </>
  );
}
