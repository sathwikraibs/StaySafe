import { useEffect, useRef, useState, type ReactNode } from "react";
import { useI18n } from "@/i18n";
import { verdictTone, verdictLabelKey, type Tone } from "@/verdict";
import { IconCheck, IconWarning, IconAlert, IconArrowRight, IconChat } from "@/icons";
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

function RiskMeter({ score, tone }: { score: number; tone: Tone }) {
  const { t } = useI18n();
  const shown = useCountUp(score);
  const pos = Math.max(2, Math.min(98, shown));
  const level = score >= 50 ? t("report.riskHigh") : score >= 20 ? t("report.riskMedium") : t("report.riskLow");
  return (
    <div className="mt-4">
      <div className="flex items-baseline justify-between gap-2 font-body text-sm text-cream-50">
        <span className="font-bold">{level}</span>
        <span className="text-cream-50/85">{t("report.riskOf", { score: shown })}</span>
      </div>
      <div className="relative mt-2 h-3 rounded-full bg-gradient-to-r from-[#9DB585] via-[#E7B266] to-[#D0634F] ring-2 ring-cream-50/40">
        <span
          className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-cream-50 shadow-warm"
          style={{ left: `${pos}%`, background: TONE_STYLE[tone].ring }}
        />
      </div>
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
  const Icon = tone === "safe" ? IconCheck : tone === "caution" ? IconWarning : IconAlert;
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // bring the answer into view (on phones it would otherwise be below the form)
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  return (
    <div ref={top} className="mt-5 scroll-mt-20 space-y-4">
      <div className={`overflow-hidden rounded-2xl bg-gradient-to-br ${style.hero} p-5 text-cream-50 shadow-warm-lg animate-fade-up sm:p-6`}>
        <div className="flex items-start gap-4">
          <div className="stamp flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20" style={{ animationDelay: "120ms" }}>
            <Icon className="h-8 w-8" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-heading text-xl font-bold sm:text-2xl">{t(verdictLabelKey(verdict))}</p>
            <p className="mt-1.5 font-body text-[15px] leading-snug text-cream-50/95">{t(`report.meaning.${tool}.${tone}`)}</p>
            {subject && (
              <p className="mt-2 inline-block max-w-full truncate rounded-lg bg-cream-50/20 px-2.5 py-1 font-mono text-xs text-cream-50">
                {subject}
              </p>
            )}
          </div>
        </div>
        <RiskMeter score={riskScore} tone={tone} />
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
