import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// In dev, proxy `/api/*` to the locally-running FastAPI backend(s). Both backends
// default to port 8000 (run one at a time locally), so a single target is enough.
// Override with API_TARGET if you run a backend on another port.
const API_TARGET = process.env.API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  server: {
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
