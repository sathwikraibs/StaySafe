import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { CheckNumberResponse } from "@/types";
import { useI18n } from "@/i18n";
import { ReportButton } from "@/components/ReportButton";
import { IconSearch, IconAlert, IconInfo } from "@/icons";

const CLAIMS = ["bank", "official", "delivery", "company", "family", "unknown"] as const;
const ASKS = ["pay_to_get", "otp", "app", "video", "nothing"] as const;
const SUSPECT_SEARCH = "https://cybercrime.gov.in/Webform/suspect_search_repository.aspx";
const CHAKSHU = "https://sancharsaathi.gov.in/sfc/";

function looksUsable(v: string): boolean {
  const s = v.trim();
  if (/^[\w.\-]{2,}@[a-z][a-z0-9]{1,}$/i.test(s.replace(/\s/g, ""))) return true;
  return /^[\d\s+\-().]{3,25}$/.test(s) && (s.match(/\d/g) || []).length >= 3;
}

function Pills<T extends string>({ items, value, onChange, label, disabled }: {
  items: readonly T[]; value: T | ""; onChange: (v: T | "") => void; label: (v: T) => string; disabled?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((id) => {
        const on = value === id;
        return (
          <button
            key={id}
            type="button"
            disabled={disabled}
            aria-pressed={on}
            onClick={() => onChange(on ? "" : id)}
            className={`btn-press rounded-full border-2 px-3.5 py-2 text-left font-body text-sm font-semibold transition-colors
              ${on ? "border-sage-500 bg-sage-500 text-cream-50" : "border-cream-200 bg-cream-100 text-ink-800 hover:border-sage-300"}`}
          >
            {label(id)}
          </button>
        );
      })}
    </div>
  );
}

export function CheckNumberPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const pace = usePace();
  const [value, setValue] = useState("");
  const [claim, setClaim] = useState<(typeof CLAIMS)[number] | "">("");
  const [ask, setAsk] = useState<(typeof ASKS)[number] | "">("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckNumberResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const usable = looksUsable(value);
  const typedBad = value.trim().length >= 3 && !usable;

  async function handleCheck() {
    if (!usable || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await pace("number", apiPostJSON<CheckNumberResponse>(`${API_BASE}/api/check-number`, { value: value.trim(), claim, ask }));
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const inputCls = "w-full rounded-xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-lg text-ink-800 outline-none transition-colors focus:border-sage-400 focus:bg-cream-50";
  const linkBtn = "btn-press mt-3 inline-flex items-center justify-center rounded-xl px-4 py-2.5 font-body text-sm font-bold shadow-warm-sm";

  return (
    <div>
      <ToolHeader path="/check-number" title={t("number.title")} subtitle={t("number.subtitle")} />

      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="block">
          <span className="mb-1.5 block font-body text-sm font-semibold text-ink-800">{t("number.label")}</span>
          <input
            type="text"
            inputMode="text"
            autoComplete="off"
            autoCapitalize="off"
            spellCheck={false}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleCheck(); }}
            placeholder={t("number.placeholder")}
            className={`${inputCls} ${typedBad ? "border-rust-400" : ""}`}
          />
          {typedBad && <span className="mt-1 block font-body text-xs font-semibold text-rust-600">{t("number.badInput")}</span>}
        </label>

        <p className="mt-5 font-body text-sm font-semibold text-ink-800">{t("number.claimTitle")}</p>
        <p className="mb-2 font-body text-xs text-dustyblue-600">{t("number.optional")}</p>
        <Pills items={CLAIMS} value={claim} onChange={setClaim} label={(id) => t(`number.claims.${id}`)} disabled={loading} />

        <p className="mb-2 mt-5 font-body text-sm font-semibold text-ink-800">{t("number.askTitle")}</p>
        <Pills items={ASKS} value={ask} onChange={setAsk} label={(id) => t(`number.asks.${id}`)} disabled={loading} />

        <div className="mt-5">
          <Button onClick={handleCheck} disabled={loading || !usable} fullWidth>
            {loading ? t("common.checking") : t("number.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="number" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="number"
          verdict={result.verdict}
          riskScore={result.risk_score}
          parts={result.score_parts}
          subject={result.value}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          {result.kind === "upi" && (
            <div className="flex items-start gap-3 rounded-2xl bg-dustyblue-100 p-4">
              <IconInfo className="mt-0.5 h-5 w-5 shrink-0 text-dustyblue-600" />
              <p className="font-body text-sm text-ink-800">{t("number.upiTip")}</p>
            </div>
          )}
          {result.details?.number_type !== "helpline" && (
            <div className="rounded-2xl bg-cream-50 p-5 shadow-warm-sm">
              <div className="flex items-center gap-2">
                <IconSearch className="h-5 w-5 text-sage-600" />
                <h3 className="font-heading text-base font-semibold text-ink-900">{t("number.govTitle")}</h3>
              </div>
              <p className="mt-1.5 font-body text-sm text-ink-800">{t("number.govText")}</p>
              <a href={SUSPECT_SEARCH} target="_blank" rel="noopener noreferrer" className={`${linkBtn} bg-sage-500 text-cream-50 hover:bg-sage-600`}>
                {t("number.govButton")}
              </a>
            </div>
          )}
          {result.details?.number_type !== "helpline" && result.details?.number_type !== "bank_1600" && (
            <ReportButton key={result.value} kind={result.kind === "upi" ? "upi" : "number"} value={result.value} />
          )}
          <div className="rounded-2xl bg-cream-50 p-5 shadow-warm-sm">
            <div className="flex items-center gap-2">
              <IconAlert className="h-5 w-5 text-terracotta-700" />
              <h3 className="font-heading text-base font-semibold text-ink-900">{t("number.reportTitle")}</h3>
            </div>
            <p className="mt-1.5 font-body text-sm text-ink-800">{t("number.reportText")}</p>
            <a href={CHAKSHU} target="_blank" rel="noopener noreferrer" className={`${linkBtn} border-2 border-sage-300 bg-cream-50 text-sage-700 hover:bg-cream-100`}>
              {t("number.reportButton")}
            </a>
          </div>
        </ResultReport>
      )}
    </div>
  );
}
