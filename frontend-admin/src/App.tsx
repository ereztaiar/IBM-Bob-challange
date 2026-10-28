/**
 * App.tsx — root component for the admin frontend.
 *
 * Sets up React Router with three routes:
 *   /login        — LoginPage (public)
 *   /dashboard    — DashboardPage (protected)
 *   /scans/:id    — ScanDetailPage (protected)
 *   /             — redirect to /dashboard
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import ProtectedRoute from "./components/ProtectedRoute";
import NavBar from "./components/NavBar";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ScanDetailPage from "./pages/ScanDetailPage";

/**
 * Wires together routing and authentication.
 * NavBar is only shown when the user is authenticated.
 */
function App(): JSX.Element {
  const { isAuthenticated, logout } = useAuth();

  return (
    <BrowserRouter>
      {isAuthenticated && <NavBar onLogout={logout} />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <DashboardPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/scans/:id"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <ScanDetailPage />
            </ProtectedRoute>
          }
        />

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
