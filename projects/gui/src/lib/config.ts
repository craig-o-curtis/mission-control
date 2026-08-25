// Backend base URLs.
//
// Locally the GUI talks to the APIs through the Vite dev proxy at `/api` (see
// vite.config.ts) — so no hardcoded URL is needed; it "just works" on the same
// origin as the dev server. The proxy forwards `/api/missions` → `<backend>/missions`,
// etc. (Both backends default to port 8000; run one at a time locally.)
//
// For production (GitHub Pages → Render) set these via PUBLIC_ env vars at
// build time. SvelteKit's `$env/dynamic/public` bakes them into the static
// bundle. Missing values fall back to the dev proxy (`/api`).
import { env } from "$env/dynamic/public";

export const MISSIONS_API: string = env.PUBLIC_MISSIONS_API || "/api";
export const CHECKLISTS_API: string = env.PUBLIC_CHECKLISTS_API || "/api";
