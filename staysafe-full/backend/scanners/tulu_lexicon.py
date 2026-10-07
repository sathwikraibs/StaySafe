"""
StaySafe - Tulu or Kannada? (both are written in Kannada letters)
--------------------------------------------------------------------
Uses open word-frequency lists from the Tulu and Kannada Wikipedias (Wikilangs, MIT licence),
downloaded when the server is built (scripts/fetch_lang_vocab.py). A word that is common in
Tulu writing but rare in Kannada (ಉಂಡು, ಬೊಕ್ಕ, ಇಜ್ಜಿ...) points to Tulu, and the other way round
(ಇದೆ, ಮತ್ತು, ಇಲ್ಲ...) points to Kannada. Words both languages share count for neither.

If the lists are missing, every function answers "don't know" and StaySafe keeps using its
built-in word lists.
"""

import math
import os
import re
import threading

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lock = threading.Lock()
_lex = {"loaded": False, "tcy": {}, "kn": {}, "hi": {}, "tcy_total": 0, "kn_total": 0, "hi_total": 0}
_latin = {"built": False, "index": {}, "totals": {}, "english": set()}
KANNADA_WORD = re.compile(r"[ಀ-೿‌‍]+")


def _load() -> None:
    with _lock:
        if _lex["loaded"]:
            return
        for lang in ("tcy", "kn", "hi"):
            path = os.path.join(_HERE, "data", f"lexicon_{lang}.tsv")
            counts = {}
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        w, _, c = line.rstrip("\n").partition("\t")
                        if w and c.isdigit():
                            counts[_norm(w)] = counts.get(_norm(w), 0) + int(c)
            except OSError:
                counts = {}
            _lex[lang] = counts
            _lex[f"{lang}_total"] = sum(counts.values())
        _lex["loaded"] = True


def _norm(word: str) -> str:
    return word.replace("‌", "").replace("‍", "").strip()


def available() -> bool:
    _load()
    return bool(_lex["tcy"]) and bool(_lex["kn"])


def _rel(lang: str, word: str) -> float:
    """Relative frequency with smoothing, so unseen words don't explode the ratio."""
    return (_lex[lang].get(word, 0) + 0.5) / (_lex[f"{lang}_total"] + 1)


def lean(text: str):
    """
    ('tcy' | 'kn' | None, strength). Strength is the average evidence per telling word;
    None when there are too few telling words or the evidence is weak.
    """
    if not available():
        return None, 0.0
    words = [_norm(w) for w in KANNADA_WORD.findall(text or "")]
    evidence = []
    for w in words:
        if len(w) < 2:
            continue
        in_t, in_k = w in _lex["tcy"], w in _lex["kn"]
        if not in_t and not in_k:
            continue
        llr = math.log(_rel("tcy", w) / _rel("kn", w))
        if abs(llr) >= 1.5:          # only words that clearly belong more to one language
            evidence.append(max(-6.0, min(6.0, llr)))
    if len(evidence) < 2:
        return None, 0.0
    total = sum(evidence)
    strength = abs(total) / len(evidence)
    if abs(total) < 4.0 or strength < 1.2:
        return None, strength
    return ("tcy" if total > 0 else "kn"), strength


def kannada_only_words(text: str, limit: int = 8) -> list:
    """Words in a Tulu answer that are common Kannada and (almost) never written in Tulu."""
    if not available():
        return []
    out = []
    for w in KANNADA_WORD.findall(text or ""):
        n = _norm(w)
        if len(n) < 3 or n in out:
            continue
        k, t = _lex["kn"].get(n, 0), _lex["tcy"].get(n, 0)
        if k >= 200 and math.log(_rel("kn", n) / _rel("tcy", n)) >= 3.0:
            out.append(n)
        if len(out) >= limit:
            break
    return out


def status() -> dict:
    _load()
    return {"tulu_words": len(_lex["tcy"]), "kannada_words": len(_lex["kn"]), "hindi_words": len(_lex["hi"])}


# --- The same languages typed in English letters --------------------------------------------------
LATIN_LANGS = ("tcy", "kn", "hi")
# Common chat English that must never count as an Indian word
_EXTRA_ENGLISH = {"ok", "okay", "pls", "plz", "sir", "madam", "bro", "hi", "hello", "thanks", "thank", "you", "the",
                  "account", "bank", "link", "otp", "upi", "kyc", "call", "msg", "message", "app", "number", "money",
                  "pay", "paid", "send", "sent", "block", "blocked", "update", "loan", "job", "card", "pin"}


def _english_words() -> set:
    try:
        from zxcvbn.frequency_lists import FREQUENCY_LISTS as F
        words = set(F["english_wikipedia"][:20000]) | set(F["us_tv_and_film"][:20000])
    except Exception:
        words = set()
    return {w for w in words if len(w) >= 2} | _EXTRA_ENGLISH


def _build_latin() -> None:
    """Index of the word lists in English letters (simple spelling -> count per language)."""
    _load()
    with _lock:
        if _latin["built"]:
            return
        from scanners.romanize import latin_forms, simple
        english = {simple(w) for w in _english_words()}
        index, totals = {}, {}
        for lang in LATIN_LANGS:
            total = 0
            for word, count in _lex[lang].items():
                if not re.search(r"[\u0900-\u097F\u0C80-\u0CFF]", word):
                    continue                  # Latin-letter words in the lists are mostly English
                for key in latin_forms(word):
                    if len(key) < 3 or key in english:
                        continue
                    slot = index.setdefault(key, {})
                    slot[lang] = slot.get(lang, 0) + count
                total += count
            totals[lang] = total
        _latin.update(built=True, index=index, totals=totals, english=english)


def latin_available() -> bool:
    _build_latin()
    return sum(1 for lang in LATIN_LANGS if _latin["totals"].get(lang)) >= 2


def _latin_keys(text: str):
    from scanners.romanize import simple
    for raw in re.findall(r"[A-Za-z]+", text or ""):
        key = simple(raw)
        if len(key) >= 3 and key not in _latin["english"]:
            yield key


def latin_lean(text: str):
    """
    ('tcy' | 'kn' | 'hi' | None, strength) for a message typed in English letters.
    Each word votes for the language that uses it much more than the others.
    """
    if not latin_available():
        return None, 0.0
    langs = [lang for lang in LATIN_LANGS if _latin["totals"].get(lang)]
    votes = {lang: 0.0 for lang in langs}
    telling = 0
    for key in _latin_keys(text):
        counts = _latin["index"].get(key)
        if not counts:
            continue
        rel = {lang: (counts.get(lang, 0) + 0.5) / (_latin["totals"][lang] + 1) for lang in langs}
        ranked = sorted(rel, key=rel.get, reverse=True)
        margin = math.log(rel[ranked[0]] / rel[ranked[1]])
        if margin >= 1.5:
            votes[ranked[0]] += min(margin, 6.0)
            telling += 1
    if telling < 2:
        return None, 0.0
    ranked = sorted(votes, key=votes.get, reverse=True)
    lead = votes[ranked[0]] - votes[ranked[1]]
    if lead < 4.0:
        return None, lead
    return ranked[0], lead / telling


def romanized_indic(text: str) -> bool:
    """True when most words of an English-letters message are Indian-language words, not English."""
    if not latin_available():
        return False
    from scanners.romanize import simple
    words = [simple(w) for w in re.findall(r"[A-Za-z]{3,}", text or "")]
    if len(words) < 3:
        return False
    indic = sum(1 for k in words if k not in _latin["english"] and k in _latin["index"])
    english = sum(1 for k in words if k in _latin["english"])
    return indic >= 2 and indic >= english * 0.6 and indic / len(words) >= 0.3


def kannada_only_latin(text: str, limit: int = 8) -> list:
    """Kannada words in a Tulu answer typed in English letters (e.g. 'madi', 'nimma', 'mattu')."""
    if not latin_available() or not _latin["totals"].get("tcy") or not _latin["totals"].get("kn"):
        return []
    out = []
    for raw in re.findall(r"[A-Za-z]+", text or ""):
        from scanners.romanize import simple
        key = simple(raw)
        counts = _latin["index"].get(key) if len(key) >= 3 and key not in _latin["english"] else None
        if not counts:
            continue
        k, t = counts.get("kn", 0), counts.get("tcy", 0)
        rk = (k + 0.5) / (_latin["totals"]["kn"] + 1)
        rt = (t + 0.5) / (_latin["totals"]["tcy"] + 1)
        if k >= 200 and math.log(rk / rt) >= 3.0 and raw.lower() not in out:
            out.append(raw.lower())
        if len(out) >= limit:
            break
    return out


def unusual_words(text: str, lang: str, limit: int = 6) -> list:
    """Words in a Kannada or Hindi answer that the language's word list has never seen:
    often a spelling mistake (a hint for the proofreading step, never changed on its own)."""
    _load()
    vocab = _lex.get(lang) or {}
    if len(vocab) < 20000:
        return []
    pattern = r"[\u0C80-\u0CFF\u200c\u200d]+" if lang == "kn" else r"[\u0900-\u097F]+"
    out = []
    for w in re.findall(pattern, text or ""):
        n = _norm(w)
        if len(n) >= 3 and n not in vocab and n not in out:
            out.append(n)
        if len(out) >= limit:
            break
    return out
