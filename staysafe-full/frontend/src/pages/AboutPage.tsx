import { PageHeader } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { useI18n } from "@/i18n";
import { IconShield, IconCheck, IconLock, IconWarning, IconChat, IconSearch } from "@/icons";
import { Section } from "@/components/Section";

export function AboutPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const { t, tl } = useI18n();

  return (
    <div className="space-y-5">
      <PageHeader title={t("about.title")} subtitle={t("about.subtitle")} />

      <Card className="p-5 sm:p-6">
        <div className="mb-2 flex items-center gap-2">
          <IconShield className="h-5 w-5 text-brand-600" />
          <h2 className="font-heading text-lg font-semibold text-ink-900">{t("about.whatTitle")}</h2>
        </div>
        <p className="font-body text-sm leading-relaxed text-ink-700">{t("about.what")}</p>
      </Card>

      <Card className="p-5 sm:p-6">
        <h2 className="font-heading text-lg font-semibold text-ink-900">{t("about.stepsTitle")}</h2>
        <ol className="mt-3 space-y-3">
          {tl("about.steps").map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-500 font-heading text-sm font-bold text-cream-50">{i + 1}</span>
              <span className="pt-0.5 font-body text-sm leading-relaxed text-ink-800">{step}</span>
            </li>
          ))}
        </ol>
        <p className="mt-4 rounded-xl bg-cream-100 p-3 font-body text-sm leading-relaxed text-ink-700">{t("about.how")}</p>
      </Card>

      <Section icon={<IconSearch className="h-5 w-5" />} title={t("about.toolsTitle")} tone="info">
        <dl className="space-y-3">
          {(["link", "message", "qr", "file", "email", "password", "network"] as const).map((k) => (
            <div key={k}>
              <dt className="font-heading text-sm font-bold text-ink-900">{t(`report.toolName.${k}`)}</dt>
              <dd className="mt-0.5 font-body text-sm text-ink-700">{t(`about.tools.${k}`)}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <div className="flex items-start gap-3 rounded-2xl border-2 border-terracotta-300 bg-terracotta-300/20 p-5">
        <IconWarning className="mt-0.5 h-5 w-5 shrink-0 text-terracotta-600" />
        <div>
          <p className="font-heading text-base font-semibold text-terracotta-700">{t("about.notGuaranteeTitle")}</p>
          <p className="mt-1 font-body text-sm text-ink-700">{t("about.notGuarantee")}</p>
        </div>
      </div>

      <Card className="p-5 sm:p-6">
        <div className="mb-3 flex items-center gap-2">
          <IconLock className="h-5 w-5 text-brand-600" />
          <h2 className="font-heading text-lg font-semibold text-ink-900">{t("about.dataTitle")}</h2>
        </div>
        <ul className="space-y-2.5">
          {tl("about.dataItems").map((item) => (
            <li key={item} className="flex items-start gap-2.5 font-body text-sm text-ink-700">
              <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </Card>

      <div className="rounded-2xl bg-brand-100 p-5">
        <p className="font-heading text-base font-semibold text-brand-700">{t("about.neverTitle")}</p>
        <p className="mt-1 font-body text-sm text-brand-700">{t("about.never")}</p>
      </div>

      <button
        onClick={() => onNavigate("/help")}
        className="btn-press card-hover flex w-full items-center gap-3 rounded-2xl bg-cream-50 p-5 text-left shadow-warm"
      >
        <IconChat className="h-5 w-5 shrink-0 text-brand-600" />
        <span className="flex-1">
          <span className="block font-body text-base font-semibold text-ink-800">{t("about.contactTitle")}</span>
          <span className="block font-body text-sm text-dustyblue-600">{t("about.contact")}</span>
        </span>
      </button>
    </div>
  );
}
