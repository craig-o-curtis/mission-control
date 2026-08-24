import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

// Base path. Defaults to the site root for frictionless local dev
// (so `pnpm run dev` serves the app at `/` and `/books` works directly).
// The GitHub Pages deploy (Phase 6) builds with BASE_PATH=/fastapi-endpoints
// so the static site is served under that subpath.
const base = process.env.BASE_PATH || "";

/** @type {import('@sveltejs/kit').Config} */
export default {
  prerender: {
    handleHttpError: "warn",
  },
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: "index.html",
      precompress: false,
    }),
    paths: {
      base,
    },
  },
};
