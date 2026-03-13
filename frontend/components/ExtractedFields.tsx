const FIELD_LABELS: Record<string, string> = {
  aadhaar_number:   "Aadhaar Number",
  pan_number:       "PAN Number",
  passport_number:  "Passport Number",
  dl_number:        "DL Number",
  name:             "Name",
  fathers_name:     "Father's Name",
  dob:              "Date of Birth",
  gender:           "Gender",
  nationality:      "Nationality",
  expiry:           "Expiry Date",
  place_of_birth:   "Place of Birth",
  place_of_issue:   "Place of Issue",
  address:          "Address",
  vehicle_classes:  "Vehicle Classes",
};

interface Props {
  fields: Record<string, string | null>;
  fieldChecks: Record<string, boolean>;
}

export default function ExtractedFields({ fields, fieldChecks }: Props) {
  const entries = Object.entries(fields).filter(([, v]) => v !== null && v !== undefined);

  if (entries.length === 0) {
    return (
      <p className="rounded-lg bg-slate-800/50 px-4 py-6 text-center text-sm text-slate-500">
        No fields could be extracted.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800">
      <table className="w-full text-sm">
        <tbody className="divide-y divide-slate-800">
          {entries.map(([key, value]) => {
            const required = key in fieldChecks;
            const ok = fieldChecks[key];
            return (
              <tr key={key} className="group transition-colors hover:bg-slate-800/40">
                <td className="w-2/5 px-4 py-3 text-slate-400">
                  <span className="flex items-center gap-2">
                    {required && (
                      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
                    )}
                    {FIELD_LABELS[key] ?? key.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3 font-medium text-slate-100 break-all">{value}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
