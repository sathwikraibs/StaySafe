import { useState } from "react";
import { PageHeader } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { useI18n, LANGUAGES } from "@/i18n";
import { clearHistory, loadHistory } from "@/history";
import { IconCheck, IconLanguage, IconHistory, IconInfo, IconArrowRight, IconGlobe } from "@/icons";

export function SettingsPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t, lang, setLang } = useI18n();
  const [historyCount, setHistoryCount] = useState(() => loadHistory().length);
  const [cleared, setCleared] = useState(false);

  return (
    <div className="space-y-6">
      <PageHeader title={t("settings.title")} subtitle={t("settings.subtitle")} />

      {/* Language */}
      <Card className="p-5 sm:p-6">
        <div className="mb-1 flex items-center gap-2">
          <IconLanguage className="h-5 w-5 text-sage-600" />
          <h2 className="font-heading text-lg font-semibold text-ink-900">{t("settings.language")}</h2>
        </div>
        <p className="mb-4 font-body text-sm text-dustyblue-600">{t("settings.languageNote")}</p>

        <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label={t("settings.language")}>
          {LANGUAGES.map((l) => {
            const active = l.code === lang;
            return (
              <button
                key={l.code}
                role="radio"
                aria-checked={active}
                onClick={() => setLang(l.code)}
                lang={l.code}
                className={`btn-press relative flex flex-col items-start rounded-2xl border-2 p-4 pr-10 text-left transition-colors
                  ${active ? "border-sage-400 bg-sage-100" : "border-cream-200 bg-cream-50 hover:border-sage-300 hover:bg-cream-100"}`}
              >
                <span className="font-heading text-xl font-bold text-ink-900">{l.native}</span>
                <span className="mt-0.5 font-body text-xs font-semibold text-dustyblue-600">
                  {l.english}{l.beta ? " · beta" : ""}
                </span>
                {active && (
                  <span className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-sage-500 text-cream-50">
                    <IconCheck className="h-4 w-4" strokeWidth={3} />
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {lang === "tcy" && (
          <p className="mt-4 rounded-xl bg-terracotta-300/20 px-3 py-2 font-body text-xs text-terracotta-700">{t("settings.betaNote")}</p>
        )}

        <div className="mt-4 flex items-start gap-2 rounded-xl bg-dustyblue-100 p-3">
          <IconGlobe className="mt-0.5 h-4 w-4 shrink-0 text-dustyblue-500" />
          <div className="font-body text-xs text-dustyblue-600">
            <p className="font-semibold text-ink-800">{t("settings.otherLangs")}</p>
            <p className="mt-0.5">{t("settings.otherLangsText")}</p>
          </div>
        </div>
      </Card>

      {/* Data */}
      <Card className="p-5 sm:p-6">
        <div className="mb-1 flex items-center gap-2">
          <IconHistory className="h-5 w-5 text-sage-600" />
          <h2 className="font-heading text-lg font-semibold text-ink-900">{t("settings.data")}</h2>
        </div>
        <p className="mb-4 font-body text-sm text-dustyblue-600">{t("settings.dataText")}</p>
        <button
          onClick={() => { clearHistory(); setHistoryCount(0); setCleared(true); }}
          disabled={historyCount === 0}
          className="btn-press w-full rounded-2xl border-2 border-rust-400 bg-cream-50 px-5 py-3 font-body text-sm font-bold text-rust-600 hover:bg-rust-400/10 disabled:cursor-not-allowed disabled:border-cream-200 disabled:text-dustyblue-400"
        >
          {cleared ? t("settings.cleared") : t("settings.clear")}
        </button>
      </Card>

      {/* About */}
      <button
        onClick={() => onNavigate("/about")}
        className="btn-press card-hover flex w-full items-center gap-3 rounded-2xl bg-cream-50 p-5 text-left shadow-warm"
      >
        <IconInfo className="h-5 w-5 text-sage-600" />
        <span className="flex-1 font-body text-base font-semibold text-ink-800">{t("settings.about")}</span>
        <IconArrowRight className="h-5 w-5 text-dustyblue-400" />
      </button>
    </div>
  );
}
