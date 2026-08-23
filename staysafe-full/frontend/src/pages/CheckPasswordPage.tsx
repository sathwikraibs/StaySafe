import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiPostJSON, NETWORK_ERROR_MSG } from "@/api";
import { API_BASE } from "@/config";
import type { CheckPasswordResponse } from "@/types";

export function CheckPasswordPage() {
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckPasswordResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!password) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<CheckPasswordResponse>(`${API_BASE}/api/check-password`, { password });
      setResult(data);
    } catch { setError(NETWORK_ERROR_MSG); } finally { setLoading(false); }
  }

  return (
    <div>
      <PageHeader title="Check a Password" subtitle="See how strong your password is and whether it has been found in any known leaks." />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">Type a password</label>
        <div className="relative">
          <input
            type={show ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3.5 pr-24 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
          />
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="btn-press absolute right-3 top-1/2 -translate-y-1/2 rounded-lg px-3 py-1.5 font-body text-xs font-semibold text-dustyblue-600 hover:bg-cream-200"
          >
            {show ? "Hide" : "Show"}
          </button>
        </div>
        <p className="mt-3 font-body text-xs text-dustyblue-600">
          Your password is checked securely and is not stored anywhere.
        </p>
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !password} fullWidth>
            {loading ? "Checking..." : "Check this password"}
          </Button>
        </div>
      </div>

      {loading && <LoadingBreath label="Checking your password safely..." />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">Strength</p>
                <p className="mt-1 font-heading text-base font-semibold text-ink-800">{result.strength_label}</p>
              </div>
              <div className="text-right">
                <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">Known leaks</p>
                <p className={`mt-1 font-heading text-base font-semibold ${result.breached ? "text-rust-600" : "text-sage-600"}`}>
                  {result.breached ? `Found in ${result.breach_count} leaks` : "Not found"}
                </p>
              </div>
            </div>
          </Card>
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
