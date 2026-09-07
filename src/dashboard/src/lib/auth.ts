import { useEffect, useState } from "react";

/**
 * Auth helpers for the Kairo dashboard.
 *
 * Login, the OAuth callback, and sessions are owned by the Kairo API
 * (src/api/oauth.py), which holds CLIENT_ID and CLIENT_SECRET server-side.
 * In development the Vite dev server proxies /auth and /api to the API (see
 * vite.config.ts); in production your reverse proxy must route /auth (and
 * /api, /health) to the API too.
 */

/** Start the Discord login flow (GET on the API). */
export const DISCORD_LOGIN_PATH = "/auth/discord";

/** End the current session (GET on the API, redirects back to the dashboard). */
export const AUTH_LOGOUT_PATH = "/auth/logout";

export interface MeUser {
  id: string;
  username: string;
  discriminator?: string | null;
  avatar?: string | null;
}

export interface ManageableGuild {
  id: string;
  name: string;
  icon?: string | null;
  bot_installed: boolean;
}

export interface MeResponse {
  user: MeUser;
  guilds: ManageableGuild[];
}

/**
 * Fetch the current session (GET /api/v1/me). Returns null when there is no
 * valid kairo_session cookie or the API is unreachable.
 */
export async function getMe(signal?: AbortSignal): Promise<MeResponse | null> {
  try {
    const res = await fetch("/api/v1/me", {
      credentials: "same-origin",
      signal,
    });
    if (!res.ok) return null;
    return (await res.json()) as MeResponse;
  } catch {
    return null;
  }
}

/**
 * Reactive session state for components. Re-fetches /api/v1/me on mount and
 * exposes a reload() to refresh after login/logout navigation.
 */
export function useSession() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getMe(controller.signal).then((data) => {
      setMe(data);
      setLoading(false);
    });
    return () => controller.abort();
  }, []);

  return { me, loading };
}