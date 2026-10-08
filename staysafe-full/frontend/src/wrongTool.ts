// "This belongs in another tool": open the right check and carry over what was pasted or uploaded.
import { getLastInput } from "@/api";
import { setPrefill, announcePrefill, type PrefillKind } from "@/helpBot";
import { handOffFile, handOffQr } from "@/share";

export type ToolId = "link" | "email" | "number" | "message" | "qr";

export const TOOL_PATH: Record<ToolId, string> = {
  link: "/scan-url", email: "/scan-email", number: "/check-number", message: "/scan-message", qr: "/scan-qr",
};
/** Translation key of each tool's name (nav labels). */
export const TOOL_LABEL: Record<ToolId, string> = {
  link: "nav.link", email: "nav.email", number: "nav.number", message: "nav.message", qr: "nav.qr",
};
const PREFILL: Partial<Record<ToolId, PrefillKind>> = { link: "url", message: "message", number: "number", email: "email" };

export function isToolId(v: string | undefined): v is ToolId {
  return !!v && v in TOOL_PATH;
}

/** Open `tool`, handing over the input (text, picture, or a QR code's text). */
export function goToTool(tool: ToolId, qrData?: string): void {
  const input = getLastInput();
  if (tool === "qr" && qrData) handOffQr(qrData);
  else if (tool === "message" && input.file) handOffFile("screenshot", input.file);
  else if (input.text && PREFILL[tool]) { setPrefill(PREFILL[tool]!, input.text); announcePrefill(); }
  window.location.hash = TOOL_PATH[tool];
  window.scrollTo({ top: 0 });
}

/** A web address and nothing else (for the email form's sender box). */
export function looksLikeLink(text: string): boolean {
  const v = text.trim();
  return !/\s/.test(v) && !v.includes("@") && (/^(https?:\/\/|www\.)\S+$/i.test(v) || /^([a-z0-9-]+\.)+[a-z]{2,}([/?#:]\S*)?$/i.test(v));
}

/** The same words the server uses (so the translations are shared). */
export const WRONG_TEXT: Record<ToolId, string> = {
  link: "This looks like a website link. Please check it in Check a Link.",
  email: "This looks like an email address. To check an email, use Check an Email.",
  number: "This looks like a phone number or UPI ID. Please check it in Check a Number or UPI ID.",
  message: "This looks like a message. Please check it in Check a Message.",
  qr: "This picture is a QR code. Please check it in Check a QR Code.",
};
