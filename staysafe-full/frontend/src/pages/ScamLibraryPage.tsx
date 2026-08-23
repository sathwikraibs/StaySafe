import { useState, useEffect, useCallback } from "react";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, NETWORK_ERROR_MSG } from "@/api";
import { API_BASE } from "@/config";
import type { ScamLibraryResponse, CategoriesResponse, ScamEntry } from "@/types";
import { IconSearch, IconChevronRight, IconArrowLeft } from "@/icons";

export function ScamLibraryPage() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [results, setResults] = useState<ScamEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ScamEntry | null>(null);

  useEffect(() => {
    apiGet<CategoriesResponse>(`${API_BASE}/api/scam-library/categories`)
      .then((d) => setCategories(d.categories))
      .catch(() => {});
  }, []);

  const search = useCallback(async (q: string, cat: string | null) => {
    setLoading(true); setError(null); setSelected(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (cat) params.set("category", cat);
      const url = `${API_BASE}/api/scam-library${params.toString() ? "?" + params.toString() : ""}`;
      const data = await apiGet<ScamLibraryResponse>(url);
      setResults(data.scams);
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => search(query, activeCategory), 300);
    return () => clearTimeout(t);
  }, [query, activeCategory, search]);

  if (selected) {
    return (
      <div>
        <button
          onClick={() => setSelected(null)}
          className="btn-press mb-4 flex items-center gap-2 font-body text-sm font-semibold text-dustyblue-600 hover:text-terracotta-600"
        >
          <IconArrowLeft className="h-4 w-4" /> Back to list
        </button>
        <div className="space-y-4 animate-fade-up">
          <Card className="p-6">
            <p className="font-body text-xs font-semibold uppercase tracking-wide text-terracotta-600">{selected.category}</p>
            <h2 className="mt-1 font-heading text-xl font-semibold text-ink-900">{selected.title}</h2>
          </Card>
          <Card className="p-5">
            <h3 className="mb-2 font-heading text-base font-semibold text-ink-800">How it works</h3>
            <p className="font-body text-sm text-ink-700">{selected.how_it_works}</p>
          </Card>
          <Card className="p-5">
            <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">Signs to watch for</h3>
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
            <h3 className="mb-2 font-heading text-base font-semibold text-ink-800">What to do</h3>
            <p className="font-body text-sm text-ink-700">{selected.what_to_do}</p>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Scam Knowledge Base" subtitle="Learn about common scams so you can spot them before they happen." />

      {/* Search */}
      <div className="relative mb-4">
        <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-dustyblue-400">
          <IconSearch className="h-5 w-5" />
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a scam..."
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-12 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
        />
      </div>

      {/* Categories */}
      {categories.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`btn-press rounded-xl px-3.5 py-2 font-body text-sm font-semibold ${!activeCategory ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
          >All</button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
              className={`btn-press rounded-xl px-3.5 py-2 font-body text-sm font-semibold ${activeCategory === cat ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
            >{cat}</button>
          ))}
        </div>
      )}

      {loading && <LoadingBreath label="Finding scams to learn about..." />}
      {error && <ErrorNotice>{error}</ErrorNotice>}

      {!loading && !error && results.length === 0 && (
        <Card className="p-8 text-center">
          <p className="font-body text-sm text-dustyblue-600">No scams found. Try a different search.</p>
        </Card>
      )}

      {!loading && !error && results.length > 0 && (
        <div className="space-y-3">
          {results.map((scam) => (
            <button
              key={scam.id}
              onClick={() => setSelected(scam)}
              className="btn-press card-hover flex w-full items-center gap-4 rounded-2xl bg-cream-50 p-5 text-left shadow-warm"
            >
              <div className="flex-1 min-w-0">
                <p className="font-body text-xs font-semibold uppercase tracking-wide text-terracotta-600">{scam.category}</p>
                <p className="mt-0.5 font-heading text-base font-semibold text-ink-900">{scam.title}</p>
                <p className="mt-1 truncate font-body text-sm text-dustyblue-600">{scam.how_it_works}</p>
              </div>
              <IconChevronRight className="h-5 w-5 shrink-0 text-dustyblue-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
