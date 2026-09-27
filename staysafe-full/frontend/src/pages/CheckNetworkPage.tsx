import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiGet, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { CheckNetworkResponse } from "@/types";
import { IconNetwork } from "@/icons";

export function CheckNetworkPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckNetworkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiGet<CheckNetworkResponse>(`${API_BASE}/api/check-network`);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <PageHeader title="Check My Connection" subtitle="Check whether your internet connection is safe and secure." />
      <div className="rounded-2xl bg-gradient-to-br from-dustyblue-100 to-cream-100 p-8 shadow-warm text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-dustyblue-200 text-dustyblue-600">
          <IconNetwork className="h-8 w-8" />
        </div>
        <p className="mb-5 font-body text-base text-ink-700/80">
          We will check your current internet connection to see if it is protected and trustworthy.
        </p>
        <Button onClick={handleCheck} disabled={loading} variant="secondary">
          {loading ? "Checking..." : "Check my connection"}
        </Button>
      </div>

      {loading && <LoadingBreath label="Checking your connection..." />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <Card className="p-4">
            <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">Your connection</p>
            <div className="mt-2 space-y-1.5">
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">Internet provider: </span>{result.isp || "Unknown"}</p>
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">Location: </span>{result.location || "Unknown"}</p>
              <p className="font-body text-sm text-ink-800"><span className="text-dustyblue-600">Address: </span>{result.ip || "Unknown"}</p>
            </div>
          </Card>
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
