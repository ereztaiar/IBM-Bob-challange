/**
 * App — root component for the user-facing frontend.
 *
 * Renders a placeholder heading while the full scan-submission UI is
 * implemented in Sub-Task 7.
 */
function App(): JSX.Element {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Website Vulnerability Checker</h1>
      <p>Enter a URL to scan for common vulnerabilities.</p>
    </main>
  );
}

export default App;
