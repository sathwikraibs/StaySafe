"""
Build-time helper (runs inside the Docker build, never on a visitor's request):
downloads the open Tulu and Kannada Wikipedia word-frequency lists from Wikilangs
(https://huggingface.co/wikilangs, MIT licence) and keeps them as small text files:
    data/lexicon_tcy.tsv   data/lexicon_kn.tsv      (word<TAB>count, most frequent first)
StaySafe uses them to tell Tulu from Kannada (both use Kannada letters) and to spot
Kannada words that slip into Tulu answers. If the download fails, the build carries on
and StaySafe falls back to its built-in word lists.
"""
import io
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data")
KEEP = {"tcy": 60000, "kn": 80000}


def fetch(lang: str) -> bool:
    url = f"https://huggingface.co/wikilangs/{lang}/resolve/main/models/vocabulary/{lang}_vocabulary.parquet"
    try:
        import pyarrow.parquet as pq
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "StaySafe-build"}),
                                     timeout=120).read()
        table = pq.read_table(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        print(f"[lexicon] {lang}: not downloaded ({type(e).__name__}: {str(e)[:80]})")
        return False
    cols = table.column_names
    data = table.to_pydict()
    word_col = next((c for c in cols if isinstance((data[c] or [None])[0], str)), None)
    count_col = next((c for c in cols if c != word_col and isinstance((data[c] or [None])[0], (int, float))), None)
    if not word_col or not count_col:
        print(f"[lexicon] {lang}: unexpected columns {cols}")
        return False
    rows = sorted(((w, int(c)) for w, c in zip(data[word_col], data[count_col])
                   if isinstance(w, str) and w.strip() and c), key=lambda x: -x[1])[:KEEP[lang]]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"lexicon_{lang}.tsv"), "w", encoding="utf-8") as f:
        for w, c in rows:
            f.write(f"{w.strip()}\t{c}\n")
    print(f"[lexicon] {lang}: kept {len(rows)} words (columns {word_col}/{count_col})")
    return True


if __name__ == "__main__":
    ok = [fetch(lang) for lang in ("tcy", "kn")]
    sys.exit(0)
