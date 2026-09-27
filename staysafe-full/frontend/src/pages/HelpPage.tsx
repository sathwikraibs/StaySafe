import { PageHeader } from "@/components/PageBits";
import { ChatCard } from "@/components/ChatWidgets";
import { IconAlert, IconArrowRight, IconBook, IconCheck, IconGlobe, IconLock, IconPhone } from "@/icons";

const HELP_TOPICS = [
  "Not sure if a message, call or link is a scam",
  "You clicked a link or installed an app you now regret",
  "Someone is asking you for money, an OTP or a PIN",
  "You don't understand a result StaySafe showed you",
];

export function HelpPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Need Help?"
        subtitle="You're not alone. Talk to a real person, or get urgent help if you've lost money."
      />

      {/* Urgent: money lost */}
      <div className="rounded-2xl border-2 border-rust-400 bg-rust-400/10 p-5 animate-fade-up sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rust-500 text-cream-50">
            <IconAlert className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-heading text-lg font-bold text-rust-600">Lost money in the last few hours?</h2>
            <p className="mt-1 font-body text-sm text-ink-700">
              Act fast — the sooner you report it, the better the chance of stopping the money.
            </p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <a
            href="tel:1930"
            className="btn-press flex items-center justify-center gap-2 rounded-2xl bg-rust-500 px-4 py-3.5 font-body text-[15px] font-bold text-cream-50 sm:text-base shadow-warm hover:bg-rust-600"
          >
            <IconPhone className="h-5 w-5" /> Call 1930 helpline
          </a>
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-press flex items-center justify-center gap-2 rounded-2xl border-2 border-rust-400 bg-cream-50 px-4 py-3.5 font-body text-[15px] font-bold text-rust-600 sm:text-base hover:bg-rust-400/10"
          >
            <IconGlobe className="h-5 w-5" /> Report at cybercrime.gov.in
          </a>
        </div>
        <p className="mt-3 font-body text-xs text-ink-700/80">
          Also call your bank's official number (from the back of your card or their official app) to block your card or account.
        </p>
      </div>

      {/* Live chat */}
      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        <ChatCard />
      </div>

      {/* What we can help with */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up sm:p-6" style={{ animationDelay: "120ms" }}>
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">We can help if…</h3>
        <ul className="space-y-2.5">
          {HELP_TOPICS.map((t) => (
            <li key={t} className="flex items-start gap-2.5 font-body text-sm text-ink-700">
              <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-sage-500" />
              <span>{t}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Safety promise */}
      <div className="flex items-start gap-3 rounded-2xl bg-dustyblue-100 p-5 animate-fade-up" style={{ animationDelay: "180ms" }}>
        <IconLock className="mt-0.5 h-5 w-5 shrink-0 text-dustyblue-600" />
        <div className="font-body text-sm text-dustyblue-600">
          <p className="font-semibold text-ink-800">Our promise</p>
          <p className="mt-1">
            StaySafe will <strong>never</strong> ask for your OTP, UPI PIN, password, card number or bank details — in chat,
            on a call, or anywhere else. If "StaySafe support" ever asks for these, it's a scam.
          </p>
        </div>
      </div>

      {/* Self-help shortcuts */}
      <div className="grid gap-3 sm:grid-cols-2 animate-fade-up" style={{ animationDelay: "240ms" }}>
        <button
          onClick={() => onNavigate("/incident")}
          className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rust-400/15 text-rust-500">
            <IconAlert className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <p className="font-body text-sm font-bold text-ink-800">I clicked a scam</p>
            <p className="font-body text-xs text-dustyblue-600">Get a step-by-step recovery plan</p>
          </div>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
        <button
          onClick={() => onNavigate("/scam-library")}
          className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sage-100 text-sage-600">
            <IconBook className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <p className="font-body text-sm font-bold text-ink-800">Learn about scams</p>
            <p className="font-body text-xs text-dustyblue-600">Common tricks and how to spot them</p>
          </div>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
      </div>

      <p className="text-center font-body text-xs text-dustyblue-500">
        Chat is provided by tawk.to. Please don't share personal documents or passwords in chat.
      </p>
    </div>
  );
}
