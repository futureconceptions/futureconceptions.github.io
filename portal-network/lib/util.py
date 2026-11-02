"""Kleine Helfer: Escaping, Slugs, Datumsformate."""
import datetime as dt
import html
import re
import unicodedata

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Berlin")
except Exception:  # pragma: no cover - Fallback ohne tzdata
    TZ = dt.timezone(dt.timedelta(hours=1))

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def slugify(text: str) -> str:
    s = str(text).lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse_datetime(value) -> dt.datetime | None:
    """ISO-Datum oder -Zeitstempel → zeitzonenbewusstes datetime (Europe/Berlin)."""
    if value in (None, ""):
        return None
    if isinstance(value, dt.datetime):
        d = value
    else:
        s = str(value).strip()
        if len(s) == 10:
            d = dt.datetime.fromisoformat(s + "T00:00:00")
        else:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=TZ)
    return d


def now() -> dt.datetime:
    return dt.datetime.now(TZ).replace(microsecond=0)


def de_date(d: dt.datetime | dt.date | None) -> str:
    if not d:
        return ""
    return f"{d.day}. {MONTHS[d.month - 1]} {d.year}"


def de_number(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def rfc822(d: dt.datetime) -> str:
    from email.utils import format_datetime
    return format_datetime(d)


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def truncate(s: str, n: int = 160) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    cut = s[: n - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",.;: ") + "…"


PLACEHOLDER_RE = re.compile(r"\[PLATZHALTER[^\]]*\]")


def has_placeholder(s: str) -> bool:
    return bool(PLACEHOLDER_RE.search(str(s or "")))
