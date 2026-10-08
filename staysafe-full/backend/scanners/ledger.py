"""
TrustLight - Score breakdown ("how we got this score")
------------------------------------------------------
Every checker records, next to each warning sign, how many points it added, so the result
page can show the score as a simple bill: reason, points, and any adjustment at the end.
Labels are the same English sentences used as findings, so the site translates them.
"""

ADJ_TRUSTED = "Known, trusted website (small warning signs count less)"
ADJ_POPULAR = "One of the world's most visited websites (small warning signs count less)"
ADJ_CAP = "The score can't go above 100"
ADJ_SAFE = "Contains a genuine-looking safety warning (e.g. 'do not share your OTP')"


class Ledger:
    """Tracks which finding added how many points."""

    def __init__(self, parts=None):
        self.parts = list(parts or [])  # [{"label": str, "points": int}]
        self._seen = {p["label"] for p in self.parts}

    def note(self, findings, points):
        """Give `points` to the newest finding not yet in the bill (or the last one)."""
        if not points:
            return points
        new = [f for f in findings if f not in self._seen]
        label = None
        if new:
            # findings.insert(0, x) puts the newest first; append puts it last
            label = new[0] if findings and findings[0] == new[0] and (len(findings) == 1 or findings[-1] in self._seen) else new[-1]
        elif self.parts:
            self.parts[-1]["points"] += points
            return points
        else:
            label = findings[-1] if findings else "Other warning signs"
        self.add(label, points)
        return points

    def add(self, label, points):
        if not points:
            return
        for p in self.parts:
            if p["label"] == label:
                p["points"] += points
                return
        self.parts.append({"label": label, "points": int(points)})
        self._seen.add(label)

    def moved(self, findings, before, after):
        """For score = max(score + x, y): record the real change."""
        self.note(findings, after - before)
        return after

    def result(self, final_score):
        """The bill, with an adjustment line when caps or discounts changed the total."""
        parts = [p for p in self.parts if p["points"]]
        raw = sum(p["points"] for p in parts)
        if raw != final_score:
            parts.append({"label": ADJ_CAP if raw > 100 and final_score == 100 else "__adjust__",
                          "points": final_score - raw})
        return parts
