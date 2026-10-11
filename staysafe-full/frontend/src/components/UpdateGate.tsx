import { useI18n } from "@/i18n";
import { useUpdateNeeded, updateNow } from "@/updates";
import { BrandMark } from "@/icons";

/** Full-screen update window: everything behind it is blurred and can't be used until updating. */
export function UpdateGate() {
  const show = useUpdateNeeded();
  const { t } = useI18n();
  if (!show) return null;
  return (
    <div
      role="alertdialog" aria-modal="true" aria-labelledby="update-title" aria-describedby="update-body"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink-900/40 p-4 backdrop-blur-md"
    >
      <div className="w-full max-w-sm rounded-3xl bg-cream-50 p-6 text-center shadow-warm-lg animate-fade-up">
        <BrandMark className="mx-auto h-14 w-14" />
        <h2 id="update-title" className="mt-4 font-heading text-xl font-bold text-ink-900">{t("update.title")}</h2>
        <p id="update-body" className="mt-2 font-body text-sm leading-relaxed text-ink-700">{t("update.body")}</p>
        <button
          type="button" onClick={() => updateNow()}
          className="btn-press mt-5 w-full rounded-2xl bg-brand-600 px-5 py-3.5 font-body text-base font-bold text-cream-50 shadow-warm hover:bg-brand-700 focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-200"
        >
          {t("update.button")}
        </button>
      </div>
    </div>
  );
}
