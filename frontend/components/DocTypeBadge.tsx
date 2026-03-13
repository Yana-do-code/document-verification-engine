const COLORS: Record<string, string> = {
  AADHAAR:         "bg-blue-900/60 text-blue-300 border-blue-700",
  PAN:             "bg-amber-900/60 text-amber-300 border-amber-700",
  PASSPORT:        "bg-emerald-900/60 text-emerald-300 border-emerald-700",
  DRIVING_LICENSE: "bg-purple-900/60 text-purple-300 border-purple-700",
  UNKNOWN:         "bg-slate-800 text-slate-400 border-slate-700",
};

const LABELS: Record<string, string> = {
  AADHAAR:         "Aadhaar Card",
  PAN:             "PAN Card",
  PASSPORT:        "Passport",
  DRIVING_LICENSE: "Driving License",
  UNKNOWN:         "Unknown",
};

export default function DocTypeBadge({ type }: { type: string }) {
  const color = COLORS[type] ?? COLORS.UNKNOWN;
  const label = LABELS[type] ?? type;
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${color}`}>
      {label}
    </span>
  );
}
