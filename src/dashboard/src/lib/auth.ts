/**
 * Auth paths for the Kairo dashboard.
 *
 * Login, the OAuth callback, and sessions are owned by the Kairo API
 * (src/api/oauth.py), which holds CLIENT_ID and CLIENT_SECRET server-side.
 * In development the Vite dev server proxies /auth to the API (see
 * vite.config.ts); in production your reverse proxy must route /auth (and
 * /api, /health) to the API too.
 */

/** Start the Discord login flow (GET on the API). */
export const DISCORD_LOGIN_PATH = "/auth/discord";

/** End the current session (GET on the API). */
export const AUTH_LOGOUT_PATH = "/auth/logout";
