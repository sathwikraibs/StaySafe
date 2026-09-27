import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { IncidentOption, IncidentPlanResponse } from "@/types";
import { IconArrowRight, IconCheck, IconAlert, IconPhone, IconGlobe } from "@/icons";
import { ChatCard } from "@/components/ChatWidgets";

/** Always-visible emergency actions: 1930 helpline + national cyber crime portal. */
function UrgentActions() {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <a
        href="tel:1930"
        className="btn-press flex items-center justify-center gap-2 rounded-2xl bg-rust-500 px-4 py-3.5 font-body text-[15px] font-bold text-cream-50 sm:text-base shadow-warm hover:bg-rust-600"
      >
        <IconPhone className="h-5 w-5" /> Lost money? Call 1930
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
  );
}

export function IncidentPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
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
        <PageHeader title="I Clicked a Scam" subtitle="Don't panic. Let's make a plan to fix it together, step by step." />
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
              <p className="font-heading text-xl font-bold">It happens to the best of us</p>
              <p className="mt-2 font-body text-base text-cream-50/90">
                Clicked a link, shared an OTP, installed an app or paid someone you don't trust?
                Acting in the next few minutes matters most.
              </p>
            </div>
          </div>
          <button
            onClick={loadOptions}
            className="btn-press mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-6 py-4 font-body text-lg font-bold text-rust-600 shadow-warm transition-colors hover:bg-cream-100"
          >
            Let's make a plan <IconArrowRight className="h-5 w-5" />
          </button>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "80ms" }}>
          <UrgentActions />
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "140ms" }}>
          <ChatCard title="Scared or confused? Talk to us" compact />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="I Clicked a Scam" subtitle="Pick what happened and we will give you a step-by-step plan." />

      {(loadingOptions || loadingPlan) && <LoadingBreath label="Putting together a plan for you..." />}
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
              <span className="flex-1 font-body text-base font-semibold text-ink-800">{opt.label}</span>
              <IconArrowRight className="h-5 w-5 text-dustyblue-400" />
            </button>
          ))}
          <div className="pt-3">
            <ChatCard title="Not listed here? Tell us what happened" compact />
          </div>
        </div>
      )}

      {plan && (
        <div className="space-y-4 animate-fade-up">
          <Card className="p-5">
            <p className="font-body text-sm text-dustyblue-600">Your plan for</p>
            <h2 className="mt-1 font-heading text-xl font-semibold text-ink-900">{plan.label}</h2>
          </Card>

          <div className="space-y-3">
            {plan.action_plan.map((step, i) => (
              <div
                key={i}
                className="flex items-start gap-4 rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-sage-200 text-sage-700">
                  <span className="font-heading text-sm font-bold">{i + 1}</span>
                </div>
                <p className="flex-1 pt-1.5 font-body text-base text-ink-800">{step}</p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl bg-sage-100 p-5">
            <div className="flex items-center gap-2 text-sage-700">
              <IconCheck className="h-5 w-5" />
              <p className="font-heading text-base font-semibold">You can do this</p>
            </div>
            <p className="mt-2 font-body text-sm text-sage-600">
              Take it one step at a time. If you need help from someone you trust, do not hesitate to ask them.
            </p>
          </div>

          <UrgentActions />

          <ChatCard title="Still worried? Talk to a real person" compact />

          <Button onClick={() => { setPlan(null); setSelected(null); }} variant="outline" fullWidth>
            Pick a different situation
          </Button>
          {onNavigate && (
            <button
              onClick={() => onNavigate("/help")}
              className="w-full text-center font-body text-sm font-semibold text-sage-600 underline-offset-4 hover:underline"
            >
              More ways to get help
            </button>
          )}
        </div>
      )}
    </div>
  );
}
