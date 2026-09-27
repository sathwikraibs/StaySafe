import { useState, type ReactNode } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { CheckedLinks } from "@/components/WebsiteDetails";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanEmailResponse } from "@/types";
import { useI18n } from "@/i18n";
import { IconEmail, IconChevronRight } from "@/icons";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;

function Field({ label, need, hint, children }: { label: string; need: "required" | "optional"; hint?: string; children: ReactNode }) {
  const { t } = useI18n();
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center gap-2 font-body text-sm font-semibold text-ink-800">
        {label}
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${need === "required" ? "bg-terracotta-300/40 text-terracotta-700" : "bg-cream-200 text-dustyblue-600"}`}>
          {t(`emailForm.${need}`)}
        </span>
      </span>
      {children}
      {hint && <span className="mt-1 block font-body text-xs text-dustyblue-600">{hint}</span>}
    </label>
  );
}

const inputCls = "w-full rounded-xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400 focus:bg-cream-50";

export function ScanEmailPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const [mode, setMode] = useState<"form" | "source">("form");
  const [sender, setSender] = useState("");
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState("");
  const [showMore, setShowMore] = useState(false);
  const [raw, setRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanEmailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const senderBad = sender.trim() !== "" && !EMAIL_RE.test(sender.trim());
  const canCheck = mode === "form" ? EMAIL_RE.test(sender.trim()) && body.trim().length > 0 : raw.trim().length > 0;

  async function handleCheck() {
    if (!canCheck || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const payload = mode === "form"
        ? { sender_email: sender.trim(), sender_name: name.trim(), subject: subject.trim(), body: body.trim(), reply_to: replyTo.trim() }
        : { raw_email: raw.trim() };
      const data = await apiPostJSON<ScanEmailResponse>(`${API_BASE}/api/scan-email`, payload);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const label = "font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600";
  const value = "-mt-1.5 break-all font-body text-sm text-ink-800 sm:mt-0";

  return (
    <div>
      <ToolHeader path="/scan-email" title={t("email.title")} subtitle={t("email.subtitle")} />

      {/* Form or full source */}
      <div className="mb-3 grid grid-cols-2 gap-1 rounded-2xl bg-cream-200/70 p-1">
        {(["form", "source"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`btn-press rounded-xl px-3 py-2.5 font-body text-sm font-bold transition-colors
              ${mode === m ? "bg-cream-50 text-ink-900 shadow-warm-sm" : "text-dustyblue-600 hover:text-ink-800"}`}
          >
            {m === "form" ? t("emailForm.simple") : t("emailForm.advanced")}
          </button>
        ))}
      </div>

      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        {mode === "form" ? (
          <div className="space-y-4">
            <Field label={t("emailForm.senderEmail")} need="required" hint={senderBad ? undefined : t("emailForm.senderEmailHint")}>
              <input
                type="email"
                inputMode="email"
                autoComplete="off"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                placeholder="alerts@example.com"
                className={`${inputCls} ${senderBad ? "border-rust-400" : ""}`}
              />
              {senderBad && <span className="mt-1 block font-body text-xs font-semibold text-rust-600">{t("emailForm.badEmail")}</span>}
            </Field>
            <Field label={t("emailForm.senderName")} need="optional">
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("emailForm.senderNamePh")} className={inputCls} />
            </Field>
            <Field label={t("emailForm.subject")} need="optional">
              <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder={t("emailForm.subjectPh")} className={inputCls} />
            </Field>
            <Field label={t("emailForm.body")} need="required">
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                placeholder={t("emailForm.bodyPh")}
                className={`${inputCls} scrollbar-warm`}
              />
            </Field>
            <button
              type="button"
              onClick={() => setShowMore(!showMore)}
              className="flex items-center gap-1 font-body text-sm font-bold text-dustyblue-600 hover:text-ink-900"
            >
              <IconChevronRight className={`h-4 w-4 transition-transform ${showMore ? "rotate-90" : ""}`} /> {t("emailForm.more")}
            </button>
            {showMore && (
              <Field label={t("emailForm.replyTo")} need="optional">
                <input type="email" value={replyTo} onChange={(e) => setReplyTo(e.target.value)} placeholder="reply@example.com" className={inputCls} />
              </Field>
            )}
          </div>
        ) : (
          <div>
            <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("email.label")}</label>
            <textarea
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              rows={8}
              placeholder={t("email.placeholder")}
              className={`${inputCls} text-sm scrollbar-warm`}
            />
            <p className="mt-3 font-body text-xs text-dustyblue-600">{t("email.tip")}</p>
            <p className="mt-2 rounded-xl bg-dustyblue-100 px-3 py-2 font-body text-xs text-dustyblue-600">{t("emailForm.advancedNote")}</p>
          </div>
        )}
        <div className="mt-5">
          <Button onClick={handleCheck} disabled={loading || !canCheck} fullWidth>
            {loading ? t("common.checking") : t("email.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="email" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="email"
          verdict={result.verdict}
          riskScore={result.risk_score}
          subject={result.subject || undefined}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
            <div className="flex items-center gap-2">
              <IconEmail className="h-5 w-5 text-dustyblue-600" />
              <h3 className="font-heading text-lg font-semibold text-ink-900">{t("email.details")}</h3>
            </div>
            <dl className="mt-3 grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
              <dt className={label}>{t("emailInfo.from")}</dt>
              <dd className={value}>{[result.from_name, result.from].filter(Boolean).join(" · ") || t("common.unknown")}</dd>
              <dt className={label}>{t("emailInfo.replyTo")}</dt>
              <dd className={value}>{result.reply_to || t("emailInfo.same")}</dd>
              <dt className={label}>{t("emailInfo.links")}</dt>
              <dd className={value}>{result.links_found?.length || 0}</dd>
            </dl>
          </div>
          {result.links_checked && result.links_checked.length > 0 && (
            <CheckedLinks links={result.links_checked} title={t("message.linksTitle")} />
          )}
        </ResultReport>
      )}
    </div>
  );
}
