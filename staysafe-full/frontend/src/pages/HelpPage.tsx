import { PageHeader } from "@/components/PageBits";
import { useChat, statusKey } from "@/chat";
import { IconAlert, IconArrowRight, IconBook, IconCheck, IconGlobe, IconLock, IconPhone, IconChat } from "@/icons";
import { useI18n } from "@/i18n";

/** Three quick actions side by side: call, report, chat. Small enough that the rest of the page shows. */
function QuickActions() {
  const { t } = useI18n();
  const chat = useChat();
  const tile = "btn-press card-hover flex flex-col items-center justify-center gap-1.5 rounded-2xl px-2 py-3.5 text-center font-body text-xs font-bold leading-tight shadow-warm-sm sm:text-sm";
  return (
    <div className="grid grid-cols-3 gap-2.5">
      <a href="tel:1930" className={`${tile} bg-rust-500 text-cream-50 hover:bg-rust-600`}>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-cream-50/20"><IconPhone className="h-5 w-5" /></span>
        {t("helpX.call")}
      </a>
      <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className={`${tile} border-2 border-rust-300 bg-cream-50 text-rust-600`}>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-rust-400/15"><IconGlobe className="h-5 w-5" /></span>
        {t("helpX.report")}
      </a>
      <button onClick={chat.openChat} disabled={!chat.enabled} className={`${tile} bg-sage-500 text-cream-50 hover:bg-sage-600 disabled:opacity-60`}>
        <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-cream-50/20">
          <IconChat className="h-5 w-5" />
          {chat.status === "online" && <span className="absolute right-0 top-0 h-2.5 w-2.5 rounded-full bg-[#9BE89B] ring-2 ring-sage-500" />}
        </span>
        {t("helpX.chat")}
      </button>
    </div>
  );
}

export function HelpPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t, tl } = useI18n();
  const chat = useChat();
  return (
    <div className="space-y-5">
      <PageHeader title={t("help.title")} subtitle={t("help.subtitle")} />

      {/* Lost money: one slim strip, not a whole screen */}
      <div className="flex items-start gap-3 rounded-2xl border-l-4 border-rust-500 bg-rust-400/10 px-4 py-3 animate-fade-up">
        <span className="relative mt-1 flex h-2.5 w-2.5 shrink-0">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rust-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-rust-500" />
        </span>
        <p className="font-body text-sm text-ink-800">
          <b className="text-rust-600">{t("help.urgentTitle")}</b> {t("helpX.urgentShort")}
        </p>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: "50ms" }}>
        <QuickActions />
        <p className="mt-2 px-1 font-body text-xs text-dustyblue-600">{t("help.bankNote")}</p>
      </div>

      {/* Talk to a person */}
      <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-sage-400 to-sage-600 p-5 text-cream-50 shadow-warm-lg animate-fade-up" style={{ animationDelay: "100ms" }}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20"><IconChat className="h-6 w-6" /></div>
          <div className="min-w-0 flex-1">
            <h2 className="font-heading text-lg font-bold">{t("chat.title")}</h2>
            <p className="flex items-center gap-1.5 font-body text-xs text-cream-50/90">
              <span className={`h-2 w-2 rounded-full ${chat.status === "online" ? "bg-[#9BE89B]" : "bg-cream-200/70"}`} />
              {chat.enabled ? t(statusKey(chat.status)) : t("chat.notReady")}
            </p>
          </div>
        </div>
        <p className="mt-3 font-body text-sm leading-relaxed text-cream-50/90">{t("chat.intro")}</p>
        <button
          onClick={chat.openChat}
          disabled={!chat.enabled}
          className="btn-press mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-6 py-3 font-body text-base font-bold text-sage-700 shadow-warm hover:bg-cream-100 disabled:opacity-60"
        >
          <IconChat className="h-5 w-5" /> {chat.unread > 0 ? t("chat.openNew", { count: chat.unread }) : t("chat.start")}
        </button>
        <p className="mt-2.5 flex items-center justify-center gap-1.5 font-body text-xs text-cream-50/80">
          <IconLock className="h-3.5 w-3.5" /> {t("chat.never")}
        </p>
      </div>

      {/* What we can help with */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up" style={{ animationDelay: "150ms" }}>
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("help.canHelpTitle")}</h3>
        <div className="flex flex-wrap gap-2">
          {tl("help.topics").map((topic) => (
            <span key={topic} className="flex items-start gap-1.5 rounded-xl bg-sage-100 px-3 py-2 font-body text-sm text-ink-800">
              <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-sage-600" /> {topic}
            </span>
          ))}
        </div>
      </div>

      {/* Safety promise */}
      <div className="flex items-start gap-3 rounded-2xl bg-dustyblue-100 p-5 animate-fade-up" style={{ animationDelay: "200ms" }}>
        <IconLock className="mt-0.5 h-5 w-5 shrink-0 text-dustyblue-600" />
        <div className="font-body text-sm text-dustyblue-600">
          <p className="font-semibold text-ink-800">{t("help.promiseTitle")}</p>
          <p className="mt-1">{t("help.promise")}</p>
        </div>
      </div>

      {/* Self-help shortcuts */}
      <div className="grid gap-3 sm:grid-cols-2 animate-fade-up" style={{ animationDelay: "250ms" }}>
        <button onClick={() => onNavigate("/incident")} className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rust-400/15 text-rust-500"><IconAlert className="h-5 w-5" /></div>
          <div className="flex-1">
            <p className="font-body text-sm font-bold text-ink-800">{t("help.clickedTitle")}</p>
            <p className="font-body text-xs text-dustyblue-600">{t("help.clickedText")}</p>
          </div>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
        <button onClick={() => onNavigate("/scam-library")} className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sage-100 text-sage-600"><IconBook className="h-5 w-5" /></div>
          <div className="flex-1">
            <p className="font-body text-sm font-bold text-ink-800">{t("help.learnTitle")}</p>
            <p className="font-body text-xs text-dustyblue-600">{t("help.learnText")}</p>
          </div>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
      </div>

      <p className="text-center font-body text-xs text-dustyblue-500">{t("help.footer")}</p>
    </div>
  );
}
