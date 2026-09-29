import { useEffect, useRef, useState, type ReactNode } from "react";
import { useI18n } from "@/i18n";
import { verdictTone, verdictLabelKey, type Tone } from "@/verdict";
import { IconArrowRight, IconChat, IconCheck, IconWarning, IconClose, IconSearch, IconInfo, IconShield } from "@/icons";
import { Section } from "@/components/Section";
import type { Check, ScorePart, Verdict } from "@/types";
import { openHelper } from "@/chat";

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
function useCountUp(target: number, ms = 1000) {
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

const TONE_ICON: Record<Tone, ReactNode> = {
  safe: <IconCheck className="h-8 w-8" strokeWidth={2.6} />,
  caution: <IconWarning className="h-8 w-8" strokeWidth={2.4} />,
  danger: <IconClose className="h-8 w-8" strokeWidth={2.6} />,
};
const TONE_BAR: Record<Tone, string> = { safe: "bg-sage-500", caution: "bg-terracotta-400", danger: "bg-rust-500" };
const TONE_CARD: Record<Tone, string> = {
  safe: "border-sage-300 bg-gradient-to-b from-sage-100/80 to-cream-50",
  caution: "border-terracotta-300 bg-gradient-to-b from-terracotta-300/25 to-cream-50",
  danger: "border-rust-400/60 bg-gradient-to-b from-rust-400/15 to-cream-50",
};

/** The simple score line: number, level and a bar. */
function ScoreLine({ score, tone }: { score: number; tone: Tone }) {
  const { t } = useI18n();
  const shown = useCountUp(score);
  const level = score >= 50 ? t("report.riskHigh") : score >= 25 ? t("report.riskMedium") : t("report.riskLow");
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-body text-sm font-semibold text-ink-700">{t("report.bill.total")}</span>
        <span className="font-heading text-lg font-bold text-ink-900">
          {shown}<span className="text-sm font-semibold text-dustyblue-500">/100</span>
          <span className={`ml-2 font-body text-xs font-bold uppercase tracking-wide ${TONE_STYLE[tone].text}`}>{level}</span>
        </span>
      </div>
      <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-cream-200">
        <div className={`h-full rounded-full ${TONE_BAR[tone]} grow-x`} style={{ width: `${Math.max(3, shown)}%` }} />
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: Check["status"] }) {
  const cls = { pass: "bg-sage-500", warn: "bg-terracotta-400", fail: "bg-rust-500", info: "bg-dustyblue-400", skip: "bg-cream-300" }[status];
  const mark = status === "pass" ? "✓" : status === "fail" ? "✕" : status === "warn" ? "!" : "i";
  return <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full font-body text-[11px] font-black text-cream-50 ${cls}`}>{mark}</span>;
}

/** What we checked, problems first. Checks that couldn't run are left out. */
export function CheckList({ checks }: { checks: Check[] }) {
  const text = useCheckText();
  const rank = { fail: 0, warn: 1, pass: 2, info: 3, skip: 4 } as const;
  const visible = checks.filter((c) => c.status !== "skip").sort((a, b) => rank[a.status] - rank[b.status]);
  if (!visible.length) return null;
  return (
    <ul className="space-y-2">
      {visible.map((c, i) => (
        <li key={`${c.id}-${i}`} className="row-in flex items-start gap-2.5" style={{ animationDelay: `${i * 40}ms` }}>
          <StatusDot status={c.status} />
          <span className={`min-w-0 flex-1 break-words font-body text-sm leading-snug sm:text-[15px] ${c.status === "fail" ? "font-semibold text-ink-900" : "text-ink-800"}`}>
            {text(c)}
          </span>
        </li>
      ))}
    </ul>
  );
}

/** "Why this score": each reason with its points; they add up to the score. */
function ScoreReasons({ parts, total }: { parts: ScorePart[]; total: number }) {
  const { t, ts } = useI18n();
  const rows = parts.filter((p) => p.points !== 0);
  const sum = rows.reduce((a, p) => a + p.points, 0);
  if (sum !== total) rows.push({ label: "__adjust__", points: total - sum });
  if (!rows.length) return <p className="font-body text-sm text-ink-700">{t("report.bill.none")}</p>;
  return (
    <ul className="divide-y divide-cream-200">
      {rows.map((p, i) => (
        <li key={i} className="flex items-start justify-between gap-3 py-2">
          <span className="min-w-0 font-body text-sm leading-snug text-ink-800">{p.label === "__adjust__" ? t("report.bill.adjust") : ts(p.label)}</span>
          <span className={`shrink-0 rounded-md px-2 py-0.5 font-body text-xs font-bold ${p.points > 0 ? "bg-rust-400/15 text-rust-600" : "bg-sage-100 text-sage-700"}`}>
            {p.points > 0 ? `+${p.points}` : `−${Math.abs(p.points)}`}
          </span>
        </li>
      ))}
      <li className="flex items-center justify-between gap-3 pt-2.5">
        <span className="font-body text-sm font-bold text-ink-900">{t("report.bill.total")}</span>
        <span className="font-heading text-base font-bold text-ink-900">{total}/100</span>
      </li>
    </ul>
  );
}

/** What to do now: clear numbered steps people can tick. */
function Tips({ tool, tone }: { tool: ReportTool; tone: Tone }) {
  const { t, tl } = useI18n();
  const tips = tl(`report.tips.${tool}.${tone}`);
  const [done, setDone] = useState<boolean[]>([]);
  if (!tips.length) return null;
  const style = TONE_STYLE[tone];
  return (
    <div className={`rounded-2xl p-4 sm:p-5 ${style.soft}`}>
      <h3 className={`font-heading text-base font-bold sm:text-lg ${style.text}`}>{t("report.todo")}</h3>
      <ol className="mt-2.5 space-y-1.5">
        {tips.map((tip, i) => (
          <li key={i}>
            <button
              type="button"
              onClick={() => setDone((d) => { const c = [...d]; c[i] = !c[i]; return c; })}
              className="flex w-full items-start gap-3 rounded-lg p-1 text-left"
            >
              <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-heading text-xs font-bold ${done[i] ? "bg-sage-500 text-cream-50" : `bg-cream-50 ${style.text}`}`}>
                {done[i] ? "✓" : i + 1}
              </span>
              <span className={`pt-0.5 font-body text-sm sm:text-[15px] ${done[i] ? "text-dustyblue-500 line-through" : "text-ink-800"}`}>{tip}</span>
            </button>
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
  /** the score breakdown from the server */
  parts?: ScorePart[];
  onNavigate?: (path: string) => void;
  /** Extra sections (details) shown after the main ones */
  children?: ReactNode;
}

/** The result for any tool: a clear summary, what to do, then the details in tidy sections. */
export function ResultReport({ tool, verdict, riskScore, subject, checks, findings, parts, onNavigate, children }: ResultReportProps) {
  const { t, ts } = useI18n();
  const tone = verdictTone(verdict);
  const style = TONE_STYLE[tone];
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);
  const visible = (checks ?? []).filter((c) => c.status !== "skip");
  const count = (s: Check["status"]) => visible.filter((c) => c.status === s).length;
  const problems = count("fail");
  const watch = count("warn");
  const partLabels = new Set((parts ?? []).map((p) => p.label));
  const notes = (findings ?? []).filter((f) => !partLabels.has(f));

  return (
    <div ref={top} className="mt-6 scroll-mt-20 space-y-3">
      {/* 1. The answer */}
      <div className={`rounded-3xl border-2 p-5 shadow-warm animate-fade-up sm:p-6 ${TONE_CARD[tone]}`}>
        <div className="flex items-start gap-4">
          <span className={`pop-in flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl text-cream-50 shadow-warm-sm ${TONE_BAR[tone]}`}>
            {TONE_ICON[tone]}
          </span>
          <div className="min-w-0 flex-1">
            <h2 className={`font-heading text-xl font-bold leading-tight sm:text-2xl ${style.text}`}>{t(verdictLabelKey(verdict))}</h2>
            <p className="mt-1.5 font-body text-[15px] leading-snug text-ink-800">{t(`report.meaning.${tool}.${tone}`)}</p>
          </div>
        </div>
        {subject && <p className="mt-3 truncate rounded-lg bg-cream-50/80 px-3 py-1.5 font-mono text-xs text-ink-700">{subject}</p>}
        <div className="mt-4"><ScoreLine score={riskScore} tone={tone} /></div>
        {visible.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {problems > 0 && <span className="rounded-full bg-rust-400/15 px-2.5 py-1 font-body text-xs font-bold text-rust-600">{t("report.chipFail", { n: problems })}</span>}
            {watch > 0 && <span className="rounded-full bg-terracotta-300/30 px-2.5 py-1 font-body text-xs font-bold text-terracotta-700">{t("report.chipWarn", { n: watch })}</span>}
            <span className="rounded-full bg-sage-100 px-2.5 py-1 font-body text-xs font-bold text-sage-700">{t("report.chipOk", { n: count("pass") })}</span>
          </div>
        )}
      </div>

      {/* 2. What to do */}
      <Tips tool={tool} tone={tone} />

      {/* 3. Why, and what was checked */}
      <Section icon={<IconSearch className="h-5 w-5" />} title={t("report.bill.title")}
        summary={riskScore > 0 ? `${riskScore}/100` : t("report.groups.pass")} tone={tone === "safe" ? "good" : tone === "caution" ? "warn" : "bad"} defaultOpen={riskScore > 0}>
        <ScoreReasons parts={parts ?? []} total={riskScore} />
      </Section>

      {visible.length > 0 && (
        <Section icon={<IconShield className="h-5 w-5" />} title={t("report.checked")}
          summary={t("report.checkedCount", { n: visible.length })} tone="info" defaultOpen>
          <CheckList checks={visible} />
        </Section>
      )}

      {notes.length > 0 && (
        <Section icon={<IconInfo className="h-5 w-5" />} title={t("report.alsoKnow")} summary={String(notes.length)}>
          <ul className="space-y-2">
            {notes.map((n, i) => (
              <li key={i} className="flex items-start gap-2.5 font-body text-sm text-ink-800">
                <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-dustyblue-400" />
                <span className="min-w-0 break-words">{ts(n)}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* 4. Tool-specific details */}
      {children}

      {tone !== "safe" && (
        <div className="grid gap-3 pt-1 sm:grid-cols-2">
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
            onClick={() => openHelper("person")}
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
