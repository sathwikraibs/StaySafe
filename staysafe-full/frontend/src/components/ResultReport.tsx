import { useEffect, useRef, useState, type ReactNode } from "react";
import { useI18n } from "@/i18n";
import { verdictTone, verdictLabelKey, type Tone } from "@/verdict";
import { IconArrowRight, IconChat } from "@/icons";
import type { Check, ScorePart, Verdict } from "@/types";
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
function useCountUp(target: number, ms = 1100) {
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

/** A short, stable report number from what was checked, like a slip from a counter. */
function reportNumber(seed: string): string {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  const hex = (h >>> 0).toString(16).toUpperCase().padStart(8, "0");
  return `${hex.slice(0, 4)}-${hex.slice(4, 6)}`;
}

/** Rubber stamp pressed onto the slip. */
function Stamp({ tone, label }: { tone: Tone; label: string }) {
  const color = TONE_STYLE[tone].ring;
  return (
    <div className="stamp-press pointer-events-none select-none" style={{ color }}>
      <div className="stamp-ink rounded-[10px] border-[3px] border-current px-1 py-1" style={{ transform: "rotate(-7deg)" }}>
        <div className="rounded-md border border-current px-3 py-1.5 text-center sm:px-4">
          <p className="font-report text-[26px] font-extrabold uppercase leading-none tracking-[0.08em] sm:text-3xl">{label}</p>
        </div>
      </div>
    </div>
  );
}

/** A ruler from 0 to 100 with the three zones and a marker that slides to the score. */
function RiskScale({ score }: { score: number }) {
  const { t } = useI18n();
  const shown = useCountUp(score);
  const level = score >= 50 ? t("report.riskHigh") : score >= 25 ? t("report.riskMedium") : t("report.riskLow");
  const levelColor = score >= 50 ? "text-rust-600" : score >= 25 ? "text-terracotta-700" : "text-sage-700";
  return (
    <div>
      <div className="flex items-end justify-between gap-3">
        <p className="font-report leading-none text-ink-900">
          <span className="text-[56px] font-bold tabular-nums tracking-tight sm:text-[64px]">{shown}</span>
          <span className="ml-1 font-mono text-sm text-dustyblue-500">/100</span>
        </p>
        <p className={`pb-2 font-mono text-[11px] font-semibold uppercase tracking-[0.18em] ${levelColor}`}>{level}</p>
      </div>
      <div className="relative mt-3 pb-5">
        <div className="flex h-3 overflow-hidden rounded-[3px] border border-ink-900/15">
          <span className="h-full bg-sage-300" style={{ width: "25%" }} />
          <span className="h-full bg-[#E9C27A]" style={{ width: "25%" }} />
          <span className="h-full bg-[#D98870]" style={{ width: "50%" }} />
        </div>
        {/* ticks every 10 */}
        <div className="absolute inset-x-0 top-3 flex justify-between px-px">
          {Array.from({ length: 11 }, (_, i) => (
            <span key={i} className={`w-px bg-ink-900/35 ${i % 5 === 0 ? "h-2.5" : "h-1.5"}`} />
          ))}
        </div>
        <div className="absolute inset-x-0 top-[26px] flex justify-between font-mono text-[10px] text-dustyblue-500">
          <span>0</span><span>50</span><span>100</span>
        </div>
        <span
          className="scale-marker absolute -top-2.5 h-0 w-0 border-x-[7px] border-t-[9px] border-x-transparent border-t-ink-900"
          style={{ left: `calc(${Math.max(0, Math.min(100, shown))}% - 7px)` }}
        />
      </div>
    </div>
  );
}

/** "How we got this score": each reason and its points, like an itemised bill. */
function ScoreBill({ parts, total }: { parts: ScorePart[]; total: number }) {
  const { t, ts } = useI18n();
  const [all, setAll] = useState(false);
  const rows = parts.filter((p) => p.points !== 0);
  const sum = rows.reduce((a, p) => a + p.points, 0);
  if (sum !== total) rows.push({ label: "__adjust__", points: total - sum });
  const shown = all ? rows : rows.slice(0, 6);
  const labelOf = (l: string) => (l === "__adjust__" ? t("report.bill.adjust") : ts(l));
  return (
    <section className="slip-section">
      <h3 className="slip-heading">{t("report.bill.title")}</h3>
      {rows.length === 0 ? (
        <p className="mt-2 font-body text-sm text-dustyblue-600">{t("report.bill.none")}</p>
      ) : (
        <ol className="mt-3 space-y-2">
          {shown.map((p, i) => (
            <li key={i} className="ledger-row flex items-baseline gap-2" style={{ animationDelay: `${250 + i * 90}ms` }}>
              <span className="min-w-0 flex-1 font-body text-[13.5px] leading-snug text-ink-800 sm:text-sm">{labelOf(p.label)}</span>
              <span className="mb-1 hidden h-px min-w-[24px] flex-1 border-b border-dotted border-ink-900/30 sm:block" />
              <span className={`shrink-0 font-mono text-sm font-semibold tabular-nums ${p.points > 0 ? "text-rust-600" : "text-sage-700"}`}>
                {p.points > 0 ? `+${p.points}` : `−${Math.abs(p.points)}`}
              </span>
            </li>
          ))}
        </ol>
      )}
      {rows.length > 6 && (
        <button onClick={() => setAll(!all)} className="mt-2 font-mono text-xs font-semibold uppercase tracking-wider text-dustyblue-600 underline underline-offset-4">
          {all ? t("report.bill.less") : t("report.bill.more", { n: rows.length - 6 })}
        </button>
      )}
      <div className="mt-3 flex items-baseline justify-between border-t-[3px] border-double border-ink-900/40 pt-2">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-ink-800">{t("report.bill.total")}</span>
        <span className="font-report text-2xl font-bold tabular-nums text-ink-900">{total}</span>
      </div>
    </section>
  );
}

function Mark({ status }: { status: Check["status"] }) {
  const color = status === "pass" ? "#647A4F" : status === "warn" ? "#C57A5E" : status === "fail" ? "#A84A3A" : "#6F8794";
  return (
    <svg viewBox="0 0 24 24" className="mt-0.5 h-5 w-5 shrink-0" aria-hidden>
      <rect x="2.5" y="2.5" width="19" height="19" rx="3" fill="none" stroke={color} strokeWidth="1.6" />
      {status === "pass" && <path d="M6.5 12.5l3.5 3.5 7.5-8" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" className="draw-path" />}
      {status === "fail" && <path d="M7.5 7.5l9 9M16.5 7.5l-9 9" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" className="draw-path" />}
      {status === "warn" && <path d="M12 6.5v7M12 17.2v.3" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" />}
      {status === "info" && <path d="M8 12h8" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" />}
    </svg>
  );
}

/** What we checked, grouped: problems first, then things to watch, then what was fine. */
export function CheckList({ checks, title }: { checks: Check[]; title?: string }) {
  const { t } = useI18n();
  const text = useCheckText();
  // Checks that couldn't run are simply left out: the other sources already covered them.
  const visible = checks.filter((c) => c.status !== "skip");
  if (!visible.length) return null;
  const groups = (["fail", "warn", "pass", "info"] as const)
    .map((st) => ({ st, items: visible.filter((c) => c.status === st) }))
    .filter((g) => g.items.length);
  const groupTitle = { fail: "report.groups.fail", warn: "report.groups.warn", pass: "report.groups.pass", info: "report.groups.info" } as const;
  const groupColor = { fail: "text-rust-600", warn: "text-terracotta-700", pass: "text-sage-700", info: "text-dustyblue-600" } as const;
  let n = 0;
  return (
    <section className="slip-section">
      <h3 className="slip-heading">{title ?? t("report.checked")}</h3>
      <div className="mt-3 space-y-4">
        {groups.map((g) => (
          <div key={g.st}>
            <p className={`mb-1.5 font-mono text-[11px] font-semibold uppercase tracking-[0.16em] ${groupColor[g.st]}`}>
              {t(groupTitle[g.st])} · {g.items.length}
            </p>
            <ul className="space-y-1.5">
              {g.items.map((c, i) => (
                <li key={`${c.id}-${i}`} className="row-in flex items-start gap-2.5" style={{ animationDelay: `${200 + (n++) * 60}ms` }}>
                  <Mark status={c.status} />
                  <span className={`min-w-0 flex-1 break-words font-body text-[14px] leading-snug sm:text-[15px] ${c.status === "fail" ? "font-semibold text-ink-900" : "text-ink-800"}`}>
                    {text(c)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

/** Notes that aren't already in the score breakdown (context, reminders, where things are). */
export function Findings({ items }: { items: string[] }) {
  const { t, ts } = useI18n();
  if (!items?.length) return null;
  return (
    <section className="slip-section">
      <h3 className="slip-heading">{t("report.alsoKnow")}</h3>
      <ul className="mt-3 space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5 font-body text-[14px] leading-snug text-ink-800 sm:text-[15px]">
            <span className="mt-[3px] font-mono text-[11px] font-semibold text-dustyblue-500">{String(i + 1).padStart(2, "0")}</span>
            <span className="min-w-0 break-words">{ts(item)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** What to do now, as a list people can tick off. */
function Tips({ tool, tone }: { tool: ReportTool; tone: Tone }) {
  const { t, tl } = useI18n();
  const tips = tl(`report.tips.${tool}.${tone}`);
  const [done, setDone] = useState<boolean[]>([]);
  if (!tips.length) return null;
  const style = TONE_STYLE[tone];
  return (
    <div className="rounded-2xl border-2 border-dashed border-ink-900/15 bg-[#FFFDF8] p-5 animate-fade-up">
      <h3 className={`font-report text-xl font-bold ${style.text}`}>{t("report.todo")}</h3>
      <p className="mt-0.5 font-mono text-[11px] uppercase tracking-[0.14em] text-dustyblue-500">{t("report.todoHint")}</p>
      <ol className="mt-3 space-y-2">
        {tips.map((tip, i) => (
          <li key={i}>
            <button
              onClick={() => setDone((d) => { const c = [...d]; c[i] = !c[i]; return c; })}
              className="flex w-full items-start gap-3 rounded-lg px-1 py-1 text-left hover:bg-cream-100"
            >
              <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-[4px] border-2 ${done[i] ? "border-sage-500 bg-sage-500" : "border-ink-900/35"}`}>
                {done[i] && <svg viewBox="0 0 24 24" className="h-3.5 w-3.5"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#FBF7F0" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
              </span>
              <span className={`font-body text-[14px] leading-snug sm:text-[15px] ${done[i] ? "text-dustyblue-500 line-through" : "text-ink-800"}`}>{tip}</span>
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
  /** Extra cards shown between the check list and the tips */
  children?: ReactNode;
}

/** The result for any tool, printed as a report slip. */
export function ResultReport({ tool, verdict, riskScore, subject, checks, findings, parts, onNavigate, children }: ResultReportProps) {
  const { t, lang } = useI18n();
  const { openChat } = useChat();
  const tone = verdictTone(verdict);
  const style = TONE_STYLE[tone];
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // bring the answer into view (on phones it would otherwise be below the form)
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);
  const [when] = useState(() => new Date());
  const dateText = (() => {
    try {
      return when.toLocaleDateString(lang === "tcy" ? "kn-IN" : `${lang}-IN`, { day: "numeric", month: "short", year: "numeric" });
    } catch {
      return when.toDateString();
    }
  })();
  const partLabels = new Set((parts ?? []).map((p) => p.label));
  const notes = (findings ?? []).filter((f) => !partLabels.has(f));

  return (
    <div ref={top} className="mt-6 scroll-mt-20 space-y-4">
      <article className={`report-slip slip-${tone} relative overflow-hidden rounded-[18px] bg-[#FFFDF8] shadow-warm-lg animate-fade-up`}>
        {/* coloured edge like the stub of a printed slip */}
        <span className="absolute inset-y-0 left-0 w-2" style={{ background: style.ring }} />
        <div className="relative pl-6 pr-5 pt-5 sm:pl-8 sm:pr-7 sm:pt-6">
          <div className="flex items-center justify-between gap-3 font-mono text-[10.5px] uppercase tracking-[0.18em] text-dustyblue-500">
            <span>{t("report.slip")} · {t(`report.toolName.${tool}`)}</span>
            <span>№ {reportNumber(`${tool}|${subject ?? ""}|${riskScore}`)}</span>
          </div>
          <div className="mt-1 font-mono text-[10.5px] uppercase tracking-[0.18em] text-dustyblue-400">{dateText}</div>

          <div className="mt-4 flex flex-col-reverse gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <h2 className={`font-report text-[28px] font-bold leading-[1.1] sm:text-[34px] ${style.text}`}>{t(verdictLabelKey(verdict))}</h2>
              <p className="mt-2 max-w-prose font-body text-[15px] leading-relaxed text-ink-800">{t(`report.meaning.${tool}.${tone}`)}</p>
            </div>
            <div className="self-end sm:self-start sm:pt-1"><Stamp tone={tone} label={t(`report.stamp.${tone}`)} /></div>
          </div>

          {subject && (
            <p className="mt-4 truncate border-l-2 border-ink-900/20 pl-3 font-mono text-xs text-ink-700">{subject}</p>
          )}
        </div>

        {/* perforation */}
        <div className="perforation mx-5 mt-5 sm:mx-7" />

        <div className="px-5 pb-6 pt-5 sm:px-7">
          <RiskScale score={riskScore} />
          <div className="mt-2">
            <ScoreBill parts={parts ?? []} total={riskScore} />
          </div>
          {checks && checks.length > 0 && <CheckList checks={checks} />}
          {notes.length > 0 && <Findings items={notes} />}
        </div>
      </article>

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
