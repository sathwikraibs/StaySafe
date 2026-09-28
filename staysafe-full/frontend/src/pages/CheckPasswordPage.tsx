import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { CheckPasswordResponse } from "@/types";
import { useI18n } from "@/i18n";
import { EmailLeakCheck } from "@/components/EmailLeakCheck";

/** Big coloured strength bar: Weak / Moderate / Strong. */
function StrengthBar({ result }: { result: CheckPasswordResponse }) {
  const { t } = useI18n();
  const score = result.strength_score ?? 100 - result.risk_score;
  const label = result.strength_label;
  const color = label === "Strong" ? "bg-sage-500" : label === "Moderate" ? "bg-terracotta-400" : "bg-rust-500";
  const text = label === "Strong" ? "text-sage-700" : label === "Moderate" ? "text-terracotta-700" : "text-rust-600";
  return (
    <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600">{t("password.strength")}</p>
          <p className={`mt-1 font-heading text-xl font-bold ${text}`}>{t(`password.labels.${label}`)}</p>
        </div>
        {result.breached !== null && result.breached !== undefined && (
          <div className="text-right">
            <p className="font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600">{t("password.leaks")}</p>
            <p className={`mt-1 font-heading text-xl font-bold ${result.breached ? "text-rust-600" : "text-sage-700"}`}>
              {result.breached ? t("password.foundIn", { count: result.breach_count.toLocaleString("en-IN") }) : t("password.notFound")}
            </p>
          </div>
        )}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-1.5">
        {[0, 1, 2].map((i) => {
          const filled = label === "Strong" ? 3 : label === "Moderate" ? 2 : 1;
          return <div key={i} className={`h-2.5 rounded-full ${i < filled ? color : "bg-cream-200"}`} />;
        })}
      </div>
      <p className="mt-2 font-body text-xs text-dustyblue-600">{t("pwInfo.score", { score })}</p>
    </div>
  );
}

export function CheckPasswordPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const pace = usePace();
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckPasswordResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!password || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await pace("password", apiPostJSON<CheckPasswordResponse>(`${API_BASE}/api/check-password`, { password }));
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <ToolHeader path="/check-password" title={t("password.title")} subtitle={t("password.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("password.label")}</label>
        <div className="relative">
          <input
            type={show ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleCheck(); }}
            placeholder={t("password.placeholder")}
            autoComplete="off"
            className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3.5 pr-24 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
          />
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="btn-press absolute right-3 top-1/2 -translate-y-1/2 rounded-lg px-3 py-1.5 font-body text-xs font-semibold text-dustyblue-600 hover:bg-cream-200"
          >
            {show ? t("password.hide") : t("password.show")}
          </button>
        </div>
        <p className="mt-3 font-body text-xs text-dustyblue-600">{t("password.note")}</p>
        <p className="mt-2 rounded-xl bg-dustyblue-100 px-3 py-2 font-body text-xs text-dustyblue-600">{t("password.tip")}</p>
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !password} fullWidth>
            {loading ? t("common.checking") : t("password.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="password" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="password"
          verdict={result.verdict}
          riskScore={result.risk_score}
          parts={result.score_parts}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <StrengthBar result={result} />
        </ResultReport>
      )}

      <EmailLeakCheck />
    </div>
  );
}
