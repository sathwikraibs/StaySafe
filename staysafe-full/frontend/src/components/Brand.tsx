/** The TrustLight name and the animated lighthouse used on the home page. */

/** "TrustLight" written as the brand: "Trust" in deep navy, "Light" in the lighthouse indigo. */
export function Wordmark({ className = "", light = false }: { className?: string; light?: boolean }) {
  return (
    <span className={`font-heading font-extrabold leading-none tracking-[-0.01em] ${className}`}>
      <span className={light ? "text-white" : "text-ink-900"}>Trust</span>
      <span className={light ? "text-beam-300" : "text-brand-600"}>Light</span>
    </span>
  );
}

/**
 * The lighthouse from the logo, on a night sea: its light sweeps slowly left and right,
 * the lamp glows, the sea moves and a few stars twinkle. Everything stops for people who
 * prefer less motion (see .lh-* rules in index.css).
 */
export function LighthouseHero({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 120" className={className} aria-hidden>
      <defs>
        <linearGradient id="lh-beam-r" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#FDE68A" stopOpacity="0.95" />
          <stop offset="1" stopColor="#FDE68A" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="lh-beam-l" x1="1" y1="0" x2="0" y2="0">
          <stop offset="0" stopColor="#FDE68A" stopOpacity="0.95" />
          <stop offset="1" stopColor="#FDE68A" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="lh-glow">
          <stop offset="0" stopColor="#FDE68A" stopOpacity="0.9" />
          <stop offset="1" stopColor="#FDE68A" stopOpacity="0" />
        </radialGradient>
        <clipPath id="lh-sky"><rect x="0" y="0" width="120" height="120" rx="60" /></clipPath>
      </defs>

      <g clipPath="url(#lh-sky)">
        <rect x="0" y="0" width="120" height="120" fill="rgba(255,255,255,0.06)" />
        {/* stars */}
        <circle className="lh-star" cx="22" cy="26" r="1.2" fill="#fff" />
        <circle className="lh-star" cx="96" cy="20" r="1" fill="#fff" style={{ animationDelay: "1.1s" }} />
        <circle className="lh-star" cx="88" cy="46" r="0.9" fill="#fff" style={{ animationDelay: "2s" }} />
        <circle className="lh-star" cx="30" cy="54" r="0.8" fill="#fff" style={{ animationDelay: "0.5s" }} />

        {/* the light: two soft beams turning around the lamp */}
        <g className="lh-beams">
          <path d="M64 40 L124 22 V58 Z" fill="url(#lh-beam-r)" />
          <path d="M56 40 L-4 22 V58 Z" fill="url(#lh-beam-l)" />
        </g>
        <circle className="lh-glow" cx="60" cy="40" r="14" fill="url(#lh-glow)" />

        {/* the lighthouse */}
        <g className="lh-tower">
          <path d="M51 36 L60 27 L69 36 Z" fill="#FFFFFF" />
          <rect x="53.5" y="35.5" width="13" height="9" rx="2" fill="#FBBF24" />
          <path d="M52.5 45 H67.5 L71 88 H49 Z" fill="#FFFFFF" />
          <path d="M51.3 59 H68.7 L69.5 68 H50.5 Z" fill="#FBBF24" />
          <rect x="42" y="86" width="36" height="5" rx="2.5" fill="#FFFFFF" />
        </g>

        {/* the sea */}
        <g className="lh-sea">
          <path d="M-40 97 q10 -5 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 V130 H-40 Z" fill="rgba(255,255,255,0.14)" />
        </g>
        <g className="lh-sea lh-sea-2">
          <path d="M-40 104 q10 -4 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 V130 H-40 Z" fill="rgba(255,255,255,0.10)" />
        </g>
      </g>
    </svg>
  );
}
