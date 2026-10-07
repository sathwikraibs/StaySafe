import { useState } from "react";
import { useI18n } from "@/i18n";
import { useInstall, isInstalledApp } from "@/share";
import { IconPhone, IconClose } from "@/icons";

const HIDE_KEY = "staysafe.installHidden.v1";

function hiddenOnHome(): boolean {
  try { return localStorage.getItem(HIDE_KEY) === "1"; } catch { return false; }
}

/**
 * "Add StaySafe to your phone", so people can share messages, links and screenshots to it.
 * place="home": only when the phone offers it, and it can be closed.
 * place="settings": also shows how to share once StaySafe is on the phone.
 */
export function InstallCard({ place }: { place: "home" | "settings" }) {
  const { t } = useI18n();
  const { canInstall, install } = useInstall();
  const [hidden, setHidden] = useState(hiddenOnHome);
  const [done, setDone] = useState(false);
  const installed = isInstalledApp();

  if (place === "home" && (hidden || !canInstall) && !done) return null;
  if (place === "settings" && !canInstall && !installed && !done) return null;

  const close = () => {
    setHidden(true);
    try { localStorage.setItem(HIDE_KEY, "1"); } catch { /* ignore */ }
  };

  return (
    <div className="relative mb-6 rounded-2xl bg-sage-100 p-5 shadow-warm animate-fade-up">
      {place === "home" && !done && (
        <button type="button" onClick={close} aria-label={t("install.later")}
          className="btn-press absolute right-3 top-3 rounded-full p-1.5 text-dustyblue-600 hover:bg-cream-50">
          <IconClose className="h-4 w-4" />
        </button>
      )}
      <div className="flex items-start gap-3 pr-6">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sage-500 text-cream-50">
          <IconPhone className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-heading text-base font-semibold text-ink-900">{t("install.title")}</h2>
          <p className="mt-1 font-body text-sm text-ink-800">
            {done || (installed && !canInstall) ? t("install.done") : t("install.text")}
          </p>
          {(done || installed) && <p className="mt-2 font-body text-xs text-dustyblue-600">{t("install.tip")}</p>}
        </div>
      </div>
      {canInstall && !done && (
        <div className="mt-4 flex gap-2">
          <button type="button" onClick={async () => { if (await install()) setDone(true); }}
            className="btn-press flex-1 rounded-xl bg-sage-500 px-4 py-3 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-sage-600">
            {t("install.button")}
          </button>
          {place === "home" && (
            <button type="button" onClick={close}
              className="btn-press rounded-xl border-2 border-sage-300 bg-cream-50 px-4 py-3 font-body text-sm font-bold text-sage-700">
              {t("install.later")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
