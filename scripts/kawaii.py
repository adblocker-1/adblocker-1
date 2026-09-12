#!/usr/bin/env python3
"""Zeichenbausteine im Kawaii-Stil fuer die Profilkarten.

Alle Figuren sind reine SVG-Pfade. Nichts haengt von einer Emoji- oder
Japanisch-Schriftart auf dem Rechner des Betrachters ab - ausser den
bewusst gesetzten japanischen Textzeilen, die immer neben einer
lateinischen Entsprechung stehen.
"""

from html import escape

# ------------------------------------------------------------- Palette
BG      = "#FFF6FA"   # Cremerosa
BG2     = "#FDE9F2"   # etwas satter, fuer den Verlauf
BORDER  = "#FFC2D6"
TITLE   = "#E36F97"
TEXT    = "#6D6178"
MUTED   = "#AB99B8"
NUMBER  = "#A874C9"
TRACK   = "#FBE0EA"
SPARK   = "#FFC9DC"
DOT     = "#FFE3EE"   # Punktmuster im Hintergrund
BLUSH   = "#FFA6BE"
INK     = "#7A5C72"   # Augen und Striche der Figuren

PASTELS = ["#FFB7C5", "#CBA6F7", "#B5EAD7", "#FFDAC1", "#A0C4FF", "#F7C8E0"]

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Ubuntu,"
        "'Helvetica Neue',Helvetica,Arial,sans-serif")
FONT_JP = ("'Hiragino Maru Gothic ProN','Yu Gothic','Meiryo',"
           "'Noto Sans JP','MS PGothic',sans-serif")


# ---------------------------------------------------------- Rahmenform
def scallop(w, h, target=9.0):
    """Pfad eines Rechtecks mit Bogenrand (wie ein Tortendeckchen).

    Die Radien werden so gewaehlt, dass die Boegen exakt aufgehen -
    sonst klafft an den Ecken eine Luecke.
    """
    nx = max(2, round((w - 2 * target) / (2 * target)))
    ny = max(2, round((h - 2 * target) / (2 * target)))
    rx = w / (2 * nx + 2)
    ry = h / (2 * ny + 2)
    p = [f"M{rx:.2f},{ry:.2f}"]
    p += [f"a{rx:.2f},{rx:.2f} 0 0 1 {2 * rx:.2f},0"] * nx
    p += [f"a{ry:.2f},{ry:.2f} 0 0 1 0,{2 * ry:.2f}"] * ny
    p += [f"a{rx:.2f},{rx:.2f} 0 0 1 {-2 * rx:.2f},0"] * nx
    p += [f"a{ry:.2f},{ry:.2f} 0 0 1 0,{-2 * ry:.2f}"] * ny
    return "".join(p) + "Z", rx, ry


# -------------------------------------------------------------- Deko
def sparkle(x, y, r, fill=SPARK, delay=0.0, op=1.0):
    """Vierzackiger Stern, der langsam blinkt."""
    d = (f"M{x} {y - r}Q{x + r * .2} {y - r * .2} {x + r} {y}"
         f"Q{x + r * .2} {y + r * .2} {x} {y + r}"
         f"Q{x - r * .2} {y + r * .2} {x - r} {y}"
         f"Q{x - r * .2} {y - r * .2} {x} {y - r}Z")
    return (f'<path fill="{fill}" opacity="{op}" d="{d}">'
            f'<animate attributeName="opacity" values="{op};{op * .2};{op}" '
            f'dur="2.8s" begin="{delay}s" repeatCount="indefinite"/></path>')


def heart(x, y, s, fill):
    return (f'<path transform="translate({x},{y}) scale({s})" fill="{fill}" '
            f'd="M5 9.2C2.2 7.3 0 5.7 0 3.6 0 1.9 1.3.7 2.9.7c1 0 1.7.5 2.1 1.1'
            f'C5.4 1.2 6.1.7 7.1.7 8.7.7 10 1.9 10 3.6c0 2.1-2.2 3.7-5 5.6z"/>')


def ribbon(x, y, s=1.0, fill="#FF9EBB"):
    """Schleife - das Kawaii-Zeichen schlechthin."""
    return f"""<g transform="translate({x},{y}) scale({s})">
  <path d="M11 6 L1 1 Q-1 6 1 11 Z" fill="{fill}"/>
  <path d="M13 6 L23 1 Q25 6 23 11 Z" fill="{fill}"/>
  <path d="M11 6 L11 12 L6 14 Z"  fill="{fill}" opacity=".8"/>
  <path d="M13 6 L13 12 L18 14 Z" fill="{fill}" opacity=".8"/>
  <circle cx="12" cy="6.5" r="3" fill="{fill}"/>
  <circle cx="12" cy="6.5" r="1.2" fill="#FFFFFF" opacity=".55"/>
</g>"""


def _face(blush_dx=6.5, blush_y=13.5):
    """Geschlossene Lachaugen, Wangenrot, kleiner Mund - bei allen
    Figuren gleich, damit sie als eine Familie wirken."""
    return f"""
  <ellipse cx="-{blush_dx}" cy="{blush_y}" rx="3.1" ry="2.1"
           fill="{BLUSH}" opacity=".55"/>
  <ellipse cx="{blush_dx}" cy="{blush_y}" rx="3.1" ry="2.1"
           fill="{BLUSH}" opacity=".55"/>
  <path d="M-6.4 10.6 Q-4.4 8.2 -2.4 10.6" stroke="{INK}" stroke-width="1.5"
        fill="none" stroke-linecap="round"/>
  <path d="M2.4 10.6 Q4.4 8.2 6.4 10.6" stroke="{INK}" stroke-width="1.5"
        fill="none" stroke-linecap="round"/>
  <path d="M-2 13.8 Q0 15.8 2 13.8" stroke="{INK}" stroke-width="1.4"
        fill="none" stroke-linecap="round"/>"""


def cat(x, y, s=1.0, fur="#FFB7C5"):
    return f"""<g transform="translate({x},{y}) scale({s})">
  <path d="M-11 -2 L-12.5 -15 L-2.5 -7 Z" fill="{fur}"/>
  <path d="M11 -2 L12.5 -15 L2.5 -7 Z"    fill="{fur}"/>
  <ellipse cx="0" cy="8" rx="14" ry="12" fill="{fur}"/>
  <path d="M-19 6 L-14.5 5 M-19 10 L-14.5 9.6" stroke="{fur}"
        stroke-width="1.3" stroke-linecap="round"/>
  <path d="M19 6 L14.5 5 M19 10 L14.5 9.6" stroke="{fur}"
        stroke-width="1.3" stroke-linecap="round"/>
  {_face()}
</g>"""


def bunny(x, y, s=1.0, fur="#E7D6FB"):
    return f"""<g transform="translate({x},{y}) scale({s})">
  <ellipse cx="-5.5" cy="-9" rx="3.6" ry="11" fill="{fur}"/>
  <ellipse cx="5.5"  cy="-9" rx="3.6" ry="11" fill="{fur}"/>
  <ellipse cx="-5.5" cy="-9" rx="1.7" ry="7.6" fill="{BLUSH}" opacity=".4"/>
  <ellipse cx="5.5"  cy="-9" rx="1.7" ry="7.6" fill="{BLUSH}" opacity=".4"/>
  <ellipse cx="0" cy="8" rx="13" ry="11.5" fill="{fur}"/>
  {_face()}
</g>"""


def bear(x, y, s=1.0, fur="#FFD9B8"):
    return f"""<g transform="translate({x},{y}) scale({s})">
  <circle cx="-10" cy="-3" r="5.5" fill="{fur}"/>
  <circle cx="10"  cy="-3" r="5.5" fill="{fur}"/>
  <circle cx="-10" cy="-3" r="2.6" fill="{BLUSH}" opacity=".45"/>
  <circle cx="10"  cy="-3" r="2.6" fill="{BLUSH}" opacity=".45"/>
  <ellipse cx="0" cy="8" rx="13.5" ry="12" fill="{fur}"/>
  <ellipse cx="0" cy="13.5" rx="6" ry="4.6" fill="#FFFFFF" opacity=".55"/>
  {_face(blush_dx=8.5, blush_y=12)}
</g>"""


# ------------------------------------------------ Achievement-Abzeichen
# GitHub bietet fuer die eigenen Profil-Achievements keine API - die
# Liste hier bildet nur nach, was tatsaechlich auf dem Profil steht,
# und muss von Hand aktualisiert werden, wenn ein neues dazukommt.
def badge_shark(r=26):
    """Kawaii-Variante des 'Pull Shark'-Abzeichens: klassische
    Hai-Seitenansicht (Tropfenkoerper, Rueckenflosse, Schwanzflosse),
    aber mit rundem Kawaii-Gesicht statt spitzen Zaehnen."""
    return f"""<g>
  <circle r="{r}" fill="#F6DCC0"/>
  <circle r="{r}" fill="none" stroke="#E3B98A" stroke-width="2"/>
  <g transform="translate(-1,3)">
    <path d="M-15 0 Q-13 -7 -2 -7 Q9 -7 15 -1
             Q9 1 -2 1 Q-11 1 -15 0 Z"
          fill="#F1C79A" stroke="#B9895A" stroke-width="1" stroke-linejoin="round"/>
    <path d="M-3 -7 L2 -15 L6 -7 Z"
          fill="#F1C79A" stroke="#B9895A" stroke-width="1" stroke-linejoin="round"/>
    <path d="M13 -2 L20 -6 L19 1 L20 6 L13 2 Z"
          fill="#F1C79A" stroke="#B9895A" stroke-width="1" stroke-linejoin="round"/>
    <circle cx="-9" cy="-2" r="1.3" fill="#7A5C72"/>
    <path d="M-13 2 Q-9 4.5 -5 2" stroke="#B9895A" stroke-width="1"
          fill="none" stroke-linecap="round"/>
  </g>
</g>"""


def badge_yolo(r=26):
    """Kawaii-Variante des 'YOLO'-Abzeichens: Pastell-Regenbogen + Herz."""
    bands = ["#FFB7C5", "#FFDAC1", "#FFF3B0", "#B5EAD7", "#A0C4FF", "#CBA6F7"]
    n = len(bands)
    rows = []
    for i, col in enumerate(bands):
        y0 = -r + (2 * r * i / n)
        y1 = -r + (2 * r * (i + 1) / n)
        rows.append(f'<rect x="-{r}" y="{y0:.2f}" width="{2*r}" '
                     f'height="{(y1 - y0) + .5:.2f}" fill="{col}"/>')
    return f"""<g>
  <clipPath id="yoloClip"><circle r="{r}"/></clipPath>
  <g clip-path="url(#yoloClip)">{"".join(rows)}</g>
  <circle r="{r}" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
  {heart(0, 2, 1.35, "#FFFFFF")}
</g>"""


def badge_vault(r=26):
    """Kawaii-Variante des 'Arctic Code Vault Contributor'-Schilds."""
    s = r * 1.05
    return f"""<g>
  <path d="M0 {-s} Q{s} {-s*.75} {s} {-s*.05}
           Q{s} {s*.85} 0 {s*1.15}
           Q{-s} {s*.85} {-s} {-s*.05}
           Q{-s} {-s*.75} 0 {-s} Z" fill="#123B6E"/>
  <path d="M0 {-s} Q{s} {-s*.75} {s} {-s*.05}
           Q{s} {s*.85} 0 {s*1.15}
           Q{-s} {s*.85} {-s} {-s*.05}
           Q{-s} {-s*.75} 0 {-s} Z" fill="none" stroke="#FFFFFF"
        stroke-width="2"/>
  <circle cx="6" cy="{-s*.42:.2f}" r="{r*.24:.2f}" fill="#FDF3D0"/>
  <path d="M{-s*.8:.2f} {s*.55:.2f} L{-s*.15:.2f} {-s*.05:.2f}
           L{s*.2:.2f} {s*.3:.2f} L{s*.8:.2f} {-s*.35:.2f}
           L{s*.8:.2f} {s*.85:.2f} L{-s*.8:.2f} {s*.85:.2f} Z"
        fill="#DCEBFA" opacity=".9"/>
</g>"""


ACHIEVEMENT_ICONS = {
    "shark": badge_shark,
    "yolo":  badge_yolo,
    "vault": badge_vault,
}


def achievement_badge(x, y, icon, title, count=None, r=26):
    """Ein Achievement-Abzeichen: Icon im Kreis, Name darunter, optional
    ein x-Chip fuer mehrfach verdiente Abzeichen (z. B. Pull Shark x2)."""
    draw = ACHIEVEMENT_ICONS[icon]
    chip = ""
    if count and count > 1:
        chip = f"""<g transform="translate({r*.72:.1f},{-r*.72:.1f})">
  <circle r="10" fill="{TITLE}"/>
  <text y="3.5" text-anchor="middle"
        style="font: 700 10px {FONT}; fill:#FFFFFF">x{count}</text>
</g>"""
    return f"""<g transform="translate({x},{y})">
  {draw(r)}
  {chip}
  <text y="{r + 17}" text-anchor="middle"
        style="font: 700 11px {FONT}; fill:{TEXT}">{escape(title)}</text>
</g>"""


# -------------------------------------------------------------- Karte
def card(w, h, title, title_jp, body, mascot="", pad_extra=0):
    """Kartenrahmen mit Bogenrand, Punktmuster, Schleife und Funkeln."""
    path, rx, ry = scallop(w, h)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
    <stop offset="0%" stop-color="{BG}"/>
    <stop offset="100%" stop-color="{BG2}"/>
  </linearGradient>
  <pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="4" r="1.6" fill="{DOT}"/>
    <circle cx="12" cy="12" r="1.6" fill="{DOT}"/>
  </pattern>
  <clipPath id="inner"><path d="{path}"/></clipPath>
</defs>
<style>
  .t  {{ font: 700 15.5px {FONT}; fill: {TITLE}; }}
  .jp {{ font: 400 10px {FONT_JP}; fill: {MUTED}; letter-spacing:1px; }}
  .n  {{ font: 700 23px {FONT}; fill: {NUMBER}; }}
  .l  {{ font: 400 10.5px {FONT}; fill: {MUTED}; letter-spacing:.5px; }}
  .b  {{ font: 400 12.5px {FONT}; fill: {TEXT}; }}
  .s  {{ font: 400 11px {FONT}; fill: {MUTED}; }}
</style>
<path d="{path}" fill="url(#bg)" stroke="{BORDER}" stroke-width="2"
      stroke-linejoin="round"/>
<g clip-path="url(#inner)"><rect width="{w}" height="{h}" fill="url(#dots)"
   opacity=".8"/></g>
<text x="{rx + 40 + pad_extra}" y="{ry + 22}" class="t">{escape(title)}</text>
<text x="{rx + 40 + pad_extra}" y="{ry + 36}" class="jp">{escape(title_jp)}</text>
{ribbon(rx + 10 + pad_extra, ry + 8, .95)}
{sparkle(w - rx - 22, ry + 12, 5.4, SPARK, 0.0)}
{sparkle(w - rx - 40, ry + 24, 3.4, SPARK, 0.9, .8)}
{sparkle(w - rx - 8, ry + 30, 3.0, SPARK, 1.7, .65)}
{mascot}
{body}
</svg>
"""
