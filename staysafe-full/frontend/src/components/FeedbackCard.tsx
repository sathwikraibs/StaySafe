import { useState, type KeyboardEvent } from "react";
import { useI18n } from "@/i18n";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import { useRatingSummary, forgetRatingSummary, MIN_TO_SHOW } from "@/ratings";
import { IconCheck, IconLock } from "@/icons";

/** Rating + feedback, sent anonymously to the team. Used in Settings and inside the AI chat. */

const TOPICS = ["love", "improve", "better_elsewhere", "bug", "idea", "language", "other"] as const;
type Topic = (typeof TOPICS)[number];

/** What the person said in the chat, so the right topic is already picked. */
export type FeedbackIntent = "praise" | "helped" | "thanks" | "negative" | "idea" | "bug";
const INTENT_TOPIC: Record<FeedbackIntent, Topic> = {
  praise: "love", helped: "love", thanks: "love", negative: "improve", idea: "idea", bug: "bug",
};

const STAR_PATH = "M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.4l-5.8 3.1 1.1-6.5L2.6 9.4l6.5-.9z";

function StarIcon({ on, size }: { on: boolean; size: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden className="block">
      <path d={STAR_PATH} fill={on ? "#F0A500" : "none"} stroke={on ? "#F0A500" : "#B8BED0"}
        strokeWidth="1.5" strokeLinejoin="round" className="transition-[fill,stroke] duration-150" />
    </svg>
  );
}

function ShareIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="18" cy="5" r="2.5" /><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="19" r="2.5" />
      <path d="m8.2 10.8 7.6-4.4M8.2 13.2l7.6 4.4" />
    </svg>
  );
}

export function FeedbackCard({ from = "settings", intent, compact = false }: {
  from?: "settings" | "ai";
  intent?: FeedbackIntent;
  compact?: boolean;
}) {
  const { t, tl, lang, ts } = useI18n();
  const [stars, setStars] = useState(0);            // never chosen for them
  const [hover, setHover] = useState(0);            // mouse only: on phones a tap is the choice
  const [topics, setTopics] = useState<Topic[]>(intent ? [INTENT_TOPIC[intent]] : []);
  const [message, setMessage] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [allowShow, setAllowShow] = useState(false);
  const summary = useRatingSummary();

  const levels = tl("feedback.levels");
  const shown = hover || stars;
  const high = stars >= 4;

  function pick(n: number) {
    setStars(n);
    if (topics.length === 0) setTopics([n >= 4 ? "love" : "improve"]);
  }
  function onKey(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowRight" || e.key === "ArrowUp") { e.preventDefault(); pick(Math.min(5, (stars || 0) + 1)); }
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") { e.preventDefault(); pick(Math.max(1, (stars || 2) - 1)); }
  }
  function toggle(x: Topic) {
    setTopics((cur) => (cur.includes(x) ? cur.filter((y) => y !== x) : [...cur, x]));
  }
  async function send() {
    if (!stars || state === "sending") return;
    setState("sending"); setError(null);
    try {
      await apiPostJSON(`${API_BASE}/api/feedback`, { stars, topics, message: message.trim(), lang, from, share: allowShow && !!message.trim() });
      forgetRatingSummary();
      setState("done");
    } catch (e) {
      setError(errorMessage(e)); setState("idle");
    }
  }
  async function share() {
    const url = typeof window !== "undefined" ? window.location.origin : "";
    const text = `${t("feedback.shareText")} ${url}`;
    try {
      if (navigator.share) await navigator.share({ title: "TrustLight", text, url });
      else window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer");
    } catch { /* closed the share sheet */ }
  }

  const pad = compact ? "p-4" : "p-5 sm:p-6";
  const starSize = compact ? 32 : 40;

  if (state === "done") {
    return (
      <div id={compact ? undefined : "feedback"} className={`rounded-3xl border border-cream-200 bg-cream-50 text-center shadow-warm-sm ${pad}`} role="status">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sage-100 text-sage-600">
          <IconCheck className="h-6 w-6" strokeWidth={2.4} />
        </span>
        <p className="mt-3 font-heading text-lg font-bold text-ink-900">{t("feedback.thanksTitle")}</p>
        <p className="mx-auto mt-1 max-w-sm font-body text-sm leading-relaxed text-dustyblue-600">
          {high ? t("feedback.thanksHigh") : t("feedback.thanksLow")}
        </p>
        {high && (
          <button type="button" onClick={share}
            className="btn-press mt-4 inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-cream-50 px-4 py-2.5 font-body text-sm font-semibold text-brand-700 hover:bg-brand-50">
            <ShareIcon className="h-4 w-4" />{t("feedback.share")}
          </button>
        )}
      </div>
    );
  }

  return (
    <div id={compact ? undefined : "feedback"} className={`rounded-3xl border border-cream-200 bg-cream-50 shadow-warm-sm ${pad}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-heading text-lg font-bold leading-tight text-ink-900">{t("feedback.title")}</h2>
          <p className="mt-1 font-body text-sm leading-relaxed text-dustyblue-600">{t("feedback.subtitle")}</p>
        </div>
        {summary && summary.count >= MIN_TO_SHOW && (
          <p className="flex shrink-0 items-center gap-1 rounded-lg bg-cream-100 px-2 py-1 font-body text-xs font-semibold text-ink-800">
            <StarIcon on size={13} />{t("feedback.socialProof", { avg: summary.average.toFixed(1), n: summary.count })}
          </p>
        )}
      </div>

      {/* stars: a tap or click chooses; only a real mouse previews on hover */}
      <div className="mt-4 flex flex-col items-center">
        <div className="flex items-center gap-1" role="radiogroup" aria-label={t("feedback.title")} tabIndex={0} onKeyDown={onKey}
          onPointerLeave={() => setHover(0)}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" role="radio" aria-checked={stars === n} tabIndex={-1}
              aria-label={`${n} / 5, ${levels[n - 1] ?? ""}`}
              onClick={() => { setHover(0); pick(n); }}
              onPointerEnter={(e) => { if (e.pointerType === "mouse") setHover(n); }}
              className={`touch-manipulation rounded-lg p-1 transition-transform duration-150 focus:outline-none focus-visible:ring-4 focus-visible:ring-beam-200 ${shown >= n ? "scale-105" : ""}`}>
              <StarIcon on={shown >= n} size={starSize} />
            </button>
          ))}
        </div>
        <p className={`mt-1.5 h-5 font-body text-sm font-semibold ${shown ? "text-ink-800" : "text-dustyblue-500"}`} aria-live="polite">
          {shown ? levels[shown - 1] : t("feedback.tapToRate")}
        </p>
      </div>

      {stars > 0 && (
        <div className="mt-4 space-y-4 border-t border-cream-200 pt-4 animate-fade-up">
          <div>
            <p className="mb-2 font-body text-sm font-semibold text-ink-800">{t("feedback.topicsTitle")}</p>
            <div className="flex flex-wrap gap-2">
              {TOPICS.map((x) => {
                const on = topics.includes(x);
                return (
                  <button key={x} type="button" aria-pressed={on} onClick={() => toggle(x)}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 font-body text-sm transition-colors
                      ${on ? "border-brand-500 bg-brand-50 font-semibold text-brand-800" : "border-cream-300 bg-cream-50 text-ink-700 hover:border-brand-300"}`}>
                    {on && <IconCheck className="h-3.5 w-3.5" strokeWidth={2.6} />}
                    {t(`feedback.topics.${x}`)}
                  </button>
                );
              })}
            </div>
          </div>

          <label className="block">
            <span className="mb-1.5 flex items-baseline gap-2 font-body text-sm font-semibold text-ink-800">
              {t("feedback.messageLabel")}
              <span className="text-xs font-normal text-dustyblue-500">{t("feedback.optional")}</span>
            </span>
            <textarea value={message} onChange={(e) => setMessage(e.target.value.slice(0, 1500))} rows={compact ? 3 : 4}
              placeholder={high ? t("feedback.placeholderHigh") : t("feedback.placeholderLow")}
              className="w-full rounded-xl border border-cream-300 bg-cream-50 p-3 font-body text-sm text-ink-900 placeholder:text-dustyblue-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100" />
          </label>

          {message.trim().length > 0 && (
            <label className="flex cursor-pointer items-center gap-2.5 font-body text-sm text-ink-800">
              <input type="checkbox" checked={allowShow} onChange={(e) => setAllowShow(e.target.checked)}
                className="h-4 w-4 shrink-0 accent-brand-600" />
              {t("feedback.shareLabel")}
            </label>
          )}

          {error && <p className="font-body text-sm font-semibold text-rust-600">{ts(error)}</p>}

          <button type="button" onClick={send} disabled={state === "sending"}
            className="btn-press w-full rounded-xl bg-brand-600 px-5 py-3 font-body text-base font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {state === "sending" ? t("feedback.sending") : t("feedback.send")}
          </button>
          <p className="flex items-center justify-center gap-1.5 font-body text-xs text-dustyblue-500">
            <IconLock className="h-3.5 w-3.5" />{t("feedback.privacy")}
          </p>
        </div>
      )}
    </div>
  );
}
