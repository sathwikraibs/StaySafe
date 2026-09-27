import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { IncidentOption, IncidentPlanResponse } from "@/types";
import { IconArrowRight, IconCheck, IconAlert, IconPhone, IconGlobe } from "@/icons";
import { ChatCard } from "@/components/ChatWidgets";
import { useI18n } from "@/i18n";
import { STEP_RESOURCES, type Resource } from "@/incidentResources";

/** One official link under a recovery step: name, what it does, and a clear button. */
function ResourceLink({ res }: { res: Resource }) {
  const { t } = useI18n();
  const button =
    res.kind === "download" ? t("resources.download") :
    res.kind === "call" ? t("resources.call") :
    res.kind === "report" ? t("resources.report") :
    res.kind === "guide" ? t("resources.guide") : t("resources.open");
  const btnCls =
    res.kind === "download" ? "bg-sage-500 hover:bg-sage-600 text-cream-50" :
    res.kind === "call" || res.kind === "report" ? "bg-rust-500 hover:bg-rust-600 text-cream-50" :
    "bg-dustyblue-500 hover:bg-dustyblue-600 text-cream-50";
  const external = !res.url.startsWith("tel:");
  return (
    <a
      href={res.url}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="btn-press card-hover flex items-center gap-3 rounded-xl border-2 border-cream-200 bg-cream-50 p-3 hover:border-sage-300"
    >
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-1.5 font-body text-sm font-bold text-ink-900">
          <span className="break-words">{res.name}</span>
          {res.platform && (
            <span className="rounded-full bg-dustyblue-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-dustyblue-600">
              {t(`resources.${res.platform}`)}
            </span>
          )}
          {res.govt && (
            <span className="rounded-full bg-sage-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-sage-700">
              {t("resources.govt")}
            </span>
          )}
        </p>
        <p className="mt-0.5 font-body text-xs text-ink-700">{t(`resources.desc.${res.desc}`)}</p>
      </div>
      <span className={`shrink-0 rounded-xl px-3 py-2 font-body text-xs font-bold shadow-warm-sm ${btnCls}`}>{button}</span>
    </a>
  );
}

/** Always-visible emergency actions: 1930 helpline + national cyber crime portal. */
function UrgentActions() {
  const { t } = useI18n();
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <a
        href="tel:1930"
        className="btn-press flex items-center justify-center gap-2 rounded-2xl bg-rust-500 px-4 py-3.5 font-body text-[15px] font-bold text-cream-50 sm:text-base shadow-warm hover:bg-rust-600"
      >
        <IconPhone className="h-5 w-5 shrink-0" /> {t("incident.call1930")}
      </a>
      <a
        href="https://cybercrime.gov.in"
        target="_blank"
        rel="noopener noreferrer"
        className="btn-press flex items-center justify-center gap-2 rounded-2xl border-2 border-rust-400 bg-cream-50 px-4 py-3.5 font-body text-[15px] font-bold text-rust-600 sm:text-base hover:bg-rust-400/10"
      >
        <IconGlobe className="h-5 w-5 shrink-0" /> {t("incident.report")}
      </a>
    </div>
  );
}

export function IncidentPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, content } = useI18n();
  // Recovery plans come from the server in English; swap in the translated version by id
  const optionLabel = (opt: IncidentOption) => content?.incidents[opt.id]?.label ?? opt.label;
  const planLabel = (p: IncidentPlanResponse) => content?.incidents[p.incident_type]?.label ?? p.label;
  const planSteps = (p: IncidentPlanResponse) => content?.incidents[p.incident_type]?.steps ?? p.action_plan;
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [options, setOptions] = useState<IncidentOption[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [plan, setPlan] = useState<IncidentPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadOptions() {
    setLoadingOptions(true); setError(null);
    try {
      const data = await apiGet<{ options: IncidentOption[] }>(`${API_BASE}/api/incident-options`);
      setOptions(data.options);
    } catch (e) { setError(errorMessage(e)); } finally { setLoadingOptions(false); }
  }

  async function getPlan(id: string) {
    setSelected(id);
    setLoadingPlan(true); setError(null); setPlan(null);
    try {
      const data = await apiPostJSON<IncidentPlanResponse>(`${API_BASE}/api/incident-plan`, { incident_type: id });
      setPlan(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoadingPlan(false); }
  }

  if (!options && !loadingOptions && !error) {
    return (
      <div className="space-y-5">
        <PageHeader title={t("incident.title")} subtitle={t("incident.subtitle")} />
        <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-rust-500 to-rust-600 p-6 text-cream-50 shadow-warm-lg animate-fade-up sm:p-8">
          <div className="flex items-start gap-4">
            <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20">
              <IconAlert className="h-8 w-8" />
              <span className="absolute -right-1 -top-1 flex h-3.5 w-3.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cream-50 opacity-75" />
                <span className="relative inline-flex h-3.5 w-3.5 rounded-full bg-cream-50" />
              </span>
            </div>
            <div>
              <p className="font-heading text-xl font-bold">{t("incident.heroTitle")}</p>
              <p className="mt-2 font-body text-base text-cream-50/90">
                {t("incident.heroText")}
              </p>
            </div>
          </div>
          <button
            onClick={loadOptions}
            className="btn-press mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-6 py-4 font-body text-lg font-bold text-rust-600 shadow-warm transition-colors hover:bg-cream-100"
          >
            {t("incident.makePlan")} <IconArrowRight className="h-5 w-5" />
          </button>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <UrgentActions />
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "140ms" }}>
          <ChatCard title={t("incident.chatScared")} compact />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={t("incident.title")} subtitle={t("incident.subtitlePick")} />

      {(loadingOptions || loadingPlan) && <LoadingSteps tool="incident" />}
      {error && <ErrorNotice>{error}</ErrorNotice>}

      {options && !loadingOptions && !plan && (
        <div className="space-y-3">
          {options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => getPlan(opt.id)}
              className="btn-press card-hover flex w-full items-center gap-4 rounded-2xl bg-cream-50 p-5 text-left shadow-warm"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-terracotta-300/30 text-terracotta-600">
                <IconAlert className="h-5 w-5" />
              </div>
              <span className="flex-1 font-body text-base font-semibold text-ink-800">{optionLabel(opt)}</span>
              <IconArrowRight className="h-5 w-5 text-dustyblue-400" />
            </button>
          ))}
          <div className="pt-3">
            <ChatCard title={t("incident.chatNotListed")} compact />
          </div>
        </div>
      )}

      {plan && (
        <div className="space-y-4 animate-fade-up">
          <Card className="p-5">
            <p className="font-body text-sm text-dustyblue-600">{t("incident.planFor")}</p>
            <h2 className="mt-1 font-heading text-xl font-semibold text-ink-900">{planLabel(plan)}</h2>
          </Card>

          <div className="space-y-3">
            {planSteps(plan).map((step, i) => {
              const resources = STEP_RESOURCES[plan.incident_type]?.[i] ?? [];
              return (
                <div
                  key={i}
                  className="rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-sage-200 text-sage-700">
                      <span className="font-heading text-sm font-bold">{i + 1}</span>
                    </div>
                    <p className="flex-1 pt-1.5 font-body text-base text-ink-800">{step}</p>
                  </div>
                  {resources.length > 0 && (
                    <div className="mt-4 space-y-2 sm:pl-[3.25rem]">
                      {resources.map((res) => <ResourceLink key={res.url} res={res} />)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p className="rounded-xl bg-dustyblue-100 px-4 py-3 font-body text-xs text-dustyblue-600">{t("resources.note")}</p>

          <div className="rounded-2xl bg-sage-100 p-5">
            <div className="flex items-center gap-2 text-sage-700">
              <IconCheck className="h-5 w-5" />
              <p className="font-heading text-base font-semibold">{t("incident.youCan")}</p>
            </div>
            <p className="mt-2 font-body text-sm text-sage-600">
              {t("incident.youCanText")}
            </p>
          </div>

          <UrgentActions />

          <ChatCard title={t("incident.chatStillWorried")} compact />

          <Button onClick={() => { setPlan(null); setSelected(null); }} variant="outline" fullWidth>
            {t("incident.pickOther")}
          </Button>
          {onNavigate && (
            <button
              onClick={() => onNavigate("/help")}
              className="w-full text-center font-body text-sm font-semibold text-sage-600 underline-offset-4 hover:underline"
            >
              {t("incident.moreHelp")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
