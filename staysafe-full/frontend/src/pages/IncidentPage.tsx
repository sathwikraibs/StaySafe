import { useEffect, useState, type ComponentType } from "react";
import { PageHeader } from "@/components/PageBits";
import {
  IconArrowRight, IconArrowLeft, IconCheck, IconAlert, IconPhone, IconGlobe, IconLink, IconKey, IconLock,
  IconMessage, IconFile, IconNetwork, IconShield, IconChat, IconChevronRight,
} from "@/icons";
import { openHelper } from "@/chat";
import { useI18n } from "@/i18n";
import { STEP_RESOURCES, type Resource } from "@/incidentResources";
import { INCIDENT_PLANS_EN } from "@/incidentPlans";

const INCIDENT_ICONS: Record<string, ComponentType<{ className?: string }>> = {
  clicked_link: IconLink, entered_password: IconKey, entered_card_details: IconLock, shared_otp: IconMessage,
  installed_app: IconFile, gave_remote_access: IconNetwork, money_transferred: IconAlert, account_accessed: IconShield,
};
/** Money-related situations: 1930 comes first */
const MONEY = new Set(["entered_card_details", "shared_otp", "money_transferred", "gave_remote_access"]);

/** One official link: small icon, name, what it does, and a clear action. */
function ResourceRow({ res }: { res: Resource }) {
  const { t } = useI18n();
  const button =
    res.kind === "download" ? t("resources.download") :
    res.kind === "call" ? t("resources.call") :
    res.kind === "report" ? t("resources.report") :
    res.kind === "guide" ? t("resources.guide") : t("resources.open");
  const tone =
    res.kind === "download" ? "bg-brand-500 text-cream-50" :
    res.kind === "call" || res.kind === "report" ? "bg-rust-500 text-cream-50" : "bg-dustyblue-500 text-cream-50";
  const external = !res.url.startsWith("tel:");
  return (
    <a
      href={res.url}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="btn-press flex items-center gap-3 rounded-xl bg-cream-100 px-3 py-2.5 hover:bg-cream-200"
    >
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-1.5 font-body text-sm font-bold text-ink-900">
          {res.name}
          {res.platform && <span className="rounded-full bg-cream-50 px-1.5 py-0.5 text-[10px] font-bold uppercase text-dustyblue-600">{t(`resources.${res.platform}`)}</span>}
          {res.govt && <span className="rounded-full bg-brand-200 px-1.5 py-0.5 text-[10px] font-bold uppercase text-brand-700">{t("resources.govt")}</span>}
        </p>
        <p className="font-body text-xs text-dustyblue-600">{t(`resources.desc.${res.desc}`)}</p>
      </div>
      <span className={`shrink-0 whitespace-nowrap rounded-lg px-2.5 py-1.5 font-body text-xs font-bold ${tone}`}>{button}</span>
    </a>
  );
}

/** One step of the plan: number, text, links, and a "Done" tick the person can set. */
function StepCard({ n, text, resources, done, onToggle, last }: {
  n: number; text: string; resources: Resource[]; done: boolean; onToggle: () => void; last: boolean;
}) {
  const { t } = useI18n();
  const [more, setMore] = useState(false);
  const shown = more ? resources : resources.slice(0, 2);
  return (
    <li className="relative flex gap-3 animate-fade-up" style={{ animationDelay: `${n * 60}ms` }}>
      {/* timeline */}
      <div className="flex flex-col items-center">
        <button
          onClick={onToggle}
          aria-pressed={done}
          className={`btn-press flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 font-heading text-sm font-bold transition-colors
            ${done ? "border-sage-500 bg-sage-500 text-cream-50" : "border-rust-400 bg-cream-50 text-rust-600"}`}
        >
          {done ? <IconCheck className="h-4 w-4" /> : n}
        </button>
        {!last && <span className={`w-0.5 flex-1 ${done ? "bg-sage-300" : "bg-cream-300"}`} />}
      </div>
      <div className={`mb-4 min-w-0 flex-1 rounded-2xl bg-cream-50 p-4 shadow-warm-sm transition-opacity ${done ? "opacity-60" : ""}`}>
        <p className={`font-body text-[15px] leading-snug text-ink-900 ${done ? "line-through decoration-sage-400" : ""}`}>{text}</p>
        {resources.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {shown.map((r) => <ResourceRow key={r.url} res={r} />)}
            {resources.length > 2 && !more && (
              <button onClick={() => setMore(true)} className="flex items-center gap-1 px-1 pt-1 font-body text-xs font-bold text-dustyblue-600">
                <IconChevronRight className="h-3.5 w-3.5" /> {t("incidentX.moreLinks", { n: resources.length - 2 })}
              </button>
            )}
          </div>
        )}
        <button onClick={onToggle} className={`mt-3 flex items-center gap-1.5 font-body text-xs font-bold ${done ? "text-sage-700" : "text-dustyblue-600"}`}>
          <span className={`flex h-4 w-4 items-center justify-center rounded border-2 ${done ? "border-sage-500 bg-sage-500 text-cream-50" : "border-dustyblue-300"}`}>
            {done && <IconCheck className="h-3 w-3" />}
          </span>
          {done ? t("incidentX.done") : t("incidentX.markDone")}
        </button>
      </div>
    </li>
  );
}

/** Slim emergency bar: call 1930 and report online. */
function UrgentBar() {
  const { t } = useI18n();
  return (
    <div className="grid grid-cols-2 gap-2">
      <a href="tel:1930" className="btn-press flex items-center justify-center gap-2 rounded-xl bg-rust-500 px-3 py-3 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-rust-600">
        <IconPhone className="h-4 w-4" /> {t("helpX.call")}
      </a>
      <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="btn-press flex items-center justify-center gap-2 rounded-xl border-2 border-rust-300 bg-cream-50 px-3 py-3 font-body text-sm font-bold text-rust-600">
        <IconGlobe className="h-4 w-4" /> {t("helpX.report")}
      </a>
    </div>
  );
}

export function IncidentPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, content } = useI18n();
  const [stage, setStage] = useState<"intro" | "pick" | "plan">("intro");
  const [planId, setPlanId] = useState<string | null>(null);
  const [done, setDone] = useState<Record<number, boolean>>({});

  useEffect(() => { window.scrollTo({ top: 0, behavior: "smooth" }); }, [stage, planId]);

  const plans = INCIDENT_PLANS_EN.map((p) => ({
    ...p,
    label: content?.incidents[p.id]?.label ?? p.label,
    steps: content?.incidents[p.id]?.steps ?? p.steps,
  }));
  const plan = plans.find((p) => p.id === planId) ?? null;

  if (stage === "intro") {
    return (
      <div className="space-y-4">
        <PageHeader title={t("incident.title")} subtitle={t("incident.subtitle")} />
        <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-rust-500 to-rust-600 p-6 text-cream-50 shadow-warm-lg animate-fade-up">
          <div className="flex items-start gap-4">
            <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20">
              <IconAlert className="h-7 w-7" />
              <span className="absolute -right-1 -top-1 flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cream-50 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-cream-50" />
              </span>
            </div>
            <div>
              <p className="font-heading text-xl font-bold">{t("incident.heroTitle")}</p>
              <p className="mt-1.5 font-body text-[15px] text-cream-50/90">{t("incident.heroText")}</p>
            </div>
          </div>
          <button
            onClick={() => setStage("pick")}
            className="btn-press mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-6 py-3.5 font-body text-lg font-bold text-rust-600 shadow-warm hover:bg-cream-100"
          >
            {t("incident.makePlan")} <IconArrowRight className="h-5 w-5" />
          </button>
        </div>
        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <p className="mb-2 px-1 font-body text-xs font-bold uppercase tracking-wide text-rust-600">{t("incidentX.lostMoney")}</p>
          <UrgentBar />
        </div>
        <button onClick={() => openHelper("home")} className="btn-press flex w-full items-center gap-3 rounded-2xl border-2 border-brand-300 bg-cream-50 p-4 text-left hover:bg-brand-100 disabled:opacity-60">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-500 text-cream-50"><IconChat className="h-5 w-5" /></span>
          <span className="min-w-0 flex-1">
            <span className="block font-body text-sm font-bold text-ink-900">{t("incident.chatScared")}</span>
            <span className="block font-body text-xs text-dustyblue-600">{t("chat.never")}</span>
          </span>
          <IconArrowRight className="h-4 w-4 text-dustyblue-400" />
        </button>
      </div>
    );
  }

  if (stage === "pick" || !plan) {
    return (
      <div>
        <PageHeader title={t("incident.title")} subtitle={t("incident.subtitlePick")} />
        <div className="grid gap-2.5 sm:grid-cols-2">
          {plans.map((opt, i) => {
            const Icon = INCIDENT_ICONS[opt.id] ?? IconAlert;
            return (
              <button
                key={opt.id}
                onClick={() => { setPlanId(opt.id); setDone({}); setStage("plan"); }}
                className="btn-press card-hover flex items-center gap-3.5 rounded-2xl bg-cream-50 p-4 text-left shadow-warm animate-fade-up"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rust-400/15 text-rust-600"><Icon className="h-5 w-5" /></span>
                <span className="min-w-0 flex-1 font-body text-[15px] font-semibold leading-snug text-ink-900">{opt.label}</span>
                <IconArrowRight className="h-5 w-5 shrink-0 text-dustyblue-400" />
              </button>
            );
          })}
        </div>
        <button onClick={() => openHelper("home")} className="btn-press mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-brand-300 bg-cream-50 px-4 py-3 font-body text-sm font-bold text-brand-700 disabled:opacity-60">
          <IconChat className="h-4 w-4" /> {t("incident.chatNotListed")}
        </button>
      </div>
    );
  }

  const count = plan.steps.length;
  const doneCount = plan.steps.filter((_, i) => done[i]).length;
  const Icon = INCIDENT_ICONS[plan.id] ?? IconAlert;
  return (
    <div>
      <button onClick={() => setStage("pick")} className="btn-press mb-4 flex items-center gap-2 font-body text-sm font-semibold text-dustyblue-600 hover:text-brand-600">
        <IconArrowLeft className="h-4 w-4" /> {t("incident.pickOther")}
      </button>

      {/* Plan header with progress */}
      <div className="mb-4 overflow-hidden rounded-3xl bg-gradient-to-br from-rust-500 to-rust-600 p-5 text-cream-50 shadow-warm-lg animate-fade-up">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cream-50/20"><Icon className="h-6 w-6" /></span>
          <div className="min-w-0">
            <p className="font-body text-xs font-bold uppercase tracking-wide text-cream-50/80">{t("incident.planFor")}</p>
            <h2 className="font-heading text-lg font-bold leading-snug">{plan.label}</h2>
          </div>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-cream-50/25">
            <div className="h-full rounded-full bg-cream-50 transition-[width] duration-500" style={{ width: `${(doneCount / count) * 100}%` }} />
          </div>
          <span className="shrink-0 font-body text-sm font-bold">{t("incidentX.progress", { done: doneCount, total: count })}</span>
        </div>
      </div>

      {MONEY.has(plan.id) && (
        <div className="mb-5">
          <p className="mb-2 px-1 font-body text-xs font-bold uppercase tracking-wide text-rust-600">{t("incidentX.firstThis")}</p>
          <UrgentBar />
        </div>
      )}

      <ol>
        {plan.steps.map((step, i) => (
          <StepCard
            key={i}
            n={i + 1}
            text={step}
            resources={STEP_RESOURCES[plan.id]?.[i] ?? []}
            done={Boolean(done[i])}
            onToggle={() => setDone((d) => ({ ...d, [i]: !d[i] }))}
            last={i === count - 1}
          />
        ))}
      </ol>

      {doneCount === count ? (
        <div className="mb-4 rounded-2xl bg-brand-600 p-5 text-cream-50 shadow-warm animate-fade-up">
          <p className="flex items-center gap-2 font-heading text-lg font-bold"><IconCheck className="h-5 w-5" /> {t("incidentX.allDone")}</p>
          <p className="mt-1 font-body text-sm text-cream-50/90">{t("incident.youCanText")}</p>
        </div>
      ) : (
        <div className="mb-4 rounded-2xl bg-sage-100 p-4">
          <p className="font-heading text-base font-semibold text-sage-700">{t("incident.youCan")}</p>
          <p className="mt-1 font-body text-sm text-sage-600">{t("incident.youCanText")}</p>
        </div>
      )}

      <p className="mb-4 rounded-xl bg-dustyblue-100 px-4 py-3 font-body text-xs text-dustyblue-600">{t("resources.note")}</p>

      <div className="grid gap-2.5 sm:grid-cols-2">
        {!MONEY.has(plan.id) && <div className="sm:col-span-2"><UrgentBar /></div>}
        <button onClick={() => openHelper("home")} className="btn-press flex items-center justify-center gap-2 rounded-2xl bg-brand-500 px-4 py-3 font-body text-sm font-bold text-cream-50 shadow-warm-sm disabled:opacity-60">
          <IconChat className="h-4 w-4" /> {t("incident.chatStillWorried")}
        </button>
        {onNavigate && (
          <button onClick={() => onNavigate("/help")} className="btn-press rounded-2xl border-2 border-brand-300 bg-cream-50 px-4 py-3 font-body text-sm font-bold text-brand-700">
            {t("incident.moreHelp")}
          </button>
        )}
      </div>
    </div>
  );
}
