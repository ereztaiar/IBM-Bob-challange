import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Vite configuration for the admin frontend.
 * The dev server runs on port 5174 to avoid clashing with frontend-user.
 * The `VITE_ADMIN_API_URL` env var is forwarded to the browser at build time.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
  },
});
