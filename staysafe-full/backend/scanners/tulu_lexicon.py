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
_lex = {"loaded": False, "tcy": {}, "kn": {}, "tcy_total": 0, "kn_total": 0}
KANNADA_WORD = re.compile(r"[ಀ-೿‌‍]+")


def _load() -> None:
    with _lock:
        if _lex["loaded"]:
            return
        for lang in ("tcy", "kn"):
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
    return {"tulu_words": len(_lex["tcy"]), "kannada_words": len(_lex["kn"])}
