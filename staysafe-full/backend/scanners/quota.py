"""
StaySafe - Careful use of every free service with a limit
----------------------------------------------------------
Every outside service we use for free has limits (so many requests a minute, so many a day).
Instead of hitting a limit and quietly skipping a check, each call asks its Quota first:

1. Per-minute limit reached?  WAIT for the next free slot (scans are allowed to take their
   time; the visitor just sees the careful-check animation a little longer). Only if the wait
   would be too long for this request do we fall back to the other checks.
2. Daily limit: never go past it. The last part of each day's allowance is kept for the most
   important calls (the ones that decide a result), and "nice to have" calls are spread over
   the day, so a busy morning can't use up the whole day and leave evening visitors without.
3. The service itself says "too many"?  We believe it: that minute (or that day) is marked as
   used, and waiting calls try again once it's over.

Priorities for a call:
    "high"   decides the result (e.g. reading a Kannada message so the rules can check it)
    "normal" adds detail to the result (default)
    "low"    only for display or when other checks already give a clear answer
"""

import os
import threading
import time
from collections import deque

_DAY = 86400


class Quota:
    def __init__(self, name, per_minute=None, per_day=None, day_offset_hours=0.0,
                 max_waiters=6, low_reserve=0.20, normal_reserve=0.05, low_spread=0.15, window=60.0):
        self.name = name
        self.window = window          # length of the per-minute window (seconds)
        self.per_minute = per_minute
        self.per_day = per_day
        self.day_offset = day_offset_hours * 3600    # when the provider's day starts, vs UTC
        self.max_waiters = max_waiters
        self.low_reserve = low_reserve
        self.normal_reserve = normal_reserve
        self.low_spread = low_spread
        self._lock = threading.Lock()
        self._minute = deque()        # times of calls in the last 60 s (one entry per unit of cost)
        self._day_key = None
        self._day_used = 0
        self._blocked_until = 0.0     # the service told us to slow down
        self._day_closed = False      # the service told us today's allowance is used
        self._waiting = 0
        self.waited_total = 0.0       # seconds spent waiting for free slots (for the status page)
        self.refused_today = 0

    # -- helpers ---------------------------------------------------------------
    def _roll_day(self, now):
        key = int((now + self.day_offset) // _DAY)
        if key != self._day_key:
            self._day_key, self._day_used, self._day_closed, self.refused_today = key, 0, False, 0

    def _day_fraction(self, now):
        return ((now + self.day_offset) % _DAY) / _DAY

    def _day_allows(self, now, cost, priority):
        if self._day_closed:
            return False
        if not self.per_day:
            return True
        left = self.per_day - self._day_used
        if cost > left:
            return False
        if priority == "high":
            return True
        reserve = self.low_reserve if priority == "low" else self.normal_reserve
        if left - cost < self.per_day * reserve:
            return False
        if priority == "low":
            # spread over the day: by 6 am about 40% may be used, by noon about 65%...
            allowed = self.per_day * min(1.0, self._day_fraction(now) + self.low_spread)
            if self._day_used + cost > allowed:
                return False
        return True

    def _minute_wait(self, now, cost):
        """Seconds until `cost` more calls fit into the per-minute limit (0 = go now)."""
        while self._minute and now - self._minute[0] >= self.window:
            self._minute.popleft()
        wait = max(0.0, self._blocked_until - now)
        if self.per_minute and cost > self.per_minute:
            return float("inf")
        if self.per_minute and len(self._minute) + cost > self.per_minute:
            # the slot frees when the oldest call that must drop out turns 60 s old
            idx = len(self._minute) + cost - self.per_minute - 1
            wait = max(wait, self._minute[idx] + self.window - now)
        return wait

    # -- the one call everybody uses ------------------------------------------
    def take(self, wait: float = 0.0, priority: str = "normal", cost: int = 1) -> bool:
        """
        True = go ahead (the call is counted). Waits up to `wait` seconds for a free per-minute
        slot. False = don't call now; use the other checks.
        """
        deadline = time.time() + max(0.0, wait)
        while True:
            with self._lock:
                now = time.time()
                self._roll_day(now)
                if not self._day_allows(now, cost, priority):
                    self.refused_today += 1
                    return False
                need = self._minute_wait(now, cost)
                if need <= 0:
                    self._minute.extend([now] * cost)
                    self._day_used += cost
                    return True
                if now + need > deadline or self._waiting >= self.max_waiters:
                    self.refused_today += 1
                    return False
                self._waiting += 1
            nap = min(need + 0.25, 5.0)   # wake up now and then in case things changed
            time.sleep(nap)
            with self._lock:
                self._waiting -= 1
                self.waited_total += nap

    # -- what the service tells us ---------------------------------------------
    def cool_down(self, seconds: float = 60.0) -> None:
        """The service said 'too many requests' for now: pause everyone for a while."""
        with self._lock:
            self._blocked_until = max(self._blocked_until, time.time() + seconds)

    def close_day(self) -> None:
        """The service said today's allowance is used up: no more calls until its day ends."""
        with self._lock:
            self._roll_day(time.time())
            self._day_closed = True

    def refund(self, cost: int = 1) -> None:
        """A counted call was never sent (e.g. we found the answer in the cache after waiting)."""
        with self._lock:
            self._day_used = max(0, self._day_used - cost)
            for _ in range(min(cost, len(self._minute))):
                self._minute.pop()

    def reset(self) -> None:
        """Forget all counts (used by the tests)."""
        with self._lock:
            self._minute.clear()
            self._day_key, self._day_used, self._day_closed = None, 0, False
            self._blocked_until, self.refused_today, self.waited_total = 0.0, 0, 0.0

    def status(self) -> dict:
        with self._lock:
            now = time.time()
            self._roll_day(now)
            while self._minute and now - self._minute[0] >= self.window:
                self._minute.popleft()
            return {"used_today": self._day_used, "per_day": self.per_day,
                    "last_minute": len(self._minute), "per_minute": self.per_minute,
                    "day_closed": self._day_closed, "paused_for_s": max(0, round(self._blocked_until - now)),
                    "refused_today": self.refused_today, "waited_s": round(self.waited_total)}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# Google's free-tier day ends at midnight Pacific time. -8 h is Pacific winter time; in summer
# our day then ends an hour after Google's, which only makes us a little more careful.
PACIFIC = -8

# The free allowances, set a little under each provider's published free limit.
# Each can be changed on Render with the environment variable shown.
QUOTAS = {
    "gemini": Quota("gemini", _env_int("GEMINI_PER_MINUTE", 8), _env_int("GEMINI_DAILY_LIMIT", 800), PACIFIC),
    "virustotal": Quota("virustotal", _env_int("VT_PER_MINUTE", 4), _env_int("VT_DAILY_LIMIT", 480)),
    "urlscan": Quota("urlscan", _env_int("URLSCAN_PER_MINUTE", 60), _env_int("URLSCAN_DAILY_LIMIT", 900)),
    "safe_browsing": Quota("safe_browsing", 300, _env_int("GSB_DAILY_LIMIT", 9000)),
    "abuseipdb": Quota("abuseipdb", 60, _env_int("ABUSEIPDB_DAILY_LIMIT", 950)),
    "proxycheck": Quota("proxycheck", 60, _env_int("PROXYCHECK_DAILY_LIMIT",
                                                   950 if os.environ.get("PROXYCHECK_KEY") else 95)),
    "ip_api": Quota("ip_api", 40),
    "mymemory": Quota("mymemory", None, _env_int("MYMEMORY_DAILY_CHARS",
                                                 48000 if os.environ.get("MYMEMORY_EMAIL") else 4800)),
    "google_translate": Quota("google_translate", None, _env_int("TRANSLATE_DAILY_CHAR_LIMIT", 15000), PACIFIC),
    "groq": Quota("groq", _env_int("GROQ_PER_MINUTE", 20), _env_int("GROQ_DAILY_LIMIT", 900)),
    "cloudflare": Quota("cloudflare", 20, _env_int("CLOUDFLARE_AI_DAILY_LIMIT", 300)),
    "bhashini": Quota("bhashini", 30, None),
    "ocrspace": Quota("ocrspace", 10, _env_int("OCRSPACE_DAILY_LIMIT", 800)),
    "crtsh": Quota("crtsh", 30, None),
    "rdap": Quota("rdap", 60, None),
    "xposedornot": Quota("xposedornot", 20, _env_int("XON_DAILY_LIMIT", 90)),
    "leakcheck": Quota("leakcheck", 20, _env_int("LEAKCHECK_DAILY_LIMIT", 300)),
    "abusech": Quota("abusech", 60, None),
    "circl": Quota("circl", 60, None),
}


def quota(name: str) -> Quota:
    return QUOTAS[name]


def quota_status() -> dict:
    return {name: q.status() for name, q in QUOTAS.items()}
