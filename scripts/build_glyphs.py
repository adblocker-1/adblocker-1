#!/usr/bin/env python3
"""Zieht die benoetigten Glyphen aus Shippori Mincho und legt sie als
SVG-Pfade in scripts/glyphs/*.json ab.

Warum Pfade statt <text>: Ein SVG, das GitHub als <img> einbindet, darf
keine Webfonts nachladen. Mit <text> haengt die Darstellung der Kanji vom
Betriebssystem des Besuchers ab - mit Pfaden sieht es ueberall gleich aus.

Dieses Skript wird nur gebraucht, wenn neue Schriftzeichen dazukommen.
Die GitHub Action braucht es nicht (sie liest nur die JSON-Dateien).

  npm pack @fontsource/shippori-mincho && tar xzf fontsource-*.tgz
  pip install fonttools brotli
  python scripts/build_glyphs.py package/files

Schrift: Shippori Mincho, (c) The Shippori Mincho Project Authors,
SIL Open Font License 1.1 - siehe scripts/glyphs/OFL.txt
"""

import json
import re
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
WEIGHTS = (500, 800)
# Reihenfolge = Vorrang: "japanese" deckt Kanji, Kana und ASCII ab.
SUBSETS = ("japanese", "latin", "latin-ext")
# Vokale mit Makron (Romaji: tōkei) fehlen in der Schrift - sie werden
# aus dem Grundbuchstaben plus Querstrich zusammengesetzt.
MACRONS = {"ā": "a", "ī": "i", "ū": "u", "ē": "e", "ō": "o",
           "Ā": "A", "Ī": "I", "Ū": "U", "Ē": "E", "Ō": "O"}


def wanted_chars():
    chars = {chr(c) for c in range(0x20, 0x7F)}
    chars |= set("ÄÖÜäöüßéèáà·–—„“”‚‘’…°×") | set(MACRONS)
    chars |= {chr(c) for c in range(0x3041, 0x3097)}   # Hiragana
    chars |= {chr(c) for c in range(0x30A1, 0x30FB)}   # Katakana
    chars |= set("ー・「」『』、。〜")
    # Alles, was im Generator als Text vorkommt
    for src in HERE.glob("*.py"):
        chars |= set(re.sub(r"[\x00-\x7f]", "", src.read_text("utf-8")))
    return chars


def draw(font, ch):
    """(Vorschub, SVG-Pfad) eines Zeichens oder None."""
    name = font.getBestCmap().get(ord(ch))
    if name is None:
        return None
    gs = font.getGlyphSet()
    pen = SVGPathPen(gs, ntos=lambda v: str(round(v)))
    # y spiegeln: Font-Koordinaten zeigen nach oben, SVG nach unten.
    gs[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
    return [gs[name].width, pen.getCommands()]


def draw_macron(font, ch, weight):
    base = MACRONS[ch]
    glyph = draw(font, base)
    if glyph is None:
        return None
    gs = font.getGlyphSet()
    bp = BoundsPen(gs)
    gs[font.getBestCmap()[ord(base)]].draw(bp)
    x0, _, x1, y1 = bp.bounds
    thick = 42 if weight >= 700 else 32
    top = -(y1 + 60 + thick)             # SVG-Koordinaten: oben = negativ
    pad = (x1 - x0) * .08
    bar = (f"M{round(x0 + pad)} {round(top)}H{round(x1 - pad)}"
           f"V{round(top + thick)}H{round(x0 + pad)}Z")
    return [glyph[0], glyph[1] + bar]


def build(files_dir, weight, chars):
    fonts = []
    for sub in SUBSETS:
        p = files_dir / f"shippori-mincho-{sub}-{weight}-normal.woff"
        if p.exists():
            fonts.append(TTFont(p))
    if not fonts:
        sys.exit(f"Keine Schriftdateien fuer {weight} in {files_dir}")

    glyphs, missing = {}, []
    for ch in sorted(chars):
        if not ch.strip() and ch != " ":
            continue
        for f in fonts:
            g = draw(f, ch)
            if g is None and ch in MACRONS:
                g = draw_macron(f, ch, weight)
            if g is not None:
                glyphs[ch] = g
                break
        else:
            missing.append(ch)

    head = fonts[0]["OS/2"]
    return {
        "font": "Shippori Mincho",
        "weight": weight,
        "upm": fonts[0]["head"].unitsPerEm,
        "ascent": head.sTypoAscender,
        "descent": head.sTypoDescender,
        "glyphs": glyphs,
    }, missing


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    files_dir = Path(sys.argv[1])
    chars = wanted_chars()
    for w in WEIGHTS:
        data, missing = build(files_dir, w, chars)
        out = HERE / "glyphs" / f"mincho-{w}.json"
        out.write_text(json.dumps(data, ensure_ascii=False,
                                  separators=(",", ":"), sort_keys=True),
                       encoding="utf-8")
        print(f"{out.name}: {len(data['glyphs'])} Glyphen, "
              f"{out.stat().st_size // 1024} KB")
        if missing:
            print("  nicht in der Schrift:", "".join(missing))


if __name__ == "__main__":
    main()
