import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanUrlResponse } from "@/types";
import { useI18n } from "@/i18n";
import { HiddenLinkGuide } from "@/components/HiddenLinkGuide";

export function ScanUrlPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiPostJSON<ScanUrlResponse>(`${API_BASE}/api/scan-url`, { url: url.trim() });
      setResult(data);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader title={t("url.title")} subtitle={t("url.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("url.label")}</label>
        <input
          type="url"
          inputMode="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
        />
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !url.trim()} fullWidth>
            {loading ? t("common.checking") : t("url.button")}
          </Button>
        </div>
      </div>

      <div className="mt-4">
        <HiddenLinkGuide onNavigate={onNavigate} showLinkButton={false} />
      </div>

      {loading && <LoadingBreath label={t("url.loading")} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
