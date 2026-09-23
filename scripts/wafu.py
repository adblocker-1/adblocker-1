"""和風 - Bausteine fuer die SVG-Grafiken des Profils.

Farben, Schrift als Pfad und die wiederkehrenden Motive (Seigaiha-Wellen,
Kirschblueten, Stempel). Keine Abhaengigkeiten ausser der Standardbibliothek.
"""

import json
import math
from html import escape
from pathlib import Path

GLYPHS = Path(__file__).resolve().parent / "glyphs"

# ------------------------------------------------------------------ Farben
# Hell = Tag auf Washi-Papier, Dunkel = Nacht in Indigo.
THEMES = {
    "light": {
        "bg": "#F5EFE3", "bg2": "#EDE3D0", "line": "#D8C9AC",
        "ink": "#1F1B17", "ink2": "#4B443C", "muted": "#857B6D",
        "shu": "#C0392B", "on_shu": "#FBF7EF",
        "gold": "#B8924A", "sakura": "#EBA9B4", "sakura_in": "#D9788A",
        "branch": "#4A3226",
        "fuji": "#2E4A70", "snow": "#FBF7EF", "hills": "#8FA3B8",
        "hills2": "#B4C1CE", "wave": "#223D63", "wave_line": "#F5EFE3",
        "wood": "#D9B98C", "wood_edge": "#A9804F", "wood_ink": "#2B2118",
        "track": "#E4D8C2",
    },
    "dark": {
        "bg": "#0F1724", "bg2": "#152031", "line": "#2B3A52",
        "ink": "#F0E8D8", "ink2": "#C9C0AF", "muted": "#8D96A6",
        "shu": "#E0533F", "on_shu": "#FBF7EF",
        "gold": "#C9A45C", "sakura": "#E7A1AE", "sakura_in": "#C9687C",
        "branch": "#2A1E1A",
        "fuji": "#22385A", "snow": "#D9E0EA", "hills": "#1B2B44",
        "hills2": "#22344F", "wave": "#172A45", "wave_line": "#4F6F99",
        "wood": "#8C6A45", "wood_edge": "#5E4529", "wood_ink": "#FBF3E4",
        "track": "#22304A",
    },
}

# Sprachfarben passend zur Palette (Indigo, Zinnober, Gold, Matcha ...)
LANG_COLORS = {
    "light": {"PowerShell": "#2E4A70", "HTML": "#C0392B", "Python": "#B8924A",
              "JavaScript": "#6E8B4E", "C#": "#7B5EA7", "Shell": "#5A6B7A"},
    "dark":  {"PowerShell": "#6D8FC2", "HTML": "#E0533F", "Python": "#C9A45C",
              "JavaScript": "#8DAE6A", "C#": "#A58BCF", "Shell": "#8A9BAA"},
}
FALLBACK_COLORS = ["#D9788A", "#8C6A45", "#4F8A8B", "#9C6B98"]


# ----------------------------------------------------------- Schrift/Pfade
class Font:
    def __init__(self, weight):
        d = json.loads((GLYPHS / f"mincho-{weight}.json").read_text("utf-8"))
        self.id = f"m{weight // 100}"
        self.upm = d["upm"]
        self.ascent = d["ascent"]
        self.glyphs = d["glyphs"]

    def has(self, ch):
        return ch in self.glyphs

    def safe(self, s):
        """Fuer Text aus der API: Unbekannte Zeichen durch ? ersetzen."""
        return "".join(c if c in self.glyphs else "?" for c in s)

    def width(self, s, size, spacing=0.0):
        """Breite in px. spacing = Sperrung in em."""
        adv = sum(self.glyphs[c][0] for c in s)
        return adv * size / self.upm + spacing * size * max(len(s) - 1, 0)


MEDIUM = Font(500)
BOLD = Font(800)


def num(v):
    """Kompakte Zahl fuer Attribute (keine 12 Nachkommastellen)."""
    v = round(v, 2)
    return str(int(v)) if v == int(v) else str(v)


class Svg:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.parts, self.defs, self.css = [], [], []
        self.used = {}

    def add(self, *parts):
        self.parts.extend(parts)

    def _ref(self, font, ch):
        gid = f"{font.id}-{ord(ch):x}"
        if gid not in self.used:
            self.used[gid] = font.glyphs[ch][1]
        return gid

    def text(self, s, x, y, size, font=BOLD, fill="#000", anchor="start",
             spacing=0.0, attrs=""):
        """Waagerechter Text als Pfade. y = Grundlinie. Gibt die Breite zurueck."""
        missing = [c for c in s if not font.has(c)]
        if missing:
            raise KeyError(f"Glyphen fehlen: {''.join(missing)!r} in {s!r} - "
                           "scripts/build_glyphs.py neu laufen lassen")
        w = font.width(s, size, spacing)
        x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        k = size / font.upm
        uses, u = [], 0.0
        for c in s:
            adv = font.glyphs[c][0]
            if font.glyphs[c][1]:          # Leerzeichen haben keinen Pfad
                ux = f' x="{num(u)}"' if u else ""
                uses.append(f'<use href="#{self._ref(font, c)}"{ux}/>')
            u += adv + spacing * font.upm
        self.parts.append(
            f'<g transform="translate({num(x0)} {num(y)}) scale({k:.5g})" '
            f'fill="{fill}"{" " + attrs if attrs else ""}>{"".join(uses)}</g>')
        return w

    def vtext(self, s, cx, top, size, font=BOLD, fill="#000", spacing=0.0):
        """Senkrechter Text (Tategaki), eine Zeichenzelle pro Zeichen.
        Nur fuer Kanji/Kana ohne kleine Kana und ohne Langvokalstrich."""
        k = size / font.upm
        y = top
        for c in s:
            w = font.glyphs[c][0] * k
            self.text(c, cx - w / 2, y + font.ascent * k, size, font, fill)
            y += size * (1 + spacing)
        return y - top

    def render(self):
        glyph_defs = "".join(f'<path id="{i}" d="{d}"/>'
                             for i, d in sorted(self.used.items()))
        css = f"<style>{''.join(self.css)}</style>" if self.css else ""
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
            f'height="{self.h}" role="img" aria-label="{escape(self.title)}">'
            f"<title>{escape(self.title)}</title>{desc}{css}"
            f"<defs>{glyph_defs}{''.join(self.defs)}</defs>"
            f"{''.join(self.parts)}</svg>\n")


# ------------------------------------------------------------------ Motive
def card_bg(svg, t, radius=16, clip_id="card"):
    """Papierkarte mit feinem Rand; legt einen Clip fuer den Inhalt an."""
    svg.defs.append(f'<clipPath id="{clip_id}"><rect width="{svg.w}" '
                    f'height="{svg.h}" rx="{radius}"/></clipPath>')
    svg.add(f'<rect x=".5" y=".5" width="{svg.w - 1}" height="{svg.h - 1}" '
            f'rx="{radius}" fill="{t["bg"]}" stroke="{t["line"]}"/>')


def seigaiha(svg, t, x0, y0, x1, y1, r=20, sid="sc"):
    """Seigaiha (青海波): Reihen ueberlappender Wellenschuppen.
    Spaeter gezeichnete (untere) Reihen liegen oben - wie im Original."""
    lw = max(r / 12, 1.2)
    rings = "".join(
        f'<circle r="{num(r * f)}" fill="none" stroke="{t["wave_line"]}" '
        f'stroke-width="{num(lw)}"/>' for f in (0.8, 0.6, 0.4, 0.2))
    svg.defs.append(f'<g id="{sid}"><circle r="{r}" fill="{t["wave"]}" '
                    f'stroke="{t["wave_line"]}" stroke-width="{num(lw)}"/>'
                    f"{rings}</g>")
    out, row, y = [], 0, y0
    while y - r < y1:
        off = r if row % 2 else 0
        x = x0 - r + off
        while x - r < x1:
            out.append(f'<use href="#{sid}" x="{num(x)}" y="{num(y)}"/>')
            x += 2 * r
        y += r / 2
        row += 1
    return "".join(out)


def blossom(cx, cy, r, rot, t, opacity=1.0):
    """Kirschbluete: fuenf Blaetter mit der typischen Kerbe an der Spitze."""
    petal = (f"M0 0C{num(-r * .55)} {num(-r * .25)} {num(-r * .62)} "
             f"{num(-r * .9)} {num(-r * .22)} {num(-r)}L0 {num(-r * .84)}"
             f"L{num(r * .22)} {num(-r)}C{num(r * .62)} {num(-r * .9)} "
             f"{num(r * .55)} {num(-r * .25)} 0 0Z")
    petals = "".join(f'<path d="{petal}" transform="rotate({a})"/>'
                     for a in (0, 72, 144, 216, 288))
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    dots = "".join(
        f'<circle cx="{num(math.sin(math.radians(a)) * r * .38)}" '
        f'cy="{num(-math.cos(math.radians(a)) * r * .38)}" r="{num(r * .07)}"/>'
        for a in range(36, 360, 72))
    return (f'<g transform="translate({num(cx)} {num(cy)}) rotate({rot})"{op}>'
            f'<g fill="{t["sakura"]}">{petals}</g>'
            f'<circle r="{num(r * .26)}" fill="{t["sakura_in"]}"/>'
            f'<g fill="{t["shu"]}">{dots}</g></g>')


def petal_path(s):
    """Einzelnes fallendes Blatt, um den Ursprung zentriert."""
    return (f"M0 {num(-s)}C{num(s * .7)} {num(-s * .6)} {num(s * .6)} "
            f"{num(s * .7)} 0 {num(s)}C{num(-s * .6)} {num(s * .7)} "
            f"{num(-s * .7)} {num(-s * .6)} 0 {num(-s)}Z")


def hanko(svg, x, y, size, chars, t, rot=-4):
    """Roter Namensstempel mit zwei senkrecht gesetzten Zeichen."""
    svg.add(f'<g transform="rotate({rot} {num(x + size / 2)} '
            f'{num(y + size / 2)})">'
            f'<rect x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" '
            f'rx="{num(size * .1)}" fill="{t["shu"]}"/>'
            f'<rect x="{num(x + size * .08)}" y="{num(y + size * .08)}" '
            f'width="{num(size * .84)}" height="{num(size * .84)}" '
            f'rx="{num(size * .06)}" fill="none" stroke="{t["on_shu"]}" '
            f'stroke-width="{num(size * .025)}"/>')
    cs = size * .38
    svg.vtext(chars, x + size / 2, y + size / 2 - cs * len(chars) / 2 - 1,
              cs, BOLD, t["on_shu"])
    svg.add("</g>")
