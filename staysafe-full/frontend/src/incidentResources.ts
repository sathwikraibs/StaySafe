// Official download / help links shown under the steps of each recovery plan.
// Only official app stores, company websites and Government of India portals.
// Keyed by incident id, then by step number (0 = first step).

export type ResourceKind = "download" | "open" | "guide" | "call" | "report";
export type Platform = "android" | "iphone" | "windows";

export interface Resource {
  kind: ResourceKind;
  name: string;
  /** key under resources.desc in the language files */
  desc: string;
  url: string;
  platform?: Platform;
  govt?: boolean;
}

const R: Record<string, Resource> = {
  playProtect: {
    kind: "guide", name: "Google Play Protect", desc: "playProtect", platform: "android",
    url: "https://support.google.com/googleplay/answer/2812853",
  },
  malwarebytesAndroid: {
    kind: "download", name: "Malwarebytes Mobile Security", desc: "malwarebytesAndroid", platform: "android",
    url: "https://play.google.com/store/apps/details?id=org.malwarebytes.antimalware",
  },
  mkavach: {
    kind: "download", name: "M-Kavach 2", desc: "mkavach", platform: "android", govt: true,
    url: "https://play.google.com/store/apps/details?id=org.cdac.updatemkavach",
  },
  escan: {
    kind: "download", name: "eScan Smartphone Safety Toolkit", desc: "escan", platform: "android", govt: true,
    url: "https://play.google.com/store/apps/details?id=com.eScanAV.certin",
  },
  malwarebytesWindows: {
    kind: "download", name: "Malwarebytes Free", desc: "malwarebytesWindows", platform: "windows",
    url: "https://www.malwarebytes.com/mwb-download",
  },
  quickhealBot: {
    kind: "download", name: "Quick Heal Bot Removal Tool", desc: "quickhealBot", platform: "windows", govt: true,
    url: "https://www.quickheal.co.in/bot-removal-tool",
  },
  googleCheckup: {
    kind: "open", name: "Google Security Checkup", desc: "googleCheckup",
    url: "https://myaccount.google.com/security-checkup",
  },
  googleDevices: {
    kind: "open", name: "Google: your devices", desc: "googleDevices",
    url: "https://myaccount.google.com/device-activity",
  },
  googlePassword: {
    kind: "open", name: "Google password", desc: "googlePassword",
    url: "https://myaccount.google.com/signinoptions/password",
  },
  google2sv: {
    kind: "open", name: "Google 2-Step Verification", desc: "google2sv",
    url: "https://myaccount.google.com/signinoptions/two-step-verification",
  },
  authenticatorAndroid: {
    kind: "download", name: "Google Authenticator", desc: "authenticator", platform: "android",
    url: "https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2",
  },
  authenticatorIphone: {
    kind: "download", name: "Google Authenticator", desc: "authenticator", platform: "iphone",
    url: "https://apps.apple.com/app/google-authenticator/id388497605",
  },
  hibp: {
    kind: "open", name: "Have I Been Pwned", desc: "hibp",
    url: "https://haveibeenpwned.com/",
  },
  call1930: {
    kind: "call", name: "1930", desc: "call1930", govt: true,
    url: "tel:1930",
  },
  cybercrime: {
    kind: "report", name: "cybercrime.gov.in", desc: "cybercrime", govt: true,
    url: "https://cybercrime.gov.in/",
  },
  chakshu: {
    kind: "report", name: "Chakshu, Sanchar Saathi", desc: "chakshu", govt: true,
    url: "https://sancharsaathi.gov.in/sfc/",
  },
  rbiCms: {
    kind: "report", name: "RBI Complaint Management System", desc: "rbiCms", govt: true,
    url: "https://cms.rbi.org.in/",
  },
  fbHacked: {
    kind: "open", name: "facebook.com/hacked", desc: "fbHacked",
    url: "https://www.facebook.com/hacked",
  },
  igHacked: {
    kind: "open", name: "instagram.com/hacked", desc: "igHacked",
    url: "https://www.instagram.com/hacked/",
  },
};

const VIRUS_SCAN = [R.playProtect, R.malwarebytesAndroid, R.mkavach, R.malwarebytesWindows, R.quickhealBot];
const REPORT_FRAUD = [R.call1930, R.cybercrime];

export const STEP_RESOURCES: Record<string, Record<number, Resource[]>> = {
  clicked_link: {
    2: VIRUS_SCAN,
    3: [R.googleCheckup, R.googleDevices],
  },
  entered_password: {
    0: [R.googlePassword, R.googleCheckup],
    1: [R.hibp],
    2: [R.google2sv, R.authenticatorAndroid, R.authenticatorIphone],
    3: [R.googleDevices],
  },
  entered_card_details: {
    0: [R.call1930],
    2: [R.cybercrime, R.rbiCms],
  },
  shared_otp: {
    1: [R.call1930],
    3: REPORT_FRAUD,
    4: [R.chakshu],
  },
  installed_app: {
    4: [R.playProtect, R.malwarebytesAndroid, R.mkavach, R.escan],
    5: [R.googleCheckup, R.googlePassword],
  },
  gave_remote_access: {
    3: [R.googleCheckup, R.googleDevices],
    5: [...REPORT_FRAUD, R.chakshu],
  },
  money_transferred: {
    0: [R.call1930],
    1: REPORT_FRAUD,
    4: [R.google2sv, R.authenticatorAndroid, R.authenticatorIphone],
  },
  account_accessed: {
    0: [R.googlePassword, R.fbHacked, R.igHacked],
    1: [R.googleDevices],
    2: [R.google2sv, R.authenticatorAndroid, R.authenticatorIphone],
    3: [R.googleCheckup],
  },
};
