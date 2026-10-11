import { useState } from "react";
import { useI18n } from "@/i18n";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import { useRatingSummary, forgetRatingSummary, MIN_TO_SHOW } from "@/ratings";

/** Rating + feedback, sent anonymously to the team (Telegram). Used in Settings and inside the AI chat. */

const TOPICS = ["love", "improve", "better_elsewhere", "bug", "idea", "language", "other"] as const;
type Topic = (typeof TOPICS)[number];
const TOPIC_EMOJI: Record<Topic, string> = {
  love: "💚", improve: "🛠️", better_elsewhere: "🔍", bug: "🐞", idea: "💡", language: "🌐", other: "✉️",
};
/** A face for each rating; the empty card shows the lighthouse's own star. */
const FACE = ["🌟", "😞", "😕", "🙂", "😊", "🤩"];

function Star({ on, hover, size }: { on: boolean; hover: boolean; size: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden
      className={`transition-transform duration-200 ${on ? "drop-shadow-[0_2px_6px_rgba(240,165,0,0.45)]" : ""} ${hover ? "scale-110" : ""}`}>
      <path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.4l-5.8 3.1 1.1-6.5L2.6 9.4l6.5-.9z"
        fill={on ? "url(#fb-gold)" : "none"} stroke={on ? "#F0A500" : "#ABB2C9"} strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  );
}

export function FeedbackCard({ from = "settings", intent, compact = false }: {
  from?: "settings" | "ai";
  /** "praise" starts at 5 stars with "I love it"; "improve" starts with "Something to improve". */
  intent?: "praise" | "improve";
  compact?: boolean;
}) {
  const { t, tl, lang, ts } = useI18n();
  const [stars, setStars] = useState(intent === "praise" ? 5 : 0);
  const [hover, setHover] = useState(0);
  const [topics, setTopics] = useState<Topic[]>(intent === "praise" ? ["love"] : intent === "improve" ? ["improve"] : []);
  const [message, setMessage] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [pop, setPop] = useState(0);
  const [allowShow, setAllowShow] = useState(false);     // only with a clear "yes" (never ticked for them)
  const summary = useRatingSummary();

  const levels = tl("feedback.levels");
  const shown = hover || stars;
  const high = stars >= 4;

  function pick(n: number) {
    setStars(n);
    setPop((p) => p + 1);
    // a sensible first topic, which they can change
    if (topics.length === 0) setTopics([n >= 4 ? "love" : "improve"]);
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
  const starSize = compact ? 34 : 44;

  if (state === "done") {
    return (
      <div id="feedback" className={`overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 text-center text-cream-50 shadow-warm ${pad}`}>
        <div className="pop-in text-5xl" aria-hidden>{high ? "🎉" : "🙏"}</div>
        <p className="mt-3 font-heading text-xl font-bold">{t("feedback.thanksTitle")}</p>
        <p className="mx-auto mt-1.5 max-w-sm font-body text-sm leading-relaxed text-brand-100">
          {high ? t("feedback.thanksHigh") : t("feedback.thanksLow")}
        </p>
        {high && (
          <button type="button" onClick={share}
            className="btn-press mt-4 inline-flex items-center gap-2 rounded-2xl bg-beam-400 px-5 py-3 font-body text-sm font-bold text-ink-900 shadow-warm hover:bg-beam-300">
            <span aria-hidden>📲</span>{t("feedback.share")}
          </button>
        )}
      </div>
    );
  }

  return (
    <div id="feedback" className="overflow-hidden rounded-3xl bg-cream-50 shadow-warm">
      <svg width="0" height="0" className="absolute" aria-hidden>
        <defs>
          <linearGradient id="fb-gold" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FDE68A" /><stop offset="1" stopColor="#F0A500" />
          </linearGradient>
        </defs>
      </svg>

      {/* header: the face changes with the stars */}
      <div className={`relative bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 text-cream-50 ${pad}`}>
        <div className="flex items-center gap-3">
          <span key={`f${shown}-${pop}`} className="pop-in flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white/15 text-3xl" aria-hidden>
            {FACE[shown]}
          </span>
          <div className="min-w-0">
            <h2 className="font-heading text-lg font-bold leading-tight">{t("feedback.title")}</h2>
            <p className="mt-0.5 font-body text-xs leading-relaxed text-brand-100">{t("feedback.subtitle")}</p>
            {summary && summary.count >= MIN_TO_SHOW && (
              <p className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-0.5 font-body text-xs font-bold text-beam-200">
                {t("feedback.socialProof", { avg: summary.average.toFixed(1), n: summary.count })}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className={pad}>
        {/* stars */}
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-1.5" role="radiogroup" aria-label={t("feedback.title")} onMouseLeave={() => setHover(0)}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" role="radio" aria-checked={stars === n} aria-label={`${n} / 5 · ${levels[n - 1] ?? ""}`}
                onClick={() => pick(n)} onMouseEnter={() => setHover(n)}
                className="btn-press rounded-full p-0.5 focus:outline-none focus-visible:ring-4 focus-visible:ring-beam-200">
                <span key={stars >= n ? `on${pop}` : "off"} className={stars >= n ? "pop-in inline-block" : "inline-block"}>
                  <Star on={shown >= n} hover={hover === n} size={starSize} />
                </span>
              </button>
            ))}
          </div>
          <p className={`mt-2 h-5 font-heading text-sm font-bold ${shown >= 4 ? "text-beam-600" : shown ? "text-ink-800" : "text-dustyblue-500"}`}>
            {shown ? levels[shown - 1] : t("feedback.pickStars")}
          </p>
        </div>

        {stars > 0 && (
          <div className="mt-4 space-y-4 animate-fade-up">
            {/* what it's about */}
            <div>
              <p className="mb-2 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600">{t("feedback.topicsTitle")}</p>
              <div className="flex flex-wrap gap-2">
                {TOPICS.map((x) => {
                  const on = topics.includes(x);
                  return (
                    <button key={x} type="button" aria-pressed={on} onClick={() => toggle(x)}
                      className={`btn-press rounded-full border-2 px-3 py-1.5 font-body text-sm font-semibold transition-colors
                        ${on ? "border-brand-500 bg-brand-100 text-brand-800" : "border-cream-200 bg-cream-50 text-ink-700 hover:border-brand-300"}`}>
                      <span aria-hidden className="mr-1">{TOPIC_EMOJI[x]}</span>{t(`feedback.topics.${x}`)}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* the message */}
            <label className="block">
              <span className="mb-1.5 flex items-center gap-2 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600">
                ✍️ <span className="rounded-full bg-cream-200 px-2 py-0.5 normal-case tracking-normal">{t("feedback.optional")}</span>
              </span>
              <textarea value={message} onChange={(e) => setMessage(e.target.value.slice(0, 1500))} rows={compact ? 3 : 4}
                placeholder={high ? t("feedback.placeholderHigh") : t("feedback.placeholderLow")}
                className="w-full rounded-2xl border-2 border-cream-200 bg-cream-50 p-3 font-body text-sm text-ink-900 placeholder:text-dustyblue-400 focus:border-brand-400 focus:outline-none" />
            </label>

            {message.trim().length > 0 && (
              <label className="flex cursor-pointer items-start gap-3 rounded-2xl bg-brand-100/60 p-3">
                <input type="checkbox" checked={allowShow} onChange={(e) => setAllowShow(e.target.checked)}
                  className="mt-0.5 h-5 w-5 shrink-0 accent-brand-600" />
                <span className="font-body text-sm">
                  <span className="block font-semibold text-ink-900">{t("feedback.shareLabel")}</span>
                  <span className="block text-xs text-dustyblue-600">{t("feedback.shareHint")}</span>
                </span>
              </label>
            )}

            {error && <p className="font-body text-sm font-semibold text-rust-600">{ts(error)}</p>}

            <button type="button" onClick={send} disabled={state === "sending"}
              className="btn-press flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-beam-400 to-beam-500 px-5 py-3.5 font-body text-base font-bold text-ink-900 shadow-warm hover:from-beam-300 hover:to-beam-400 disabled:opacity-60">
              {state === "sending" ? t("feedback.sending") : <><span aria-hidden>⭐</span>{t("feedback.send")}</>}
            </button>
            <p className="text-center font-body text-xs text-dustyblue-500">🔒 {t("feedback.privacy")}</p>
          </div>
        )}
      </div>
    </div>
  );
}
