import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostForm, apiPostJSON, errorMessage } from "@/api";
import { QrCameraScanner } from "@/components/QrCameraScanner";
import { API_BASE } from "@/config";
import type { ScanQrResponse } from "@/types";
import { useI18n } from "@/i18n";
import { Section } from "@/components/Section";
import { LinkDetails } from "@/components/WebsiteDetails";
import { IconQr, IconCamera } from "@/icons";

export function ScanQrPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const pace = usePace();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanQrResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [camera, setCamera] = useState(false);

  async function handleCheck(photo?: File) {
    const img = photo ?? file;
    if (!img || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", img);
      const data = await pace("qr", apiPostForm<ScanQrResponse>(`${API_BASE}/api/scan-qr`, fd));
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  // The phone read the QR code itself: only its contents are sent to be checked
  async function checkText(text: string) {
    setCamera(false);
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await pace("qr", apiPostJSON<ScanQrResponse>(`${API_BASE}/api/scan-qr-text`, { data: text }));
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const typeLabel = (type: string) => {
    const key = `qr.types.${type}`;
    return t(key) === key ? type : t(key);
  };

  return (
    <div>
      <ToolHeader path="/scan-qr" title={t("qr.title")} subtitle={t("qr.subtitle")} />
      {camera ? (
        <div className="mb-4">
          <QrCameraScanner
            onText={checkText}
            onPhoto={(f) => { setCamera(false); setFile(f); handleCheck(f); }}
            onClose={() => setCamera(false)}
          />
        </div>
      ) : null}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        {!camera && (
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <p className="font-body text-sm text-ink-700">{t("qrCam.openHint")}</p>
            <button
              type="button"
              onClick={() => { setResult(null); setError(null); setCamera(true); }}
              disabled={loading}
              className="btn-press inline-flex items-center gap-2 rounded-full border-2 border-[#8C6A9B] bg-cream-50 px-4 py-2 font-body text-sm font-bold text-[#6E4E7C] hover:bg-[#8C6A9B]/10 disabled:opacity-60"
            >
              <IconCamera className="h-4 w-4" /> {t("qrCam.open")}
            </button>
          </div>
        )}
        <UploadZone
          accept="image/*"
          label={t("qr.uploadLabel")}
          camera={false}
          compress
          hint={t("qr.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={() => handleCheck()} disabled={loading} fullWidth>
              {loading ? t("common.checking") : t("qr.button")}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingSteps tool="qr" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="qr"
          verdict={result.verdict}
          riskScore={result.risk_score}
          parts={result.score_parts}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          {result.raw_data && (
            <Section icon={<IconQr className="h-5 w-5" />} title={t("qr.contains")} tone="info" defaultOpen
              summary={result.qr_type ? typeLabel(result.qr_type) : undefined}>
              <p className="break-all rounded-xl bg-cream-100 p-3 font-mono text-xs text-ink-800 sm:text-sm">{result.raw_data}</p>
            </Section>
          )}
          {result.qr_type === "url" && <LinkDetails details={result.details} />}
        </ResultReport>
      )}
    </div>
  );
}
