"use client";

import Image from "next/image";
import { formatBytes } from "@/lib/compress";

interface Props {
  file: File;
  originalSize?: number;
  compressedSize?: number;
}

export default function DocumentPreview({ file, originalSize, compressedSize }: Props) {
  const isPDF = file.type === "application/pdf";
  const url = URL.createObjectURL(file);

  const orig = originalSize ?? file.size;
  const comp = compressedSize ?? file.size;
  const didCompress = comp < orig && comp > 0;
  const saved = didCompress ? Math.round((1 - comp / orig) * 100) : 0;

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">

      {/* ── Header with size info ── */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-slate-800 px-4 py-3">

        {/* File type dot */}
        <div className={`h-2 w-2 shrink-0 rounded-full ${isPDF ? "bg-red-400" : "bg-violet-400"}`} />

        {/* Filename */}
        <span className="truncate text-sm text-slate-400">{file.name}</span>

        {/* Size strip — always visible */}
        <div className="ml-auto flex items-center gap-2 text-xs">
          {isPDF && (
            <span className="rounded bg-red-900/40 px-1.5 py-0.5 font-medium text-red-300">PDF</span>
          )}

          {didCompress ? (
            <>
              <span className="text-slate-500 line-through">{formatBytes(orig)}</span>
              <svg className="h-3 w-3 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
              <span className="font-medium text-teal-400">{formatBytes(comp)}</span>
              <span className="rounded-full bg-teal-900/60 px-1.5 py-0.5 font-semibold text-teal-300">
                -{saved}%
              </span>
            </>
          ) : (
            <span className="font-medium text-slate-300">{formatBytes(orig)}</span>
          )}
        </div>
      </div>

      {/* ── Preview area ── */}
      <div className="relative bg-slate-950">
        {isPDF ? (
          <iframe
            src={url}
            title="PDF preview"
            className="h-80 w-full rounded-b-xl border-0"
          />
        ) : (
          <div className="flex items-center justify-center p-4" style={{ minHeight: 220 }}>
            <Image
              src={url}
              alt="Document preview"
              width={480}
              height={320}
              className="max-h-72 w-auto rounded-lg object-contain shadow-lg"
              unoptimized
            />
          </div>
        )}
      </div>
    </div>
  );
}
