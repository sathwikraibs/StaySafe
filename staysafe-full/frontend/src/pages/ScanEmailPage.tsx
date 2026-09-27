import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanEmailResponse } from "@/types";
import { useI18n } from "@/i18n";

export function ScanEmailPage() {
  const { t } = useI18n();
  const [raw, setRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanEmailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!raw.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanEmailResponse>(`${API_BASE}/api/scan-email`, { raw_email: raw.trim() });
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

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

      {loading && <LoadingBreath label={t("email.loading")} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <Card className="p-4">
            <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">{t("email.details")}</p>
            <div className="mt-2 space-y-1.5">
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">{t("email.from")}</span>{result.from || t("common.unknown")}</p>
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">{t("email.replyTo")}</span>{result.reply_to || t("common.unknown")}</p>
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">{t("email.links")}</span>{result.links_found?.length || 0}</p>
            </div>
            {result.links_found && result.links_found.length > 0 && (
              <div className="mt-3 rounded-xl bg-cream-100 p-3">
                {result.links_found.map((link, i) => (
                  <p key={i} className="break-all font-body text-xs text-dustyblue-600">{link}</p>
                ))}
              </div>
            )}
          </Card>
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
