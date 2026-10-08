"""
TrustLight - RBI Alert List of unauthorised forex trading platforms
-------------------------------------------------------------------
The Reserve Bank of India lists apps and websites that are NOT allowed to offer forex trading
to people in India (FEMA). Fake "forex / binary option / trading tips" groups push exactly
these, and money lost on them is not protected.

A copy of the list ships with TrustLight (data/rbi_alert_list.json). Once a week the server also
reads RBI's own page and adds any new websites it finds there, so the list keeps up without
anyone editing the file. Names are matched in messages; websites are matched in links.
"""

import json
import os
import re
import threading
import time

import requests

RBI_PAGE = "https://rbi.org.in/scripts/bs_viewcontent.aspx?Id=4235"
REFRESH_SECONDS = 7 * 86400
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_state = {"entities": [], "domains": {}, "extra": 0, "loaded_at": 0.0, "loading": False,
          "problem": None, "updated": None}
_lock = threading.Lock()

TRADE_WORDS = re.compile(r"\b(forex|fx|trad(e|ing|er)|invest|profit|returns?|binary|option|crypto|signal|"
                         r"deposit|withdraw|broker|ट्रेडिंग|निवेश|ಟ್ರೇಡಿಂಗ್|ಹೂಡಿಕೆ)", re.IGNORECASE)


# stronger signs of a money-making pitch (for app names made of everyday words, like "Trust Trade")
MONEY_WORDS = re.compile(r"\b(forex|invest|profit|returns?|binary|crypto|signal|deposit|withdraw|earn|income|"
                         r"commission|vip|निवेश|मुनाफ़ा|ಹೂಡಿಕೆ|ಲಾಭ)", re.IGNORECASE)


def _base(domain: str) -> str:
    d = domain.lower().strip().strip("/")
    d = re.sub(r"^https?://", "", d).split("/")[0]
    return re.sub(r"^www\.", "", d)


def _load_bundled() -> None:
    try:
        data = json.load(open(os.path.join(_HERE, "data", "rbi_alert_list.json"), encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        _state["problem"] = f"bundled list: {type(e).__name__}"
        return
    ents = data.get("entities") or []
    domains = {}
    for e in ents:
        for d in e.get("domains") or []:
            domains[_base(d)] = e["name"]
    with _lock:
        _state.update(entities=ents, domains=domains, updated=data.get("updated"))


def _refresh_from_rbi() -> None:
    """Add websites from RBI's live page (names stay from the bundled copy)."""
    try:
        r = requests.get(RBI_PAGE, timeout=30, headers={"User-Agent": "Mozilla/5.0 TrustLight/2.0"})
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")
        found = set(_base(m) for m in re.findall(r"https?://[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", r.text))
        found = {d for d in found if not d.endswith(("rbi.org.in", "gov.in", "nic.in", "w3.org", "google.com",
                                                     "googleapis.com", "gstatic.com", "youtube.com", "twitter.com",
                                                     "x.com", "facebook.com", "linkedin.com", "instagram.com"))}
        if not 40 <= len(found) <= 400:     # page layout changed: keep what we have
            raise RuntimeError(f"only {len(found)} websites found")
        with _lock:
            new = []
            for d in sorted(found):
                if d not in _state["domains"]:
                    _state["domains"][d] = d
                    new.append(d)
            _state["extra"] = len(new)
            _state["extra_list"] = new[:20]
            _state["problem"] = None
    except Exception as e:  # noqa: BLE001
        _state["problem"] = f"RBI page: {type(e).__name__}: {str(e)[:60]}"
    finally:
        with _lock:
            _state["loaded_at"] = time.time()
            _state["loading"] = False


def ensure_loaded(offline: bool = False) -> None:
    if not _state["entities"]:
        _load_bundled()
    if offline:
        return
    with _lock:
        if _state["loading"] or time.time() - _state["loaded_at"] < REFRESH_SECONDS:
            return
        _state["loading"] = True
    threading.Thread(target=_refresh_from_rbi, daemon=True).start()


def domain_hit(host: str, reg: str, offline: bool = False):
    """The listed platform's name if this website is on the RBI Alert List, else None."""
    ensure_loaded(offline)
    h = _base(host or "")
    for cand in (h, _base(reg or "")):
        if cand and cand in _state["domains"]:
            return _state["domains"][cand]
    # subdomains of listed websites (in.puprime.com, hi.octafx.com)
    for d, name in _state["domains"].items():
        if h.endswith("." + d):
            return name
    return None


def names_in_text(text: str, offline: bool = False) -> list:
    """Listed platforms a message talks about (short names only in a trading context)."""
    ensure_loaded(offline)
    text = text or ""
    trading = TRADE_WORDS.search(text) is not None
    found = []
    for e in _state["entities"]:
        name = re.sub(r"\s+(limited|ltd\.?)$", "", e["name"], flags=re.I).strip()
        compact = re.sub(r"[^A-Za-z0-9]", "", name)
        if len(compact) < 5:
            # XM, FBS, XTB, FXCM...: only as a capitalised word in a message about trading
            if trading and re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text):
                found.append(e["name"])
            continue
        parts = [re.escape(p) for p in re.split(r"[\s.\-]+", name) if p]
        pattern = r"(?<![A-Za-z0-9])" + r"[\s.\-]?".join(parts) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            if e.get("domains") or MONEY_WORDS.search(text):   # app-only names (Trust Trade...) need a money pitch
                found.append(e["name"])
    return found[:3]


def status() -> dict:
    if not _state["entities"]:
        _load_bundled()
    return {"platforms": len(_state["entities"]), "websites": len(_state["domains"]),
            "added_from_rbi": _state["extra"], "added_websites": _state.get("extra_list", []), "list_date": _state["updated"], "problem": _state["problem"]}
