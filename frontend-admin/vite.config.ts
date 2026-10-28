import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite configuration for the admin frontend.
 * - Dev server on port 5174 (avoids clash with user frontend on 5173)
 * - Test environment: jsdom so React components can render in Vitest
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "ui-shared": path.resolve(__dirname, "../ui-shared/src"),
    },
  },
  server: {
    port: 5174,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/test/setup.ts"],
  },
});
