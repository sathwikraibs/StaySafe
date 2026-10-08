import type { ComponentType } from "react";

export interface TabChoice<T extends string> {
  id: T;
  label: string;
  icon?: ComponentType<{ className?: string }>;
}

/**
 * Two (or more) ways to do the same check, as tabs: only the chosen one is shown, so the page
 * never shows two forms at once.
 */
export function ChoiceTabs<T extends string>({ value, onChange, choices, disabled }: {
  value: T;
  onChange: (v: T) => void;
  choices: TabChoice<T>[];
  disabled?: boolean;
}) {
  return (
    <div role="tablist" className="mb-3 grid gap-1 rounded-2xl bg-cream-200/70 p-1" style={{ gridTemplateColumns: `repeat(${choices.length}, minmax(0, 1fr))` }}>
      {choices.map((c) => {
        const active = c.id === value;
        return (
          <button
            key={c.id}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={disabled}
            onClick={() => onChange(c.id)}
            className={`btn-press flex min-w-0 items-center justify-center gap-2 rounded-xl px-2 py-3 font-body text-sm font-bold leading-tight transition-colors disabled:opacity-60
              ${active ? "bg-cream-50 text-ink-900 shadow-warm-sm" : "text-dustyblue-600 hover:text-ink-800"}`}
          >
            {c.icon && <c.icon className={`h-5 w-5 shrink-0 ${active ? "text-brand-600" : ""}`} />}
            <span className="min-w-0 text-center">{c.label}</span>
          </button>
        );
      })}
    </div>
  );
}
