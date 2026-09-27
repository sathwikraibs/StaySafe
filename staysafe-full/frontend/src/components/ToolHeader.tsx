import { ALL_NAV } from "@/nav";
import { themeFor } from "@/toolTheme";

/** Colourful page header for each tool: its own colour, icon and a soft moving background. */
export function ToolHeader({ path, title, subtitle }: { path: string; title: string; subtitle?: string }) {
  const th = themeFor(path);
  const Icon = ALL_NAV.find((n) => n.path === path)?.icon;
  return (
    <div className="relative mb-5 overflow-hidden rounded-3xl p-5 shadow-warm animate-fade-up sm:p-6" style={{ background: th.soft }}>
      <span className="header-blob pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full opacity-40" style={{ background: th.from }} />
      <span className="header-blob pointer-events-none absolute -bottom-16 right-24 h-28 w-28 rounded-full opacity-20" style={{ background: th.to, animationDelay: "-3s" }} />
      <div className="relative flex items-center gap-4">
        {Icon && (
          <span
            className="header-icon flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl text-cream-50 shadow-warm sm:h-16 sm:w-16"
            style={{ backgroundImage: `linear-gradient(135deg, ${th.from}, ${th.to})` }}
          >
            <Icon className="h-7 w-7 sm:h-8 sm:w-8" />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="font-heading text-2xl font-bold leading-tight text-ink-900 sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1.5 font-body text-[15px] leading-snug" style={{ color: th.ink }}>{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}
