import { useEffect, useState, type ReactNode } from "react";
import { ALL_NAV, MAIN_TOOLS, MORE_TOOLS, HELP_NAV, EXTRA_NAV, navLabel, type NavItem } from "@/nav";
import { BrandMark, IconChevronRight, IconAlert, IconSettings, IconChat, IconClose, IconHome, IconMessage, IconLink, IconEmail as IconMail } from "@/icons";
import { openHelper } from "@/chat";
import { useI18n, LANGUAGES } from "@/i18n";
import { FloatingHelpButton } from "@/components/ChatWidgets";
import { Wordmark } from "@/components/Brand";
import { themeFor } from "@/toolTheme";

interface LayoutProps {
  children: ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

/** A labelled group of links in the laptop sidebar. */
function SideGroup({ title, items, currentPath, onNavigate }: { title?: string; items: NavItem[]; currentPath: string; onNavigate: (p: string) => void }) {
  const { t } = useI18n();
  return (
    <div className="mb-3">
      {title && <p className="px-3.5 pb-1 pt-2 font-body text-[11px] font-bold uppercase tracking-wider text-dustyblue-500">{title}</p>}
      {items.map((item) => {
        const active = currentPath === item.path;
        return (
          <button
            key={item.path}
            onClick={() => onNavigate(item.path)}
            className={`btn-press mb-0.5 flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left font-body text-sm font-semibold
              ${active ? "bg-brand-50 text-brand-700 ring-1 ring-brand-100" : "text-ink-700 hover:bg-cream-100"}`}
          >
            <item.icon className={`h-5 w-5 shrink-0 ${active ? "text-brand-600" : "text-dustyblue-400"}`} />
            <span>{t(item.label)}</span>
          </button>
        );
      })}
    </div>
  );
}

export function Layout({ children, currentPath, onNavigate }: LayoutProps) {
  const { t, lang } = useI18n();
  const crumbs = buildCrumbs(currentPath);
  const langShort = LANGUAGES.find((l) => l.code === lang)?.short ?? "EN";

  return (
    <div className="min-h-screen bg-mist">
      {/* ---------- Laptop sidebar ---------- */}
      <aside className="fixed left-0 top-0 z-30 hidden h-full w-64 flex-col border-r border-cream-200 bg-cream-100/80 backdrop-blur-md lg:flex">
        <div className="flex items-center gap-3 px-6 py-6">
          <button onClick={() => onNavigate("/")} aria-label={t("nav.home")} className="btn-press shrink-0">
            <BrandMark className="h-11 w-11 shrink-0 shadow-warm-sm rounded-xl" />
          </button>
          {/* the name opens About & Privacy: what TrustLight is and how it handles your data */}
          <button onClick={() => onNavigate("/about")} aria-label={t("nav.about")} className="text-left">
            <Wordmark className="block text-[22px]" />
            <span className="mt-1 block font-body text-[11px] font-semibold text-dustyblue-500">{t("common.tagline")}</span>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-1 scrollbar-warm">
          <SideGroup items={[ALL_NAV[0]]} currentPath={currentPath} onNavigate={onNavigate} />
          <button
            onClick={() => openHelper("home")}
            className="btn-press mb-3 flex w-full items-center gap-3 rounded-xl bg-brand-500 px-3.5 py-2.5 text-left font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-brand-600"
          >
            <IconChat className="h-5 w-5 shrink-0" />
            <span>{t("chat.floating")}</span>
          </button>
          <SideGroup title={t("nav.checkGroup")} items={MAIN_TOOLS} currentPath={currentPath} onNavigate={onNavigate} />
          <SideGroup title={t("nav.moreGroup")} items={MORE_TOOLS} currentPath={currentPath} onNavigate={onNavigate} />
        </nav>

        {/* Help section — always visible at the bottom of the sidebar */}
        <div className="space-y-2 border-t border-cream-200 px-3 py-4">
          <p className="px-2 pb-1 font-body text-[11px] font-bold uppercase tracking-wider text-dustyblue-500">{t("nav.getHelp")}</p>
          {HELP_NAV.map((item) => (
            <SidebarHelpButton key={item.path} item={item} active={currentPath === item.path} onNavigate={onNavigate} />
          ))}
          <div className="flex gap-1 pt-1">
            {EXTRA_NAV.map((item) => {
              const active = currentPath === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => onNavigate(item.path)}
                  className={`btn-press flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-2 font-body text-xs font-semibold
                    ${active ? "bg-brand-200 text-brand-700" : "text-dustyblue-600 hover:bg-cream-200"}`}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{t(item.label)}</span>
                </button>
              );
            })}
          </div>
          <button onClick={() => openHelper("person")}
            className="btn-press flex w-full items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 font-body text-xs font-semibold text-dustyblue-500 hover:bg-cream-100 hover:text-brand-600">
            <IconMail className="h-4 w-4 shrink-0" />{t("nav.writeUs")}
          </button>
        </div>
      </aside>

      <div className="lg:pl-64">
        {/* ---------- Top bar ---------- */}
        <header className="sticky top-0 z-20 border-b border-cream-200 bg-cream-50/90 backdrop-blur-md">
          <div className="flex items-center gap-2 px-4 py-3 sm:px-5 lg:px-8">
            <div className="flex items-center gap-2 lg:hidden">
              <button onClick={() => onNavigate("/")} aria-label={t("nav.home")} className="btn-press shrink-0">
                <BrandMark className="h-8 w-8 shrink-0" />
              </button>
              {/* hide the word on very narrow phones so the emergency button always fits; it opens About & Privacy */}
              <button onClick={() => onNavigate("/about")} aria-label={t("nav.about")} className="hidden min-[360px]:inline">
                <Wordmark className="text-[19px]" />
              </button>
            </div>

            {/* Phone: always-visible emergency shortcut + settings */}
            <div className="ml-auto flex items-center gap-2 lg:hidden">
            {currentPath !== "/incident" && currentPath !== "/" && (
              <button
                onClick={() => onNavigate("/incident")}
                className="btn-press flex items-center gap-1.5 rounded-full bg-rust-500 px-3 py-2 font-body text-xs font-bold text-cream-50 shadow-warm-sm"
              >
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cream-50 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-cream-50" />
                </span>
                <span className="whitespace-nowrap">{t("nav.clickedScamPill")}</span>
              </button>
            )}
              <button
                onClick={() => onNavigate("/settings")}
                aria-label={t("nav.settingsAria")}
                className={`btn-press flex h-9 items-center gap-1 rounded-full border-2 px-2.5 font-body text-xs font-bold
                  ${currentPath === "/settings" ? "border-brand-400 bg-brand-200 text-brand-700" : "border-cream-200 bg-cream-100 text-dustyblue-600"}`}
              >
                <IconSettings className="h-4 w-4" />
                <span>{langShort}</span>
              </button>
            </div>

            <div className="ml-auto hidden items-center gap-1.5 lg:flex">
              {crumbs.map((c, i) => (
                <span key={c.path} className="flex items-center gap-1.5">
                  {i > 0 && <IconChevronRight className="h-4 w-4 text-dustyblue-400" />}
                  <button
                    onClick={() => onNavigate(c.path)}
                    className={`font-body text-sm ${i === crumbs.length - 1 ? "font-semibold text-ink-800" : "text-dustyblue-600 hover:text-brand-600"}`}
                  >
                    {t(c.label)}
                  </button>
                </span>
              ))}
            </div>
          </div>
        </header>

        <main className="px-4 py-6 pb-44 sm:px-5 lg:px-8 lg:py-8 lg:pb-28">
          <div className="mx-auto max-w-3xl">{children}</div>
        </main>
      </div>

      {/* ---------- Phone bottom menu: all tools, swipe sideways ---------- */}
      <PhoneMenu currentPath={currentPath} onNavigate={onNavigate} />

      <FloatingHelpButton onNavigate={onNavigate} currentPath={currentPath} />
    </div>
  );
}

/**
 * Phone bottom menu: five fixed buttons, no sideways scrolling. "Ask AI" opens TrustLight AI;
 * "More" opens a sheet with every other tool, help, settings and privacy.
 */
function PhoneMenu({ currentPath, onNavigate }: { currentPath: string; onNavigate: (p: string) => void }) {
  const { t } = useI18n();
  const [more, setMore] = useState(false);
  useEffect(() => setMore(false), [currentPath]);
  const inMore = [...MORE_TOOLS, ...HELP_NAV, ...EXTRA_NAV, MAIN_TOOLS[2], MAIN_TOOLS[3]].some((i) => i.path === currentPath);

  const tab = (key: string, label: string, Icon: NavItem["icon"], active: boolean, onClick: () => void, strong = false) => (
    <button key={key} onClick={onClick}
      className={`btn-press relative flex flex-1 flex-col items-center gap-1 px-1 pb-2.5 pt-2.5 ${
        strong ? "text-brand-700" : active ? "text-brand-700" : "text-dustyblue-500"} ${active ? "bg-cream-200/80" : ""}`}>
      {active && <span className="absolute left-3 right-3 top-0 h-[3px] rounded-b-full bg-current" />}
      {strong ? (
        <span className="-mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-brand-500 text-cream-50 shadow-warm-sm"><Icon className="h-5 w-5" /></span>
      ) : <Icon className="h-5 w-5" />}
      <span className="whitespace-nowrap font-body text-[10px] font-semibold">{label}</span>
    </button>
  );

  return (
    <>
      {more && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setMore(false)}>
          <div className="absolute inset-0 bg-ink-900/30" />
          <div onClick={(e) => e.stopPropagation()}
            className="absolute inset-x-0 bottom-0 max-h-[80vh] overflow-y-auto rounded-t-3xl bg-cream-50 px-4 pb-24 pt-4 shadow-warm-lg animate-fade-up">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-heading text-base font-bold text-ink-900">{t("nav.moreTitle")}</p>
              <button onClick={() => setMore(false)} aria-label={t("common.close")} className="rounded-full p-2 hover:bg-cream-200"><IconClose className="h-5 w-5" /></button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[...MAIN_TOOLS.slice(2), ...MORE_TOOLS].map((item) => (
                <button key={item.path} onClick={() => onNavigate(item.path)}
                  className={`flex items-center gap-2.5 rounded-xl px-3 py-3 text-left font-body text-sm font-semibold ${
                    currentPath === item.path ? "bg-brand-200 text-brand-700" : "bg-cream-100 text-ink-800"}`}>
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ background: themeFor(item.path).soft, color: themeFor(item.path).ink }}>
                    <item.icon className="h-[18px] w-[18px]" />
                  </span>{t(item.label)}
                </button>
              ))}
            </div>
            <div className="mt-3 grid gap-2">
              {HELP_NAV.map((item) => (
                <button key={item.path} onClick={() => onNavigate(item.path)}
                  className={`flex items-center gap-2.5 rounded-xl px-3 py-3 text-left font-body text-sm font-bold ${
                    item.tone === "urgent" ? "bg-rust-500 text-cream-50" : "border-2 border-brand-300 text-brand-700"}`}>
                  <item.icon className="h-5 w-5 shrink-0" />{t(item.label)}
                </button>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              {EXTRA_NAV.map((item) => (
                <button key={item.path} onClick={() => onNavigate(item.path)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-cream-100 px-3 py-2.5 font-body text-xs font-semibold text-dustyblue-600">
                  <item.icon className="h-4 w-4" />{t(item.label)}
                </button>
              ))}
            </div>
            <button onClick={() => { setMore(false); openHelper("person"); }}
              className="mt-3 flex w-full items-center justify-center gap-1.5 py-1.5 font-body text-xs font-semibold text-dustyblue-500">
              <IconMail className="h-4 w-4" />{t("nav.writeUs")}
            </button>
          </div>
        </div>
      )}
      <nav
        className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-cream-200 bg-cream-100/95 backdrop-blur-md lg:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {tab("home", t("nav.home"), IconHome, currentPath === "/", () => onNavigate("/"))}
        {tab("msg", t("nav.messageShort"), IconMessage, currentPath === "/scan-message", () => onNavigate("/scan-message"))}
        {tab("ai", t("nav.ask"), IconChat, false, () => openHelper("home"), true)}
        {tab("link", t("nav.linkShort"), IconLink, currentPath === "/scan-url", () => onNavigate("/scan-url"))}
        {tab("more", t("nav.more"), IconMore, more || inMore, () => setMore(!more))}
      </nav>
    </>
  );
}

/** Four squares: "more tools". */
function IconMore({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.8" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.8" />
    </svg>
  );
}

function SidebarHelpButton({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate: (p: string) => void }) {
  const { t } = useI18n();
  if (item.tone === "urgent") {
    return (
      <button
        onClick={() => onNavigate(item.path)}
        className={`btn-press flex w-full items-center gap-3 rounded-xl px-3.5 py-3 text-left font-body text-sm font-bold shadow-warm-sm transition-colors
          ${active ? "bg-rust-600 text-cream-50" : "bg-rust-500 text-cream-50 hover:bg-rust-600"}`}
      >
        <span className="relative flex h-5 w-5 items-center justify-center">
          <IconAlert className="h-5 w-5" />
          {!active && (
            <span className="absolute -right-1 -top-1 flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cream-50 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-cream-50" />
            </span>
          )}
        </span>
        <span>{t(item.label)}</span>
      </button>
    );
  }
  return (
    <button
      onClick={() => onNavigate(item.path)}
      className={`btn-press flex w-full items-center gap-3 rounded-xl border-2 px-3.5 py-2.5 text-left font-body text-sm font-bold transition-colors
        ${active ? "border-brand-400 bg-brand-200 text-brand-700" : "border-brand-300 bg-cream-50 text-brand-700 hover:bg-brand-100"}`}
    >
      <item.icon className="h-5 w-5" />
      <span>{t(item.label)}</span>
    </button>
  );
}

function buildCrumbs(path: string): { path: string; label: string }[] {
  const crumbs = [{ path: "/", label: "nav.home" }];
  if (path !== "/") {
    crumbs.push({ path, label: navLabel(path) });
  }
  return crumbs;
}
