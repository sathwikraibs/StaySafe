import { useEffect, useRef, useState, type ReactNode } from "react";
import { IconUpload, IconClose, IconCamera, IconImage, IconFolder } from "@/icons";
import { useI18n } from "@/i18n";
import { ImageCropper } from "@/components/ImageCropper";

interface UploadZoneProps {
  accept?: string;
  label: string;
  hint?: string;
  onFile: (file: File) => void;
  onClear?: () => void;
  selectedPreview?: ReactNode;
  disabled?: boolean;
  /** Shrink big photos before sending (screenshots and QR photos). Never used for files we fingerprint. */
  compress?: boolean;
  /** show the "Take a photo" button (not needed for files) */
  camera?: boolean;
  /** offer "Crop" for pictures, so only the important part is checked */
  crop?: boolean;
}

/** Scissors, for the crop button. */
function IconCrop({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M6 2v14a2 2 0 0 0 2 2h14" /><path d="M18 22V8a2 2 0 0 0-2-2H2" />
    </svg>
  );
}

/** Big phone photos (4000px, 5 MB) are shrunk so they upload and read quickly. */
async function shrinkImage(file: File, maxSide = 2000): Promise<File> {
  if (!file.type.startsWith("image/") || file.type === "image/gif" || file.type === "image/svg+xml") return file;
  try {
    const bitmap = await createImageBitmap(file);
    const { width, height } = bitmap;
    const scale = Math.min(1, maxSide / Math.max(width, height));
    if (scale === 1 && file.size < 1_500_000) { bitmap.close?.(); return file; }
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const blob: Blob | null = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.92));
    if (!blob || blob.size >= file.size) return file;
    const name = file.name.replace(/\.[^.]+$/, "") + ".jpg";
    return new File([blob], name, { type: "image/jpeg" });
  } catch {
    return file;
  }
}

export function UploadZone({ accept, label, hint, onFile, onClear, selectedPreview, disabled, compress, camera = true, crop = false }: UploadZoneProps) {
  const { t } = useI18n();
  const pickRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const imagesOnly = (accept || "").startsWith("image");
  const [picture, setPicture] = useState<File | null>(null);   // the picture as chosen, for cropping
  const [cropping, setCropping] = useState(false);
  const [cropped, setCropped] = useState(false);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  async function handleFile(original: File, fromCrop = false) {
    setFileName(original.name || t("upload.photo"));
    if (original.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(original));
      if (!fromCrop) { setPicture(original); setCropped(false); }
    }
    const file = compress ? await shrinkImage(original) : original;
    onFile(file);
  }

  function clear() {
    setFileName(null);
    setPreview(null);
    setPicture(null);
    setCropped(false);
    if (pickRef.current) pickRef.current.value = "";
    if (cameraRef.current) cameraRef.current.value = "";
    onClear?.();
  }

  const onChange = (e: { target: HTMLInputElement }) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  return (
    <div>
      <input ref={pickRef} type="file" accept={accept} className="hidden" onChange={onChange} />
      {/* Opens the phone camera straight away (on laptops it simply opens the file picker) */}
      <input ref={cameraRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={onChange} />

      {!fileName ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files?.[0];
            if (f) handleFile(f);
          }}
          className={`rounded-2xl border-2 border-dashed p-5 transition-colors sm:p-6
            ${dragging ? "border-sage-400 bg-sage-100" : "border-sage-300 bg-cream-100"}
            ${disabled ? "pointer-events-none opacity-50" : ""}`}
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="upload-bob flex h-14 w-14 items-center justify-center rounded-2xl bg-sage-200 text-sage-600">
              <IconUpload className="h-7 w-7" />
            </div>
            <p className="font-body text-base font-semibold text-ink-800">{label}</p>
            {hint && <p className="font-body text-sm text-dustyblue-600">{hint}</p>}
          </div>
          <div className={`mt-4 grid gap-2.5 ${camera ? "grid-cols-2" : "grid-cols-1"}`}>
            {camera && <button
              type="button"
              disabled={disabled}
              onClick={() => cameraRef.current?.click()}
              className="btn-press flex flex-col items-center justify-center gap-1.5 rounded-xl bg-sage-500 px-3 py-3.5 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-sage-600 sm:flex-row"
            >
              <IconCamera className="h-5 w-5" /> {t("upload.camera")}
            </button>}
            <button
              type="button"
              disabled={disabled}
              onClick={() => pickRef.current?.click()}
              className="btn-press flex flex-col items-center justify-center gap-1.5 rounded-xl border-2 border-sage-300 bg-cream-50 px-3 py-3 font-body text-sm font-bold text-sage-700 hover:bg-sage-100 sm:flex-row"
            >
              {imagesOnly ? <IconImage className="h-5 w-5" /> : <IconFolder className="h-5 w-5" />}
              {imagesOnly ? t("upload.gallery") : t("upload.files")}
            </button>
          </div>
          <p className="mt-3 hidden text-center font-body text-xs text-dustyblue-500 sm:block">{t("upload.drag")}</p>
        </div>
      ) : (
        <div className="flex items-center gap-4 rounded-2xl border-2 border-sage-200 bg-cream-100 p-3 animate-fade-up">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sage-200 text-sage-600">
            {preview ? <img src={preview} alt="" className="h-full w-full object-cover" /> : selectedPreview ?? <IconUpload className="h-6 w-6" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-body text-sm font-semibold text-ink-800">{fileName}</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5">
              {crop && picture && (
                <button
                  type="button"
                  onClick={() => setCropping(true)}
                  disabled={disabled}
                  className="btn-press flex items-center gap-1.5 rounded-full bg-sage-500 px-3 py-1.5 font-body text-xs font-bold text-cream-50 hover:bg-sage-600"
                >
                  <IconCrop className="h-3.5 w-3.5" /> {cropped ? t("crop.again") : t("crop.button")}
                </button>
              )}
              <button
                type="button"
                onClick={clear}
                className="flex items-center gap-1 font-body text-xs font-semibold text-dustyblue-500 hover:text-terracotta-600"
              >
                <IconClose className="h-3.5 w-3.5" /> {t("common.chooseDifferentFile")}
              </button>
            </div>
            {crop && picture && !cropped && <p className="mt-1 font-body text-[11px] text-dustyblue-600">{t("crop.tip")}</p>}
          </div>
        </div>
      )}
      {cropping && picture && (
        <ImageCropper
          file={picture}
          onCancel={() => setCropping(false)}
          onDone={(f) => { setCropping(false); setCropped(true); void handleFile(f, true); }}
        />
      )}
    </div>
  );
}
