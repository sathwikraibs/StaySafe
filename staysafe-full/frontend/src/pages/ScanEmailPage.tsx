import { useState, type ReactNode } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { CheckedLinks } from "@/components/WebsiteDetails";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanEmailResponse } from "@/types";
import { useI18n } from "@/i18n";
import { IconEmail, IconChevronRight } from "@/icons";
import { Section } from "@/components/Section";

const FIND_EMAIL = /[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/;

/** "name [at] example [dot] com", "name @ x.com", "name at x dot com" -> "name@example.com" */
function unhide(raw: string): string {
  return raw
    .replace(/\s*[[({]\s*(?:at|@)\s*[\])}]\s*/gi, "@")
    .replace(/\s*[[({]\s*(?:dot|\.)\s*[\])}]\s*/gi, ".")
    .replace(/(\w)\s+at\s+(?=[\w-]+(?:\s+dot\s+|\.)[a-z])/gi, "$1@")
    .replace(/(\w)\s+dot\s+(?=[a-z])/gi, "$1.")
    .replace(/([\w.-])\s*@\s*(?=[\w-])/g, "$1@");
}

/** "ManageEngine <itom@x.com" -> { name: "ManageEngine", email: "itom@x.com" } */
function splitSender(input: string): { name: string; email: string } {
  const raw = unhide(input);
  const m = raw.match(FIND_EMAIL);
  if (!m || m.index === undefined) return { name: "", email: "" };
  const email = m[0].replace(/^[.']+|[.']+$/g, "").toLowerCase();
  const name = (raw.slice(0, m.index) + " " + raw.slice(m.index + m[0].length))
    .replace(/\b(from|sender|mailto)\s*:/gi, " ")
    .replace(/[<>"'()[\]]/g, " ")
    .replace(/\s+/g, " ")
    .replace(/^[\s,;:.-]+|[\s,;:.-]+$/g, "");
  return { name, email };
}

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
  const pace = usePace();
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

  const [cleaned, setCleaned] = useState<string | null>(null);
  const [movedName, setMovedName] = useState<string | null>(null);
  const senderBad = sender.trim() !== "" && !FIND_EMAIL.test(unhide(sender));
  const canCheck = mode === "form" ? FIND_EMAIL.test(unhide(sender)) && body.trim().length > 0 : raw.trim().length > 0;

  // Tidy up whatever was pasted into an email box, e.g. 'Name <address' or 'From: x@y.com'
  function tidySender() {
    const { name: n, email } = splitSender(sender);
    const typed = sender.trim();
    // Only a company or person's name was typed: move it to the name box and ask for the address
    if (!email && typed && !typed.includes("@") && !/\.[a-z]{2,}$/i.test(typed)) {
      if (!name.trim()) setName(typed.replace(/^(from|sender)\s*:\s*/i, "").replace(/[<>"]/g, "").trim());
      setSender("");
      setMovedName(typed);
      setCleaned(null);
      return;
    }
    setMovedName(null);
    if (!email || email === sender.trim()) { setCleaned(null); return; }
    setSender(email);
    if (n && !name.trim()) setName(n);
    setCleaned(email);
  }
  function tidyReply() {
    const { email } = splitSender(replyTo);
    if (email && email !== replyTo.trim()) setReplyTo(email);
  }

  async function handleCheck() {
    if (!canCheck || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const payload = mode === "form"
        ? { sender_email: splitSender(sender).email || sender.trim(), sender_name: name.trim() || splitSender(sender).name, subject: subject.trim(), body: body.trim(), reply_to: splitSender(replyTo).email }
        : { raw_email: raw.trim() };
      const data = await pace("email", apiPostJSON<ScanEmailResponse>(`${API_BASE}/api/scan-email`, payload));
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
            <Field label={t("emailForm.senderEmail")} need="required" hint={senderBad || cleaned ? undefined : t("emailForm.senderEmailHint")}>
              <input
                type="text"
                inputMode="email"
                autoComplete="off"
                autoCapitalize="off"
                spellCheck={false}
                value={sender}
                onChange={(e) => { setSender(e.target.value); setCleaned(null); setMovedName(null); }}
                onBlur={tidySender}
                onPaste={() => setTimeout(tidySender, 0)}
                placeholder="alerts@example.com"
                className={`${inputCls} ${senderBad ? "border-rust-400" : ""}`}
              />
              {senderBad && <span className="mt-1 block font-body text-xs font-semibold text-rust-600">{t("emailForm.badEmail")}</span>}
              {cleaned && <span className="mt-1 block font-body text-xs font-semibold text-sage-700">{t("emailForm.cleaned", { email: cleaned })}</span>}
              {movedName && <span className="mt-1 block font-body text-xs font-semibold text-terracotta-700">{t("emailForm.movedName", { name: movedName })}</span>}
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
                <input type="text" inputMode="email" autoCapitalize="off" value={replyTo} onChange={(e) => setReplyTo(e.target.value)} onBlur={tidyReply} placeholder="reply@example.com" className={inputCls} />
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
          parts={result.score_parts}
          subject={result.subject || undefined}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <Section icon={<IconEmail className="h-5 w-5" />} title={t("email.details")} tone="info" summary={result.from || undefined}>
            <dl className="grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
              <dt className={label}>{t("emailInfo.from")}</dt>
              <dd className={value}>{[result.from_name, result.from].filter(Boolean).join(" · ") || t("common.unknown")}</dd>
              <dt className={label}>{t("emailInfo.replyTo")}</dt>
              <dd className={value}>{result.reply_to || t("emailInfo.same")}</dd>
              <dt className={label}>{t("emailInfo.links")}</dt>
              <dd className={value}>{result.links_found?.length || 0}</dd>
            </dl>
          </Section>
          {result.links_checked && result.links_checked.length > 0 && (
            <CheckedLinks links={result.links_checked} title={t("message.linksTitle")} />
          )}
        </ResultReport>
      )}
    </div>
  );
}
