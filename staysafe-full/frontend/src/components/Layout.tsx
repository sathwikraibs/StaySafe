import type { ReactNode } from "react";
import { ALL_NAV, navLabel } from "@/nav";
import { IconShield, IconChevronRight } from "@/icons";

interface LayoutProps {
  children: ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

export function Layout({ children, currentPath, onNavigate }: LayoutProps) {
  const crumbs = buildCrumbs(currentPath);

  return (
    <div className="min-h-screen bg-cream-50">
      <aside className="fixed left-0 top-0 z-30 hidden h-full w-64 flex-col border-r border-cream-200 bg-cream-100/80 backdrop-blur-md lg:flex">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sage-400 text-cream-50 shadow-warm-sm">
            <IconShield className="h-6 w-6" />
          </div>
          <div>
            <p className="font-heading text-xl font-bold text-ink-900">StaySafe</p>
            <p className="font-body text-xs text-dustyblue-600">Your safety checkup</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-2 scrollbar-warm">
          {ALL_NAV.map((item) => {
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
        <div className="px-6 py-4">
          <p className="font-body text-xs text-dustyblue-600">Take your time. We are here to help.</p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-cream-200 bg-cream-50/90 backdrop-blur-md">
          <div className="flex items-center gap-2 px-5 py-3 lg:px-8">
            <div className="flex items-center gap-2 lg:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sage-400 text-cream-50">
                <IconShield className="h-5 w-5" />
              </div>
              <span className="font-heading text-lg font-bold text-ink-900">StaySafe</span>
            </div>
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

        <main className="px-5 py-6 pb-28 lg:px-8 lg:py-8 lg:pb-12">
          <div className="mx-auto max-w-3xl">{children}</div>
        </main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-cream-200 bg-cream-100/95 backdrop-blur-md lg:hidden">
        <div className="flex overflow-x-auto scrollbar-warm">
          {ALL_NAV.map((item) => {
            const active = currentPath === item.path;
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`btn-press flex min-w-[4.5rem] flex-1 flex-col items-center gap-1 px-2 py-2.5
                  ${active ? "text-sage-600" : "text-dustyblue-500"}`}
              >
                <item.icon className={`h-5 w-5 ${active ? "text-sage-600" : "text-dustyblue-500"}`} />
                <span className="font-body text-[10px] font-semibold">{item.short}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

function buildCrumbs(path: string): { path: string; label: string }[] {
  const crumbs = [{ path: "/", label: "Home" }];
  if (path !== "/") {
    crumbs.push({ path, label: navLabel(path) });
  }
  return crumbs;
}
