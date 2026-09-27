import { useEffect, type ReactNode } from "react";
import { ALL_NAV, HOME_TOOLS, HELP_NAV, navLabel, type NavItem } from "@/nav";

import { IconShield, IconChevronRight, IconAlert } from "@/icons";
import { FloatingHelpButton } from "@/components/ChatWidgets";
import { loadChat, hasChattedBefore } from "@/chat";

interface LayoutProps {
  children: ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

const MAIN_NAV: NavItem[] = [ALL_NAV[0], ...HOME_TOOLS];

// Phone bottom menu: 5 fixed tabs that always fit on screen (no sideways scrolling).
// Every other tool is on the Home page; "Clicked a scam?" is always in the top bar.
const PHONE_NAV_PATHS = ["/", "/scan-url", "/scan-message", "/scan-qr", "/help"];
const PHONE_NAV: NavItem[] = PHONE_NAV_PATHS.map((p) => ALL_NAV.find((n) => n.path === p)!).filter(Boolean);

export function Layout({ children, currentPath, onNavigate }: LayoutProps) {
  const crumbs = buildCrumbs(currentPath);

  // Load live chat early only where people are likely to need it (or if they've chatted before),
  // so the rest of the site stays fast. It also loads instantly when someone taps "Need help?".
  useEffect(() => {
    if (currentPath === "/help" || currentPath === "/incident" || hasChattedBefore()) {
      const t = setTimeout(loadChat, 800);
      return () => clearTimeout(t);
    }
  }, [currentPath]);

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
            <p className="font-body text-xs text-dustyblue-600">Your safety checkup</p>
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
                <item.icon className={`h-5 w-5 ${active ? "text-sage-600" : "text-dustyblue-500"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Help section — always visible at the bottom of the sidebar */}
        <div className="space-y-2 border-t border-cream-200 px-3 py-4">
          <p className="px-2 pb-1 font-body text-[11px] font-bold uppercase tracking-wider text-dustyblue-500">Get help</p>
          {HELP_NAV.map((item) => (
            <SidebarHelpButton key={item.path} item={item} active={currentPath === item.path} onNavigate={onNavigate} />
          ))}
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
              <span className="font-heading text-lg font-bold text-ink-900">StaySafe</span>
            </button>

            {/* Phone: always-visible emergency shortcut */}
            {currentPath !== "/incident" && (
              <button
                onClick={() => onNavigate("/incident")}
                className="btn-press ml-auto flex items-center gap-1.5 rounded-full bg-rust-500 px-3.5 py-2 font-body text-xs font-bold text-cream-50 shadow-warm-sm lg:hidden"
              >
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cream-50 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-cream-50" />
                </span>
                Clicked a scam?
              </button>
            )}

            <div className="ml-auto hidden items-center gap-1.5 lg:flex">
              {crumbs.map((c, i) => (
                <span key={c.path} className="flex items-center gap-1.5">
                  {i > 0 && <IconChevronRight className="h-4 w-4 text-dustyblue-400" />}
                  <button
                    onClick={() => onNavigate(c.path)}
                    className={`font-body text-sm ${i === crumbs.length - 1 ? "font-semibold text-ink-800" : "text-dustyblue-600 hover:text-terracotta-600"}`}
                  >
                    {c.label}
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

      {/* ---------- Phone bottom menu ---------- */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-30 border-t border-cream-200 bg-cream-100/95 backdrop-blur-md lg:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="grid grid-cols-5">
          {PHONE_NAV.map((item) => {
            const active = currentPath === item.path;
            const color =
              item.tone === "urgent" ? (active ? "text-rust-600" : "text-rust-500") :
              item.tone === "help" ? (active ? "text-sage-700" : "text-sage-600") :
              active ? "text-sage-600" : "text-dustyblue-500";
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`btn-press flex flex-col items-center gap-1 px-1 py-2.5 ${color}
                  ${active ? "bg-cream-200/70" : ""}`}
              >
                <item.icon className="h-5 w-5" />
                <span className="whitespace-nowrap font-body text-[10px] font-semibold">{item.short}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <FloatingHelpButton onNavigate={onNavigate} currentPath={currentPath} />
    </div>
  );
}

function SidebarHelpButton({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate: (p: string) => void }) {
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
        <span>{item.label}</span>
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
      <span>{item.label}</span>
    </button>
  );
}

function buildCrumbs(path: string): { path: string; label: string }[] {
  const crumbs = [{ path: "/", label: "Home" }];
  if (path !== "/") {
    crumbs.push({ path, label: navLabel(path) });
  }
  return crumbs;
}
