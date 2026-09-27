import { useRef, useState, type ReactNode } from "react";
import { IconUpload, IconClose } from "@/icons";

interface UploadZoneProps {
  accept?: string;
  label: string;
  hint?: string;
  onFile: (file: File) => void;
  onClear?: () => void;
  selectedPreview?: ReactNode;
  disabled?: boolean;
}

export function UploadZone({ accept, label, hint, onFile, onClear, selectedPreview, disabled }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  function handleFile(file: File) {
    setFileName(file.name);
    onFile(file);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
        }}
      />
      {!fileName ? (
        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files?.[0];
            if (f) handleFile(f);
          }}
          className={`btn-press flex w-full flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-8
            ${dragging ? "border-sage-400 bg-sage-100" : "border-sage-300 bg-cream-100 hover:bg-sage-100/50"}
            ${disabled ? "opacity-50" : ""}`}
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-sage-200 text-sage-600">
            <IconUpload className="h-7 w-7" />
          </div>
          <p className="font-body text-base font-semibold text-ink-800">{label}</p>
          {hint && <p className="font-body text-sm text-dustyblue-600">{hint}</p>}
        </button>
      ) : (
        <div className="flex items-center gap-4 rounded-2xl bg-cream-100 p-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sage-200 text-sage-600">
            {selectedPreview ?? <IconUpload className="h-6 w-6" />}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="truncate font-body text-sm font-semibold text-ink-800">{fileName}</p>
            <button
              type="button"
              onClick={() => { setFileName(null); if (inputRef.current) inputRef.current.value = ""; onClear?.(); }}
              className="mt-1 flex items-center gap-1 font-body text-xs text-dustyblue-500 hover:text-terracotta-600"
            >
              <IconClose className="h-3.5 w-3.5" /> Choose a different file
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
