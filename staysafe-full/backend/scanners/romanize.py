"""
TrustLight - Indian words in English letters
--------------------------------------------
People often type Tulu, Kannada and Hindi in English letters ("yenk call battundu",
"nimma account block aagide", "aapka khata band ho jayega"). To recognise those words we
turn the Kannada-script and Devanagari word lists into English letters the way people
usually write them, and bring every spelling to one simple form:

    ಉಂಡು -> undu      ಮಾಡಿ -> madi      खाता -> khata -> kata
    "yer", "eer" -> er      "aagide" -> agide      "malpule" -> malpule

The simple form drops the differences people don't keep when typing (long/short vowels,
aspirated letters, doubled letters, a leading "y" before e), so "illa", "ila" and "illaa"
all match.
"""

import re

# --- Kannada script -> English letters ---------------------------------------------------------
_KN_VOWELS = {"ಅ": "a", "ಆ": "aa", "ಇ": "i", "ಈ": "ii", "ಉ": "u", "ಊ": "uu", "ಋ": "ru", "ಎ": "e", "ಏ": "ee",
              "ಐ": "ai", "ಒ": "o", "ಓ": "oo", "ಔ": "au"}
_KN_SIGNS = {"ಾ": "aa", "ಿ": "i", "ೀ": "ii", "ು": "u", "ೂ": "uu", "ೃ": "ru", "ೆ": "e", "ೇ": "ee", "ೈ": "ai",
             "ೊ": "o", "ೋ": "oo", "ೌ": "au"}
_KN_CONS = {"ಕ": "k", "ಖ": "kh", "ಗ": "g", "ಘ": "gh", "ಙ": "n", "ಚ": "ch", "ಛ": "chh", "ಜ": "j", "ಝ": "jh",
            "ಞ": "n", "ಟ": "t", "ಠ": "th", "ಡ": "d", "ಢ": "dh", "ಣ": "n", "ತ": "t", "ಥ": "th", "ದ": "d", "ಧ": "dh",
            "ನ": "n", "ಪ": "p", "ಫ": "ph", "ಬ": "b", "ಭ": "bh", "ಮ": "m", "ಯ": "y", "ರ": "r", "ಲ": "l", "ವ": "v",
            "ಶ": "sh", "ಷ": "sh", "ಸ": "s", "ಹ": "h", "ಳ": "l", "ೞ": "l", "ಱ": "r"}
_KN_VIRAMA, _KN_ANUSVARA, _KN_VISARGA = "್", "ಂ", "ಃ"

# --- Devanagari -> English letters ---------------------------------------------------------------
_HI_VOWELS = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu", "ऋ": "ri", "ए": "e", "ऐ": "ai",
              "ओ": "o", "औ": "au", "ऑ": "o"}
_HI_SIGNS = {"ा": "aa", "ि": "i", "ी": "ii", "ु": "u", "ू": "uu", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o",
             "ौ": "au", "ॉ": "o"}
_HI_CONS = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh",
            "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh",
            "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v",
            "श": "sh", "ष": "sh", "स": "s", "ह": "h", "क़": "k", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh",
            "फ़": "f", "य़": "y"}
_HI_VIRAMA, _HI_ANUSVARA, _HI_CHANDRA, _HI_NUKTA, _HI_VISARGA = "्", "ं", "ँ", "़", "ः"


def _transliterate(word: str, vowels, signs, cons, virama, anusvara_set, schwa_drop: bool) -> str:
    out = []
    chars = [c for c in word if c not in "‌‍"]
    i = 0
    while i < len(chars):
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if c in cons:
            base = cons[c]
            if nxt == _HI_NUKTA:          # क + ़ written as two characters
                base = cons.get(c + _HI_NUKTA, base)
                i += 1
                nxt = chars[i + 1] if i + 1 < len(chars) else ""
            if nxt == virama:
                out.append(base)
                i += 2
                continue
            if nxt in signs:
                out.append(base + signs[nxt])
                i += 2
                continue
            # inherent "a": Hindi drops it at the end of a word (कमल -> kamal)
            last = i + 1 >= len(chars) or chars[i + 1] in anusvara_set and i + 2 >= len(chars)
            out.append(base if (schwa_drop and last) else base + "a")
            i += 1
            continue
        if c in vowels:
            out.append(vowels[c])
        elif c in anusvara_set:
            out.append("n")
        i += 1
    return "".join(out)


def kannada_to_latin(word: str) -> str:
    return _transliterate(word, _KN_VOWELS, _KN_SIGNS, _KN_CONS, _KN_VIRAMA, {_KN_ANUSVARA, _KN_VISARGA}, False)


def devanagari_to_latin(word: str) -> str:
    return _transliterate(word, _HI_VOWELS, _HI_SIGNS, _HI_CONS, _HI_VIRAMA,
                          {_HI_ANUSVARA, _HI_CHANDRA, _HI_VISARGA}, True)


def to_latin(word: str) -> str:
    if re.search(r"[ಀ-೿]", word):
        return kannada_to_latin(word)
    if re.search(r"[ऀ-ॿ]", word):
        return devanagari_to_latin(word)
    return word


def latin_forms(word: str) -> set:
    """The simple spellings a word is typed with. Hindi drops the short 'a' inside words when
    spoken (आपका is said 'aapka', not 'aapaka'), so that form is added too."""
    lat = to_latin(word)
    forms = {simple(lat)}
    if re.search(r"[\u0900-\u097F]", word):
        forms.add(simple(re.sub(r"(?<=[aeiou][^aeiou])a(?=[^aeiouy][aeiou])", "", lat)))
    return {f for f in forms if f}


def simple(word: str) -> str:
    """One spelling for the ways people type the same word in English letters."""
    w = word.lower()
    w = re.sub(r"[^a-z]", "", w)
    w = re.sub(r"(?<=[kgcjtdpb])h", "", w)        # kh->k, bh->b, th->t (aspiration isn't kept when typing)
    w = w.replace("sh", "s").replace("w", "v").replace("z", "j").replace("q", "k").replace("x", "ks")
    w = w.replace("ph", "f").replace("f", "p")
    w = re.sub(r"^y(?=e)", "", w)                  # yenk/enk, yer/er
    w = re.sub(r"([a-z])\1+", r"\1", w)            # aa->a, ee->e, ll->l, tt->t
    w = w.replace("ii", "i").replace("uu", "u")
    w = w.replace("ou", "u").replace("au", "av")
    return w
