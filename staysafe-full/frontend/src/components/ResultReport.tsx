import { useEffect, useRef, useState, type ReactNode } from "react";
import { useI18n } from "@/i18n";
import { verdictTone, verdictLabelKey, type Tone } from "@/verdict";
import { IconArrowRight, IconChat } from "@/icons";
import type { Check, Verdict } from "@/types";
import { useChat } from "@/chat";

export type ReportTool = "link" | "message" | "qr" | "file" | "password" | "network" | "email";

const TONE_STYLE: Record<Tone, { hero: string; ring: string; text: string; soft: string; chip: string }> = {
  safe: {
    hero: "from-sage-400 to-sage-600",
    ring: "#647A4F",
    text: "text-sage-700",
    soft: "bg-sage-100",
    chip: "bg-sage-100 text-sage-700",
  },
  caution: {
    hero: "from-terracotta-400 to-terracotta-600",
    ring: "#C57A5E",
    text: "text-terracotta-700",
    soft: "bg-terracotta-300/25",
    chip: "bg-terracotta-300/30 text-terracotta-700",
  },
  danger: {
    hero: "from-rust-400 to-rust-600",
    ring: "#A84A3A",
    text: "text-rust-600",
    soft: "bg-rust-400/15",
    chip: "bg-rust-400/15 text-rust-600",
  },
};

/** "3 years", "5 months", "12 days" in the website language. */
export function useFormatAge() {
  const { t } = useI18n();
  return (days: number | null | undefined): string => {
    if (days === null || days === undefined) return "";
    if (days >= 365) {
      const n = Math.floor(days / 365);
      return n === 1 ? t("report.age.year1") : t("report.age.years", { n });
    }
    if (days >= 60) return t("report.age.months", { n: Math.floor(days / 30) });
    if (days >= 30) return t("report.age.month1");
    return days === 1 ? t("report.age.day1") : t("report.age.days", { n: days });
  };
}

/** Turns a check from the server into a sentence in the website language. */
export function useCheckText() {
  const { t, ts } = useI18n();
  const formatAge = useFormatAge();
  const exists = (key: string) => t(key) !== key;
  return (c: Check): string => {
    const base = `checks.${c.id}`;
    const hasValue = c.value !== null && c.value !== undefined && c.value !== "";
    let value: string | number = hasValue ? (c.value as string | number) : "";
    if (typeof value === "string" && (c.id === "file_type" || c.id === "google")) value = ts(value);
    if (typeof value === "number" && (c.id === "pw_leaks" || c.id === "virustotal" || c.id === "file_vt")) {
      value = value.toLocaleString("en-IN");
    }
    if (c.id === "page" && c.status === "fail" && c.value === "apk") return t(`${base}.failApk`);
    if (c.id === "page" && c.status === "fail" && c.value === "program") return t(`${base}.failProgram`);
    const vars = { value, age: c.id === "age" && typeof c.value === "number" ? formatAge(c.value) : "" };
    if (hasValue && exists(`${base}.${c.status}V`)) return t(`${base}.${c.status}V`, vars);
    if (exists(`${base}.${c.status}`)) return t(`${base}.${c.status}`, vars);
    return t(`${base}.pass`, vars);
  };
}

/** Counts up from 0 so the number feels alive. */
function useCountUp(target: number, ms = 900) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / ms);
      setValue(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, ms]);
  return value;
}

/** Shield badge: tick (safe), exclamation (careful) or cross (risky), with a gentle animation. */
function VerdictBadge({ tone }: { tone: Tone }) {
  return (
    <div className="relative flex h-24 w-24 shrink-0 items-center justify-center sm:h-28 sm:w-28">
      <span className={`absolute inset-0 rounded-full bg-cream-50/20 ${tone === "safe" ? "badge-glow" : "badge-pulse"}`} />
      <span className="absolute inset-2 rounded-full bg-cream-50/15" />
      <svg viewBox="0 0 64 64" className="stamp relative h-16 w-16 sm:h-20 sm:w-20" style={{ animationDelay: "150ms" }}>
        <path d="M32 5 10 13v17c0 14 9.5 24.5 22 29 12.5-4.5 22-15 22-29V13z" fill="#FBF7F0" />
        <path d="M32 5 10 13v17c0 14 9.5 24.5 22 29 12.5-4.5 22-15 22-29V13z" fill="none" stroke="#FBF7F0" strokeWidth="3" strokeLinejoin="round" />
        {tone === "safe" && <path d="m21 32 7.5 7.5L44 24" fill="none" stroke={TONE_STYLE.safe.ring} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" className="draw-path" />}
        {tone === "caution" && (<><path d="M32 19v16" stroke={TONE_STYLE.caution.ring} strokeWidth="6.5" strokeLinecap="round" /><circle cx="32" cy="44" r="3.8" fill={TONE_STYLE.caution.ring} /></>)}
        {tone === "danger" && <path d="m23 23 18 18M41 23 23 41" stroke={TONE_STYLE.danger.ring} strokeWidth="6.5" strokeLinecap="round" className="draw-path" />}
      </svg>
      {tone === "safe" && (
        <>
          <span className="sparkle absolute right-1 top-2 h-2.5 w-2.5 rounded-full bg-cream-50" />
          <span className="sparkle absolute bottom-3 left-0 h-2 w-2 rounded-full bg-cream-50" style={{ animationDelay: ".6s" }} />
          <span className="sparkle absolute left-3 top-0 h-1.5 w-1.5 rounded-full bg-cream-50" style={{ animationDelay: "1.1s" }} />
        </>
      )}
    </div>
  );
}

/** Half-circle gauge from green to red with a needle pointing at the risk score. */
function RiskGauge({ score }: { score: number }) {
  const { t } = useI18n();
  const shown = useCountUp(score);
  const angle = -90 + (Math.max(0, Math.min(100, shown)) / 100) * 180;
  const level = score >= 50 ? t("report.riskHigh") : score >= 20 ? t("report.riskMedium") : t("report.riskLow");
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 118" className="w-44 sm:w-52">
        <defs>
          <linearGradient id="gauge-grad" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#9DB585" />
            <stop offset="50%" stopColor="#E7B266" />
            <stop offset="100%" stopColor="#D0634F" />
          </linearGradient>
        </defs>
        <path d="M20 100a80 80 0 0 1 160 0" fill="none" stroke="rgba(251,247,240,.25)" strokeWidth="18" strokeLinecap="round" />
        <path d="M20 100a80 80 0 0 1 160 0" fill="none" stroke="url(#gauge-grad)" strokeWidth="14" strokeLinecap="round" />
        <g style={{ transform: `rotate(${angle}deg)`, transformOrigin: "100px 100px", transition: "transform .2s linear" }}>
          <path d="M100 100 L100 34" stroke="#FBF7F0" strokeWidth="5" strokeLinecap="round" />
        </g>
        <circle cx="100" cy="100" r="10" fill="#FBF7F0" />
      </svg>
      <p className="-mt-1 font-heading text-3xl font-bold leading-none text-cream-50">{shown}<span className="text-base font-semibold text-cream-50/75">/100</span></p>
      <p className="mt-1 rounded-full bg-cream-50/20 px-3 py-0.5 font-body text-xs font-bold uppercase tracking-wide text-cream-50">{level}</p>
    </div>
  );
}

function StatusIcon({ status }: { status: Check["status"] }) {
  const map = {
    pass: "bg-sage-500 text-cream-50",
    warn: "bg-terracotta-400 text-cream-50",
    fail: "bg-rust-500 text-cream-50",
    info: "bg-dustyblue-400 text-cream-50",
    skip: "bg-cream-300 text-ink-700",
  } as const;
  return (
    <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${map[status]}`}>
      {status === "pass" && (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} className="h-4 w-4"><path d="M5 12.5l4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
      )}
      {status === "warn" && <span className="font-heading text-sm font-bold leading-none">!</span>}
      {status === "fail" && (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} className="h-4 w-4"><path d="M7 7l10 10M17 7L7 17" strokeLinecap="round" /></svg>
      )}
      {status === "info" && <span className="font-heading text-sm font-bold leading-none">i</span>}
      {status === "skip" && <span className="h-0.5 w-3 rounded bg-ink-700/60" />}
    </span>
  );
}

const ROW_BG: Record<Check["status"], string> = {
  pass: "bg-sage-100/70",
  warn: "bg-terracotta-300/20",
  fail: "bg-rust-400/10 ring-1 ring-rust-400/40",
  info: "bg-dustyblue-100/70",
  skip: "bg-cream-100",
};

export function CheckList({ checks, title }: { checks: Check[]; title?: string }) {
  const { t } = useI18n();
  const text = useCheckText();
  if (!checks.length) return null;
  // Problems first, then things to watch, then the good news
  const rank = { fail: 0, warn: 1, pass: 2, info: 3, skip: 4 } as const;
  const sorted = [...checks].sort((a, b) => rank[a.status] - rank[b.status]);
  const count = (s: Check["status"]) => checks.filter((c) => c.status === s).length;
  const chips = [
    { n: count("pass"), key: "report.chipOk", cls: "bg-sage-200 text-sage-700" },
    { n: count("warn"), key: "report.chipWarn", cls: "bg-terracotta-300/40 text-terracotta-700" },
    { n: count("fail"), key: "report.chipFail", cls: "bg-rust-400/20 text-rust-600" },
    { n: count("skip"), key: "report.chipSkip", cls: "bg-cream-200 text-ink-700" },
  ].filter((c) => c.n > 0);

  return (
    <div className="rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-heading text-lg font-semibold text-ink-900">{title ?? t("report.checked")}</h3>
        <div className="flex flex-wrap gap-1.5">
          {chips.map((c) => (
            <span key={c.key} className={`rounded-full px-2.5 py-1 font-body text-xs font-bold ${c.cls}`}>
              {t(c.key, { n: c.n })}
            </span>
          ))}
        </div>
      </div>
      <ul className="mt-4 space-y-2">
        {sorted.map((c, i) => (
          <li key={`${c.id}-${i}`} className={`row-in flex items-center gap-3 rounded-xl px-3 py-2.5 ${ROW_BG[c.status]}`} style={{ animationDelay: `${150 + i * 70}ms` }}>
            <StatusIcon status={c.status} />
            <span className={`min-w-0 flex-1 break-words font-body text-sm sm:text-[15px] ${c.status === "fail" ? "font-semibold text-ink-900" : "text-ink-800"}`}>
              {text(c)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Findings({ items, tone }: { items: string[]; tone: Tone }) {
  const { t, ts } = useI18n();
  if (!items?.length) return null;
  const dot = tone === "safe" ? "bg-sage-400" : tone === "caution" ? "bg-terracotta-400" : "bg-rust-500";
  return (
    <div className="rounded-2xl bg-cream-100 p-5 animate-fade-up">
      <h3 className="mb-3 font-heading text-lg font-semibold text-ink-900">{t("report.noticed")}</h3>
      <ul className="space-y-2.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5 font-body text-sm text-ink-800 sm:text-[15px]">
            <span className={`mt-[7px] h-2 w-2 shrink-0 rounded-full ${dot}`} />
            <span className="min-w-0 break-words">{ts(item)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Tips({ tool, tone }: { tool: ReportTool; tone: Tone }) {
  const { t, tl } = useI18n();
  const tips = tl(`report.tips.${tool}.${tone}`);
  if (!tips.length) return null;
  const style = TONE_STYLE[tone];
  return (
    <div className={`rounded-2xl p-5 animate-fade-up ${style.soft}`}>
      <h3 className={`mb-3 font-heading text-lg font-semibold ${style.text}`}>{t("report.todo")}</h3>
      <ol className="space-y-2.5">
        {tips.map((tip, i) => (
          <li key={i} className="flex items-start gap-3 font-body text-sm text-ink-800 sm:text-[15px]">
            <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cream-50 font-heading text-xs font-bold ${style.text}`}>
              {i + 1}
            </span>
            <span className="pt-0.5">{tip}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

interface ResultReportProps {
  tool: ReportTool;
  verdict: Verdict | string;
  riskScore: number;
  /** What was checked, e.g. the link or file name */
  subject?: string;
  checks?: Check[];
  findings?: string[];
  onNavigate?: (path: string) => void;
  /** Extra cards shown between the check list and the tips */
  children?: ReactNode;
}

/** The full, colourful result for any tool. */
export function ResultReport({ tool, verdict, riskScore, subject, checks, findings, onNavigate, children }: ResultReportProps) {
  const { t } = useI18n();
  const { openChat } = useChat();
  const tone = verdictTone(verdict);
  const style = TONE_STYLE[tone];
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // bring the answer into view (on phones it would otherwise be below the form)
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  return (
    <div ref={top} className="mt-5 scroll-mt-20 space-y-4">
      <div className={`relative overflow-hidden rounded-3xl bg-gradient-to-br ${style.hero} p-5 text-cream-50 shadow-warm-lg animate-fade-up sm:p-7`}>
        {/* soft background shapes */}
        <span className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-cream-50/10" />
        <span className="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-cream-50/10" />
        <span className="pointer-events-none absolute right-24 top-10 h-3 w-3 rounded-full bg-cream-50/30" />
        <div className="relative flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:gap-6 sm:text-left">
          <VerdictBadge tone={tone} />
          <div className="w-full min-w-0 flex-1">
            <p className="font-heading text-2xl font-bold leading-tight sm:text-3xl">{t(verdictLabelKey(verdict))}</p>
            <p className="mt-2 font-body text-[15px] leading-snug text-cream-50/95 sm:text-base">{t(`report.meaning.${tool}.${tone}`)}</p>
            {subject && (
              <p className="mx-auto mt-3 block max-w-full truncate rounded-lg bg-ink-900/20 px-3 py-1.5 font-mono text-xs text-cream-50 sm:mx-0 sm:inline-block">
                {subject}
              </p>
            )}
          </div>
          <div className="shrink-0"><RiskGauge score={riskScore} /></div>
        </div>
        {checks && checks.length > 0 && (
          <div className="relative mt-5 grid grid-cols-3 gap-2">
            {([["pass", "report.statOk"], ["warn", "report.statWarn"], ["fail", "report.statFail"]] as const).map(([st, key]) => {
              const n = checks.filter((c) => c.status === st).length;
              return (
                <div key={st} className="rounded-2xl bg-cream-50/15 px-2 py-2.5 text-center backdrop-blur-sm">
                  <p className="font-heading text-2xl font-bold leading-none">{n}</p>
                  <p className="mt-1 font-body text-[11px] font-bold uppercase tracking-wide text-cream-50/85">{t(key)}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {checks && checks.length > 0 && <CheckList checks={checks} />}

      {findings && <Findings items={findings} tone={tone} />}

      {children}

      <Tips tool={tool} tone={tone} />

      {tone !== "safe" && (
        <div className="grid gap-3 sm:grid-cols-2">
          {tone === "danger" && onNavigate && (
            <button
              onClick={() => onNavigate("/incident")}
              className="btn-press flex items-center justify-between gap-3 rounded-2xl bg-rust-500 px-4 py-3.5 text-left font-body text-sm font-bold text-cream-50 shadow-warm hover:bg-rust-600"
            >
              <span>{t("report.recovery")}</span>
              <IconArrowRight className="h-5 w-5 shrink-0" />
            </button>
          )}
          <button
            onClick={openChat}
            className={`btn-press flex items-center justify-between gap-3 rounded-2xl border-2 border-sage-300 bg-cream-50 px-4 py-3.5 text-left font-body text-sm font-bold text-sage-700 hover:bg-sage-100 ${tone === "caution" ? "sm:col-span-2" : ""}`}
          >
            <span>{t("report.askUs")}</span>
            <IconChat className="h-5 w-5 shrink-0" />
          </button>
        </div>
      )}
    </div>
  );
}
