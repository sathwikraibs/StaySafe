import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanQrResponse } from "@/types";
import { useI18n } from "@/i18n";

export function ScanQrPage() {
  const { t } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanQrResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const data = await apiPostForm<ScanQrResponse>(`${API_BASE}/api/scan-qr`, fd);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <PageHeader title={t("qr.title")} subtitle={t("qr.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <UploadZone
          accept="image/*"
          label={t("qr.uploadLabel")}
          hint={t("qr.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={handleCheck} disabled={loading} fullWidth>
              {loading ? t("common.checking") : t("qr.button")}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingBreath label={t("qr.loading")} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          {result.raw_data && (
            <Card className="p-4">
              <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">{t("qr.contains")}</p>
              <p className="mt-1 break-words font-body text-sm text-ink-800">{result.raw_data}</p>
              {result.qr_type && (
                <p className="mt-2 font-body text-xs text-dustyblue-600">{t("qr.type", { type: t(`qr.types.${result.qr_type}`).startsWith("qr.") ? result.qr_type : t(`qr.types.${result.qr_type}`) })}</p>
              )}
            </Card>
          )}
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
