import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// In dev, proxy `/api/*` to the locally-running FastAPI backend(s). Both backends
// default to port 8000 (run one at a time locally), so a single target is enough.
// Override with API_TARGET if you run a backend on another port.
const API_TARGET = process.env.API_TARGET ?? "http://127.0.0.1:8000";

// Base path. Defaults to the site root for frictionless local dev
// (so `pnpm run dev` serves the app at `/` and `/missions` works directly).
// The GitHub Pages deploy (Phase 6) builds with BASE_PATH=/fastapi-endpoints
// so the static site is served under that subpath.
const base = process.env.BASE_PATH || "";

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit({
      preprocess: vitePreprocess(),
      prerender: { handleHttpError: "warn" },
      adapter: adapter({ fallback: "index.html", precompress: false }),
      paths: { base },
    }),
  ],
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
