/**
 * ProtectedRoute — wraps React Router routes.
 * Redirects unauthenticated visitors to /login.
 */
import { Navigate } from "react-router-dom";

interface ProtectedRouteProps {
  /** Whether the current user is authenticated. */
  isAuthenticated: boolean;
  /** The child element to render when authenticated. */
  children: React.ReactElement;
}

/**
 * Renders children when authenticated, otherwise redirects to /login.
 * @param props.isAuthenticated - Authentication flag from useAuth.
 * @param props.children - The protected page element.
 */
function ProtectedRoute({
  isAuthenticated,
  children,
}: ProtectedRouteProps): React.ReactElement {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default ProtectedRoute;
