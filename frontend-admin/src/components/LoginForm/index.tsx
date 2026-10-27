/**
 * LoginForm — username/password form that calls useAuth.login().
 */
import { useState, FormEvent } from "react";
import type { UseAuthReturn } from "../../hooks/useAuth";
import styles from "./LoginForm.module.css";

interface LoginFormProps {
  /** login() action from useAuth. */
  onLogin: UseAuthReturn["login"];
  /** Error message to display, or null. */
  error: string | null;
  /** Whether a login request is in flight. */
  loading: boolean;
}

/**
 * Renders a username/password form.
 * Delegates submit to the parent-supplied onLogin handler.
 */
function LoginForm({ onLogin, error, loading }: LoginFormProps): JSX.Element {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  /**
   * Handle form submission — prevent default and call onLogin.
   * @param e - The form submit event.
   */
  async function handleSubmit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    await onLogin(username, password);
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} aria-label="Admin login form">
      <h1 className={styles.title}>Admin Login</h1>

      {error && (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      )}

      <label htmlFor="username" className={styles.label}>
        Username
      </label>
      <input
        id="username"
        type="text"
        className={styles.input}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
        required
      />

      <label htmlFor="password" className={styles.label}>
        Password
      </label>
      <input
        id="password"
        type="password"
        className={styles.input}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="current-password"
        required
      />

      <button
        type="submit"
        className={styles.button}
        disabled={loading}
        aria-busy={loading}
      >
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}

export default LoginForm;
