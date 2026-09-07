interface LogoProps {
  className?: string;
}

/** Pyramid + sun mark. */
export function KairoMark({ className }: LogoProps) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" aria-hidden>
      <path
        d="M20 6 L34.5 30 H5.5 L20 6 Z"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinejoin="round"
      />
      <circle cx="20" cy="19.5" r="3.2" fill="currentColor" />
      <path
        d="M11.5 33.2 h17 M8 36.4 h24"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.5"
      />
    </svg>
  );
}

export function Wordmark({ className = "h-7" }: LogoProps) {
  return (
    <span className="flex items-center gap-2.5 text-sand">
      <KairoMark className={`${className} text-gold`} />
      <span className="text-xl font-semibold tracking-[0.02em]">
        Kairo<span className="text-gold">.</span>
      </span>
    </span>
  );
}
