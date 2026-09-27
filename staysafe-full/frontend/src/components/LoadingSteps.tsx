import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n";

export type WaitingTool =
  | "link" | "message" | "screenshot" | "qr" | "file" | "password" | "network" | "email" | "incident";

/**
 * Friendly progress while the server works. Steps tick off one by one; the last step
 * ("putting your report together") keeps spinning until the answer arrives. If the free
 * server is waking up, we say so kindly and keep showing that we're still there.
 */
export function LoadingSteps({ tool }: { tool: WaitingTool }) {
  const { t, tl } = useI18n();
  const steps = tl(`waiting.${tool}`);
  const still = tl("waiting.still");
  const [elapsed, setElapsed] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    box.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  useEffect(() => {
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - started), 250);
    return () => clearInterval(timer);
  }, []);

  const STEP_MS = 1400;
  const done = Math.min(steps.length - 1, Math.floor(elapsed / STEP_MS));
  const allTicked = done >= steps.length - 1;
  const slow = elapsed > 8000;
  const stillLine = allTicked && still.length ? still[Math.floor(elapsed / 4000) % still.length] : "";
  const progress = Math.min(96, (done / Math.max(1, steps.length - 1)) * 80 + Math.min(16, elapsed / 2500));

  return (
    <div ref={box} className="mt-5 overflow-hidden rounded-2xl bg-cream-50 shadow-warm animate-fade-up" role="status" aria-live="polite">
      <div className="bg-gradient-to-r from-sage-200 via-dustyblue-100 to-sage-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 shrink-0 items-center justify-center">
            <span className="absolute h-10 w-10 rounded-full bg-sage-300/60 animate-breath" />
            <span className="absolute h-6 w-6 rounded-full bg-sage-400/70 animate-breath-delayed" />
            <span className="relative h-3 w-3 rounded-full bg-sage-600" />
          </div>
          <p className="font-heading text-base font-semibold text-ink-900 sm:text-lg">{t("waiting.title")}</p>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-cream-50/70">
          <div
            className="h-full rounded-full bg-gradient-to-r from-sage-400 to-sage-600 transition-[width] duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <ul className="space-y-2.5 px-5 py-4">
        {steps.map((step, i) => {
          const state = i < done ? "done" : i === done ? "now" : "later";
          return (
            <li
              key={i}
              className={`flex items-center gap-3 font-body text-sm transition-opacity duration-500 sm:text-[15px]
                ${state === "later" ? "opacity-40" : "opacity-100"}`}
            >
              {state === "done" ? (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sage-500 text-cream-50">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} className="h-3.5 w-3.5">
                    <path d="M5 12.5l4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              ) : state === "now" ? (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                  <span className="h-5 w-5 animate-spin rounded-full border-[3px] border-sage-200 border-t-sage-600" />
                </span>
              ) : (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                  <span className="h-2.5 w-2.5 rounded-full bg-dustyblue-300" />
                </span>
              )}
              <span className={state === "now" ? "font-semibold text-ink-900" : "text-ink-700"}>{step}</span>
            </li>
          );
        })}
      </ul>

      {(stillLine || slow) && (
        <div className="space-y-2 border-t border-cream-200 bg-cream-100/60 px-5 py-3.5">
          {stillLine && <p className="font-body text-sm font-semibold text-sage-700 animate-pulse">{stillLine}</p>}
          {slow && <p className="font-body text-sm text-dustyblue-600">{t("waiting.wake")}</p>}
        </div>
      )}
    </div>
  );
}
