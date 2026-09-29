import { useChat, statusKey } from "@/chat";
import { useI18n } from "@/i18n";
import { useState } from "react";
import { IconChat, IconLock } from "@/icons";
import { HelpBot } from "@/components/HelpBot";

/** Floating "Need help?" button — sits above the phone menu, bottom-right on laptops. */
export function FloatingHelpButton({ onNavigate, currentPath }: { onNavigate: (p: string) => void; currentPath: string }) {
  const chat = useChat();
  const { t } = useI18n();
  const [helper, setHelper] = useState(false);
  if (chat.open) return null; // the chat window is showing
  if (helper) return <HelpBot onClose={() => setHelper(false)} onNavigate={onNavigate} currentPath={currentPath} />;
  // These pages already show a big chat card, so the floating button would just cover it
  if (currentPath === "/help" || currentPath === "/incident") return null;

  // A reply from our team is waiting: go straight to the chat. Otherwise the helper answers first.
  const handleClick = () => (chat.unread > 0 ? chat.openChat() : setHelper(true));

  return (
    <button
      onClick={handleClick}
      aria-label={t("chat.floatingAria")}
      data-help-fab
      className="btn-press fixed bottom-[5.25rem] right-4 z-40 flex items-center gap-2 rounded-full bg-sage-500 py-3 pl-3 pr-3 text-cream-50 shadow-warm-lg transition-colors hover:bg-sage-600 sm:pr-5 lg:bottom-6 lg:right-6"
      style={{ marginBottom: "env(safe-area-inset-bottom)" }}
    >
      <span className="relative flex h-7 w-7 items-center justify-center">
        <IconChat className="h-6 w-6" />
        {chat.unread > 0 ? (
          <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-rust-500 px-1 font-body text-[11px] font-bold text-cream-50 ring-2 ring-sage-500">
            {chat.unread}
          </span>
        ) : chat.status === "online" ? (
          <span className="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full bg-[#7CD67C] ring-2 ring-sage-500" />
        ) : null}
      </span>
      <span className="hidden font-body text-sm font-bold sm:inline">{t("chat.floating")}</span>
    </button>
  );
}

/** Big chat card used on the Help and "I clicked a scam" pages. */
export function ChatCard({ title, compact = false }: { title?: string; compact?: boolean }) {
  const chat = useChat();
  const { t, lang } = useI18n();
  const online = chat.status === "online";

  return (
    <div className={`overflow-hidden rounded-2xl bg-gradient-to-br from-sage-400 to-sage-600 text-cream-50 shadow-warm-lg ${compact ? "p-5" : "p-6 sm:p-7"}`}>
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20">
          <IconChat className="h-7 w-7" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-heading text-lg font-bold sm:text-xl">{title ?? t("chat.title")}</h2>
          {chat.enabled ? (
            <p className="mt-1 flex items-center gap-2 font-body text-sm text-cream-50/90">
              <span className={`h-2.5 w-2.5 rounded-full ${online ? "bg-[#9BE89B]" : "bg-cream-200/70"}`} />
              {t(statusKey(chat.status))}
            </p>
          ) : (
            <p className="mt-1 font-body text-sm text-cream-50/90">{t("chat.notReady")}</p>
          )}
        </div>
      </div>

      {!compact && (
        <p className="mt-4 font-body text-sm leading-relaxed text-cream-50/90">
          {t("chat.intro")}
        </p>
      )}

      <button
        onClick={chat.openChat}
        disabled={!chat.enabled}
        className="btn-press mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-6 py-3.5 font-body text-base font-bold text-sage-700 shadow-warm transition-colors hover:bg-cream-100 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <IconChat className="h-5 w-5" />
        {chat.unread > 0 ? t("chat.openNew", { count: chat.unread }) : t("chat.start")}
      </button>

      <p className="mt-3 flex items-center justify-center gap-1.5 font-body text-xs text-cream-50/80">
        <IconLock className="h-3.5 w-3.5" />
        {t("chat.never")}
      </p>
      {lang !== "en" && (
        <p className="mt-1 text-center font-body text-[11px] text-cream-50/70">{t("chat.chatInEnglish")}</p>
      )}
    </div>
  );
}
