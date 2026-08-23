import type { ReactNode } from "react";

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="font-heading text-2xl font-semibold text-ink-900 sm:text-3xl">{title}</h1>
      {subtitle && <p className="mt-2 font-body text-base text-dustyblue-600">{subtitle}</p>}
    </div>
  );
}

export function FindingsList({ items, title = "What we noticed" }: { items: string[]; title?: string }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="mt-4 rounded-2xl bg-cream-100 p-5">
      <h3 className="mb-3 font-heading text-lg font-semibold text-ink-800">{title}</h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 font-body text-sm text-ink-700">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-terracotta-400" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ErrorNotice({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border-2 border-rust-400 bg-rust-400/15 p-4 animate-fade-up">
      <div className="shrink-0 text-rust-500">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16v.5" />
        </svg>
      </div>
      <p className="font-body text-sm text-rust-600">{children}</p>
    </div>
  );
}
