import { HOME_TOOLS } from "@/nav";
import { IconShield, IconArrowRight } from "@/icons";

export function HomePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  return (
    <div>
      {/* Hero */}
      <div className="mb-8 rounded-2xl bg-gradient-to-br from-sage-100 via-cream-100 to-dustyblue-100 p-6 shadow-warm sm:p-8 animate-fade-up">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sage-400 text-cream-50">
            <IconShield className="h-6 w-6" />
          </div>
          <span className="font-heading text-lg font-semibold text-sage-700">StaySafe</span>
        </div>
        <h1 className="font-heading text-2xl font-bold text-ink-900 sm:text-3xl">
          Let's check things together
        </h1>
        <p className="mt-3 max-w-lg font-body text-base text-ink-700/80">
          Not sure if a link, message, or file is safe? You are in the right place.
          Pick a tool below and we will take a careful look for you.
        </p>
      </div>

      {/* Tool grid */}
      <h2 className="mb-4 font-heading text-lg font-semibold text-ink-800">What would you like to check?</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {HOME_TOOLS.map((tool, i) => (
          <button
            key={tool.path}
            onClick={() => onNavigate(tool.path)}
            className="btn-press card-hover group flex items-center gap-4 rounded-2xl bg-cream-50 p-5 text-left shadow-warm animate-fade-up"
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-sage-100 text-sage-600 transition-colors group-hover:bg-sage-200">
              <tool.icon className="h-7 w-7" />
            </div>
            <div className="flex-1">
              <p className="font-heading text-base font-semibold text-ink-900">{tool.label}</p>
            </div>
            <div className="text-dustyblue-400 transition-transform group-hover:translate-x-1 group-hover:text-terracotta-500">
              <IconArrowRight className="h-5 w-5" />
            </div>
          </button>
        ))}
      </div>

      {/* Reassurance */}
      <div className="mt-8 rounded-2xl bg-dustyblue-100 p-5">
        <p className="font-body text-sm text-dustyblue-600">
          Everything you check here is private to you. Take your time, there is no rush.
          If something feels wrong, trust your gut and let us help you look closer.
        </p>
      </div>
    </div>
  );
}
