"""
TrustLight - Protective DNS: two more free, independent opinions on every website
--------------------------------------------------------------------------------
Some free public DNS services refuse to look up websites that their threat-intelligence
partners know spread malware or phishing:

  Cloudflare 1.1.1.2 ("1.1.1.1 for Families", malware blocking): answers 0.0.0.0 for them.
  Quad9 (9.9.9.9, run by a Swiss non-profit, fed by 20+ security companies): answers
      "no such website" (NXDOMAIN) for them, even though the website really exists.

Asking both takes well under a second, needs no key or sign-up, and costs nothing. We use the
standard DNS-over-HTTPS format (RFC 8484), so nothing extra has to be installed.

A website both of them block is almost certainly dangerous; one of them blocking it is a
warning sign. Real, well-known websites are never marked this way by us (the link check
skips its known-good list).
"""

import base64
import socket
import struct

import requests

from scanners.quota import quota

# name -> (DoH address, how it shows a blocked website)
RESOLVERS = {
    "Cloudflare": ("https://security.cloudflare-dns.com/dns-query", "zero_ip"),
    "Quad9": ("https://dns.quad9.net/dns-query", "nxdomain"),
}
TIMEOUT = 4.0


def build_query(name: str, qtype: int = 1) -> bytes:
    """A DNS question in wire format (id 0, as RFC 8484 recommends for caching)."""
    labels = []
    for part in name.strip(".").split("."):
        raw = part.encode("idna") if any(ord(c) > 127 for c in part) else part.encode()
        if not raw or len(raw) > 63:
            raise ValueError("bad label")
        labels.append(bytes([len(raw)]) + raw)
    return struct.pack(">HHHHHH", 0, 0x0100, 1, 0, 0, 0) + b"".join(labels) + b"\x00" + struct.pack(">HH", qtype, 1)


def _skip_name(data: bytes, pos: int) -> int:
    while True:
        length = data[pos]
        if length == 0:
            return pos + 1
        if length & 0xC0 == 0xC0:          # compressed: a 2-byte pointer ends the name
            return pos + 2
        pos += 1 + length


def parse_answer(data: bytes) -> dict:
    """{'rcode': int, 'ips': [...]} from a DNS answer in wire format."""
    if len(data) < 12:
        raise ValueError("short answer")
    _id, flags, qd, an, _ns, _ar = struct.unpack(">HHHHHH", data[:12])
    pos = 12
    for _ in range(qd):
        pos = _skip_name(data, pos) + 4
    ips = []
    for _ in range(an):
        pos = _skip_name(data, pos)
        rtype, _cls, _ttl, rdlen = struct.unpack(">HHIH", data[pos:pos + 10])
        pos += 10
        if rtype == 1 and rdlen == 4:
            ips.append(socket.inet_ntoa(data[pos:pos + 4]))
        pos += rdlen
    return {"rcode": flags & 0x000F, "ips": ips}


def ask(resolver: str, host: str):
    """The resolver's answer for `host`, or None if it couldn't be asked."""
    url, _ = RESOLVERS[resolver]
    try:
        query = base64.urlsafe_b64encode(build_query(host)).rstrip(b"=").decode()
        r = requests.get(url, params={"dns": query}, headers={"accept": "application/dns-message"}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return parse_answer(r.content)
    except Exception:
        return None


def check(host: str, really_exists) -> dict:
    """
    {'status': 'fail'|'warn'|'pass'|'skip', 'source': str, 'blocked_by': [...]}
    `really_exists`: True when the normal lookup found the website (so a "no such website"
    from Quad9 means it is blocked, not that it's gone).
    """
    if not host or not quota("protective_dns").take(wait=3, cost=2):
        return {"status": "skip"}
    blocked, answered = [], 0
    for name, (_, style) in RESOLVERS.items():
        out = ask(name, host)
        if out is None:
            continue
        answered += 1
        if style == "zero_ip" and out["ips"] and all(ip == "0.0.0.0" for ip in out["ips"]):
            blocked.append(name)
        elif style == "nxdomain" and out["rcode"] == 3 and really_exists:
            blocked.append(name)
    if not answered:
        return {"status": "skip"}
    if len(blocked) >= 2:
        return {"status": "fail", "source": " + ".join(blocked), "blocked_by": blocked}
    if blocked:
        return {"status": "warn", "source": blocked[0], "blocked_by": blocked}
    return {"status": "pass", "blocked_by": []}
