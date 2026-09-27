// The file checker reports what a file really is ("Windows program", "an Android app"...).
// This adds translations for each type name, with and without "a"/"an" in front.
export function withFileTypes(types: Record<string, string>, table: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = { ...table };
  for (const [en, tr] of Object.entries(types)) {
    out[en] = tr;
    out[`a ${en}`] = tr;
    out[`an ${en}`] = tr;
  }
  return out;
}
