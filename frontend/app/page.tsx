"use client";

import { useState, useCallback } from "react";
import UploadZone from "@/components/UploadZone";
import DocumentPreview from "@/components/DocumentPreview";
import DocTypeBadge from "@/components/DocTypeBadge";
import ConfidenceBar from "@/components/ConfidenceBar";
import ExtractedFields from "@/components/ExtractedFields";
import ValidationResult from "@/components/ValidationResult";
import { verifyDocument, type VerifyResponse } from "@/lib/api";
import { compressFile } from "@/lib/compress";

// ── State machine ──────────────────────────────────────────────────────────

type State =
  | { phase: "idle" }
  | { phase: "compressing" }
  | {
      phase: "ready" | "loading" | "error" | "result";
      originalFile: File;
      displayFile: File;     // original for preview
      uploadFile: File;      // compressed for upload
      originalSize: number;
      compressedSize: number;
      data?: VerifyResponse;
      message?: string;
    };

// ── Helpers ────────────────────────────────────────────────────────────────

function StatusBanner({ icon, color, title, body }: {
  icon: React.ReactNode;
  color: string;
  title: string;
  body?: string;
}) {
  return (
    <div className={`rounded-xl border ${color} p-5`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{icon}</div>
        <div>
          <p className="font-semibold">{title}</p>
          {body && <p className="mt-1 text-sm opacity-80">{body}</p>}
        </div>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function Home() {
  const [state, setState] = useState<State>({ phase: "idle" });
  const [uploadKey, setUploadKey] = useState(0);

  // Step 1 — file dropped → compress immediately
  const onFile = useCallback(async (file: File) => {
    setState({ phase: "compressing" });
    const result = await compressFile(file);
    setState({
      phase: "ready",
      originalFile: file,
      displayFile: file,          // show original image in preview
      uploadFile: result.file,    // upload the compressed version
      originalSize: result.originalSize,
      compressedSize: result.compressedSize,
    });
  }, []);

  // Step 2 — verify clicked → upload compressed file
  const onVerify = useCallback(async () => {
    if (state.phase !== "ready" && state.phase !== "result" && state.phase !== "error") return;
    const { originalFile, displayFile, uploadFile, originalSize, compressedSize } = state;
    setState({ phase: "loading", originalFile, displayFile, uploadFile, originalSize, compressedSize });
    try {
      const data = await verifyDocument(uploadFile);
      setState({ phase: "result", originalFile, displayFile, uploadFile, originalSize, compressedSize, data });
    } catch (err: unknown) {
      setState({
        phase: "error",
        originalFile,
        displayFile,
        uploadFile,
        originalSize,
        compressedSize,
        message: err instanceof Error ? err.message : "Unexpected error.",
      });
    }
  }, [state]);

  const onReset = useCallback(() => {
    setState({ phase: "idle" });
    setUploadKey((k) => k + 1);
  }, []);

  const isLoading = state.phase === "loading";
  const isCompressing = state.phase === "compressing";
  const hasFile = state.phase !== "idle" && state.phase !== "compressing";

  return (
    <div className="min-h-screen bg-slate-950">

      {/* ── Header ── */}
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-100">Document Verification Engine</h1>
              <p className="text-xs text-slate-500">OCR-powered identity document analysis</p>
            </div>
          </div>
          <span className="rounded-full bg-emerald-900/50 px-2.5 py-1 text-xs font-medium text-emerald-400">
            Live
          </span>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">

          {/* ── Left: Upload + Preview ── */}
          <div className="space-y-5">
            <div>
              <h2 className="text-base font-semibold text-slate-100">Upload Document</h2>
              <p className="mt-1 text-sm text-slate-500">
                Aadhaar · PAN · Passport · Driving Licence
              </p>
            </div>

            <UploadZone onFile={onFile} disabled={isLoading || isCompressing} resetKey={uploadKey} />

            {/* Compressing spinner */}
            {isCompressing && (
              <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3 text-sm text-slate-400">
                <svg className="h-4 w-4 animate-spin text-violet-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Compressing image…
              </div>
            )}

            {/* Document preview with size info.
                After verification, use the server-side compressed size so PDFs
                also show a compression comparison when the page was OCR-processed. */}
            {hasFile && "displayFile" in state && (
              <DocumentPreview
                file={state.displayFile}
                originalSize={state.originalSize}
                compressedSize={
                  state.phase === "result" && state.data?.file_info
                    ? state.data.file_info.compressed_size_bytes
                    : state.compressedSize
                }
              />
            )}

            {/* Action buttons */}
            <div className="flex gap-3">
              {(state.phase === "ready" || state.phase === "result" || state.phase === "error") && (
                <button
                  onClick={onVerify}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet-500 active:scale-95"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                  </svg>
                  {state.phase === "result" ? "Re-verify" : "Verify Document"}
                </button>
              )}
              {isLoading && (
                <button disabled className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-violet-600/60 px-5 py-3 text-sm font-semibold text-white opacity-70 cursor-not-allowed">
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  Analysing…
                </button>
              )}
              {(hasFile || isCompressing) && !isLoading && (
                <button
                  onClick={onReset}
                  className="rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-400 transition hover:border-slate-500 hover:text-slate-200"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* ── Right: Results ── */}
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-semibold text-slate-100">Verification Results</h2>
              <p className="mt-1 text-sm text-slate-500">Extracted fields and validation status</p>
            </div>

            {/* Idle */}
            {(state.phase === "idle" || state.phase === "compressing") && (
              <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-slate-800 py-20 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-900">
                  <svg className="h-6 w-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-400">No results yet</p>
                  <p className="mt-1 text-xs text-slate-600">Upload a document and click Verify</p>
                </div>
              </div>
            )}

            {/* Ready — waiting for verify click */}
            {state.phase === "ready" && (
              <StatusBanner
                color="border-violet-800 bg-violet-950/30 text-violet-300"
                icon={
                  <svg className="h-5 w-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
                title="Document ready"
                body="Click Verify Document to run OCR analysis and extract fields."
              />
            )}

            {/* Loading skeleton */}
            {isLoading && (
              <div className="space-y-4 animate-pulse">
                <div className="h-8 w-32 rounded-full bg-slate-800" />
                <div className="h-3 w-full rounded bg-slate-800" />
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="h-10 w-2/5 rounded-lg bg-slate-800" />
                      <div className="h-10 flex-1 rounded-lg bg-slate-800" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error */}
            {state.phase === "error" && (
              <StatusBanner
                color="border-red-800 bg-red-950/40 text-red-300"
                icon={
                  <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                }
                title="Processing failed"
                body={state.message}
              />
            )}

            {/* Results */}
            {state.phase === "result" && state.data && (
              <div className="space-y-5">
                {/* Doc type */}
                <div className="flex items-center rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3">
                  <DocTypeBadge type={state.data.document_type} />
                </div>

                {/* UNKNOWN — show clear message instead of empty results */}
                {state.data.document_type === "UNKNOWN" ? (
                  <div className="rounded-xl border border-amber-800 bg-amber-950/40 p-5">
                    <div className="flex items-start gap-3">
                      <svg className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                      </svg>
                      <div>
                        <p className="font-semibold text-amber-300">Document not recognised</p>
                        <p className="mt-1 text-sm text-amber-400">
                          The OCR could not extract enough text to identify this document.
                          Try uploading a clearer image or the front side of the document.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <ConfidenceBar value={state.data.confidence} />

                    <ValidationResult
                      status={state.data.validation.status}
                      missingFields={state.data.validation.missing_fields}
                    />

                    <div>
                      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
                        Extracted Fields
                      </p>
                      <ExtractedFields
                        fields={state.data.extracted_data}
                        fieldChecks={state.data.validation.field_checks}
                      />
                    </div>
                  </>
                )}

                {/* Raw JSON toggle */}
                <details className="group rounded-xl border border-slate-800">
                  <summary className="cursor-pointer select-none px-4 py-3 text-xs font-medium text-slate-500 hover:text-slate-300">
                    Raw JSON response
                  </summary>
                  <pre className="scrollbar-hide overflow-x-auto px-4 pb-4 text-xs text-slate-400">
                    {JSON.stringify(state.data, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>

        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="mt-16 border-t border-slate-800 px-6 py-6">
        <p className="text-center text-xs text-slate-600">
          Document Verification Engine — Powered by Tesseract OCR + FastAPI + Next.js
        </p>
      </footer>
    </div>
  );
}
