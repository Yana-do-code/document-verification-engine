const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface VerifyResponse {
  document_type: "AADHAAR" | "PAN" | "PASSPORT" | "DRIVING_LICENSE" | "UNKNOWN";
  extracted_data: Record<string, string | null>;
  validation: {
    status: "valid" | "invalid";
    missing_fields: string[];
    field_checks: Record<string, boolean>;
    name_match_score?: number;
  };
  confidence: number;
}

export async function verifyDocument(file: File): Promise<VerifyResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/api/v1/verify-document`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Verification failed");
  }

  return res.json();
}
