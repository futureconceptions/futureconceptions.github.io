"""Outbound HTTP fetching with SSRF protection and robots.txt compliance.

* Only http/https on default-ish ports.
* Every hostname is resolved and every resolved address must be public
  (no loopback, private, link-local, multicast, reserved or metadata ranges).
* Redirects are followed manually so every hop is re-validated.
* Response size is capped.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.config import get_settings


class UnsafeURLError(ValueError):
    pass


class FetchError(RuntimeError):
    pass


ALLOWED_PORTS = {None, 80, 443, 8080, 8443}


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
                or addr.is_reserved or addr.is_unspecified
                or (isinstance(addr, ipaddress.IPv4Address) and addr in ipaddress.ip_network("100.64.0.0/10")))


def validate_url(url: str, resolver=None) -> str:
    resolver = resolver or socket.getaddrinfo
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("only http(s) URLs are allowed")
    if not parsed.hostname:
        raise UnsafeURLError("URL has no host")
    if parsed.username or parsed.password:
        raise UnsafeURLError("credentials in URL are not allowed")
    if parsed.port not in ALLOWED_PORTS:
        raise UnsafeURLError("port not allowed")
    if get_settings().fetch_allow_private_networks:
        return url
    host = parsed.hostname
    try:
        infos = resolver(host, parsed.port or (443 if parsed.scheme == "https" else 80),
                         proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise UnsafeURLError(f"cannot resolve host: {host}") from e
    if not infos:
        raise UnsafeURLError("host resolved to no addresses")
    for info in infos:
        ip = info[4][0]
        if not _is_public_ip(ip):
            raise UnsafeURLError(f"host resolves to a non-public address ({ip})")
    return url


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: bytes
    content_type: str


def safe_get(url: str, *, max_bytes: int | None = None, timeout: float | None = None,
             max_redirects: int = 5, headers: dict | None = None,
             client: httpx.Client | None = None) -> FetchResult:
    s = get_settings()
    max_bytes = max_bytes or s.fetch_max_bytes
    hdrs = {"User-Agent": s.fetch_user_agent, **(headers or {})}
    own = client is None
    client = client or httpx.Client(timeout=timeout or s.fetch_timeout_seconds,
                                    follow_redirects=False)
    try:
        current = url
        for _ in range(max_redirects + 1):
            validate_url(current)
            with client.stream("GET", current, headers=hdrs) as r:
                if r.is_redirect:
                    loc = r.headers.get("location")
                    if not loc:
                        raise FetchError("redirect without location")
                    current = urljoin(current, loc)
                    continue
                buf = bytearray()
                for chunk in r.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > max_bytes:
                        raise FetchError("response exceeds size limit")
                return FetchResult(current, r.status_code, bytes(buf),
                                   r.headers.get("content-type", ""))
        raise FetchError("too many redirects")
    finally:
        if own:
            client.close()


def robots_allows(url: str, *, client: httpx.Client | None = None) -> bool:
    """Return False only when robots.txt exists and disallows our agent.
    A missing/unreachable robots.txt is treated as allowed (RFC 9309 §2.3.1.3
    for 4xx); 5xx is treated as disallowed (§2.3.1.4)."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        res = safe_get(robots_url, max_bytes=500_000, client=client)
    except (FetchError, UnsafeURLError, httpx.HTTPError):
        return True
    if res.status_code >= 500:
        return False
    if res.status_code >= 400:
        return True
    rp = RobotFileParser()
    rp.parse(res.content.decode("utf-8", "ignore").splitlines())
    return rp.can_fetch(get_settings().fetch_user_agent, url)
