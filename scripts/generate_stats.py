#!/usr/bin/env python3
"""Erzeugt die Pastell-Statistikkarten fuer das Profil-README.

Die Karten liegen als SVG im Repo (assets/) statt sie von fremden
Gratis-Diensten zu laden - die sind regelmaessig ueberlastet und liefern
dann 429/500, worauf GitHub ein kaputtes Bild anzeigt.

Aufruf:
  python scripts/generate_stats.py                 # holt die Daten von der GitHub-API
  python scripts/generate_stats.py --snapshot x.json
"""

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USER = "adblocker-1"
OUT = Path(__file__).resolve().parent.parent / "assets"

# ------------------------------------------------------------------ Palette
BG      = "#FFF5F7"
BORDER  = "#FFD3DF"
TITLE   = "#E8799A"
TEXT    = "#6D6178"
MUTED   = "#A796B4"
NUMBER  = "#B07CC6"
TRACK   = "#FBE4EA"
BG2     = "#FDEBF3"
SPARK   = "#FFC9DC"
CAT     = "#FFAFC8"

LANG_COLORS = {
    "PowerShell": "#FFB7C5",
    "HTML":       "#CBA6F7",
    "JavaScript": "#B5EAD7",
    "Python":     "#FFDAC1",
    "C#":         "#A0C4FF",
    "Shell":      "#F7C8E0",
}
FALLBACK = ["#FFB7C5", "#CBA6F7", "#B5EAD7", "#FFDAC1", "#A0C4FF", "#F7C8E0"]

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Ubuntu,"
        "'Helvetica Neue',Helvetica,Arial,sans-serif")


# ------------------------------------------------------------------- Daten
def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": f"{USER}-profile-stats"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch():
    u = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    return {
        "user": {k: u[k] for k in
                 ("login", "name", "followers", "following",
                  "public_repos", "created_at")},
        "repos": [{"name": r["name"], "language": r["language"],
                   "description": r["description"],
                   "size": r["size"], "stars": r["stargazers_count"],
                   "forks": r["forks_count"], "pushed_at": r["pushed_at"],
                   "created_at": r["created_at"]}
                  # Das Profil-Repo selbst ist kein Projekt und taucht
                  # sonst in "Zuletzt aktualisiert" und der Repo-Zahl auf.
                  for r in repos if not r["fork"] and r["name"] != USER],
    }


# -------------------------------------------------------------- Bausteine
def sparkle(x, y, r, fill, op=1.0):
    """Vierzackiger Funkel-Stern."""
    return (f'<path opacity="{op}" fill="{fill}" d="M{x} {y - r}'
            f'Q{x + r * .18} {y - r * .18} {x + r} {y}'
            f'Q{x + r * .18} {y + r * .18} {x} {y + r}'
            f'Q{x - r * .18} {y + r * .18} {x - r} {y}'
            f'Q{x - r * .18} {y - r * .18} {x} {y - r}Z"/>')


def kitty(x, y, s=1.0):
    """Kleines Katzengesicht - reine Pfade, damit nichts von einer
    Emoji-Schriftart auf dem Rechner des Betrachters abhaengt."""
    return f"""<g transform="translate({x},{y}) scale({s})">
  <path d="M2 10 L3 -3 L12 5 Z"   fill="{CAT}"/>
  <path d="M24 10 L23 -3 L14 5 Z" fill="{CAT}"/>
  <ellipse cx="13" cy="13" rx="11.5" ry="9.5" fill="{CAT}"/>
  <circle cx="9"  cy="12" r="1.5" fill="#FFFFFF"/>
  <circle cx="17" cy="12" r="1.5" fill="#FFFFFF"/>
  <path d="M11.6 15.8 Q13 17.2 14.4 15.8" stroke="#FFFFFF"
        stroke-width="1.3" fill="none" stroke-linecap="round"/>
</g>"""


def card(w, h, title, body, deco=True):
    sparks = ""
    if deco:
        sparks = (sparkle(w - 96, 26, 5, SPARK)
                  + sparkle(w - 78, 16, 3, SPARK, .75)
                  + sparkle(w - 66, 32, 3.6, SPARK, .55))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{BG}"/>
    <stop offset="100%" stop-color="{BG2}"/>
  </linearGradient>
</defs>
<style>
  .t {{ font: 700 15px {FONT}; fill: {TITLE}; }}
  .n {{ font: 700 23px {FONT}; fill: {NUMBER}; }}
  .l {{ font: 400 10.5px {FONT}; fill: {MUTED}; letter-spacing:.5px; }}
  .b {{ font: 400 12.5px {FONT}; fill: {TEXT}; }}
  .s {{ font: 400 11px {FONT}; fill: {MUTED}; }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="20" fill="url(#bg)"
      stroke="{BORDER}" stroke-width="2"/>
<rect x="7" y="7" width="{w - 14}" height="{h - 14}" rx="15" fill="none"
      stroke="{SPARK}" stroke-width="1.4" stroke-dasharray="1 6"
      stroke-linecap="round" opacity=".85"/>
<text x="26" y="36" class="t">{escape(title)}</text>
{sparks}
{body}
</svg>
"""


def heart(x, y, s, fill):
    return (f'<path transform="translate({x},{y}) scale({s})" fill="{fill}" '
            f'd="M5 9.2C2.2 7.3 0 5.7 0 3.6 0 1.9 1.3.7 2.9.7c1 0 1.7.5 2.1 1.1'
            f'C5.4 1.2 6.1.7 7.1.7 8.7.7 10 1.9 10 3.6c0 2.1-2.2 3.7-5 5.6z"/>')


# ----------------------------------------------------------------- Karten
def card_stats(d):
    u, repos = d["user"], d["repos"]
    since = datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
    last = max(datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
               for r in repos)
    langs = len({r["language"] for r in repos if r["language"]})

    cells = [
        (str(len(repos)),                     "REPOSITORIES"),
        (str(langs),                          "SPRACHEN"),
        (str(sum(r["stars"] for r in repos)), "STERNE"),
        (str(u["followers"]),                 "FOLLOWER"),
        (since.strftime("%Y"),                "DABEI SEIT"),
        (last.strftime("%m/%Y"),              "LETZTER PUSH"),
    ]
    body = [kitty(388, 14, 1.15)]
    for i, (num, lab) in enumerate(cells):
        x = 28 + (i % 3) * 143
        y = 88 + (i // 3) * 58
        body.append(f'<text x="{x}" y="{y}" class="n">{num}</text>')
        body.append(heart(x, y + 6, 0.62, SPARK))
        body.append(f'<text x="{x + 10}" y="{y + 17}" class="l">{lab}</text>')
    return card(450, 178, "\u2727  Adblocker  \u00b7  GitHub  \u2727",
                "\n".join(body))


def card_langs(d):
    counts = Counter(r["language"] for r in d["repos"] if r["language"])
    total = sum(counts.values())
    order = counts.most_common()

    bar_x, bar_y, bar_w, bar_h, gap = 28, 78, 394, 13, 2
    body, cx = [], bar_x
    body.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" '
                f'height="{bar_h}" rx="6" fill="{TRACK}"/>')
    body.append(f'<clipPath id="clip"><rect x="{bar_x}" y="{bar_y}" '
                f'width="{bar_w}" height="{bar_h}" rx="6"/></clipPath>')
    body.append('<g clip-path="url(#clip)">')
    for i, (lang, n) in enumerate(order):
        w = bar_w * n / total - (gap if i < len(order) - 1 else 0)
        col = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        body.append(f'<rect x="{cx:.1f}" y="{bar_y}" width="{max(w, 0):.1f}" '
                    f'height="{bar_h}" fill="{col}"/>')
        cx += bar_w * n / total
    body.append("</g>")

    # Feste Spalten mit rechtsbuendiger Prozentzahl - eine geschaetzte
    # Textbreite (Zeichen * Pixel) laesst lange Namen ueberlappen.
    for i, (lang, n) in enumerate(order):
        col_x = 28 + (i % 2) * 209
        y = 128 + (i // 2) * 28
        col = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        pct = 100 * n / total
        body.append(f'<circle cx="{col_x + 6}" cy="{y - 4}" r="5.5" fill="{col}"/>')
        body.append(f'<text x="{col_x + 20}" y="{y}" class="b">{escape(lang)}</text>')
        body.append(f'<text x="{col_x + 189}" y="{y}" class="s" '
                    f'text-anchor="end">{pct:.0f}%  ({n})</text>')
    body.append(f'<text x="28" y="162" class="s">aus {len(d["repos"])} '
                f'Repositories  \u00b7  {total} mit erkannter Sprache</text>')
    return card(450, 178, "\u2727  Repositories nach Sprache", "\n".join(body))


def card_recent(d):
    repos = sorted(d["repos"], key=lambda r: r["pushed_at"], reverse=True)[:5]
    # Wurzelskala: ein einzelnes 640-KB-Repo wuerde linear alle anderen
    # Balken auf unsichtbare Striche zusammendruecken.
    mx = max(r["size"] for r in repos) or 1
    body = []
    for i, r in enumerate(repos):
        y = 72 + i * 25
        d = r["pushed_at"][:10]
        date = f"{d[8:10]}.{d[5:7]}.{d[0:4]}"
        w = 8 + 232 * (r["size"] / mx) ** 0.5
        col = FALLBACK[i % len(FALLBACK)]
        body.append(heart(28, y - 8, 0.75, col))
        body.append(f'<text x="45" y="{y}" class="b">{escape(r["name"])}</text>')
        body.append(f'<text x="470" y="{y}" class="s">{date}</text>')
        body.append(f'<rect x="560" y="{y - 9}" width="240" height="9" '
                    f'rx="4.5" fill="{TRACK}"/>')
        body.append(f'<rect x="560" y="{y - 9}" width="{w:.1f}" height="9" '
                    f'rx="4.5" fill="{col}"/>')
        body.append(f'<text x="890" y="{y}" class="s" text-anchor="end">'
                    f'{r["size"]} KB</text>')
    return card(914, 196, "\u2727  Zuletzt aktualisiert  \u00b7  Balken = Repo-Gr\u00f6\u00dfe",
                "\n".join(body))


# --------------------------------------------------------- Projekttabelle
# Beschreibung kommt aus dem GitHub-Feld des jeweiligen Repos. Nur fuer
# Repos ohne gepflegte Beschreibung steht hier ein Ersatztext.
DESCRIPTIONS = {
    "UnifiController-PRTG":
        "UniFi-Switches, APs und Gateways in PRTG - auf allen Plattformen "
        "von Cloud Key bis Legacy-Controller.",
    "Cove-Data-Protection-PRTG":
        "Cove Data Protection im PRTG-Blick behalten.",
}

# Reihenfolge zaehlt: der erste Treffer im Repo-Namen gewinnt.
EMOJI_RULES = [
    ("unifi", "\U0001F4E1"),        # Satellitenschuessel
    ("firewall", "\U0001F525"),     # Feuer
    ("migration", "\U0001F504"),    # Pfeile im Kreis
    ("sophos", "\U0001F6E1\uFE0F"),  # Schild
    ("365", "\U0001F4BE"),          # Diskette
    ("backup", "\u2601\uFE0F"),      # Wolke
    ("cove", "\U0001F5C4\uFE0F"),    # Aktenschrank
    ("mail", "\u2709\uFE0F"),        # Briefumschlag
    ("hyperv", "\U0001F5A5\uFE0F"),  # Bildschirm
    ("flappy", "\U0001F426"),       # Vogel
    ("prtg", "\U0001F4CA"),         # Diagramm
]
FALLBACK_EMOJI = "\u2728"           # Funkeln

MARK_START = "<!-- PROJEKTE:START -->"
MARK_END = "<!-- PROJEKTE:ENDE -->"
MAX_DESC = 170


def emoji_for(name):
    low = name.lower().replace("-", "")
    for key, emo in EMOJI_RULES:
        if key in low:
            return emo
    return FALLBACK_EMOJI


def describe(r):
    text = (r.get("description") or DESCRIPTIONS.get(r["name"], "")).strip()
    if not text:
        return "&nbsp;"
    if len(text) > MAX_DESC:
        text = text[:MAX_DESC].rsplit(" ", 1)[0].rstrip(" .,;-") + " ..."
    # Ein rohes | wuerde die Markdown-Tabelle sprengen.
    return text.replace("|", "\\|").replace("\n", " ")


def project_table(d):
    rows = ["| \u2661 | Projekt | Worum es geht |", "| :-: | :-- | :-- |"]
    for r in sorted(d["repos"], key=lambda x: x["pushed_at"], reverse=True):
        url = f"https://github.com/{USER}/{r['name']}"
        rows.append(f"| {emoji_for(r['name'])} | **[{r['name']}]({url})** | "
                    f"{describe(r)} |")
    return "\n".join(rows)


def update_readme(d):
    """Ersetzt die Tabelle zwischen den Markern. Fehlen die Marker, wird
    nichts angefasst - lieber unveraendert als halb zerstoert."""
    readme = Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text(encoding="utf-8")
    if MARK_START not in text or MARK_END not in text:
        print("Marker fehlen - README unveraendert.")
        return
    head, rest = text.split(MARK_START, 1)
    _, tail = rest.split(MARK_END, 1)
    new = (f"{head}{MARK_START}\n{project_table(d)}\n{MARK_END}{tail}")
    if new != text:
        readme.write_text(new, encoding="utf-8")
        print(f"README.md: Projekttabelle aktualisiert ({len(d['repos'])} Repos)")
    else:
        print("README.md: Projekttabelle bereits aktuell")


# ------------------------------------------------------------------- Main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot")
    a = ap.parse_args()
    d = json.load(open(a.snapshot, encoding="utf-8")) if a.snapshot else fetch()
    if not d["repos"]:
        sys.exit("Keine Repositories gefunden - Abbruch, damit keine leeren "
                 "Karten committet werden.")
    OUT.mkdir(exist_ok=True)
    for name, svg in (("stats", card_stats(d)),
                      ("langs", card_langs(d)),
                      ("recent", card_recent(d))):
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"assets/{name}.svg geschrieben ({len(svg)} Zeichen)")
    update_readme(d)


if __name__ == "__main__":
    main()
