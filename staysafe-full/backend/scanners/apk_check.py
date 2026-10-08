"""
TrustLight - What an Android app (APK) asks to do, read offline
----------------------------------------------------------------
Fake "wedding card", "RTO challan", "bank KYC" and "electricity bill" apps sent on WhatsApp are
among the most common scams in India. Once installed they read your SMS (bank OTPs), take over
the screen through Accessibility, or read notifications, and then empty the bank account.

Every APK has a small AndroidManifest.xml (stored in Android's compact binary XML format) that
lists the app's package name and the permissions it needs. We read it here with a tiny parser,
no extra library and no upload anywhere.
"""

import io
import re
import struct
import zipfile

import requests

from scanners.security import safe_zip_read

# permission -> (plain-language finding, score)
RISKY_PERMISSIONS = {
    "android.permission.RECEIVE_SMS": ("can read your incoming SMS, including bank OTPs", 35),
    "android.permission.READ_SMS": ("can read your incoming SMS, including bank OTPs", 35),
    "android.permission.SEND_SMS": ("can send SMS from your phone without you knowing", 20),
    "android.permission.BIND_ACCESSIBILITY_SERVICE": ("can see and control everything on your screen (Accessibility)", 35),
    "android.permission.BIND_NOTIFICATION_LISTENER_SERVICE": ("can read all your notifications, including OTPs", 25),
    "android.permission.BIND_DEVICE_ADMIN": ("asks to become a device administrator, which makes it hard to remove", 25),
    "android.permission.SYSTEM_ALERT_WINDOW": ("can draw over other apps, used to show fake login screens", 15),
    "android.permission.READ_CALL_LOG": ("can read your call history", 10),
    "android.permission.CALL_PHONE": ("can make phone calls (used to forward your calls)", 10),
    "android.permission.READ_CONTACTS": ("can read your contacts", 10),
    "android.permission.REQUEST_INSTALL_PACKAGES": ("can install other apps", 10),
}
BRAND_WORDS = re.compile(
    r"(sbi|yono|hdfc|icici|axis|kotak|canara|pnb|baroda|bank|kyc|aadhaa?r|pan ?card|rto|challan|parivahan|"
    r"fastag|electricity|bescom|mseb|income ?tax|refund|pm ?kisan|police|customs|courier|"
    r"wedding|invitation|reward|redeem|loan|paytm|phonepe|gpay|upi)", re.IGNORECASE)


def _strings(chunk: bytes):
    """Decode an Android string pool chunk."""
    header_size, size = struct.unpack_from("<HI", chunk, 2)
    count, _styles, flags, strings_start, _ = struct.unpack_from("<IIIII", chunk, 8)
    utf8 = bool(flags & 0x100)
    offsets = struct.unpack_from(f"<{count}I", chunk, header_size)
    out = []
    for off in offsets:
        pos = strings_start + off
        try:
            if utf8:
                n = chunk[pos]
                pos += 2 if n & 0x80 else 1           # length in UTF-16 units (skipped)
                n = chunk[pos]
                if n & 0x80:
                    n = ((n & 0x7F) << 8) | chunk[pos + 1]
                    pos += 2
                else:
                    pos += 1
                out.append(chunk[pos:pos + n].decode("utf-8", "replace"))
            else:
                n = struct.unpack_from("<H", chunk, pos)[0]
                pos += 2
                if n & 0x8000:
                    n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", chunk, pos)[0]
                    pos += 2
                out.append(chunk[pos:pos + n * 2].decode("utf-16-le", "replace"))
        except Exception:
            out.append("")
    return out


def read_manifest(axml: bytes) -> dict:
    """{'package': str, 'permissions': [..]} from a binary AndroidManifest.xml."""
    info = {"package": "", "permissions": []}
    if len(axml) < 8 or struct.unpack_from("<H", axml, 0)[0] != 0x0003:
        return info
    pos = struct.unpack_from("<H", axml, 2)[0]
    strings = []
    while pos + 8 <= len(axml):
        ctype, hsize, csize = struct.unpack_from("<HHI", axml, pos)
        if csize < 8:
            break
        chunk = axml[pos:pos + csize]
        if ctype == 0x0001:                           # string pool
            strings = _strings(chunk)
        elif ctype == 0x0102 and strings:             # start of an element
            name_idx = struct.unpack_from("<I", chunk, 20)[0]
            attr_start, attr_size, attr_count = struct.unpack_from("<HHH", chunk, 24)
            tag = strings[name_idx] if name_idx < len(strings) else ""
            if tag == "manifest":
                for i in range(attr_count):
                    a = 16 + attr_start + i * max(attr_size, 20)
                    _ns, aname, raw = struct.unpack_from("<III", chunk, a)
                    if aname < len(strings) and strings[aname] == "package" and raw < len(strings):
                        info["package"] = strings[raw]
        pos += csize
    info["permissions"] = sorted({s for s in strings if s.startswith("android.permission.")})
    return info


PLAY_URL = "https://play.google.com/store/apps/details"
_PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")
_play_cache: dict = {}


def on_play_store(package: str):
    """True / False: is there a Play Store app with this exact package name? None: couldn't tell."""
    from scanners import url_scanner
    from scanners.quota import quota
    if url_scanner.OFFLINE or not package or not _PACKAGE.match(package):
        return None
    if package in _play_cache:
        return _play_cache[package]
    if not quota("play_store").take(wait=3):
        return None
    try:
        r = requests.get(PLAY_URL, params={"id": package, "hl": "en", "gl": "IN"}, timeout=6,
                         headers={"User-Agent": url_scanner.USER_AGENT}, allow_redirects=True)
    except Exception:
        return None
    answer = True if r.status_code == 200 else False if r.status_code == 404 else None
    if answer is not None:
        _play_cache[package] = answer
        if len(_play_cache) > 2000:
            _play_cache.clear()
    return answer


NOT_ON_PLAY = ("This app uses the name of a bank, payment app or government office, but no app called "
               "{package} exists on the Google Play Store. Fake apps sent on WhatsApp work like this")


def analyze_apk(filename: str, data: bytes) -> dict:
    """Findings and score for an Android app file."""
    out = {"findings": [], "score": 0, "package": "", "permissions": [], "points": {}}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            manifest = read_manifest(safe_zip_read(z, "AndroidManifest.xml", 2 * 1024 * 1024))
    except Exception:
        return out
    out["package"], out["permissions"] = manifest["package"], manifest["permissions"]

    seen, total, each = [], 0, {}
    for perm in manifest["permissions"]:
        if perm in RISKY_PERMISSIONS:
            text, points = RISKY_PERMISSIONS[perm]
            if text not in seen:
                seen.append(text)
                total += points
                each[f"This app {text}"] = points
    if seen:
        out["findings"].extend(f"This app {text}" for text in seen[:4])
        perms = set(manifest["permissions"])
        steals_otp = perms & {"android.permission.RECEIVE_SMS", "android.permission.READ_SMS",
                              "android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"}
        controls = perms & {"android.permission.BIND_ACCESSIBILITY_SERVICE", "android.permission.SYSTEM_ALERT_WINDOW"}
        if steals_otp and controls:
            total += 20  # reading OTPs AND controlling the screen is the typical banking-trojan combo
        out["score"] += min(70, total)
        shown = out["findings"][-len(seen[:4]):]
        for f in shown:
            out["points"][f] = each.get(f, 0)
        # the combo bonus and the 70-point cap go to the first line
        out["points"][shown[0]] += min(70, total) - sum(out["points"][f] for f in shown)

    who = (filename or "") + " " + manifest["package"]
    if BRAND_WORDS.search(who):
        out["findings"].append(
            "Banks, RTO, electricity boards and government offices never send apps as files. "
            "Install apps only from the Play Store")
        out["score"] += 25
        out["points"][out["findings"][-1]] = 25
        # Real bank and government apps are on the Play Store under their own name: check
        if on_play_store(manifest["package"]) is False:
            text = NOT_ON_PLAY.format(package=manifest["package"])
            out["findings"].insert(0, text)
            out["score"] += 20
            out["points"][text] = 20
    return out
