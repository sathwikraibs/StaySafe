"""
StaySafe daily accuracy test (run by .github/workflows/daily-accuracy.yml).

Every day: today's real scam links (fair test x3, blind test x1), the newest real malware
fingerprints, genuine messages, QR codes and phone numbers. Every Sunday also the full fixed
test sets for every checker. Results go to staysafe-full/accuracy/ in this repository.
Stops by itself once 250 still-online scam links have been tested in the fair test.

Needs the secret STAYSAFE_STATUS_KEY. The key is never printed or saved.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://staysafe-api.onrender.com"
KEY = os.environ.get("STAYSAFE_STATUS_KEY", "")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "staysafe-full", "accuracy")
GOAL = 250


def call(path: str, params: dict):
    q = urllib.parse.urlencode(dict(params, key=KEY))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{API}{path}?{q}", timeout=200) as r:
                return json.loads(r.read().decode())
        except Exception as e:              # the free server may be waking up
            err = type(e).__name__
            time.sleep(30)
    return {"error": err}


def main():
    if not KEY:
        print("STAYSAFE_STATUS_KEY secret is not set. Add it in Settings > Secrets and variables > Actions.")
        sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    summary_path = os.path.join(OUT, "summary.json")
    summary = json.load(open(summary_path)) if os.path.exists(summary_path) else {
        "fair": {"online": 0, "caught": 0}, "blind": {"online": 0, "caught": 0}, "days": 0, "finished": False}
    if summary.get("finished"):
        print(f"Finished earlier: {summary['fair']['caught']}/{summary['fair']['online']} caught. Nothing to do.")
        return

    today = datetime.date.today()
    runs = [("links", "/api/selftest/links", {"set": "10"})] * 3 + [("links", "/api/selftest/links", {"set": "9"})] + [
        ("files", "/api/selftest/files", {"set": "6"}),
        ("messages", "/api/selftest/messages", {"set": "5"}),
        ("qr", "/api/selftest/qr", {}),
        ("numbers", "/api/selftest/numbers", {}),
    ]
    if today.weekday() == 6:      # Sunday: every fixed test set too
        runs += [("links", "/api/selftest/links", {"set": s}) for s in "12345678"]
        runs += [("files", "/api/selftest/files", {"set": s}) for s in "12345"]
        runs += [("messages", "/api/selftest/messages", {"set": s}) for s in "12346"]

    day = {"date": today.isoformat(), "results": [], "missed_scam_links": [], "wrong": []}
    for kind, path, params in runs:
        r = call(path, params)
        label = f"{kind} {params.get('set', '')}".strip()
        entry = {"test": label, "right": r.get("right"), "error": r.get("error")}
        if params.get("set") in ("9", "10") and kind == "links":
            which = "fair" if params["set"] == "10" else "blind"
            online = [x for x in r.get("results", []) if x.get("still_online")]
            summary[which]["online"] += len(online)
            summary[which]["caught"] += sum(1 for x in online if x.get("right"))
            entry["caught_while_still_online"] = r.get("caught_while_still_online")
            day["missed_scam_links"] += [{"test": which, "url": x.get("url"), "verdict": x.get("verdict"),
                                          "why": x.get("why")} for x in online if not x.get("right")]
        elif r.get("wrong"):
            day["wrong"].append({"test": label, "wrong": r.get("wrong")})
        day["results"].append(entry)
        print(label, entry.get("right") or entry.get("error"))

    summary["days"] += 1
    summary["last_run"] = today.isoformat()
    for k in ("fair", "blind"):
        s = summary[k]
        s["percent"] = round(100 * s["caught"] / s["online"], 1) if s["online"] else None
    if summary["fair"]["online"] >= GOAL:
        summary["finished"] = True
    with open(os.path.join(OUT, "history.jsonl"), "a") as f:
        f.write(json.dumps(day) + "\n")
    json.dump(summary, open(summary_path, "w"), indent=2)
    print("Totals:", json.dumps(summary))


if __name__ == "__main__":
    main()
