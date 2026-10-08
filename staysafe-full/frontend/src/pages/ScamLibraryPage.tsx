import { useState, useEffect, useMemo, type ReactNode } from "react";
import { ToolHeader } from "@/components/ToolHeader";
import { Card } from "@/components/Card";
import { IconSearch, IconChevronRight, IconArrowLeft, IconPhone, IconAlert, IconCheck, IconArrowRight } from "@/icons";
import { useI18n } from "@/i18n";
import { SCAMS_EN, type Scam } from "@/scamLibrary";
import { scamsHi } from "@/i18n/scams-hi";
import { scamsKn } from "@/i18n/scams-kn";
import { scamsTcy } from "@/i18n/scams-tcy";
import type { ScamExtra } from "@/i18n/scams-types";

const EXTRA: Record<string, Record<string, ScamExtra>> = { hi: scamsHi, kn: scamsKn, tcy: scamsTcy };

/** Small line drawings, one per scam type. */
function ScamIcon({ name, className = "h-6 w-6" }: { name: Scam["icon"]; className?: string }) {
  const p: Record<Scam["icon"], ReactNode> = {
    bank: <><path d="M3 10h18L12 4z" /><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18" /></>,
    bag: <><path d="M5 8h14l-1 12H6z" /><path d="M9 8V6a3 3 0 0 1 6 0v2" /></>,
    job: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M9 7V5h6v2M3 12h18" /></>,
    chart: <><path d="M4 19V5M4 19h16" /><path d="m7 15 4-4 3 3 5-6" /></>,
    police: <><path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z" /><path d="m9.5 12 1.8 1.8L15 10" /></>,
    monitor: <><rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4M12 8v3M12 13.2v.3" /></>,
    heart: <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />,
    sim: <><path d="M7 3h7l4 4v14H7z" /><rect x="9.5" y="11" width="6" height="6" rx="1" /></>,
    bolt: <path d="M13 3 5 14h6l-1 7 8-11h-6z" />,
    box: <><path d="m3 7 9-4 9 4v10l-9 4-9-4z" /><path d="m3 7 9 4 9-4M12 11v10" /></>,
    gift: <><rect x="3" y="9" width="18" height="12" rx="1" /><path d="M3 13h18M12 9v12M12 9s-4-6-6-3 6 3 6 3 8-.5 6-3-6 3-6 3" /></>,
    upi: <><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M9 8h6M9 11h6M9 8c3 0 3 3 0 3l5 5" /></>,
    video: <><rect x="3" y="6" width="13" height="12" rx="2" /><path d="m16 10 5-3v10l-5-3" /></>,
    loan: <><circle cx="9" cy="9" r="5" /><path d="M14.5 10.5A5 5 0 1 1 9 16" /><path d="M8 7h2.5M8 9.2h2.5M9 7c1.8 0 1.8 2.2 0 2.2l2 2" /></>,
    phone: <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />,
    chat: <><path d="M4 5h16v11H9l-5 4z" /><path d="M9 10h.01M12 10h.01M15 10h.01" /></>,
    family: <><circle cx="8" cy="7" r="3" /><circle cx="17" cy="9" r="2.3" /><path d="M2.5 20a5.5 5.5 0 0 1 11 0M13.5 20a4 4 0 0 1 8 0" /></>,
    car: <><path d="M5 16V11l2-5h10l2 5v5z" /><path d="M5 11h14" /><circle cx="8" cy="16" r="1.8" /><circle cx="16" cy="16" r="1.8" /></>,
    tag: <><path d="M3 12V4h8l10 10-8 8z" /><circle cx="7.5" cy="8.5" r="1.5" /></>,
    app: <><rect x="6" y="2.5" width="12" height="19" rx="2.5" /><path d="M10 18.5h4M9 8l2 2 4-4" /></>,
  };
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
      {p[name]}
    </svg>
  );
}

const LEVEL_STYLE = {
  3: "bg-rust-400/15 text-rust-600",
  2: "bg-terracotta-300/35 text-terracotta-700",
  1: "bg-dustyblue-100 text-dustyblue-600",
} as const;

const ICON_BG = ["#E0F4F1", "#EEE8FC", "#FDF1DA", "#FCE6EE", "#DFF3F7", "#E5EAFE", "#ECEDFE", "#FDE8E2"];
const ICON_FG = ["#0E6E69", "#5737B0", "#8C5409", "#A2305B", "#1A6B82", "#2D3FB0", "#3730A3", "#A9402A"];

export function ScamLibraryPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, lang, content } = useI18n();
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // English entries + the translation for the chosen language
  const scams = useMemo<Scam[]>(() => SCAMS_EN.map((s) => ({
    ...s,
    ...(content?.scams[s.id] ?? {}),
    ...(EXTRA[lang]?.[s.id] ?? {}),
  })), [lang, content]);

  const categories = useMemo(() => Array.from(new Set(scams.map((s) => s.category))), [scams]);
  useEffect(() => setActiveCategory(null), [lang]);
  useEffect(() => { window.scrollTo({ top: 0, behavior: "smooth" }); }, [selectedId]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return scams.filter((s) => {
      if (activeCategory && s.category !== activeCategory) return false;
      if (!q) return true;
      return [s.title, s.how_it_works, s.category, s.what_to_do, s.example ?? "", ...s.red_flags].some((f) => f.toLowerCase().includes(q));
    }).sort((a, b) => b.level - a.level);
  }, [scams, query, activeCategory]);

  const selected = scams.find((s) => s.id === selectedId) ?? null;
  const colorOf = (id: string) => SCAMS_EN.findIndex((s) => s.id === id) % ICON_BG.length;

  if (selected) {
    const c = colorOf(selected.id);
    return (
      <div>
        <button
          onClick={() => setSelectedId(null)}
          className="btn-press mb-4 flex items-center gap-2 font-body text-sm font-semibold text-dustyblue-600 hover:text-brand-600"
        >
          <IconArrowLeft className="h-4 w-4" /> {t("library.backToList")}
        </button>
        <div className="space-y-4 animate-fade-up">
          <div className="relative overflow-hidden rounded-3xl p-6 shadow-warm" style={{ background: ICON_BG[c] }}>
            <span className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-cream-50/40" />
            <div className="relative flex items-start gap-4">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cream-50 shadow-warm-sm" style={{ color: ICON_FG[c] }}>
                <ScamIcon name={selected.icon} className="h-8 w-8" />
              </span>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-body text-xs font-bold uppercase tracking-wide" style={{ color: ICON_FG[c] }}>{selected.category}</span>
                  <span className={`rounded-full px-2 py-0.5 font-body text-[11px] font-bold ${LEVEL_STYLE[selected.level]}`}>{t(`libraryX.level${selected.level}`)}</span>
                </div>
                <h2 className="mt-1 font-heading text-xl font-bold text-ink-900 sm:text-2xl">{selected.title}</h2>
              </div>
            </div>
          </div>

          <Card className="p-5">
            <h3 className="mb-2 font-heading text-lg font-semibold text-ink-900">{t("library.how")}</h3>
            <p className="font-body text-[15px] leading-relaxed text-ink-700">{selected.how_it_works}</p>
          </Card>

          {selected.example && (
            <div className="rounded-2xl bg-sage-100 p-5">
              <h3 className="mb-3 font-heading text-lg font-semibold text-ink-900">{t("libraryX.example")}</h3>
              <div className="relative max-w-md rounded-2xl rounded-tl-sm bg-cream-50 px-4 py-3 shadow-warm-sm">
                <p className="font-body text-[15px] text-ink-800">{selected.example}</p>
                <span className="absolute -top-2 right-3 rounded-full bg-rust-500 px-2 py-0.5 font-body text-[10px] font-bold uppercase text-cream-50">{t("common.risky")}</span>
              </div>
              <p className="mt-2 font-body text-xs text-dustyblue-600">{t("libraryX.exampleNote")}</p>
            </div>
          )}

          <Card className="p-5">
            <h3 className="mb-3 flex items-center gap-2 font-heading text-lg font-semibold text-rust-600"><IconAlert className="h-5 w-5" /> {t("library.signs")}</h3>
            <ul className="space-y-2.5">
              {selected.red_flags.map((flag, i) => (
                <li key={i} className="flex items-start gap-2.5 rounded-xl bg-rust-400/10 px-3 py-2.5 font-body text-sm text-ink-800 animate-fade-up" style={{ animationDelay: `${i * 70}ms` }}>
                  <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-rust-500" />
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </Card>

          {selected.check && selected.check.length > 0 && (
            <Card className="p-5">
              <h3 className="mb-3 flex items-center gap-2 font-heading text-lg font-semibold text-sage-700"><IconCheck className="h-5 w-5" /> {t("libraryX.check")}</h3>
              <ol className="space-y-2.5">
                {selected.check.map((step, i) => (
                  <li key={i} className="flex items-start gap-3 font-body text-sm text-ink-800">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sage-200 font-heading text-xs font-bold text-sage-700">{i + 1}</span>
                    <span className="pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </Card>
          )}

          <div className="rounded-2xl bg-sage-100 p-5">
            <h3 className="mb-2 font-heading text-lg font-semibold text-sage-700">{t("library.todo")}</h3>
            <p className="font-body text-[15px] text-ink-800">{selected.what_to_do}</p>
          </div>

          <div className="grid gap-2.5 sm:grid-cols-2">
            {selected.tool && onNavigate && (
              <button onClick={() => onNavigate(selected.tool!)} className="btn-press flex items-center justify-between gap-2 rounded-2xl bg-brand-500 px-4 py-3.5 text-left font-body text-sm font-bold text-cream-50 shadow-warm hover:bg-brand-600 sm:col-span-2">
                {t("libraryX.tryTool")} <IconArrowRight className="h-5 w-5 shrink-0" />
              </button>
            )}
            <a href="tel:1930" className="btn-press flex items-center justify-center gap-2 rounded-2xl bg-rust-500 px-4 py-3 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-rust-600">
              <IconPhone className="h-5 w-5" /> {t("libraryX.lostMoney")}
            </a>
            <a href="https://sancharsaathi.gov.in/sfc/" target="_blank" rel="noopener noreferrer" className="btn-press flex items-center justify-center gap-2 rounded-2xl border-2 border-rust-300 bg-cream-50 px-4 py-3 font-body text-sm font-bold text-rust-600">
              {t("libraryX.reportChakshu")}
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <ToolHeader path="/scam-library" title={t("library.title")} subtitle={t("library.subtitle")} />

      <div className="mb-4 flex items-start gap-3 rounded-2xl border-2 border-terracotta-300 bg-terracotta-300/20 p-4">
        <IconAlert className="mt-0.5 h-5 w-5 shrink-0 text-terracotta-700" />
        <p className="font-body text-sm text-ink-800"><b className="text-terracotta-700">{t("libraryX.tipTitle")}:</b> {t("libraryX.tip")}</p>
      </div>

      <div className="relative mb-4">
        <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-dustyblue-400">
          <IconSearch className="h-5 w-5" />
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("library.search")}
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-12 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-brand-400"
        />
      </div>

      <div className="no-scrollbar -mx-4 mb-5 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
        <button
          onClick={() => setActiveCategory(null)}
          className={`btn-press shrink-0 rounded-full px-4 py-2 font-body text-sm font-semibold ${!activeCategory ? "bg-ink-800 text-cream-50" : "bg-cream-100 text-dustyblue-600"}`}
        >{t("library.all")}</button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
            className={`btn-press shrink-0 whitespace-nowrap rounded-full px-4 py-2 font-body text-sm font-semibold ${activeCategory === cat ? "bg-ink-800 text-cream-50" : "bg-cream-100 text-dustyblue-600"}`}
          >{cat}</button>
        ))}
      </div>

      <p className="mb-3 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-500">{t("libraryX.count", { n: results.length })}</p>

      {results.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="font-body text-sm text-dustyblue-600">{t("library.none")}</p>
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {results.map((scam, i) => {
            const c = colorOf(scam.id);
            return (
              <button
                key={scam.id}
                onClick={() => setSelectedId(scam.id)}
                className="btn-press card-hover group flex w-full items-start gap-3.5 rounded-2xl bg-cream-50 p-4 text-left shadow-warm animate-fade-up"
                style={{ animationDelay: `${Math.min(i, 10) * 35}ms` }}
              >
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-transform group-hover:scale-105" style={{ background: ICON_BG[c], color: ICON_FG[c] }}>
                  <ScamIcon name={scam.icon} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-1.5">
                    <span className="font-body text-[11px] font-bold uppercase tracking-wide" style={{ color: ICON_FG[c] }}>{scam.category}</span>
                    {scam.level === 3 && <span className={`rounded-full px-1.5 py-0.5 font-body text-[10px] font-bold ${LEVEL_STYLE[3]}`}>{t("libraryX.level3")}</span>}
                  </span>
                  <span className="mt-0.5 block font-heading text-[15px] font-semibold leading-snug text-ink-900">{scam.title}</span>
                  <span className="mt-1 line-clamp-2 block font-body text-sm text-dustyblue-600">{scam.how_it_works}</span>
                </span>
                <IconChevronRight className="mt-3 h-5 w-5 shrink-0 text-dustyblue-400" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
