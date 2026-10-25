/**
 * App — root component for the admin frontend.
 *
 * Renders a placeholder heading while the full admin dashboard UI is
 * implemented in Sub-Task 8.
 */
function App(): JSX.Element {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Website Vulnerability Checker — Admin</h1>
      <p>Admin dashboard — scan history and management.</p>
    </main>
  );
}

export default App;
