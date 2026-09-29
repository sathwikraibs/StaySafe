import type { ReactNode } from "react";
import { PageHeader } from "@/components/PageBits";
import { openHelper } from "@/chat";
import { IconAlert, IconArrowRight, IconBook, IconCheck, IconGlobe, IconLock, IconPhone, IconChat } from "@/icons";
import { useI18n } from "@/i18n";

/** A plain white card with a coloured strip on the left and a clear heading. */
function Section({ accent, icon, title, children, delay = 0 }: {
  accent: string; icon: ReactNode; title: string; children: ReactNode; delay?: number;
}) {
  return (
    <section className="overflow-hidden rounded-2xl bg-cream-50 shadow-warm animate-fade-up" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex">
        <span className="w-1.5 shrink-0" style={{ background: accent }} />
        <div className="min-w-0 flex-1 p-5">
          <h2 className="flex items-center gap-2.5 font-heading text-lg font-bold text-ink-900">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg text-cream-50" style={{ background: accent }}>{icon}</span>
            {title}
          </h2>
          <div className="mt-3">{children}</div>
        </div>
      </div>
    </section>
  );
}

export function HelpPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t, tl } = useI18n();

  return (
    <div className="space-y-4">
      <PageHeader title={t("help.title")} subtitle={t("help.subtitle")} />

      {/* 1. Emergency */}
      <Section accent="#A84A3A" icon={<IconAlert className="h-4 w-4" />} title={t("help.urgentTitle")}>
        <p className="font-body text-sm text-ink-700">{t("helpX.urgentShort")}</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <a href="tel:1930" className="btn-press flex items-center justify-center gap-2 rounded-xl bg-rust-500 px-3 py-3 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-rust-600">
            <IconPhone className="h-4 w-4" /> {t("helpX.call")}
          </a>
          <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="btn-press flex items-center justify-center gap-2 rounded-xl border-2 border-rust-300 bg-cream-50 px-3 py-3 font-body text-sm font-bold text-rust-600">
            <IconGlobe className="h-4 w-4" /> {t("helpX.report")}
          </a>
        </div>
        <p className="mt-2.5 font-body text-xs text-dustyblue-600">{t("help.bankNote")}</p>
      </Section>

      {/* 2. Talk to a person */}
      <Section accent="#647A4F" icon={<IconChat className="h-4 w-4" />} title={t("chat.title")} delay={60}>
        <p className="font-body text-xs font-semibold text-sage-700">{t("chat.unknown")}</p>
        <p className="mt-2 font-body text-sm text-ink-700">{t("chat.intro")}</p>
        <button
          onClick={() => openHelper("home")}
          className="btn-press mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-sage-500 px-4 py-3 font-body text-base font-bold text-cream-50 shadow-warm-sm hover:bg-sage-600"
        >
          <IconChat className="h-5 w-5" /> {t("chat.askAi")}
        </button>
        <button onClick={() => openHelper("person")} className="mt-2 w-full text-center font-body text-sm font-semibold text-sage-700 underline underline-offset-2">
          {t("chat.start")}
        </button>
        <p className="mt-2.5 flex items-center gap-1.5 font-body text-xs text-dustyblue-600">
          <IconLock className="h-3.5 w-3.5 shrink-0" /> {t("chat.never")}
        </p>
      </Section>

      {/* 3. What we help with */}
      <Section accent="#54707B" icon={<IconCheck className="h-4 w-4" />} title={t("help.canHelpTitle")} delay={120}>
        <ul className="space-y-2">
          {tl("help.topics").map((topic) => (
            <li key={topic} className="flex items-start gap-2.5 font-body text-sm text-ink-800">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-sage-100 text-sage-600"><IconCheck className="h-3 w-3" /></span>
              {topic}
            </li>
          ))}
        </ul>
      </Section>

      {/* 4. Do it yourself */}
      <div className="grid gap-3 sm:grid-cols-2 animate-fade-up" style={{ animationDelay: "180ms" }}>
        <button onClick={() => onNavigate("/incident")} className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rust-400/15 text-rust-500"><IconAlert className="h-5 w-5" /></span>
          <span className="min-w-0 flex-1">
            <span className="block font-body text-sm font-bold text-ink-800">{t("help.clickedTitle")}</span>
            <span className="block font-body text-xs text-dustyblue-600">{t("help.clickedText")}</span>
          </span>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
        <button onClick={() => onNavigate("/scam-library")} className="btn-press card-hover flex items-center gap-3 rounded-2xl bg-cream-50 p-4 text-left shadow-warm">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sage-100 text-sage-600"><IconBook className="h-5 w-5" /></span>
          <span className="min-w-0 flex-1">
            <span className="block font-body text-sm font-bold text-ink-800">{t("help.learnTitle")}</span>
            <span className="block font-body text-xs text-dustyblue-600">{t("help.learnText")}</span>
          </span>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
      </div>

      {/* 5. Promise */}
      <div className="flex items-start gap-3 rounded-2xl bg-dustyblue-100 p-4">
        <IconLock className="mt-0.5 h-5 w-5 shrink-0 text-dustyblue-600" />
        <p className="font-body text-sm text-dustyblue-600"><b className="text-ink-800">{t("help.promiseTitle")}.</b> {t("help.promise")}</p>
      </div>

      <p className="text-center font-body text-xs text-dustyblue-500">{t("help.footer")}</p>
    </div>
  );
}
