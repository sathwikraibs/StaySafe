import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostForm, apiPostJSON, errorMessage } from "@/api";
import { QrCameraScanner } from "@/components/QrCameraScanner";
import { API_BASE } from "@/config";
import type { ScanQrResponse } from "@/types";
import { useI18n } from "@/i18n";
import { LinkDetails } from "@/components/WebsiteDetails";
import { IconQr, IconCamera } from "@/icons";

export function ScanQrPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
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
      const data = await apiPostForm<ScanQrResponse>(`${API_BASE}/api/scan-qr`, fd);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  // The phone read the QR code itself: only its contents are sent to be checked
  async function checkText(text: string) {
    setCamera(false);
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanQrResponse>(`${API_BASE}/api/scan-qr-text`, { data: text });
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
      ) : (
        <button
          onClick={() => { setResult(null); setError(null); setCamera(true); }}
          disabled={loading}
          className="btn-press card-hover mb-4 flex w-full items-center gap-4 rounded-2xl bg-gradient-to-br from-[#A283B0] to-[#6E4E7C] p-5 text-left text-cream-50 shadow-warm-lg disabled:opacity-60"
        >
          <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20"><IconCamera className="h-7 w-7" /></span>
          <span className="min-w-0">
            <span className="block font-heading text-lg font-bold">{t("qrCam.open")}</span>
            <span className="block font-body text-sm text-cream-50/85">{t("qrCam.openHint")}</span>
          </span>
        </button>
      )}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
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
            <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
              <div className="flex items-center gap-2">
                <IconQr className="h-5 w-5 text-dustyblue-600" />
                <h3 className="font-heading text-lg font-semibold text-ink-900">{t("qr.contains")}</h3>
                {result.qr_type && (
                  <span className="ml-auto rounded-full bg-cream-50 px-2.5 py-1 font-body text-xs font-bold text-dustyblue-600">
                    {typeLabel(result.qr_type)}
                  </span>
                )}
              </div>
              <p className="mt-3 break-all rounded-xl bg-cream-50 p-3 font-mono text-xs text-ink-800 sm:text-sm">{result.raw_data}</p>
            </div>
          )}
          {result.qr_type === "url" && <LinkDetails details={result.details} />}
        </ResultReport>
      )}
    </div>
  );
}
