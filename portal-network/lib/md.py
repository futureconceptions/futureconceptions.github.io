"""Kleiner Markdown-Konverter (Teilmenge) ohne Abhängigkeiten.

Blöcke: Überschriften (#–######), Absätze, Listen (-, *, 1.), Zitate (>),
Tabellen (| a | b |), horizontale Linie (---).
Inline: **fett**, *kursiv*, `code`, [Text](URL), [PLATZHALTER: …] (wird markiert).
Roh-HTML wird bewusst escaped (Inhalte kommen auch aus KI-Entwürfen).
"""
import re

from .util import esc, slugify

_UL = re.compile(r"^\s*[-*]\s+(.*)$")
_OL = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_H = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_PH = re.compile(r"\[PLATZHALTER[^\]]*\]")


def inline(text: str) -> str:
    stash = []

    def keep(html_snippet):
        stash.append(html_snippet)
        return f"\x00{len(stash) - 1}\x00"

    # Platzhalter zuerst (sonst Konflikt mit Link-Syntax)
    text = _PH.sub(lambda m: keep(f'<mark class="ph">{esc(m.group(0))}</mark>'), text)
    text = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{esc(m.group(1))}</code>"), text)

    def link(m):
        label, url = m.group(1), m.group(2).strip()
        ext = url.startswith(("http://", "https://"))
        attrs = ' rel="noopener" target="_blank"' if ext else ""
        return keep(f'<a href="{esc(url)}"{attrs}>{inline(label)}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def _is_block_start(line: str) -> bool:
    return bool(_H.match(line) or _UL.match(line) or _OL.match(line)
                or line.startswith(">") or line.lstrip().startswith("|")
                or line.strip() in ("---", "***"))


def _table(rows):
    def cells(r):
        r = r.strip().strip("|")
        return [c.strip() for c in r.split("|")]
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]] if len(rows) > 1 and set(rows[1].replace("|", "").strip()) <= set("-: ") else [cells(r) for r in rows[1:]]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += [f"<th scope=\"col\">{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def convert(text: str, heading_offset: int = 0) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)
    used_ids = set()
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = _H.match(line)
        if m:
            level = min(6, len(m.group(1)) + heading_offset)
            htext = m.group(2)
            custom = re.search(r"\s*\{#([\w-]+)\}$", htext)
            if custom:
                htext = htext[:custom.start()]
            hid = custom.group(1) if custom else (slugify(htext) or f"abschnitt-{i}")
            while hid in used_ids:
                hid += "-x"
            used_ids.add(hid)
            out.append(f'<h{level} id="{hid}">{inline(htext)}</h{level}>')
            i += 1
            continue
        if line.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue
        for rx, tag in ((_UL, "ul"), (_OL, "ol")):
            if rx.match(line):
                items = []
                while i < n and lines[i].strip():
                    mm = rx.match(lines[i])
                    if mm:
                        items.append(mm.group(1))
                    elif lines[i].startswith((" ", "\t")) and items:
                        items[-1] += " " + lines[i].strip()
                    else:
                        break
                    i += 1
                out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
                break
        else:
            if line.startswith(">"):
                quote = []
                while i < n and lines[i].startswith(">"):
                    quote.append(lines[i][1:].lstrip())
                    i += 1
                out.append(f"<blockquote>{convert(chr(10).join(quote))}</blockquote>")
            elif line.lstrip().startswith("|"):
                rows = []
                while i < n and lines[i].lstrip().startswith("|"):
                    rows.append(lines[i])
                    i += 1
                out.append(_table(rows))
            else:
                para = []
                while i < n and lines[i].strip() and not (para and _is_block_start(lines[i])):
                    ln = lines[i].rstrip()
                    # Zeilenende mit Backslash = harter Zeilenumbruch (z. B. Anschriften)
                    para.append(ln[:-1].strip() + "\x01" if ln.endswith("\\") else ln.strip())
                    i += 1
                text_ = inline(" ".join(para)).replace("\x01 ", "<br>").replace("\x01", "<br>")
                out.append(f"<p>{text_}</p>")
            continue
    return "\n".join(out)


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"[#>*`|\-\[\]()]", " ", text)))
