import { MAIN_TOOLS, MORE_TOOLS } from "@/nav";
import { InstallCard } from "@/components/InstallCard";
import { IconShield, IconArrowRight, IconAlert, IconLock, IconChevronRight, IconCheck, IconChat } from "@/icons";
import { useI18n } from "@/i18n";
import { themeFor } from "@/toolTheme";
import { openHelper } from "@/chat";

const TOOL_IDS: Record<string, string> = {
  "/scan-url": "link", "/scan-message": "message", "/scan-qr": "qr", "/scan-file": "file",
  "/check-password": "password", "/check-network": "network", "/scan-email": "email",
  "/dashboard": "dashboard", "/scam-library": "library",
};

/** Shield with gentle rings: the picture on the welcome card. */
function HeroArt() {
  return (
    <div className="relative flex h-20 w-20 shrink-0 items-center justify-center sm:h-36 sm:w-36" aria-hidden>
      <span className="hero-ring absolute inset-0 rounded-full border-2 border-sage-300" />
      <span className="hero-ring absolute inset-3 rounded-full border-2 border-sage-300/70" style={{ animationDelay: "0.8s" }} />
      <span className="absolute inset-3 rounded-full bg-gradient-to-br from-sage-300 to-sage-500 opacity-90 shadow-warm-lg sm:inset-6" />
      <IconShield className="relative h-8 w-8 text-cream-50 sm:h-14 sm:w-14" />
      <span className="hero-float absolute -right-1 top-0 flex h-6 w-6 items-center justify-center rounded-full bg-cream-50 text-sage-600 shadow-warm sm:top-3 sm:h-8 sm:w-8">
        <IconCheck className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
      </span>
      <span className="hero-float absolute -left-1 bottom-1 hidden h-7 w-7 items-center justify-center rounded-full bg-cream-50 text-terracotta-600 shadow-warm sm:flex" style={{ animationDelay: "1.2s" }}>
        <IconLock className="h-3.5 w-3.5" />
      </span>
    </div>
  );
}

/** Home: a short welcome to StaySafe, quick help, the four main checks, then everything else. */
export function HomePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t } = useI18n();
  return (
    <div>
      {/* Welcome */}
      <div className="relative mb-4 overflow-hidden rounded-3xl bg-gradient-to-br from-sage-100 via-cream-100 to-dustyblue-100 p-5 shadow-warm animate-fade-up sm:p-8">
        <span className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-sage-200/50 blur-2xl" />
        <span className="pointer-events-none absolute -bottom-20 left-10 h-40 w-40 rounded-full bg-terracotta-300/30 blur-2xl" />
        <div className="relative flex items-center gap-4 sm:gap-6">
          <div className="min-w-0 flex-1">
            <h1 className="font-heading text-[22px] font-bold leading-tight text-ink-900 sm:text-3xl">{t("home.title")}</h1>
            <p className="mt-2 max-w-lg font-body text-sm text-ink-700/85 sm:mt-3 sm:text-base">{t("home.intro")}</p>
            <div className="mt-3 flex flex-wrap gap-1.5 sm:mt-4 sm:gap-2">
              {["homeX.chip1", "homeX.chip2", "homeX.chip3"].map((k) => (
                <span key={k} className="flex items-center gap-1 rounded-full bg-cream-50/80 px-2.5 py-1 font-body text-[11px] font-bold text-sage-700 shadow-warm-sm sm:text-xs">
                  <IconCheck className="h-3.5 w-3.5" /> {t(k)}
                </span>
              ))}
            </div>
          </div>
          <HeroArt />
        </div>
      </div>

      {/* Quick help: emergency, and StaySafe AI next to it */}
      <div className="mb-7 grid grid-cols-[1fr_auto] gap-2 animate-fade-up" style={{ animationDelay: "60ms" }}>
        <button
          onClick={() => onNavigate("/incident")}
          className="btn-press group flex min-w-0 items-center gap-2.5 rounded-full border-2 border-rust-400 bg-rust-400/10 py-1.5 pl-1.5 pr-3 text-left hover:bg-rust-400/20"
        >
          <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-rust-500 text-cream-50">
            <IconAlert className="h-4 w-4" />
            <span className="absolute -right-0.5 -top-0.5 flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rust-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-rust-500 ring-2 ring-cream-50" />
            </span>
          </span>
          <span className="min-w-0 flex-1 font-body text-sm font-bold leading-tight text-rust-600">{t("homeX.urgent")}</span>
          <IconArrowRight className="h-4 w-4 shrink-0 text-rust-500 transition-transform group-hover:translate-x-0.5" />
        </button>
        <button
          onClick={() => openHelper("home")}
          className="btn-press flex items-center gap-2 rounded-full border-2 border-sage-300 bg-cream-50 py-1.5 pl-1.5 pr-3 hover:bg-sage-100"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-sage-500 text-cream-50">
            <IconChat className="h-4 w-4" />
          </span>
          <span className="whitespace-nowrap font-body text-sm font-bold text-sage-700">{t("nav.ask")}</span>
        </button>
      </div>

      <InstallCard place="home" />

      {/* The four main checks */}
      <h2 className="mb-3 font-heading text-lg font-semibold text-ink-800">{t("home.toolsTitle")}</h2>
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
