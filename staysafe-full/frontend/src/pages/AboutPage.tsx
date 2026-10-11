import { PageHeader } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { useI18n } from "@/i18n";
import { IconShield, IconCheck, IconLock, IconWarning, IconChat, IconSearch } from "@/icons";
import { Section } from "@/components/Section";

/** Fill in the project number from bestpractices.dev once the badge is earned; the row appears then. */
const OPENSSF_PROJECT = "";
const CODE_URL = "https://github.com/sathwikraibs/StaySafe";

/** Independent checks anyone can open to see the live result for this website. */
function independentChecks(host: string) {
  const h = encodeURIComponent(host);
  const rows: { key: string; url: string }[] = [
    { key: "security", url: `https://developer.mozilla.org/en-US/observatory/analyze?host=${h}` },
    { key: "connection", url: `https://www.ssllabs.com/ssltest/analyze.html?d=${h}&hideResults=on` },
    { key: "safe", url: `https://transparencyreport.google.com/safe-browsing/search?url=${h}` },
    { key: "code", url: CODE_URL },
  ];
  if (OPENSSF_PROJECT) rows.push({ key: "openssf", url: `https://www.bestpractices.dev/projects/${OPENSSF_PROJECT}` });
  return rows;
}

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

      <Card className="p-5 sm:p-6">
        <div className="mb-1 flex items-center gap-2">
          <IconCheck className="h-5 w-5 text-sage-600" />
          <h2 className="font-heading text-lg font-semibold text-ink-900">{t("about.verifiedTitle")}</h2>
        </div>
        <p className="mb-3 font-body text-sm text-ink-700">{t("about.verifiedIntro")}</p>
        <ul className="divide-y divide-cream-200">
          {independentChecks(typeof window !== "undefined" ? window.location.hostname : "").map(({ key, url }) => (
            <li key={key}>
              <a href={url} target="_blank" rel="noopener noreferrer"
                className="group flex items-center gap-3 py-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 rounded-lg">
                <span className="min-w-0 flex-1">
                  <span className="block font-body text-sm font-semibold text-ink-900 group-hover:text-brand-700">{t(`about.verified.${key}.name`)}</span>
                  <span className="block font-body text-xs text-dustyblue-600">{t(`about.verified.${key}.desc`)}</span>
                </span>
                <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-dustyblue-500 group-hover:text-brand-600" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
                </svg>
              </a>
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
