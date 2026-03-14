"use client";

import { useCallback, useState } from "react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
  resetKey?: number; // increment to reset the input
}

const ACCEPTED = ["image/jpeg", "image/png", "image/tiff", "application/pdf"];

export default function UploadZone({ onFile, disabled, resetKey }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = useCallback(
    (file: File) => {
      setError(null);
      if (!ACCEPTED.includes(file.type)) {
        setError("Only JPG, PNG, TIFF and PDF files are supported.");
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setError("File must be under 5 MB.");
        return;
      }
      onFile(file);
    },
    [onFile]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handle(file);
    },
    [handle]
  );

  return (
    <div className="space-y-3">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={[
          "flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 cursor-pointer transition-all duration-200",
          disabled
            ? "opacity-40 cursor-not-allowed border-slate-700"
            : dragging
            ? "border-violet-400 bg-violet-950/30"
            : "border-slate-700 hover:border-violet-500 hover:bg-slate-900",
        ].join(" ")}
      >
        {/* Upload icon */}
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-800">
          <svg className="h-7 w-7 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-slate-200">
            Drag & drop or <span className="text-violet-400">browse</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">JPG, PNG, TIFF, PDF — max 5 MB</p>
        </div>
        <input
          key={resetKey}
          type="file"
          accept=".jpg,.jpeg,.png,.tiff,.tif,.pdf"
          className="sr-only"
          disabled={disabled}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handle(f); }}
        />
      </label>

      {error && (
        <p className="flex items-center gap-2 rounded-lg bg-red-950/50 px-4 py-2 text-sm text-red-400">
          <svg className="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}
