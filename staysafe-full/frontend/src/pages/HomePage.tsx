import { useState } from "react";
import { MAIN_TOOLS, MORE_TOOLS } from "@/nav";
import { IconShield, IconArrowRight, IconAlert, IconLock, IconChevronRight } from "@/icons";
import { useI18n } from "@/i18n";
import { themeFor } from "@/toolTheme";
import { openHelper } from "@/chat";
import { understand, setPrefill, helpTopics } from "@/helpBot";

const TOOL_IDS: Record<string, string> = {
  "/scan-url": "link", "/scan-message": "message", "/scan-qr": "qr", "/scan-file": "file",
  "/check-password": "password", "/check-network": "network", "/scan-email": "email",
  "/dashboard": "dashboard", "/scam-library": "library",
};

/**
 * Home: one clear starting point. People describe what happened (any language) or paste what
 * they got; a pasted link or message goes straight to the right check, anything else to
 * StaySafe AI. The four main checks come next; everything else is one tap away.
 */
export function HomePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t, lang } = useI18n();
  const [text, setText] = useState("");
  const examples = helpTopics(lang).filter((tp) => ["lost_money", "digital_arrest", "job_invest"].includes(tp.id));

  function go(value: string) {
    const v = value.trim();
    if (!v) return;
    const r = understand(v, lang);
    if (r.kind === "link") { setPrefill("url", r.link); onNavigate("/scan-url"); return; }
    if (r.kind === "message") { setPrefill("message", r.text); onNavigate("/scan-message"); return; }
    openHelper("home", v);
    setText("");
  }

  return (
    <div>
      {/* Ask StaySafe AI: the main way in */}
      <div className="relative mb-4 overflow-hidden rounded-3xl bg-gradient-to-br from-sage-100 via-cream-100 to-dustyblue-100 p-5 shadow-warm animate-fade-up sm:p-7">
        <span className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-sage-200/50 blur-2xl" />
        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sage-400 to-sage-600 text-cream-50 shadow-warm-sm">
              <IconShield className="h-6 w-6" />
            </span>
            <h1 className="font-heading text-[21px] font-bold leading-tight text-ink-900 sm:text-2xl">{t("homeX.askTitle")}</h1>
          </div>
          <p className="mt-2.5 font-body text-sm text-ink-700/90 sm:text-base">{t("homeX.askIntro")}</p>
          <form onSubmit={(e) => { e.preventDefault(); go(text); }} className="mt-4">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); go(text); } }}
              rows={3}
              maxLength={5000}
              placeholder={t("homeX.askPlaceholder")}
              className="w-full resize-none rounded-2xl border-2 border-sage-300 bg-cream-50 px-4 py-3 font-body text-base text-ink-800 shadow-warm-sm outline-none transition-colors focus:border-sage-500"
            />
            <button type="submit" disabled={!text.trim()}
              className="btn-press mt-2.5 flex w-full items-center justify-center gap-2 rounded-2xl bg-sage-500 px-5 py-3.5 font-body text-base font-bold text-cream-50 shadow-warm-sm transition-colors hover:bg-sage-600 disabled:opacity-60">
              {t("homeX.askButton")} <IconArrowRight className="h-5 w-5" />
            </button>
          </form>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {examples.map((tp) => (
              <button key={tp.id} type="button" onClick={() => openHelper("home", tp.q)}
                className="rounded-full bg-cream-50/90 px-3 py-1.5 text-left font-body text-xs font-semibold text-sage-700 shadow-warm-sm hover:bg-cream-50">
                {tp.q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Emergency */}
      <button
        onClick={() => onNavigate("/incident")}
        className="btn-press group mb-7 flex w-full min-w-0 items-center gap-2.5 rounded-2xl border-2 border-rust-400 bg-rust-400/10 py-2 pl-2 pr-3 text-left hover:bg-rust-400/20 animate-fade-up"
        style={{ animationDelay: "60ms" }}
      >
        <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-rust-500 text-cream-50">
          <IconAlert className="h-4 w-4" />
          <span className="absolute -right-0.5 -top-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rust-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-rust-500 ring-2 ring-cream-50" />
          </span>
        </span>
        <span className="min-w-0 flex-1 font-body text-sm font-bold leading-tight text-rust-600">{t("homeX.urgent")}</span>
        <IconArrowRight className="h-4 w-4 shrink-0 text-rust-500 transition-transform group-hover:translate-x-0.5" />
      </button>

      {/* The four main checks */}
      <h2 className="mb-3 font-heading text-lg font-semibold text-ink-800">{t("homeX.checkTitle")}</h2>
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        {MAIN_TOOLS.map((tool, i) => {
          const th = themeFor(tool.path);
          return (
            <button
              key={tool.path}
              onClick={() => onNavigate(tool.path)}
              className="btn-press card-hover group relative flex flex-col items-start gap-3 overflow-hidden rounded-2xl bg-cream-50 p-4 text-left shadow-warm animate-fade-up sm:p-5"
              style={{ animationDelay: `${80 + i * 45}ms` }}
            >
              <span className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full opacity-60 transition-transform duration-500 group-hover:scale-125" style={{ background: th.soft }} />
              <span
                className="relative flex h-11 w-11 items-center justify-center rounded-2xl text-cream-50 shadow-warm-sm transition-transform group-hover:-rotate-6 group-hover:scale-105"
                style={{ backgroundImage: `linear-gradient(135deg, ${th.from}, ${th.to})` }}
              >
                <tool.icon className="h-6 w-6" />
              </span>
              <span className="relative">
                <span className="block font-heading text-[15px] font-semibold leading-snug text-ink-900 sm:text-base">{t(tool.label)}</span>
                <span className="mt-1 block font-body text-xs leading-snug text-dustyblue-600 sm:text-sm">{t(`homeX.desc.${TOOL_IDS[tool.path]}`)}</span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Everything else: a simple list */}
      <h2 className="mb-3 mt-7 font-heading text-base font-semibold text-ink-800">{t("homeX.moreTitle")}</h2>
      <div className="overflow-hidden rounded-2xl bg-cream-50 shadow-warm">
        {MORE_TOOLS.map((tool, i) => {
          const th = themeFor(tool.path);
          return (
            <button key={tool.path} onClick={() => onNavigate(tool.path)}
              className={`flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-cream-100 ${i ? "border-t border-cream-200" : ""}`}>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-cream-50"
                style={{ backgroundImage: `linear-gradient(135deg, ${th.from}, ${th.to})` }}>
                <tool.icon className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-body text-sm font-bold text-ink-900">{t(tool.label)}</span>
                <span className="block font-body text-xs text-dustyblue-600">{t(`homeX.desc.${TOOL_IDS[tool.path]}`)}</span>
              </span>
              <IconChevronRight className="h-4 w-4 shrink-0 text-dustyblue-400" />
            </button>
          );
        })}
      </div>

      {/* Reassurance */}
      <div className="mt-7 flex items-start gap-3 rounded-2xl bg-dustyblue-100 p-5">
        <IconLock className="mt-0.5 h-5 w-5 shrink-0 text-dustyblue-500" />
        <p className="font-body text-sm text-dustyblue-600">
          {t("home.privacy")}{" "}
          <button onClick={() => onNavigate("/about")} className="font-semibold text-sage-700 underline underline-offset-2">
            {t("home.privacyLink")}
          </button>
        </p>
      </div>
    </div>
  );
}
