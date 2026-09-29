import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n";

type Box = { x: number; y: number; w: number; h: number };   // in 0..1 of the picture
type Drag = { kind: "move" | "nw" | "ne" | "sw" | "se" | "n" | "s" | "w" | "e"; sx: number; sy: number; start: Box };

const MIN = 0.06;
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/**
 * Crop a picture right on the site: drag the box, or its corners and edges, to keep only the
 * part that matters (the message, or the QR code). Works with a finger or a mouse.
 */
export function ImageCropper({ file, onDone, onCancel }: {
  file: File;
  onDone: (cropped: File) => void;
  onCancel: () => void;
}) {
  const { t } = useI18n();
  const [url] = useState(() => URL.createObjectURL(file));
  const [box, setBox] = useState<Box>({ x: 0.04, y: 0.04, w: 0.92, h: 0.92 });
  const [busy, setBusy] = useState(false);
  const frame = useRef<HTMLDivElement>(null);
  const img = useRef<HTMLImageElement>(null);
  const drag = useRef<Drag | null>(null);

  useEffect(() => () => URL.revokeObjectURL(url), [url]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); };
    window.addEventListener("keydown", onKey);
    const old = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = old; };
  }, [onCancel]);

  function start(kind: Drag["kind"], e: { clientX: number; clientY: number; pointerId: number; currentTarget: Element; stopPropagation(): void; preventDefault(): void }) {
    e.stopPropagation();
    e.preventDefault();
    (e.currentTarget as Element).setPointerCapture?.(e.pointerId);
    drag.current = { kind, sx: e.clientX, sy: e.clientY, start: box };
  }

  function move(e: { clientX: number; clientY: number }) {
    const d = drag.current;
    const rect = img.current?.getBoundingClientRect();
    if (!d || !rect) return;
    const dx = (e.clientX - d.sx) / rect.width;
    const dy = (e.clientY - d.sy) / rect.height;
    let { x, y, w, h } = d.start;
    if (d.kind === "move") {
      x = clamp(x + dx, 0, 1 - w);
      y = clamp(y + dy, 0, 1 - h);
    } else {
      if (d.kind.includes("w")) { const nx = clamp(x + dx, 0, x + w - MIN); w += x - nx; x = nx; }
      if (d.kind.includes("e")) { w = clamp(w + dx, MIN, 1 - x); }
      if (d.kind.includes("n")) { const ny = clamp(y + dy, 0, y + h - MIN); h += y - ny; y = ny; }
      if (d.kind.includes("s")) { h = clamp(h + dy, MIN, 1 - y); }
    }
    setBox({ x, y, w, h });
  }

  async function finish() {
    const el = img.current;
    if (!el) return;
    setBusy(true);
    try {
      const nw = el.naturalWidth, nh = el.naturalHeight;
      const sx = Math.round(box.x * nw), sy = Math.round(box.y * nh);
      const sw = Math.max(1, Math.round(box.w * nw)), sh = Math.max(1, Math.round(box.h * nh));
      const canvas = document.createElement("canvas");
      canvas.width = sw;
      canvas.height = sh;
      const ctx = canvas.getContext("2d");
      if (!ctx) { onCancel(); return; }
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, sw, sh);
      ctx.drawImage(el, sx, sy, sw, sh, 0, 0, sw, sh);
      const type = file.type === "image/png" ? "image/png" : "image/jpeg";
      const blob: Blob | null = await new Promise((res) => canvas.toBlob(res, type, 0.95));
      if (!blob) { onCancel(); return; }
      const name = (file.name || "picture").replace(/\.[^.]+$/, "") + (type === "image/png" ? "-cropped.png" : "-cropped.jpg");
      onDone(new File([blob], name, { type }));
    } finally {
      setBusy(false);
    }
  }

  const handle = (kind: Drag["kind"], cls: string) => (
    <span
      onPointerDown={(e) => start(kind, e)}
      className={`absolute z-10 h-7 w-7 touch-none ${cls}`}
      style={{ cursor: `${kind}-resize` }}
    >
      <span className="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-sage-600 bg-cream-50 shadow-warm-sm" />
    </span>
  );

  return (
    <div role="dialog" aria-modal="true" aria-label={t("crop.title")}
      className="fixed inset-0 z-[60] flex flex-col bg-ink-900 animate-fade-up">
      <div className="flex items-center justify-between gap-3 px-4 py-3 text-cream-50">
        <div className="min-w-0">
          <p className="font-heading text-base font-bold">{t("crop.title")}</p>
          <p className="font-body text-xs text-cream-50/80">{t("crop.hint")}</p>
        </div>
        <button type="button" onClick={() => setBox({ x: 0, y: 0, w: 1, h: 1 })}
          className="shrink-0 rounded-full bg-cream-50/15 px-3 py-1.5 font-body text-xs font-bold text-cream-50 hover:bg-cream-50/25">
          {t("crop.whole")}
        </button>
      </div>

      <div ref={frame} className="flex min-h-0 flex-1 items-center justify-center px-4 pb-2"
        onPointerMove={move} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}>
        <div className="relative max-h-full max-w-full touch-none select-none">
          <img ref={img} src={url} alt="" draggable={false}
            className="block max-h-[calc(100vh-11rem)] max-w-full select-none object-contain" />
          {/* dim the parts that will be cut away */}
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-0 right-0 top-0 bg-ink-900/60" style={{ height: `${box.y * 100}%` }} />
            <div className="absolute bottom-0 left-0 right-0 bg-ink-900/60" style={{ height: `${(1 - box.y - box.h) * 100}%` }} />
            <div className="absolute left-0 bg-ink-900/60" style={{ top: `${box.y * 100}%`, height: `${box.h * 100}%`, width: `${box.x * 100}%` }} />
            <div className="absolute right-0 bg-ink-900/60" style={{ top: `${box.y * 100}%`, height: `${box.h * 100}%`, width: `${(1 - box.x - box.w) * 100}%` }} />
          </div>
          <div
            onPointerDown={(e) => start("move", e)}
            className="absolute cursor-move touch-none border-2 border-cream-50 shadow-[0_0_0_1px_rgba(0,0,0,0.4)]"
            style={{ left: `${box.x * 100}%`, top: `${box.y * 100}%`, width: `${box.w * 100}%`, height: `${box.h * 100}%` }}
          >
            <span className="pointer-events-none absolute inset-y-0 left-1/3 w-px bg-cream-50/40" />
            <span className="pointer-events-none absolute inset-y-0 left-2/3 w-px bg-cream-50/40" />
            <span className="pointer-events-none absolute inset-x-0 top-1/3 h-px bg-cream-50/40" />
            <span className="pointer-events-none absolute inset-x-0 top-2/3 h-px bg-cream-50/40" />
            {handle("nw", "-left-3.5 -top-3.5")}
            {handle("ne", "-right-3.5 -top-3.5")}
            {handle("sw", "-bottom-3.5 -left-3.5")}
            {handle("se", "-bottom-3.5 -right-3.5")}
            {handle("n", "-top-3.5 left-1/2 -translate-x-1/2")}
            {handle("s", "-bottom-3.5 left-1/2 -translate-x-1/2")}
            {handle("w", "-left-3.5 top-1/2 -translate-y-1/2")}
            {handle("e", "-right-3.5 top-1/2 -translate-y-1/2")}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 px-4 pb-4 pt-2" style={{ paddingBottom: "calc(1rem + env(safe-area-inset-bottom))" }}>
        <button type="button" onClick={onCancel}
          className="rounded-2xl border-2 border-cream-50/40 px-4 py-3 font-body text-base font-bold text-cream-50 hover:bg-cream-50/10">
          {t("crop.cancel")}
        </button>
        <button type="button" onClick={finish} disabled={busy}
          className="rounded-2xl bg-sage-500 px-4 py-3 font-body text-base font-bold text-cream-50 hover:bg-sage-600 disabled:opacity-60">
          {t("crop.use")}
        </button>
      </div>
    </div>
  );
}
