import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n";
import { themeFor, type ToolTheme } from "@/toolTheme";

export type WaitingTool =
  | "link" | "message" | "screenshot" | "qr" | "file" | "password" | "network" | "email" | "number" | "incident";

const TOOL_PATH: Record<WaitingTool, string> = {
  link: "/scan-url", message: "/scan-message", screenshot: "/scan-message", qr: "/scan-qr", file: "/scan-file",
  password: "/check-password", network: "/check-network", email: "/scan-email", number: "/check-number", incident: "",
};
const INCIDENT_THEME: ToolTheme = { soft: "#FCE5E2", ink: "#A52A21", from: "#E5675A", to: "#A52A21" };

/** A small moving picture that is different for every tool. */
function ToolAnimation({ tool, th }: { tool: WaitingTool; th: ToolTheme }) {
  const s = { stroke: th.ink, strokeWidth: 3, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const light = th.from;
  switch (tool) {
    case "link":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <path {...s} d="M40 56 56 40" />
          <path {...s} d="M44 34l4-4a12 12 0 0 1 17 17l-4 4" />
          <path {...s} d="M52 62l-4 4a12 12 0 0 1-17-17l4-4" />
          <g className="anim-sweep">
            <circle cx="30" cy="70" r="11" fill={th.soft} stroke={light} strokeWidth="3.5" />
            <path d="M38 78l8 8" stroke={light} strokeWidth="5" strokeLinecap="round" />
          </g>
        </svg>
      );
    case "message":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <path {...s} d="M18 24h60a6 6 0 0 1 6 6v30a6 6 0 0 1-6 6H40l-14 12V66h-8a6 6 0 0 1-6-6V30a6 6 0 0 1 6-6z" fill={th.soft} />
          {[34, 48, 62].map((x, i) => (
            <circle key={x} cx={x} cy="45" r="5" fill={i === 1 ? th.ink : light} className="anim-dot" style={{ animationDelay: `${i * 0.18}s` }} />
          ))}
        </svg>
      );
    case "screenshot":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <rect x="28" y="10" width="40" height="76" rx="7" {...s} fill={th.soft} />
          {[26, 36, 46, 56, 66].map((y, i) => <path key={y} d={`M36 ${y}h${i % 2 ? 18 : 24}`} stroke={light} strokeWidth="3" strokeLinecap="round" />)}
          <rect x="30" y="14" width="36" height="4" rx="2" fill={th.ink} opacity="0.85" className="anim-scan" />
        </svg>
      );
    case "qr":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          {[[18, 18], [58, 18], [18, 58]].map(([x, y]) => (
            <g key={`${x}${y}`}><rect x={x} y={y} width="20" height="20" rx="3" {...s} /><rect x={x + 6} y={y + 6} width="8" height="8" rx="1" fill={th.ink} /></g>
          ))}
          {[[60, 60], [70, 66], [62, 72], [74, 76], [48, 50], [48, 64], [66, 48]].map(([x, y]) => <rect key={`${x}-${y}`} x={x} y={y} width="6" height="6" rx="1" fill={light} />)}
          <rect x="12" y="14" width="72" height="4" rx="2" fill="#E5675A" opacity="0.85" className="anim-scan" />
        </svg>
      );
    case "file":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <path {...s} fill={th.soft} d="M26 12h30l16 16v56H26z" />
          <path {...s} d="M56 12v16h16" />
          {[40, 50, 60, 70].map((y) => <path key={y} d={`M34 ${y}h28`} stroke={light} strokeWidth="3" strokeLinecap="round" />)}
          <g className="anim-sweep-y">
            <circle cx="62" cy="58" r="10" fill={th.soft} stroke={th.ink} strokeWidth="3.5" />
            <path d="M69 65l8 8" stroke={th.ink} strokeWidth="5" strokeLinecap="round" />
          </g>
        </svg>
      );
    case "password":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <path {...s} d="M34 42V32a14 14 0 0 1 28 0v10" className="anim-shackle" />
          <rect x="24" y="42" width="48" height="36" rx="8" {...s} fill={th.soft} />
          {[36, 46, 56, 66].map((x, i) => <circle key={x} cx={x - 2} cy="60" r="4" fill={th.ink} className="anim-fill" style={{ animationDelay: `${i * 0.25}s` }} />)}
        </svg>
      );
    case "network":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <circle cx="48" cy="72" r="6" fill={th.ink} />
          {[16, 28, 40].map((r, i) => (
            <path key={r} d={`M${48 - r * 0.75} ${72 - r * 0.66}A${r} ${r} 0 0 1 ${48 + r * 0.75} ${72 - r * 0.66}`} stroke={th.ink} strokeWidth="5" fill="none" strokeLinecap="round" className="anim-wave" style={{ animationDelay: `${i * 0.25}s` }} />
          ))}
        </svg>
      );
    case "email":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <g className="anim-rise"><rect x="30" y="22" width="36" height="34" rx="3" fill="#FFFFFF" stroke={light} strokeWidth="3" /><path d="M37 32h22M37 40h16" stroke={light} strokeWidth="3" strokeLinecap="round" /></g>
          <path {...s} fill={th.soft} d="M16 40l32 22 32-22v38H16z" />
          <path {...s} d="M16 78l24-20M80 78 56 58" />
        </svg>
      );
    case "number":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <rect {...s} x="30" y="14" width="36" height="68" rx="7" fill={th.soft} />
          <path {...s} d="M42 72h12" />
          <g className="anim-wave"><path d="M70 30a12 12 0 0 1 0 18" stroke={light} strokeWidth="4" fill="none" strokeLinecap="round" /><path d="M76 24a20 20 0 0 1 0 30" stroke={light} strokeWidth="4" fill="none" strokeLinecap="round" /></g>
          <path {...s} d="M40 30h16M40 40h16M40 50h10" /><circle cx="48" cy="60" r="3" fill={th.ink} className="anim-dot" />
        </svg>
      );
    case "incident":
      return (
        <svg viewBox="0 0 96 96" className="h-full w-full">
          <g className="anim-spin-slow" style={{ transformOrigin: "48px 48px" }}>
            <circle cx="48" cy="48" r="32" fill="none" stroke={th.from} strokeWidth="14" strokeDasharray="25 25.3" />
          </g>
          <circle cx="48" cy="48" r="18" fill={th.soft} />
          <path d="M48 58s-10-6-10-13a6 6 0 0 1 10-4 6 6 0 0 1 10 4c0 7-10 13-10 13z" fill={th.ink} className="anim-dot" />
        </svg>
      );
  }
}

/** Time each step is shown. Every scan takes at least (number of steps x this). */
export const STEP_MS = 1300;

/**
 * Lets a scan take its time: the answer is shown only after every step has been worked
 * through, so people can see each check happen. Errors are shown straight away.
 */
export function usePace() {
  const { tl } = useI18n();
  return async function pace<T>(tool: WaitingTool, work: Promise<T>): Promise<T> {
    const min = tl(`waiting.${tool}`).length * STEP_MS + 400;
    const started = Date.now();
    const out = await work;
    const left = min - (Date.now() - started);
    if (left > 0) await new Promise((r) => setTimeout(r, left));
    return out;
  };
}

/**
 * Friendly progress while we check. Steps tick off one by one; the last step keeps going
 * until the answer arrives, with a changing reassuring line underneath.
 */
export function LoadingSteps({ tool }: { tool: WaitingTool }) {
  const { t, tl } = useI18n();
  const steps = tl(`waiting.${tool}`);
  const still = tl("waiting.still");
  const [elapsed, setElapsed] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  const th = tool === "incident" ? INCIDENT_THEME : themeFor(TOOL_PATH[tool]);

  useEffect(() => {
    box.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - started), 250);
    return () => clearInterval(timer);
  }, []);

  const done = Math.min(steps.length - 1, Math.floor(elapsed / STEP_MS));
  const allTicked = done >= steps.length - 1;
  const stillLine = allTicked && still.length ? still[Math.floor((elapsed - STEP_MS * (steps.length - 1)) / 3500) % still.length] : "";
  // keeps creeping forward so it never looks stuck
  const progress = Math.min(97, (done / Math.max(1, steps.length - 1)) * 78 + 19 * (1 - Math.exp(-elapsed / 20000)));

  return (
    <div ref={box} className="mt-5 overflow-hidden rounded-3xl bg-cream-50 shadow-warm-lg animate-fade-up" role="status" aria-live="polite">
      <div className="relative flex items-center gap-4 px-5 py-5" style={{ background: th.soft }}>
        <div className="h-20 w-20 shrink-0 sm:h-24 sm:w-24"><ToolAnimation tool={tool} th={th} /></div>
        <div className="min-w-0 flex-1">
          <p className="font-heading text-lg font-bold text-ink-900 sm:text-xl">{t("waiting.title")}</p>
          <p key={done + stillLine} className="mt-1 font-body text-sm font-semibold animate-fade-up" style={{ color: th.ink }}>
            {stillLine || steps[done]}
          </p>
          <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-cream-50/80">
            <div
              className="progress-shine h-full rounded-full transition-[width] duration-700 ease-out"
              style={{ width: `${progress}%`, backgroundImage: `linear-gradient(90deg, ${th.from}, ${th.to})` }}
            />
          </div>
        </div>
      </div>

      <ul className="space-y-2.5 px-5 py-4">
        {steps.map((step, i) => {
          const state = i < done ? "done" : i === done ? "now" : "later";
          return (
            <li key={i} className={`flex items-center gap-3 font-body text-sm transition-all duration-500 sm:text-[15px] ${state === "later" ? "opacity-35" : "opacity-100"}`}>
              {state === "done" ? (
                <span className="pop-in flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-cream-50" style={{ background: th.to }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} className="h-3.5 w-3.5"><path d="M5 12.5l4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </span>
              ) : state === "now" ? (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                  <span className="h-5 w-5 animate-spin rounded-full border-[3px] border-cream-200" style={{ borderTopColor: th.to }} />
                </span>
              ) : (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center"><span className="h-2.5 w-2.5 rounded-full bg-cream-300" /></span>
              )}
              <span className={state === "now" ? "font-semibold text-ink-900" : "text-ink-700"}>{step}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
