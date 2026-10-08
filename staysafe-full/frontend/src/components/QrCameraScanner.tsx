import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n";
import { IconCamera, IconClose } from "@/icons";

interface Props {
  /** QR text read by the phone itself (fast path) */
  onText: (text: string) => void;
  /** a still photo from the camera, when the browser can't read QR codes itself */
  onPhoto: (file: File) => void;
  onClose: () => void;
}

type Detector = { detect: (src: HTMLVideoElement) => Promise<{ rawValue: string }[]> };

/** Live camera view: point at a QR code and it is read automatically. */
export function QrCameraScanner({ onText, onPhoto, onClose }: Props) {
  const { t } = useI18n();
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [canAutoRead, setCanAutoRead] = useState(false);

  useEffect(() => {
    let stopped = false;
    let timer = 0;

    async function start() {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
        if (stopped) { s.getTracks().forEach((tr) => tr.stop()); return; }
        stream.current = s;
        if (video.current) {
          video.current.srcObject = s;
          await video.current.play().catch(() => undefined);
        }
        const BD = (window as unknown as { BarcodeDetector?: new (o: { formats: string[] }) => Detector }).BarcodeDetector;
        if (BD) {
          const detector = new BD({ formats: ["qr_code"] });
          setCanAutoRead(true);
          const scan = async () => {
            if (stopped || !video.current) return;
            try {
              const codes = await detector.detect(video.current);
              if (codes.length && codes[0].rawValue) {
                navigator.vibrate?.(60);
                stop();
                onText(codes[0].rawValue);
                return;
              }
            } catch { /* keep trying */ }
            timer = window.setTimeout(scan, 350);
          };
          scan();
        }
      } catch {
        setProblem(t("qrCam.noCamera"));
      }
    }

    function stop() {
      stopped = true;
      window.clearTimeout(timer);
      stream.current?.getTracks().forEach((tr) => tr.stop());
    }

    start();
    return stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function capture() {
    const v = video.current;
    if (!v || !v.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d")?.drawImage(v, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      stream.current?.getTracks().forEach((tr) => tr.stop());
      onPhoto(new File([blob], "qr-camera.jpg", { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  }

  return (
    <div className="overflow-hidden rounded-2xl bg-ink-900 shadow-warm-lg animate-fade-up">
      <div className="relative aspect-square w-full sm:aspect-video">
        {problem ? (
          <div className="flex h-full items-center justify-center p-6 text-center font-body text-sm text-cream-50">{problem}</div>
        ) : (
          <>
            <video ref={video} playsInline muted className="h-full w-full object-cover" />
            {/* aiming frame with a moving scan line */}
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="relative h-3/5 w-3/5 max-w-xs rounded-3xl border-4 border-cream-50/90 shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]">
                <span className="qr-cam-line absolute left-3 right-3 h-0.5 rounded bg-beam-400 shadow-[0_0_12px_#FBBF24]" />
              </div>
            </div>
            <p className="absolute inset-x-0 bottom-3 text-center font-body text-sm font-semibold text-cream-50 drop-shadow">
              {canAutoRead ? t("qrCam.pointAuto") : t("qrCam.point")}
            </p>
          </>
        )}
        <button onClick={onClose} aria-label={t("qrCam.close")} className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-ink-900/60 text-cream-50">
          <IconClose className="h-5 w-5" />
        </button>
      </div>
      {!problem && !canAutoRead && (
        <button onClick={capture} className="btn-press flex w-full items-center justify-center gap-2 bg-brand-500 px-4 py-3.5 font-body text-base font-bold text-cream-50">
          <IconCamera className="h-5 w-5" /> {t("qrCam.capture")}
        </button>
      )}
    </div>
  );
}
