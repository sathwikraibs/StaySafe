import { useState, useEffect, useMemo } from "react";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScamLibraryResponse, ScamEntry } from "@/types";
import { IconSearch, IconChevronRight, IconArrowLeft } from "@/icons";
import { useI18n } from "@/i18n";

export function ScamLibraryPage() {
  const { t, content } = useI18n();
  const [query, setQuery] = useState("");
  const [allScams, setAllScams] = useState<ScamEntry[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Load the whole library once; search happens here so it works in every language
  useEffect(() => {
    apiGet<ScamLibraryResponse>(`${API_BASE}/api/scam-library`)
      .then((d) => setAllScams(d.scams))
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  // Swap in the translated text for each entry (falls back to English)
  const scams = useMemo<ScamEntry[]>(
    () => allScams.map((s) => ({ ...s, ...(content?.scams[s.id] ?? {}) })),
    [allScams, content],
  );

  const categories = useMemo(() => Array.from(new Set(scams.map((s) => s.category))), [scams]);

  // Reset the category filter when the language changes (names change)
  useEffect(() => setActiveCategory(null), [content]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return scams.filter((s) => {
      if (activeCategory && s.category !== activeCategory) return false;
      if (!q) return true;
      return [s.title, s.how_it_works, s.category, s.what_to_do, ...s.red_flags].some((f) => f.toLowerCase().includes(q));
    });
  }, [scams, query, activeCategory]);

  const selected = scams.find((s) => s.id === selectedId) ?? null;

  if (selected) {
    return (
      <div>
        <button
          onClick={() => setSelectedId(null)}
          className="btn-press mb-4 flex items-center gap-2 font-body text-sm font-semibold text-dustyblue-600 hover:text-terracotta-600"
        >
          <IconArrowLeft className="h-4 w-4" /> {t("library.backToList")}
        </button>
        <div className="space-y-4 animate-fade-up">
          <Card className="p-6">
            <p className="font-body text-xs font-semibold uppercase tracking-wide text-terracotta-600">{selected.category}</p>
            <h2 className="mt-1 font-heading text-xl font-semibold text-ink-900">{selected.title}</h2>
          </Card>
          <Card className="p-5">
            <h3 className="mb-2 font-heading text-base font-semibold text-ink-800">{t("library.how")}</h3>
            <p className="font-body text-sm text-ink-700">{selected.how_it_works}</p>
          </Card>
          <Card className="p-5">
            <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("library.signs")}</h3>
            <ul className="space-y-2">
              {selected.red_flags.map((flag, i) => (
                <li key={i} className="flex items-start gap-2 font-body text-sm text-ink-700">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-terracotta-400" />
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card className="p-5">
            <h3 className="mb-2 font-heading text-base font-semibold text-ink-800">{t("library.todo")}</h3>
            <p className="font-body text-sm text-ink-700">{selected.what_to_do}</p>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={t("library.title")} subtitle={t("library.subtitle")} />

      <div className="relative mb-4">
        <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-dustyblue-400">
          <IconSearch className="h-5 w-5" />
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("library.search")}
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-12 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
        />
      </div>

      {categories.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`btn-press rounded-xl px-3.5 py-2 font-body text-sm font-semibold ${!activeCategory ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
          >{t("library.all")}</button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
              className={`btn-press rounded-xl px-3.5 py-2 font-body text-sm font-semibold ${activeCategory === cat ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
            >{cat}</button>
          ))}
        </div>
      )}

      {loading && <LoadingBreath label={t("library.loading")} />}
      {error && <ErrorNotice>{error}</ErrorNotice>}

      {!loading && !error && results.length === 0 && (
        <Card className="p-8 text-center">
          <p className="font-body text-sm text-dustyblue-600">{t("library.none")}</p>
        </Card>
      )}

      {!loading && !error && results.length > 0 && (
        <div className="space-y-3">
          {results.map((scam) => (
            <button
              key={scam.id}
              onClick={() => setSelectedId(scam.id)}
              className="btn-press card-hover flex w-full items-center gap-4 rounded-2xl bg-cream-50 p-5 text-left shadow-warm"
            >
              <div className="min-w-0 flex-1">
                <p className="font-body text-xs font-semibold uppercase tracking-wide text-terracotta-600">{scam.category}</p>
                <p className="mt-0.5 font-heading text-base font-semibold text-ink-900">{scam.title}</p>
                <p className="mt-1 line-clamp-2 font-body text-sm text-dustyblue-600">{scam.how_it_works}</p>
              </div>
              <IconChevronRight className="h-5 w-5 shrink-0 text-dustyblue-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
