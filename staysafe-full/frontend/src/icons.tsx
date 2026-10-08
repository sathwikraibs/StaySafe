interface IconProps {
  className?: string;
  strokeWidth?: number;
}

const base = (sw = 1.9) => ({
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: sw,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export function IconHome({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 11.5 12 4l8 7.5" />
      <path d="M6 10.5V19a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-8.5" />
      <path d="M10 20v-5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5" />
    </svg>
  );
}

export function IconLink({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="2.6" y="8.2" width="11" height="7.6" rx="3.8" transform="rotate(-45 8.1 12)" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M10.4 13.6a3.3 3.3 0 0 0 4.7 0l3.3-3.3a3.3 3.3 0 0 0-4.7-4.7l-1.1 1.1" />
      <path d="M13.6 10.4a3.3 3.3 0 0 0-4.7 0l-3.3 3.3a3.3 3.3 0 0 0 4.7 4.7l1.1-1.1" />
    </svg>
  );
}

export function IconMessage({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M5.5 4.5h13a2.5 2.5 0 0 1 2.5 2.5v7.5a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5V17A2.5 2.5 0 0 1 3 14.5V7a2.5 2.5 0 0 1 2.5-2.5z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M5.5 4.5h13a2.5 2.5 0 0 1 2.5 2.5v7.5a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5V17A2.5 2.5 0 0 1 3 14.5V7a2.5 2.5 0 0 1 2.5-2.5z" />
      <path d="M7.5 9h9M7.5 12.5h5.5" />
    </svg>
  );
}

export function IconQr({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" fill="currentColor" opacity=".16" stroke="none" />
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.8" />
      <path d="M6.5 6.5h1v1h-1zM16.5 6.5h1v1h-1zM6.5 16.5h1v1h-1z" fill="currentColor" />
      <path d="M14 14h2.5v2.5M20.5 14v.01M14 20.5h2.5M20.5 17.5v3h-1.5" />
    </svg>
  );
}

export function IconFile({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M6.5 3h7.5l5 5v11.5A1.5 1.5 0 0 1 17.5 21h-11A1.5 1.5 0 0 1 5 19.5v-15A1.5 1.5 0 0 1 6.5 3z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z" />
      <path d="M14 3v5h5" />
      <path d="M8.5 13h7M8.5 16.5h4.5" />
    </svg>
  );
}

export function IconKey({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="8" cy="15" r="4.5" fill="currentColor" opacity=".16" stroke="none" />
      <circle cx="8" cy="15" r="4.5" />
      <path d="M11.3 11.7 20 3M16.5 6.5l2.5 2.5M14 9l2 2" />
      <circle cx="8" cy="15" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconNetwork({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M12 20.5 6.6 14a8 8 0 0 1 10.8 0z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M2.5 8.5a14 14 0 0 1 19 0" />
      <path d="M5.5 11.8a9.5 9.5 0 0 1 13 0" />
      <path d="M8.6 15a5 5 0 0 1 6.8 0" />
      <circle cx="12" cy="18.6" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconEmail({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="3" y="5" width="18" height="14" rx="2.5" fill="currentColor" opacity=".16" stroke="none" />
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="m3.8 6.5 7 5.5a2 2 0 0 0 2.4 0l7-5.5" />
    </svg>
  );
}

export function IconDashboard({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M3.5 16a8.5 8.5 0 0 1 17 0z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M3.5 16a8.5 8.5 0 0 1 17 0" />
      <path d="M12 16l3.5-4.5" />
      <circle cx="12" cy="16" r="1.5" fill="currentColor" stroke="none" />
      <path d="M3.5 19.5h17" />
    </svg>
  );
}

export function IconAlert({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M12 3 2 20h20L12 3z" />
      <path d="M12 10v5M12 18v.5" />
    </svg>
  );
}

export function IconBook({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M12 6.5C10 5 7.2 4.5 3.5 4.8v13.5c3.7-.3 6.5.2 8.5 1.7z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M12 6.5C10 5 7.2 4.5 3.5 4.8v13.5c3.7-.3 6.5.2 8.5 1.7 2-1.5 4.8-2 8.5-1.7V4.8C16.8 4.5 14 5 12 6.5z" />
      <path d="M12 6.5V20" />
    </svg>
  );
}

export function IconShield({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function IconUpload({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2" />
      <path d="M12 15V4M12 4l-3 3M12 4l3 3" />
    </svg>
  );
}

export function IconSearch({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4-4" />
    </svg>
  );
}

export function IconCheck({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="m5 12 4 4 10-10" />
    </svg>
  );
}

export function IconWarning({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5M12 16v.5" />
    </svg>
  );
}

export function IconClose({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  );
}

export function IconArrowRight({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function IconArrowLeft({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M19 12H5M11 6l-6 6 6 6" />
    </svg>
  );
}

export function IconChevronRight({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="m9 6 6 6-6 6" />
    </svg>
  );
}

export function IconHistory({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 12a8 8 0 1 0 3-6.2L4 8" />
      <path d="M4 4v4h4" />
      <path d="M12 8v4l3 2" />
    </svg>
  );
}

export function IconChat({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M12 3.5c4.7 0 8.5 3.3 8.5 7.4s-3.8 7.4-8.5 7.4c-1 0-2-.15-2.9-.43L4.5 19.8l1.2-3.6C4.3 14.8 3.5 13 3.5 10.9c0-4.1 3.8-7.4 8.5-7.4z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M12 3.5c4.7 0 8.5 3.3 8.5 7.4s-3.8 7.4-8.5 7.4c-1 0-2-.15-2.9-.43L4.5 19.8l1.2-3.6C4.3 14.8 3.5 13 3.5 10.9c0-4.1 3.8-7.4 8.5-7.4z" />
      <path d="M8.5 11h.01M12 11h.01M15.5 11h.01" strokeWidth="2.6" />
    </svg>
  );
}

export function IconPhone({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M6.6 3.5h2.6l1.6 4.2-2 1.4a11.5 11.5 0 0 0 6.1 6.1l1.4-2 4.2 1.6v2.6a2 2 0 0 1-2.2 2A16.6 16.6 0 0 1 4.6 5.7a2 2 0 0 1 2-2.2z" fill="currentColor" opacity=".16" stroke="none" />
      <path d="M6.6 3.5h2.6l1.6 4.2-2 1.4a11.5 11.5 0 0 0 6.1 6.1l1.4-2 4.2 1.6v2.6a2 2 0 0 1-2.2 2A16.6 16.6 0 0 1 4.6 5.7a2 2 0 0 1 2-2.2z" />
    </svg>
  );
}

export function IconHelp({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="3.5" />
      <path d="m5.6 5.6 3.9 3.9M14.5 14.5l3.9 3.9M18.4 5.6l-3.9 3.9M9.5 14.5l-3.9 3.9" />
    </svg>
  );
}

export function IconLock({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

export function IconGlobe({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}

export function IconSettings({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
    </svg>
  );
}

export function IconInfo({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8v.5" />
    </svg>
  );
}

export function IconLanguage({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 5h8M8 3v2M10 5c-.5 3.5-2.5 6.5-6 8M6 9c1 2 2.8 3.5 5 4.5" />
      <path d="m13 21 4-9 4 9M14.5 18h5" />
    </svg>
  );
}

export function IconCamera({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 8a2 2 0 0 1 2-2h1.5l1.5-2h6l1.5 2H18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
      <circle cx="12" cy="12.5" r="3.5" />
    </svg>
  );
}

export function IconImage({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="3.5" y="4.5" width="17" height="15" rx="2" />
      <circle cx="9" cy="10" r="1.6" />
      <path d="m4 17 5-4.5 4 3.5 3-2.5 4 3.5" />
    </svg>
  );
}

export function IconFolder({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M3.5 7a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z" />
    </svg>
  );
}

/** The TrustLight lighthouse app icon: warns you before danger. Full colour tile. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden>
      <rect width="100" height="100" rx="22.5" fill="#3730A3" />
      <g transform="translate(50 50) scale(0.86) translate(-50 -53)">
        <path d="M57 32 L86 22 V44 Z" fill="#FDE68A" />
        <path d="M43 32 L14 22 V44 Z" fill="#FDE68A" />
        <path d="M40 29 L50 19 L60 29 Z" fill="#FFFFFF" />
        <rect x="43" y="29" width="14" height="10" rx="2" fill="#FBBF24" />
        <path d="M42 40 H58 L62 82 H38 Z" fill="#FFFFFF" />
        <path d="M40.6 55 H59.4 L60.2 64 H39.8 Z" fill="#FBBF24" />
        <rect x="30" y="81" width="40" height="6" rx="3" fill="#FFFFFF" />
      </g>
    </svg>
  );
}
