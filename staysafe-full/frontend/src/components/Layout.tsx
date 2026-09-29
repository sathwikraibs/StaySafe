import { useEffect, useRef, useState, type ReactNode } from "react";
import { ALL_NAV, HOME_TOOLS, HELP_NAV, EXTRA_NAV, navLabel, type NavItem } from "@/nav";
import { IconShield, IconChevronRight, IconAlert, IconSettings } from "@/icons";
import { useI18n, LANGUAGES } from "@/i18n";
import { FloatingHelpButton } from "@/components/ChatWidgets";

interface LayoutProps {
  children: ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

const MAIN_NAV: NavItem[] = [ALL_NAV[0], ...HOME_TOOLS];

// Phone bottom menu: every tool, in a row you can swipe sideways.
const PHONE_NAV: NavItem[] = ALL_NAV;

export function Layout({ children, currentPath, onNavigate }: LayoutProps) {
  const { t, lang } = useI18n();
  const crumbs = buildCrumbs(currentPath);
  const langShort = LANGUAGES.find((l) => l.code === lang)?.short ?? "EN";

  return (
    <div className="min-h-screen bg-cream-50">
      {/* ---------- Laptop sidebar ---------- */}
      <aside className="fixed left-0 top-0 z-30 hidden h-full w-64 flex-col border-r border-cream-200 bg-cream-100/80 backdrop-blur-md lg:flex">
        <button onClick={() => onNavigate("/")} className="flex items-center gap-3 px-6 py-6 text-left">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sage-400 text-cream-50 shadow-warm-sm">
            <IconShield className="h-6 w-6" />
          </div>
          <div>
            <p className="font-heading text-xl font-bold text-ink-900">StaySafe</p>
            <p className="font-body text-xs text-dustyblue-600">{t("common.tagline")}</p>
          </div>
        </button>

        <nav className="flex-1 overflow-y-auto px-3 py-2 scrollbar-warm">
          {MAIN_NAV.map((item) => {
            const active = currentPath === item.path;
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`btn-press mb-1 flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left font-body text-sm font-semibold
                  ${active ? "bg-sage-200 text-sage-700" : "text-ink-700 hover:bg-cream-200"}`}
              >
                <item.icon className={`h-5 w-5 shrink-0 ${active ? "text-sage-600" : "text-dustyblue-500"}`} />
                <span>{t(item.label)}</span>
              </button>
            );
          })}
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
                    ${active ? "bg-sage-200 text-sage-700" : "text-dustyblue-600 hover:bg-cream-200"}`}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{t(item.label)}</span>
                </button>
              );
            })}
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        {/* ---------- Top bar ---------- */}
        <header className="sticky top-0 z-20 border-b border-cream-200 bg-cream-50/90 backdrop-blur-md">
          <div className="flex items-center gap-2 px-4 py-3 sm:px-5 lg:px-8">
            <button onClick={() => onNavigate("/")} className="flex items-center gap-2 lg:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sage-400 text-cream-50">
                <IconShield className="h-5 w-5" />
              </div>
              {/* hide the word on narrow phones so the emergency button always fits */}
              <span className="hidden font-heading text-lg font-bold text-ink-900 min-[420px]:inline">StaySafe</span>
            </button>

            {/* Phone: always-visible emergency shortcut + settings */}
            <div className="ml-auto flex items-center gap-2 lg:hidden">
            {currentPath !== "/incident" && (
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
                  ${currentPath === "/settings" ? "border-sage-400 bg-sage-200 text-sage-700" : "border-cream-200 bg-cream-100 text-dustyblue-600"}`}
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
                    className={`font-body text-sm ${i === crumbs.length - 1 ? "font-semibold text-ink-800" : "text-dustyblue-600 hover:text-terracotta-600"}`}
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

function PhoneMenu({ currentPath, onNavigate }: { currentPath: string; onNavigate: (p: string) => void }) {
  const { t } = useI18n();
  const row = useRef<HTMLDivElement>(null);
  const [moreLeft, setMoreLeft] = useState(false);
  const [moreRight, setMoreRight] = useState(true);

  const updateHints = () => {
    const el = row.current;
    if (!el) return;
    setMoreLeft(el.scrollLeft > 8);
    setMoreRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 8);
  };

  // Keep the current page's button in view
  useEffect(() => {
    const el = row.current?.querySelector<HTMLElement>(`[data-path="${currentPath}"]`);
    el?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    const timer = setTimeout(updateHints, 400);
    return () => clearTimeout(timer);
  }, [currentPath]);

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 border-t border-cream-200 bg-cream-100/95 backdrop-blur-md lg:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="relative">
        <div ref={row} onScroll={updateHints} className="no-scrollbar flex snap-x overflow-x-auto">
          {PHONE_NAV.map((item) => {
            const active = currentPath === item.path;
            const color =
              item.tone === "urgent" ? (active ? "text-rust-600" : "text-rust-500") :
              item.tone === "help" ? (active ? "text-sage-700" : "text-sage-600") :
              active ? "text-sage-700" : "text-dustyblue-500";
            return (
              <button
                key={item.path}
                data-path={item.path}
                onClick={() => onNavigate(item.path)}
                className={`btn-press relative flex min-w-[4.6rem] shrink-0 snap-start flex-col items-center gap-1 px-2 pb-2.5 pt-2.5 ${color}
                  ${active ? "bg-cream-200/80" : ""}`}
              >
                {active && <span className="absolute left-3 right-3 top-0 h-[3px] rounded-b-full bg-current" />}
                <item.icon className="h-5 w-5" />
                <span className="whitespace-nowrap font-body text-[10px] font-semibold">{t(item.short)}</span>
              </button>
            );
          })}
        </div>
        {/* soft edges show there are more tools to swipe to */}
        {moreLeft && <div className="pointer-events-none absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-cream-100 to-transparent" />}
        {moreRight && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex w-10 items-center justify-end bg-gradient-to-l from-cream-100 via-cream-100/80 to-transparent pr-1">
            <IconChevronRight className="h-4 w-4 text-dustyblue-500" />
          </div>
        )}
      </div>
    </nav>
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
        ${active ? "border-sage-400 bg-sage-200 text-sage-700" : "border-sage-300 bg-cream-50 text-sage-700 hover:bg-sage-100"}`}
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
