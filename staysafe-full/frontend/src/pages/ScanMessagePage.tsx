import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { apiPostJSON, apiPostForm, NETWORK_ERROR_MSG } from "@/api";
import { API_BASE } from "@/config";
import type { ScanMessageResponse } from "@/types";

export function ScanMessagePage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanMessageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheckText() {
    if (!text.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanMessageResponse>(`${API_BASE}/api/scan-message`, { text: text.trim() });
      setResult(data);
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoading(false); }
  }

  async function handleCheckScreenshot() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const data = await apiPostForm<ScanMessageResponse>(`${API_BASE}/api/scan-screenshot`, fd);
      setResult(data);
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoading(false); }
  }

  return (
    <div>
      <PageHeader title="Check a Message" subtitle="Paste a text message or upload a screenshot of a message you received." />

      {/* Text tab */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">Paste the message text</h3>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          placeholder="Paste the message here..."
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400 scrollbar-warm"
        />
        <div className="mt-4">
          <Button onClick={handleCheckText} disabled={loading || !text.trim()} fullWidth>
            {loading ? "Checking..." : "Check this message"}
          </Button>
        </div>
      </div>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-cream-200" />
        <span className="font-body text-sm text-dustyblue-500">or</span>
        <div className="h-px flex-1 bg-cream-200" />
      </div>

      {/* Screenshot tab */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">Upload a screenshot</h3>
        <UploadZone
          accept="image/*"
          label="Tap to choose a screenshot"
          hint="A photo of the message on your screen works too"
          onFile={setFile}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={handleCheckScreenshot} disabled={loading} fullWidth>
              {loading ? "Checking..." : "Check this screenshot"}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingBreath label="Reading the message carefully..." />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <FindingsList items={result.patterns_detected} title="Patterns we noticed" />
        </div>
      )}
    </div>
  );
}
