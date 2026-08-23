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
