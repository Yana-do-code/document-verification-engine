interface Props {
  status: "valid" | "invalid";
  missingFields: string[];
}

const FIELD_LABELS: Record<string, string> = {
  aadhaar_number: "Aadhaar Number",
  pan_number: "PAN Number",
  passport_number: "Passport Number",
  dl_number: "DL Number",
  name: "Name",
  dob: "Date of Birth",
  nationality: "Nationality",
};

export default function ValidationResult({ status, missingFields }: Props) {
  const isValid = status === "valid";
  return (
    <div
      className={`rounded-xl border p-4 ${
        isValid
          ? "border-emerald-800 bg-emerald-950/40"
          : "border-red-800 bg-red-950/40"
      }`}
    >
      <div className="flex items-center gap-3">
        {isValid ? (
          <svg className="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ) : (
          <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        )}
        <div>
          <p className={`font-semibold ${isValid ? "text-emerald-300" : "text-red-300"}`}>
            {isValid ? "Document Verified" : "Verification Failed"}
          </p>
          {!isValid && missingFields.length > 0 && (
            <p className="mt-0.5 text-xs text-red-400">
              Missing:{" "}
              {missingFields.map((f) => FIELD_LABELS[f] ?? f).join(", ")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
