import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite configuration for the user-facing frontend.
 * Dev server runs on port 5173. Vitest uses jsdom for component tests.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "ui-shared": path.resolve(__dirname, "../ui-shared/src"),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
