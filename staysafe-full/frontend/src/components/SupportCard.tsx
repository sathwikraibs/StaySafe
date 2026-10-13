import { useEffect, useState } from "react";
import { useI18n } from "@/i18n";
import { apiGet } from "@/api";
import { API_BASE } from "@/config";
import { isPhoneOrTablet } from "@/share";
import { BrandMark, IconCheck } from "@/icons";

/**
 * "Support TrustLight": an optional contribution, shown only when a payment page or UPI ID is set on
 * the server (SUPPORT_LINK / SUPPORT_UPI). Calm and factual: what it pays for, and that every check
 * stays free either way.
 */
interface SupportInfo { available: boolean; link: string; upi: string; name: string }

let cached: Promise<SupportInfo | null> | null = null;
function loadSupport(): Promise<SupportInfo | null> {
  cached ??= apiGet<SupportInfo>(`${API_BASE}/api/support`).catch(() => null);
  return cached;
}

export function SupportCard() {
  const { t, tl } = useI18n();
  const [info, setInfo] = useState<SupportInfo | null>(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => { let on = true; void loadSupport().then((i) => { if (on) setInfo(i); }); return () => { on = false; }; }, []);
  if (!info?.available) return null;

  const phone = isPhoneOrTablet();
  const upiLink = info.upi ? `upi://pay?pa=${encodeURIComponent(info.upi)}&pn=${encodeURIComponent(info.name || "TrustLight")}&cu=INR` : "";
  async function copy() {
    try { await navigator.clipboard.writeText(info!.upi); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* ignore */ }
  }

  return (
    <section id="support" className="rounded-3xl border border-cream-200 bg-cream-50 p-5 shadow-warm-sm sm:p-6">
      <div className="flex items-start gap-3">
        <BrandMark className="h-10 w-10 shrink-0 rounded-xl" />
        <div className="min-w-0">
          <h2 className="font-heading text-lg font-bold leading-tight text-ink-900">{t("support.title")}</h2>
          <p className="mt-1 font-body text-sm leading-relaxed text-dustyblue-600">{t("support.text")}</p>
        </div>
      </div>

      <ul className="mt-4 space-y-2">
        {tl("support.points").map((p, i) => (
          <li key={i} className="flex items-start gap-2 font-body text-sm text-ink-800">
            <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-sage-600" strokeWidth={2.4} />{p}
          </li>
        ))}
      </ul>

      <div className="mt-5 space-y-3">
        {info.link && (
          <a href={info.link} target="_blank" rel="noopener noreferrer"
            className="btn-press block w-full rounded-xl bg-brand-600 px-5 py-3 text-center font-body text-base font-semibold text-white hover:bg-brand-700">
            {t("support.button")}
          </a>
        )}
        {info.upi && (
          <div className="rounded-2xl bg-cream-100 p-3">
            <p className="font-body text-xs font-semibold text-dustyblue-600">{t("support.upiLabel")}</p>
            <div className="mt-1 flex items-center gap-2">
              <span className="min-w-0 flex-1 truncate font-mono text-sm font-semibold text-ink-900">{info.upi}</span>
              <button type="button" onClick={copy}
                className="shrink-0 rounded-lg border border-cream-300 bg-cream-50 px-3 py-1.5 font-body text-xs font-semibold text-brand-700 hover:bg-brand-50">
                {copied ? t("support.copied") : t("support.copy")}
              </button>
            </div>
            {phone ? (
              <a href={upiLink}
                className={`mt-3 block w-full rounded-xl px-5 py-2.5 text-center font-body text-sm font-semibold ${info.link ? "border border-brand-300 bg-cream-50 text-brand-700" : "bg-brand-600 text-white hover:bg-brand-700"}`}>
                {t("support.upiPay")}
              </a>
            ) : (
              <p className="mt-2 font-body text-xs text-dustyblue-600">{t("support.upiHint")}</p>
            )}
          </div>
        )}
      </div>

      <p className="mt-4 text-center font-body text-xs text-dustyblue-500">{t("support.note")}</p>
    </section>
  );
}
