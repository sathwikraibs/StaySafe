import { useState, type ReactNode } from "react";

export type SectionTone = "neutral" | "good" | "warn" | "bad" | "info";

const TONE: Record<SectionTone, { icon: string; pill: string }> = {
  neutral: { icon: "bg-cream-200 text-ink-700", pill: "bg-cream-200 text-ink-700" },
  good: { icon: "bg-sage-100 text-sage-700", pill: "bg-sage-100 text-sage-700" },
  warn: { icon: "bg-terracotta-300/30 text-terracotta-700", pill: "bg-terracotta-300/30 text-terracotta-700" },
  bad: { icon: "bg-rust-400/15 text-rust-600", pill: "bg-rust-400/15 text-rust-600" },
  info: { icon: "bg-dustyblue-100 text-dustyblue-600", pill: "bg-dustyblue-100 text-dustyblue-600" },
};

/**
 * One block of the result, always in the same shape: icon, title, a short summary on the
 * right, and a › / ˄ to open or close it. Important blocks start open; details start closed.
 */
export function Section({ icon, title, summary, tone = "neutral", defaultOpen = false, children }: {
  icon: ReactNode;
  title: string;
  summary?: ReactNode;
  tone?: SectionTone;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const style = TONE[tone];
  return (
    <section className="overflow-hidden rounded-2xl border border-cream-200 bg-cream-50 shadow-warm-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-cream-100/70 sm:px-5"
      >
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${style.icon}`}>{icon}</span>
        <span className="min-w-0 flex-1">
          <span className="block font-heading text-[15px] font-bold text-ink-900 sm:text-base">{title}</span>
        </span>
        {summary !== undefined && summary !== null && summary !== "" && (
          <span className={`max-w-[45%] shrink-0 truncate rounded-full px-2.5 py-1 font-body text-xs font-bold ${style.pill}`}>{summary}</span>
        )}
        <svg viewBox="0 0 24 24" className={`h-5 w-5 shrink-0 text-dustyblue-500 transition-transform duration-200 ${open ? "-rotate-90" : ""}`} aria-hidden>
          <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && <div className="border-t border-cream-200 px-4 pb-4 pt-3 animate-fade-up sm:px-5">{children}</div>}
    </section>
  );
}
