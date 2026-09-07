import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Kairo dashboard dev server.
//
// In development the dashboard talks to the Kairo API (python src/run.py,
// http://127.0.0.1:8080 by default) through this Vite proxy so the browser never
// needs to know where the API lives.
//
// The listening port comes from the PORT environment variable when set
// (managed previews / isolated workspaces inject it) and falls back to 5173
// for local development. This makes a manual preview-port override actually
// take effect instead of the server silently staying on 5173.
const dashboardPort = Number(process.env.PORT) || 5173;
const portIsInjected = Boolean(process.env.PORT);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // bind 0.0.0.0 so managed previews can reach the dev server
    port: dashboardPort,
    // When a port is explicitly provided, fail instead of silently hopping to
    // another port — a preview pinned to the requested port would otherwise
    // show a stale or dead page.
    strictPort: portIsInjected,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
      "/auth": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
});
