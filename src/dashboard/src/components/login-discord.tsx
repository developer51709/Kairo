import { DISCORD_LOGIN_PATH } from "../lib/auth";
import { DiscordMark } from "./icons";

interface LoginDiscordProps {
  size?: "md" | "lg";
  fullWidth?: boolean;
  className?: string;
}

/**
 * Primary "Login with Discord" CTA.
 *
 * Starts the server-side OAuth flow owned by the Kairo API, which holds
 * CLIENT_ID/CLIENT_SECRET and never exposes them to the browser. In dev the
 * /auth path is proxied to the API by Vite.
 *
 * The label collapses to "Sign in" on small screens so the header never
 * overflows a phone viewport.
 */
export function LoginDiscord({
  size = "md",
  fullWidth = false,
  className = "",
}: LoginDiscordProps) {
  const base = [
    "group inline-flex items-center justify-center gap-2.5 rounded-xl font-semibold",
    "bg-discord text-white shadow-[0_10px_32px_-8px_rgba(88,101,242,0.55)]",
    "transition-all duration-200 hover:bg-discord-hover hover:shadow-[0_14px_38px_-8px_rgba(88,101,242,0.65)]",
    "active:translate-y-px",
    fullWidth ? "w-full" : "",
    className,
  ].join(" ");

  const sizing =
    size === "lg"
      ? "px-6 py-3.5 text-base sm:px-7"
      : "px-3.5 py-2.5 text-sm sm:px-5";

  return (
    <a href={DISCORD_LOGIN_PATH} className={`${base} ${sizing}`}>
      <DiscordMark
        className={size === "lg" ? "h-5 w-5 shrink-0" : "h-4 w-4 shrink-0"}
      />
      <span className="sm:hidden">Sign in</span>
      <span className="hidden sm:inline">Login with Discord</span>
    </a>
  );
}
