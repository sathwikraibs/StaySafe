interface IconProps {
  className?: string;
  strokeWidth?: number;
}

const base = (sw = 2) => ({
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
      <path d="M9 15 15 9" />
      <path d="M10.5 7.5 11.8 6.2a3.5 3.5 0 0 1 5 5l-1.3 1.3" />
      <path d="M13.5 16.5 12.2 17.8a3.5 3.5 0 0 1-5-5l1.3-1.3" />
    </svg>
  );
}

export function IconMessage({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H8l-4 3V6a1 1 0 0 1 1-1z" />
      <path d="M8 9h8M8 12h5" />
    </svg>
  );
}

export function IconQr({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <rect x="14" y="4" width="6" height="6" rx="1" />
      <rect x="4" y="14" width="6" height="6" rx="1" />
      <path d="M14 14h2v2M18 14v6M14 18h2M14 20h6" />
    </svg>
  );
}

export function IconFile({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M14 3v5h5" />
      <path d="M10 13h5M10 16h5" />
    </svg>
  );
}

export function IconKey({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <circle cx="8" cy="15" r="4" />
      <path d="M10.8 12.2 20 3M17 6l2 2M14 9l2.5 2.5" />
    </svg>
  );
}

export function IconNetwork({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M5 12a7 7 0 0 1 14 0" />
      <path d="M8 12a4 4 0 0 1 8 0" />
      <circle cx="12" cy="12" r="1.5" />
      <path d="M12 13.5V18M12 18l-2 2M12 18l2 2" />
    </svg>
  );
}

export function IconEmail({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </svg>
  );
}

export function IconDashboard({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M4 13a8 8 0 0 1 16 0" />
      <path d="M12 13l4-3" />
      <circle cx="12" cy="13" r="1.5" />
      <path d="M3 18h18" />
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
      <path d="M5 4a1 1 0 0 1 1-1h6v17H6a1 1 0 0 1-1-1V4z" />
      <path d="M19 4a1 1 0 0 0-1-1h-6v17h6a1 1 0 0 0 1-1V4z" />
      <path d="M8 7h2M8 10h2" />
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
      <path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.1A8 8 0 1 1 20 12z" />
      <path d="M8.5 11h.01M12 11h.01M15.5 11h.01" />
    </svg>
  );
}

export function IconPhone({ className, strokeWidth }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base(strokeWidth)}>
      <path d="M5 4h3l2 5-2.5 1.5a11 11 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" />
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
