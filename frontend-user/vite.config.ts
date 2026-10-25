import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Vite configuration for the user-facing frontend.
 * The dev server runs on port 5173 (Vite default).
 * The `VITE_API_URL` env var is forwarded to the browser at build time.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
