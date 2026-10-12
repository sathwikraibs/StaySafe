import { useI18n } from "@/i18n";
import { useRatingSummary, MIN_TO_SHOW } from "@/ratings";
import { languageName } from "@/components/TranslationPanel";

function Stars({ value, size = 18 }: { value: number; size?: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" aria-hidden>
      {[1, 2, 3, 4, 5].map((n) => {
        const fill = Math.max(0, Math.min(1, value - (n - 1)));   // partly filled for 4.6 etc.
        return (
          <svg key={n} viewBox="0 0 24 24" width={size} height={size}>
            <defs>
              <linearGradient id={`rs-${n}-${Math.round(fill * 100)}`}>
                <stop offset={`${fill * 100}%`} stopColor="#F0A500" />
                <stop offset={`${fill * 100}%`} stopColor="#D7DBE8" />
              </linearGradient>
            </defs>
            <path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.4l-5.8 3.1 1.1-6.5L2.6 9.4l6.5-.9z"
              fill={`url(#rs-${n}-${Math.round(fill * 100)})`} />
          </svg>
        );
      })}
    </span>
  );
}

/** Average stars, how many of each, and the latest reviews people allowed to be shown. */
export function RatingSummary() {
  const { t, lang } = useI18n();
  const s = useRatingSummary();
  if (!s || s.count < MIN_TO_SHOW) return null;
  const max = Math.max(1, ...Object.values(s.stars));
  const when = (at: number) => {
    try { return new Date(at * 1000).toLocaleDateString(lang === "tcy" ? "kn-IN" : `${lang}-IN`, { day: "numeric", month: "short", year: "numeric" }); }
    catch { return ""; }
  };

  return (
    <section className="overflow-hidden rounded-3xl bg-cream-50 shadow-warm">
      <div className="flex flex-col gap-5 p-5 sm:flex-row sm:items-center sm:p-6">
        <div className="flex shrink-0 flex-col items-center sm:w-40">
          <p className="font-heading text-5xl font-extrabold text-ink-900">{s.average.toFixed(1)}</p>
          <Stars value={s.average} size={22} />
          <p className="mt-1 font-body text-xs font-semibold text-dustyblue-600">
            {t("feedback.outOf")} · {t("feedback.ratings", { n: s.count })}
          </p>
        </div>
        <div className="flex-1 space-y-1.5">
          {(["5", "4", "3", "2", "1"] as const).map((k) => (
            <div key={k} className="flex items-center gap-2">
              <span className="w-6 text-right font-body text-xs font-bold text-ink-700">{k}★</span>
              <span className="h-2.5 flex-1 overflow-hidden rounded-full bg-cream-200">
                <span className="block h-full rounded-full bg-gradient-to-r from-beam-300 to-beam-500 grow-x origin-left"
                  style={{ width: `${(s.stars[k] / max) * 100}%` }} />
              </span>
              <span className="w-8 font-body text-xs text-dustyblue-600">{s.stars[k]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-cream-200 bg-cream-100/60 p-5 sm:p-6">
        <h2 className="mb-3 font-heading text-lg font-semibold text-ink-900">{t("feedback.peopleTitle")}</h2>
        {s.reviews.length === 0 ? (
          <p className="font-body text-sm text-dustyblue-600">{t("feedback.noReviews")}</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {s.reviews.map((r) => (
              <li key={r.id} className="rounded-2xl bg-cream-50 p-4 shadow-warm-sm">
                <div className="flex items-center justify-between gap-2">
                  <Stars value={r.stars} size={15} />
                  <span className="font-body text-[11px] text-dustyblue-500">{when(r.at)}</span>
                </div>
                <p className="mt-2 font-body text-sm leading-relaxed text-ink-800">“{r.text}”</p>
                {r.lang !== lang && (
                  <p className="mt-1.5 font-body text-[11px] font-semibold text-dustyblue-500">{languageName(r.lang, lang)}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
