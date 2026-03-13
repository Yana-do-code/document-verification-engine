"use client";

import Image from "next/image";

interface Props {
  file: File;
}

export default function DocumentPreview({ file }: Props) {
  const isPDF = file.type === "application/pdf";
  const url = URL.createObjectURL(file);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
        <div className={`h-2 w-2 rounded-full ${isPDF ? "bg-red-400" : "bg-violet-400"}`} />
        <span className="truncate text-sm text-slate-400">{file.name}</span>
        <span className="ml-auto shrink-0 text-xs text-slate-600">
          {(file.size / 1024).toFixed(0)} KB
        </span>
      </div>
      <div className="relative flex items-center justify-center bg-slate-950 p-4" style={{ minHeight: 220 }}>
        {isPDF ? (
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <svg className="h-14 w-14 text-red-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm">PDF — preview not available</p>
            <p className="text-xs text-slate-600">Will be converted to image on the server</p>
          </div>
        ) : (
          <Image
            src={url}
            alt="Document preview"
            width={480}
            height={320}
            className="max-h-72 w-auto rounded-lg object-contain shadow-lg"
            unoptimized
          />
        )}
      </div>
    </div>
  );
}
