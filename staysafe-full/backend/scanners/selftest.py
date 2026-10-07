"""
StaySafe - live accuracy test for the owner
--------------------------------------------
Open on the live server (needs the secret STATUS_KEY):

    /api/selftest/links?key=<STATUS_KEY>              list of test groups
    /api/selftest/links?key=<STATUS_KEY>&set=1        run group 1 (about a minute)
    /api/selftest/links?key=<STATUS_KEY>&url=a.com&url=b.com   check your own links

Every link is checked exactly like a visitor's link (all lists, Google, VirusTotal, Cloudflare,
website age...). The answer is short so it can be copied and pasted back for review.
"""

import random
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, request

selftest_bp = Blueprint("selftest", __name__)

# Separate workers, so a test never slows down real visitors' checks
_POOL = ThreadPoolExecutor(max_workers=6)
DEADLINE = 150          # the server stops any request at 180 s

SAFE, CAUTION, DANGEROUS = "SAFE", "CAUTION", "DANGEROUS"
NOT_SAFE = "NOT_SAFE"   # CAUTION or DANGEROUS are both right

LINK_SETS = {
    "1": ("Genuine Indian banks, payments and government", [
        ("https://www.onlinesbi.sbi", SAFE), ("https://www.hdfcbank.com", SAFE),
        ("https://www.incometax.gov.in/iec/foportal/", SAFE), ("https://www.karnatakabank.com", SAFE),
        ("https://paytm.com", SAFE), ("https://www.phonepe.com", SAFE),
    ]),
    "2": ("Genuine shops, local news, universities and share links", [
        ("https://www.amazon.in", SAFE), ("https://www.flipkart.com", SAFE),
        ("https://www.udayavani.com", SAFE), ("https://presidencyuniversity.in", SAFE),
        ("https://youtu.be/dQw4w9WgXcQ", SAFE), ("https://wa.me/919876543210", SAFE),
    ]),
    "3": ("Genuine but less known, or our own site", [
        ("https://staysafe-tool.vercel.app", SAFE), ("https://tcy.wikipedia.org", SAFE),
        ("https://mescom.karnataka.gov.in", SAFE), ("https://groww.in", SAFE),
        ("https://github.com/sathwikraibs/StaySafe", SAFE), ("https://www.mangaloretoday.com", SAFE),
    ]),
    "4": ("Known dangerous test pages (made by Google and others for testing)", [
        ("https://testsafebrowsing.appspot.com/s/phishing.html", DANGEROUS),
        ("https://testsafebrowsing.appspot.com/s/malware.html", DANGEROUS),
        ("https://www.google.com/url?q=https://testsafebrowsing.appspot.com/s/phishing.html", DANGEROUS),
        ("http://malware.wicar.org/data/eicar.com", NOT_SAFE),
        ("https://www.octafx.com", DANGEROUS), ("https://exness.com", DANGEROUS),
    ]),
    "5": ("Fake Indian scam addresses (most do not exist, as scam sites are taken down quickly)", [
        ("https://sbi-kyc-update-2026.xyz/login", DANGEROUS), ("https://hdfcbank-reward-points.top", DANGEROUS),
        ("https://incometax-refund-gov.in/claim", DANGEROUS), ("https://dtdc-courier-redelivery.com", NOT_SAFE),
        ("https://www.sbi.co.in@sbi-kyc.online/login", DANGEROUS), ("https://bescom-bill-disconnection.com", DANGEROUS),
    ]),
    "6": ("Tricky: app downloads, short links, free hosting", [
        ("https://f-droid.org/F-Droid.apk", NOT_SAFE),
        ("https://drive.google.com/uc?id=1xyz&export=download&name=SBI_YONO.apk", NOT_SAFE),
        ("https://sbi-rewards.firebaseapp.com", DANGEROUS), ("https://sites.google.com/view/sbi-kyc-update", NOT_SAFE),
        ("https://bit.ly/3sbi-kyc", NOT_SAFE), ("https://hdfc-kyc.trycloudflare.com", DANGEROUS),
    ]),
    "7": ("Real scam links reported in the last few hours (picked from today's public lists)", None),
    "8": ("Big shared websites that scammers also misuse (the websites themselves are fine)", [
        ("https://github.com/sathwikraibs/StaySafe", SAFE), ("https://www.karnatakabank.com", SAFE),
        ("https://raw.githubusercontent.com/python/cpython/main/README.rst", SAFE),
        ("https://docs.google.com/document/u/0/", SAFE), ("https://www.dropbox.com/home", SAFE),
        ("https://bit.ly/", SAFE),
    ]),
}


def _fresh_scam_links(n=6):
    """A few links from today's OpenPhish / URLhaus lists, so the test uses live scams."""
    from scanners import url_scanner as u
    u.ensure_feeds()
    keys = [k for k, src in list(u._FEEDS.get("urls", {}).items()) if src in ("OpenPhish", "URLhaus")]
    random.shuffle(keys)
    return [("http://" + k, DANGEROUS) for k in keys[:n]]


def _right(expect, verdict):
    if expect is None:
        return None
    if expect == NOT_SAFE:
        return verdict in (CAUTION, DANGEROUS)
    return verdict == expect


def _one(url, expect):
    from scanners.url_scanner import scan_url
    t = time.time()
    try:
        r = scan_url(url)
    except Exception as e:
        return {"url": url, "expected": expect, "verdict": "ERROR", "right": False,
                "error": f"{type(e).__name__}: {str(e)[:120]}"}
    checks = {c["id"]: c["status"] for c in r.get("checks", [])}
    return {
        "url": url[:140], "expected": expect, "verdict": r["verdict"], "score": r["risk_score"],
        "right": _right(expect, r["verdict"]), "seconds": round(time.time() - t, 1),
        "why": [f[:160] for f in r.get("findings", [])[:4]],
        "checks": checks,
        "final_url": (r.get("details") or {}).get("final_url") or None,
    }


@selftest_bp.route("/api/selftest/links", methods=["GET"])
def selftest_links_route():
    from scanners.security import has_status_key
    if not has_status_key():
        return jsonify({"error": "Not found"}), 404
    own = [u.strip() for u in request.args.getlist("url") if u.strip()][:6]
    pick = str(request.args.get("set") or "").strip()
    if own:
        cases, title = [(u, None) for u in own], "Your links"
    elif pick in LINK_SETS:
        title, cases = LINK_SETS[pick]
        if cases is None:
            cases = _fresh_scam_links()
            if not cases:
                return jsonify({"set": pick, "error": "Today's public lists are still loading. Open again in a minute."})
    else:
        return jsonify({"how": "Add &set=1 (then 2, 3 ... 8) to the address, or &url=<link> to check your own (up to 6).",
                        "sets": {k: v[0] for k, v in LINK_SETS.items()}})
    began = time.time()
    futures = [(u, e, _POOL.submit(_one, u, e)) for u, e in cases]
    results = []
    for u, e, f in futures:
        try:
            results.append(f.result(timeout=max(1, DEADLINE - (time.time() - began))))
        except Exception:
            results.append({"url": u, "expected": e, "verdict": "STILL_RUNNING", "right": None,
                            "note": "Took too long this time. Open the same address again, it will be quick."})
    graded = [r for r in results if r.get("right") is not None]
    return jsonify({
        "set": pick or "own", "title": title,
        "right": f"{sum(1 for r in graded if r['right'])}/{len(graded)}",
        "wrong": [r["url"] for r in graded if not r["right"]],
        "seconds": round(time.time() - began, 1),
        "results": results,
    })
