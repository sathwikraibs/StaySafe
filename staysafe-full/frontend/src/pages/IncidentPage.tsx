import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, apiPostJSON, NETWORK_ERROR_MSG } from "@/api";
import { API_BASE } from "@/config";
import type { IncidentOption, IncidentPlanResponse } from "@/types";
import { IconArrowRight, IconCheck, IconAlert } from "@/icons";

export function IncidentPage() {
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
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoadingOptions(false); }
  }

  async function getPlan(id: string) {
    setSelected(id);
    setLoadingPlan(true); setError(null); setPlan(null);
    try {
      const data = await apiPostJSON<IncidentPlanResponse>(`${API_BASE}/api/incident-plan`, { incident_type: id });
      setPlan(data);
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoadingPlan(false); }
  }

  if (!options && !loadingOptions && !error) {
    return (
      <div>
        <PageHeader title="I Clicked a Scam" subtitle="Don't worry. Let's make a plan to fix it together, step by step." />
        <div className="rounded-2xl bg-gradient-to-br from-terracotta-300/30 to-cream-100 p-8 text-center shadow-warm">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-terracotta-300/40 text-terracotta-600">
            <IconAlert className="h-8 w-8" />
          </div>
          <p className="mb-2 font-heading text-lg font-semibold text-ink-800">It happens to the best of us</p>
          <p className="mb-5 font-body text-base text-ink-700/80">
            If you clicked something or gave information to someone you do not trust,
            we can help. Tap below to see what kind of thing happened.
          </p>
          <Button onClick={loadOptions}>Let's make a plan</Button>
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

          <Button onClick={() => { setPlan(null); setSelected(null); }} variant="outline" fullWidth>
            Pick a different situation
          </Button>
        </div>
      )}
    </div>
  );
}
