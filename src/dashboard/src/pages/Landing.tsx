import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import { LoginDiscord } from "../components/login-discord";
import { Wordmark } from "../components/logo";
import { AUTH_LOGOUT_PATH, useSession } from "../lib/auth";
import type { MeResponse } from "../lib/auth";
import {
  ArrowRightIcon,
  BoltIcon,
  CheckIcon,
  CompassIcon,
  KeyIcon,
  MenuIcon,
  PlugIcon,
  ScrollIcon,
  ServerIcon,
  ShieldIcon,
  SlidersIcon,
  TagIcon,
  TerminalIcon,
  UsersIcon,
  XIcon,
} from "../components/icons";

/* ------------------------------------------------------------------ */
/* Data                                                                */
/* ------------------------------------------------------------------ */

interface Feature {
  icon: ComponentType<{ className?: string }>;
  title: string;
  body: string;
}

const FEATURES: Feature[] = [
  {
    icon: ShieldIcon,
    title: "Moderation & cases",
    body: "Ban, kick, timeout and warn with durable case files. Browse history, resolve cases and add staff notes without scrolling Discord.",
  },
  {
    icon: BoltIcon,
    title: "AutoMod engine",
    body: "Tune spam, mention, link and word rules with thresholds and actions. Exempt roles and channels — all from a form, never code.",
  },
  {
    icon: TagIcon,
    title: "Roles & welcome",
    body: "Auto-roles, button and select role menus, welcome and leave messages. Compose them visually and save in a click.",
  },
  {
    icon: ScrollIcon,
    title: "Event logging",
    body: "Route message, member and moderation events to the channels you choose, with per-category toggles and ignore rules.",
  },
  {
    icon: UsersIcon,
    title: "Community tools",
    body: "Tickets, suggestions, giveaways, polls and starboard settings — with live status panels for everything currently running.",
  },
  {
    icon: CompassIcon,
    title: "Guild onboarding",
    body: "A setup wizard that creates channels, roles and sane defaults, then shows exactly what is still left to configure.",
  },
];

const ROADMAP_PILLS = [
  "Verification",
  "Leveling",
  "Role menus",
  "Custom commands",
  "Suggestions",
  "Giveaways",
  "Polls",
  "Starboard",
  "Reminders",
  "Slowmode",
  "Appeal system",
  "Audit history",
];

const STEPS = [
  {
    icon: PlugIcon,
    num: "01",
    title: "Invite Kairo",
    body: "Add Kairo to your server with one invite link. Slash commands work immediately — no code, no containers.",
  },
  {
    icon: KeyIcon,
    num: "02",
    title: "Sign in with Discord",
    body: "Server staff authorise with the Discord accounts they already have. No extra passwords, no shared logins.",
  },
  {
    icon: SlidersIcon,
    num: "03",
    title: "Manage from the web",
    body: "Toggle modules, pick channels and review cases from the dashboard. Changes apply the moment you save.",
  },
];

/* ------------------------------------------------------------------ */
/* Landing page                                                        */
/* ------------------------------------------------------------------ */

export default function Landing() {
  return (
    <div className="bg-night">
      <SiteHeader />
      <AuthBanner />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <SelfHost />
        <ClosingCta />
      </main>
      <SiteFooter />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Header                                                              */
/* ------------------------------------------------------------------ */

const HEADER_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how" },
  { label: "Self-host", href: "#selfhost" },
];

function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { me } = useSession();

  return (
    <header className="sticky top-0 z-40 border-b border-line/60 bg-night/80 backdrop-blur-md">
      <div className="relative mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-3 px-5 sm:px-8">
        <a
          href="#top"
          aria-label="Kairo home"
          className="shrink-0"
          onClick={() => setMenuOpen(false)}
        >
          <Wordmark />
        </a>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-8 text-sm text-dune md:flex">
          {HEADER_LINKS.map((link) => (
            <a key={link.href} href={link.href} className="transition-colors hover:text-sand">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden md:block">
            <HeaderAuth me={me} />
          </div>
          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((open) => !open)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line text-dune transition-colors hover:border-gold/40 hover:text-gold md:hidden"
          >
            {menuOpen ? <XIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile menu — overlay so opening/closing never shifts the page */}
        {menuOpen && (
          <div
            id="mobile-menu"
            className="absolute inset-x-0 top-full border-b border-line/70 bg-night/95 shadow-[0_24px_50px_-12px_rgba(0,0,0,0.85)] backdrop-blur-lg md:hidden"
          >
            <nav className="flex flex-col px-5 py-2 sm:px-8">
              {HEADER_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className="border-b border-line/50 py-4 text-base font-medium text-sand transition-colors last:border-b-0 hover:text-gold"
                >
                  {link.label}
                </a>
              ))}
              <div className="py-4">
                <MobileAuth me={me} onNavigate={() => setMenuOpen(false)} />
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* Auth feedback + session chips                                       */
/* ------------------------------------------------------------------ */

/**
 * One-shot banner for ?auth=success / ?auth=error (set by the API after the
 * Discord OAuth round-trip), then the query param is cleaned from the URL.
 */
function AuthBanner() {
  const [notice, setNotice] = useState<{ tone: "ok" | "err"; text: string } | null>(
    null,
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const auth = params.get("auth");
    if (auth === "success") {
      setNotice({ tone: "ok", text: "Signed in with Discord — welcome to Kairo." });
    } else if (auth === "error") {
      setNotice({ tone: "err", text: "Sign-in didn't complete. Please try again." });
    }
    if (auth) {
      params.delete("auth");
      const qs = params.toString();
      window.history.replaceState(
        null,
        "",
        qs ? `${window.location.pathname}?${qs}` : window.location.pathname,
      );
    }
  }, []);

  if (!notice) return null;

  return (
    <div className="border-b border-line/60">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-3 px-5 py-3 sm:px-8">
        <span
          aria-hidden
          className={`h-2 w-2 shrink-0 rounded-full ${
            notice.tone === "ok" ? "bg-gold" : "bg-red-400"
          }`}
        />
        <p className="text-sm text-sand">{notice.text}</p>
        <button
          type="button"
          onClick={() => setNotice(null)}
          className="ml-auto shrink-0 rounded-md p-1 text-mist transition-colors hover:text-sand"
          aria-label="Dismiss"
        >
          <XIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function userInitial(username: string): string {
  return (username.trim()[0] ?? "?").toUpperCase();
}

function HeaderAuth({ me }: { me: MeResponse | null }) {
  if (!me) return <LoginDiscord />;
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-gold/30 bg-gold/15 text-xs font-bold text-gold">
        {userInitial(me.user.username)}
      </span>
      <span className="max-w-32 truncate text-sm font-medium text-sand">
        {me.user.username}
      </span>
      <a
        href={AUTH_LOGOUT_PATH}
        className="rounded-lg px-2.5 py-1.5 text-xs text-mist transition-colors hover:bg-panel hover:text-gold"
      >
        Sign out
      </a>
    </div>
  );
}

function MobileAuth({
  me,
  onNavigate,
}: {
  me: MeResponse | null;
  onNavigate: () => void;
}) {
  if (!me) return <LoginDiscord fullWidth />;
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex min-w-0 items-center gap-2.5">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-gold/30 bg-gold/15 text-xs font-bold text-gold">
          {userInitial(me.user.username)}
        </span>
        <span className="truncate text-sm font-medium text-sand">
          {me.user.username}
        </span>
      </span>
      <a
        href={AUTH_LOGOUT_PATH}
        onClick={onNavigate}
        className="shrink-0 rounded-lg border border-line px-3 py-2 text-xs text-mist transition-colors hover:border-gold/40 hover:text-gold"
      >
        Sign out
      </a>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Hero                                                                */
/* ------------------------------------------------------------------ */

function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      {/* Ambient glows + blueprint grid */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="bg-blueprint absolute inset-0" />
        <div className="absolute left-1/2 top-[-360px] h-[680px] w-[940px] -translate-x-1/2 rounded-full bg-gold/[0.08] blur-[130px]" />
        <div className="absolute -left-44 top-1/3 h-[460px] w-[460px] rounded-full bg-discord/[0.09] blur-[120px]" />
        <div className="absolute -right-32 top-1/2 h-[360px] w-[360px] rounded-full bg-gold/[0.05] blur-[100px]" />
      </div>

      <div className="relative mx-auto grid w-full max-w-6xl items-center gap-16 px-5 pb-24 pt-14 sm:px-8 lg:grid-cols-[1.02fr_0.98fr] lg:gap-10 lg:pb-32 lg:pt-20">
        {/* Copy */}
        <div>
          <span className="rise inline-flex max-w-full flex-wrap items-center gap-2.5 rounded-full border border-gold/25 bg-gold/[0.07] px-4 py-1.5 text-xs font-medium tracking-wide text-gold-bright">
            <span className="status-dot h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
            <span className="min-w-0">Self-hostable · Open source</span>
            <span className="hidden sm:inline">· discord.py</span>
          </span>

          <h1
            className="rise mt-6 text-[clamp(2.45rem,9vw,3.4rem)] font-bold leading-[1.08] tracking-tight text-sand sm:text-6xl sm:leading-[1.04] lg:text-[4.2rem]"
            style={{ animationDelay: "90ms" }}
          >
            Your server.
            <span className="text-gold-gradient mt-1 block pb-1.5">
              One command center.
            </span>
          </h1>

          <p
            className="rise mt-7 max-w-xl text-lg leading-relaxed text-dune"
            style={{ animationDelay: "180ms" }}
          >
            Kairo pairs a powerful Discord bot with a fast, self-hostable web
            dashboard. Moderation cases, AutoMod rules, roles, logging and
            community tools — configured in one place, applied instantly.
          </p>

          <div
            className="rise mt-9 flex flex-wrap items-center gap-4"
            style={{ animationDelay: "270ms" }}
          >
            <LoginDiscord size="lg" />
            <a
              href="#features"
              className="group inline-flex items-center gap-2 rounded-xl border border-line bg-panel/60 px-6 py-3.5 text-base font-medium text-sand transition-colors hover:border-gold/40 hover:text-gold"
            >
              Explore the dashboard
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
          </div>

          <ul
            className="rise mt-10 flex flex-wrap gap-x-7 gap-y-2.5 text-sm text-mist"
            style={{ animationDelay: "360ms" }}
          >
            {["Moderation & cases", "AutoMod rules", "Roles & logging", "Community tools"].map(
              (item) => (
                <li key={item} className="flex items-center gap-2">
                  <CheckIcon className="h-4 w-4 text-gold/80" />
                  {item}
                </li>
              ),
            )}
          </ul>
        </div>

        {/* Product preview */}
        <DashboardMock />
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard preview mock                                              */
/* ------------------------------------------------------------------ */

function DashboardMock() {
  return (
    <div className="rise relative" style={{ animationDelay: "220ms" }}>
      {/* Glow under the window */}
      <div
        aria-hidden
        className="absolute -inset-8 rounded-[36px] bg-gold/[0.07] blur-3xl"
      />

      <div className="relative overflow-hidden rounded-2xl border border-line bg-panel shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)] backdrop-blur">
        {/* Title bar */}
        <div className="flex items-center gap-2 border-b border-line px-4 py-3 sm:gap-3">
          <div className="hidden shrink-0 gap-1.5 sm:flex">
            <span className="h-2.5 w-2.5 rounded-full bg-[#3a3427]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#3a3427]" />
            <span className="h-2.5 w-2.5 rounded-full bg-gold/60" />
          </div>
          <div className="flex min-w-0 flex-1 items-center justify-center gap-2 rounded-md border border-line bg-coal px-3 py-1 text-[11px] text-mist">
            <ShieldIcon className="h-3 w-3 shrink-0 text-gold/70" />
            <span className="truncate">kairo — server overview</span>
          </div>
          <span className="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border border-line bg-coal px-2.5 py-1 text-[10px] text-dune">
            <span className="status-dot h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
            <span className="hidden sm:inline">Online · </span>
            42 ms
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[148px_1fr]">
          {/* Sidebar */}
          <aside className="hidden border-r border-line p-3 sm:block">
            {[
              { icon: SlidersIcon, label: "Overview", active: true },
              { icon: ShieldIcon, label: "Moderation" },
              { icon: BoltIcon, label: "AutoMod" },
              { icon: ScrollIcon, label: "Logging" },
              { icon: TagIcon, label: "Roles" },
              { icon: UsersIcon, label: "Community" },
            ].map((item) => (
              <div
                key={item.label}
                className={
                  item.active
                    ? "mb-1 flex items-center gap-2 rounded-lg bg-gold/10 px-2.5 py-2 text-xs font-medium text-sand"
                    : "mb-1 flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-mist"
                }
              >
                <item.icon className="h-3.5 w-3.5 text-gold/80" />
                {item.label}
              </div>
            ))}

            <div className="mt-5 rounded-xl border border-line bg-coal/70 p-3">
              <p className="text-[10px] uppercase tracking-wider text-mist">
                Bot health
              </p>
              <p className="mt-1.5 text-lg font-semibold text-sand">100%</p>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-line">
                <div className="h-full w-full rounded-full bg-gold/80" />
              </div>
            </div>
          </aside>

          {/* Main panel */}
          <div className="p-4 sm:p-5">
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Servers", value: "12" },
                { label: "Open cases", value: "3" },
                { label: "AutoMod rules", value: "6" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border border-line bg-coal/60 px-3 py-3"
                >
                  <p className="text-[10px] uppercase tracking-wider text-mist">
                    {stat.label}
                  </p>
                  <p className="mt-1 text-2xl font-bold text-sand">{stat.value}</p>
                </div>
              ))}
            </div>

            <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-dune">
              Recent activity
            </p>
            <div className="mt-2.5 overflow-hidden rounded-xl border border-line">
              {[
                { user: "@nova", action: "Timeout · 10m", tag: "case #481", tone: "text-gold-bright" },
                { user: "@kai", action: "Warn · spam rule", tag: "case #480", tone: "text-dune" },
                { user: "@lumen", action: "Kick · raid guard", tag: "case #479", tone: "text-dune" },
              ].map((row) => (
                <div
                  key={row.tag}
                  className="flex min-w-0 items-center justify-between gap-3 border-b border-line/70 bg-coal/40 px-3.5 py-2.5 last:border-b-0"
                >
                  <span className="flex min-w-0 items-center gap-2.5 text-xs text-sand">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gold/15 text-[9px] font-bold text-gold">
                      {row.user[1].toUpperCase()}
                    </span>
                    <span className="truncate">{row.user}</span>
                  </span>
                  <span className="hidden min-w-0 truncate text-xs text-dune md:inline">
                    {row.action}
                  </span>
                  <span className={`shrink-0 whitespace-nowrap text-[10px] ${row.tone}`}>
                    {row.tag}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-4 flex flex-wrap gap-2.5">
              <span className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1.5 text-[11px] font-medium text-gold">
                Open Moderation
              </span>
              <span className="rounded-lg border border-line px-3 py-1.5 text-[11px] text-mist">
                Configure AutoMod
              </span>
            </div>
          </div>
        </div>
      </div>

      <p className="mt-4 text-center text-xs text-mist">
        Early preview of the dashboard interface — under active construction.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Features                                                            */
/* ------------------------------------------------------------------ */

function Features() {
  return (
    <section id="features" className="relative scroll-mt-20 border-t border-line/50">
      <div className="mx-auto w-full max-w-6xl px-5 py-24 sm:px-8 lg:py-32">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-gold">
            Dashboard features
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-sand sm:text-[2.6rem] sm:leading-[1.1]">
            Every module you run in Discord
            <span className="text-gold-gradient"> deserves a control panel.</span>
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-dune">
            Kairo's web dashboard turns walls of embeds into clear screens —
            deeper settings, searchable history and instant saves.
          </p>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <article
              key={feature.title}
              className="group relative rounded-2xl border border-line bg-panel p-6 transition-all duration-300 hover:-translate-y-1 hover:border-gold/35 hover:bg-well"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-gold/20 bg-gold/[0.08] text-gold transition-transform duration-300 group-hover:scale-105">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-sand">
                {feature.title}
              </h3>
              <p className="mt-2.5 text-sm leading-relaxed text-dune">
                {feature.body}
              </p>
              <span
                aria-hidden
                className="absolute right-5 top-5 text-gold/0 transition-colors duration-300 group-hover:text-gold/60"
              >
                <ArrowRightIcon className="h-4 w-4 -rotate-45" />
              </span>
            </article>
          ))}
        </div>

        {/* Roadmap pills */}
        <div className="mt-14">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-mist">
            And the module list keeps growing
          </p>
          <div className="mt-5 flex flex-wrap gap-2.5">
            {ROADMAP_PILLS.map((pill) => (
              <span
                key={pill}
                className="rounded-full border border-line bg-coal/60 px-4 py-1.5 text-xs tracking-wide text-dune transition-colors hover:border-gold/35 hover:text-gold"
              >
                {pill}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* How it works                                                        */
/* ------------------------------------------------------------------ */

function HowItWorks() {
  return (
    <section id="how" className="relative scroll-mt-20 overflow-hidden border-t border-line/50">
      <div
        aria-hidden
        className="pointer-events-none absolute right-[-220px] top-10 h-[480px] w-[480px] rounded-full bg-discord/[0.07] blur-[120px]"
      />
      <div className="relative mx-auto w-full max-w-6xl px-5 py-24 sm:px-8 lg:py-32">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-gold">
            How it works
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-sand sm:text-[2.6rem] sm:leading-[1.1]">
            From invite to fully configured
            <span className="text-gold-gradient"> in minutes.</span>
          </h2>
        </div>

        <div className="mt-14 grid gap-10 md:grid-cols-3 md:gap-6">
          {STEPS.map((step, index) => (
            <div key={step.num} className="relative">
              {index < STEPS.length - 1 && (
                <div
                  aria-hidden
                  className="absolute left-full top-10 hidden h-px w-6 -translate-y-1/2 bg-gradient-to-r from-gold/40 to-transparent md:block lg:w-10"
                />
              )}
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-gold/25 bg-gold/[0.08] text-gold">
                <step.icon className="h-6 w-6" />
              </div>
              <p className="mt-6 text-xs font-semibold tracking-[0.24em] text-mist">
                Step {step.num}
              </p>
              <h3 className="mt-2 text-xl font-semibold text-sand">{step.title}</h3>
              <p className="mt-3 text-[15px] leading-relaxed text-dune">
                {step.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Self-hosting                                                        */
/* ------------------------------------------------------------------ */

const SELF_HOST_POINTS = [
  "Runs in one process — bot, API and the SQLite database travel together.",
  "Modular by design: every feature is auto-discovered and can be disabled per server.",
  "No telemetry and no vendor lock-in — your data lives in a local file you own.",
  "Composable internals: configuration, logging and events are first-class citizens.",
];

function SelfHost() {
  return (
    <section id="selfhost" className="scroll-mt-20 border-t border-line/50">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-14 px-5 py-24 sm:px-8 lg:grid-cols-2 lg:py-32">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-gold">
            Self-hosted by design
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-sand sm:text-[2.6rem] sm:leading-[1.1]">
            Your server, your stack,
            <span className="text-gold-gradient"> your data.</span>
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-dune">
            Kairo is built to run on hardware you control — a Raspberry Pi, a
            VPS, or a spare laptop. The dashboard and the API it talks to are
            plain Python and Vite, with no external service required.
          </p>

          <ul className="mt-8 space-y-3.5">
            {SELF_HOST_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3 text-[15px] leading-relaxed text-dune">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-gold/30 bg-gold/10">
                  <CheckIcon className="h-3 w-3 text-gold" />
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>

        {/* Stack visual */}
        <div aria-hidden className="relative">
          <div className="absolute -inset-6 rounded-3xl bg-gold/[0.05] blur-2xl" />
          <div className="relative space-y-3">
            {[
              {
                icon: ServerIcon,
                name: "Kairo bot",
                meta: "discord.py · slash commands · Components V2",
                tone: "border-gold/25 text-gold",
              },
              {
                icon: TerminalIcon,
                name: "REST API",
                meta: "aiohttp · X-API-Key auth · same process as the bot",
                tone: "border-line text-dune",
              },
              {
                icon: SlidersIcon,
                name: "Web dashboard",
                meta: "Vite · TypeScript · talks to the API only",
                tone: "border-line text-dune",
              },
              {
                icon: ShieldIcon,
                name: "SQLite",
                meta: "migrations · repositories · your data, local",
                tone: "border-line text-dune",
              },
            ].map((layer) => (
              <div
                key={layer.name}
                className={`flex items-center gap-4 rounded-2xl border bg-panel px-5 py-4 ${layer.tone}`}
              >
                <layer.icon className="h-5 w-5 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-sand">{layer.name}</p>
                  <p className="truncate text-xs text-mist">{layer.meta}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Closing CTA                                                         */
/* ------------------------------------------------------------------ */

function ClosingCta() {
  return (
    <section className="relative overflow-hidden border-t border-line/50">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="bg-blueprint absolute inset-0" />
        <div className="absolute left-1/2 top-1/2 h-[420px] w-[820px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gold/[0.08] blur-[130px]" />
      </div>
      <div className="relative mx-auto w-full max-w-3xl px-5 py-24 text-center sm:px-8 lg:py-28">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-gold">
          The dashboard is under construction
        </p>
        <h2 className="mt-4 text-4xl font-bold tracking-tight text-sand sm:text-5xl">
          Ready to take command?
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-dune">
          Set Kairo up in your server, sign in with Discord, and land in the
          command center once the session layer ships.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <LoginDiscord size="lg" />
          <a
            href="#features"
            className="inline-flex items-center gap-2 rounded-xl border border-line bg-panel/60 px-6 py-3.5 text-base font-medium text-sand transition-colors hover:border-gold/40 hover:text-gold"
          >
            See the feature set
            <ArrowRightIcon className="h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Footer                                                              */
/* ------------------------------------------------------------------ */

function SiteFooter() {
  return (
    <footer className="border-t border-line/60">
      <div className="mx-auto w-full max-w-6xl px-5 py-14 sm:px-8">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1.2fr]">
          <div>
            <Wordmark />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-mist">
              An open-source Discord platform — built with Python, discord.py
              and Vite for people who like to run their own stack.
            </p>
          </div>

          <FooterColumn
            title="Dashboard"
            links={[
              { label: "Features", href: "#features" },
              { label: "How it works", href: "#how" },
              { label: "Self-hosting", href: "#selfhost" },
            ]}
          />
          <FooterColumn
            title="Get started"
            links={[
              { label: "Login with Discord", href: "/auth/discord" },
              { label: "Developer Portal", href: "https://discord.com/developers/applications", external: true },
            ]}
          />
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-dune">
              Project status
            </p>
            <ul className="mt-4 space-y-2.5 text-sm text-mist">
              <li>Early development · dashboard v0.1</li>
              <li>Phase 6 of 9 on the roadmap</li>
              <li className="flex items-center gap-2">
                <span className="status-dot h-1.5 w-1.5 rounded-full bg-gold" />
                More coming soon
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-line/60 pt-6 text-xs text-mist sm:flex-row sm:items-center">
          <p>
            © {new Date().getFullYear()} Kairo — early development. Dashboard v0.1.
          </p>
          <p>
            Discord OAuth2 · SQLite · Python &amp; Vite
          </p>
        </div>
      </div>
    </footer>
  );
}

interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

function FooterColumn({ title, links }: { title: string; links: FooterLink[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-dune">
        {title}
      </p>
      <ul className="mt-4 space-y-2.5">
        {links.map((link) => (
          <li key={link.label}>
            <a
              href={link.href}
              {...(link.external ? { target: "_blank", rel: "noreferrer" } : {})}
              className="text-sm text-mist transition-colors hover:text-gold"
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
