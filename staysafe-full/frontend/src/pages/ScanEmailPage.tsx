import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanEmailResponse } from "@/types";
import { useI18n } from "@/i18n";
import { IconEmail } from "@/icons";

export function ScanEmailPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const [raw, setRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanEmailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!raw.trim() || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanEmailResponse>(`${API_BASE}/api/scan-email`, { raw_email: raw.trim() });
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const label = "font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600";
  const value = "-mt-1.5 break-all font-body text-sm text-ink-800 sm:mt-0";

  return (
    <div>
      <PageHeader title={t("email.title")} subtitle={t("email.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("email.label")}</label>
        <textarea
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          rows={8}
          placeholder={t("email.placeholder")}
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-sm text-ink-800 outline-none transition-colors focus:border-sage-400 scrollbar-warm"
        />
        <p className="mt-3 font-body text-xs text-dustyblue-600">
          {t("email.tip")}
        </p>
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !raw.trim()} fullWidth>
            {loading ? t("common.checking") : t("email.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="email" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="email"
          verdict={result.verdict}
          riskScore={result.risk_score}
          subject={result.subject || undefined}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
            <div className="flex items-center gap-2">
              <IconEmail className="h-5 w-5 text-dustyblue-600" />
              <h3 className="font-heading text-lg font-semibold text-ink-900">{t("email.details")}</h3>
            </div>
            <dl className="mt-3 grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
              <dt className={label}>{t("emailInfo.from")}</dt>
              <dd className={value}>{result.from || t("common.unknown")}</dd>
              <dt className={label}>{t("emailInfo.replyTo")}</dt>
              <dd className={value}>{result.reply_to || t("emailInfo.same")}</dd>
              <dt className={label}>{t("emailInfo.links")}</dt>
              <dd className={value}>{result.links_found?.length || 0}</dd>
            </dl>
            {result.links_found && result.links_found.length > 0 && (
              <div className="mt-3 space-y-1 rounded-xl bg-cream-50 p-3">
                {result.links_found.map((link, i) => (
                  <p key={i} className="break-all font-mono text-xs text-dustyblue-600">{link}</p>
                ))}
              </div>
            )}
          </div>
        </ResultReport>
      )}
    </div>
  );
}
