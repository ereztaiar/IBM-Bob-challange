/**
 * LoginPage — full-page login screen for the admin frontend.
 * Redirects to /dashboard on successful authentication.
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import LoginForm from "../../components/LoginForm";
import { useAuth } from "../../hooks/useAuth";
import styles from "./LoginPage.module.css";

/**
 * Renders the centred login card.
 * Automatically redirects to /dashboard when already authenticated.
 */
function LoginPage(): JSX.Element {
  const { isAuthenticated, login, error, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      void navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  return (
    <main className={styles.page}>
      <LoginForm onLogin={login} error={error} loading={loading} />
    </main>
  );
}

export default LoginPage;
