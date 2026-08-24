// SPA mode: render entirely in the browser, no server-side rendering,
// no prerendering. The static adapter emits a single fallback `index.html`
// (plus hashed assets) that serves every client-side route.
export const ssr = false;
export const prerender = false;
export const trailingSlash = "ignore";
