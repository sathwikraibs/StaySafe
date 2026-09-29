import { useState } from "react";
import { Button } from "@/components/Button";
import { ErrorNotice } from "@/components/PageBits";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import { IconCheck, IconWarning } from "@/icons";
import { useI18n } from "@/i18n";

interface LeakResult {
  breached: boolean;
  breach_count: number;
  breaches: string[];
  fields?: string[];
  source?: string;
}

/** "Has my email appeared in a data leak?" (names of the leaks only, never the leaked data). */
export function EmailLeakCheck() {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LeakResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function check() {
    if (!email.trim() || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      setResult(await apiPostJSON<LeakResult>(`${API_BASE}/api/check-email-breach`, { email: email.trim() }));
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div className="rounded-2xl bg-cream-50 p-5 shadow-warm animate-fade-up">
      <h3 className="font-heading text-lg font-semibold text-ink-900">{t("leak.title")}</h3>
      <p className="mt-1 font-body text-sm text-dustyblue-600">{t("leak.subtitle")}</p>
      <input
        type="text"
        inputMode="email"
        autoCapitalize="off"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") check(); }}
        placeholder="name@example.com"
        className="mt-3 w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
      />
      <div className="mt-3">
        <Button onClick={check} disabled={loading || !email.trim()} fullWidth>
          {loading ? t("common.checking") : t("leak.button")}
        </Button>
      </div>
      {error && <div className="mt-3"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className={`mt-4 rounded-2xl p-4 animate-fade-up ${result.breached ? "bg-rust-400/10" : "bg-sage-100"}`}>
          <p className={`flex items-center gap-2 font-heading text-base font-bold ${result.breached ? "text-rust-600" : "text-sage-700"}`}>
            {result.breached ? <IconWarning className="h-5 w-5 shrink-0" /> : <IconCheck className="h-5 w-5 shrink-0" />}
            {result.breached ? t("leak.found", { n: result.breach_count }) : t("leak.notFound")}
          </p>
          {result.breached && (
            <>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {result.breaches.slice(0, 20).map((b) => (
                  <li key={b} className="rounded-lg bg-cream-50 px-2.5 py-1 font-body text-xs font-semibold text-ink-800">{b}</li>
                ))}
              </ul>
              <p className="mt-3 font-body text-sm text-ink-700">{t("leak.todo")}</p>
            </>
          )}
          {result.source && (
            <p className="mt-3 font-body text-[11px] text-dustyblue-500">
              {t("leak.source", { source: result.source })}
              {result.source === "LeakCheck" && (
                <> · <a href="https://leakcheck.io" target="_blank" rel="noopener noreferrer" className="underline">Powered by LeakCheck</a></>
              )}
            </p>
          )}
        </div>
      )}
      <p className="mt-3 font-body text-xs text-dustyblue-500">{t("leak.privacy")}</p>
    </div>
  );
}
