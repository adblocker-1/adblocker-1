#!/usr/bin/env python3
"""Erzeugt die Kawaii-Statistikkarten und die Projektliste fuers README.

Die Karten liegen als SVG im Repo (assets/) statt sie von fremden
Gratis-Diensten zu laden - die sind regelmaessig ueberlastet und liefern
dann 429/500, worauf GitHub ein kaputtes Bild anzeigt.

Aufruf:
  python scripts/generate_stats.py                 # Daten von der GitHub-API
  python scripts/generate_stats.py --snapshot x.json
"""

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kawaii import (BLUSH, PASTELS, SPARK, TRACK, achievement_badge, bear,
                    bunny, card, cat, heart, sparkle)

USER = "adblocker-1"
OUT = Path(__file__).resolve().parent.parent / "assets"

LANG_COLORS = {
    "PowerShell": "#FFB7C5",
    "HTML":       "#CBA6F7",
    "JavaScript": "#B5EAD7",
    "Python":     "#FFDAC1",
    "C#":         "#A0C4FF",
    "Shell":      "#F7C8E0",
}


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
    body = []
    for i, (num, lab) in enumerate(cells):
        x = 40 + (i % 3) * 126
        y = 104 + (i // 3) * 56
        body.append(f'<text x="{x}" y="{y}" class="n">{num}</text>')
        body.append(heart(x, y + 6, 0.6, SPARK))
        body.append(f'<text x="{x + 10}" y="{y + 17}" class="l">{lab}</text>')
    body.append('<text x="40" y="198" class="jp">'
                '\u304d\u3089\u304d\u3089 \u30fb 6\u6642\u9593\u3054\u3068'
                '\u306b\u66f4\u65b0 \u30fb alle 6 Stunden frisch</text>')
    return card(460, 214, "Adblocker \u306e GitHub",
                "\u3010 \u30d7\u30ed\u30d5\u30a3\u30fc\u30eb \u3011",
                "\n".join(body), mascot=cat(410, 92, 1.0))


def card_langs(d):
    counts = Counter(r["language"] for r in d["repos"] if r["language"])
    total = sum(counts.values())
    order = counts.most_common()

    bar_x, bar_y, bar_w, bar_h, gap = 40, 100, 326, 14, 2
    body = [f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
            f'rx="7" fill="{TRACK}"/>',
            f'<clipPath id="clip"><rect x="{bar_x}" y="{bar_y}" '
            f'width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>',
            '<g clip-path="url(#clip)">']
    cx = bar_x
    for i, (lang, n) in enumerate(order):
        w = bar_w * n / total - (gap if i < len(order) - 1 else 0)
        col = LANG_COLORS.get(lang, PASTELS[i % len(PASTELS)])
        body.append(f'<rect x="{cx:.1f}" y="{bar_y}" width="{max(w, 0):.1f}" '
                    f'height="{bar_h}" fill="{col}"/>')
        cx += bar_w * n / total
    body.append("</g>")
    body.append(heart(bar_x + bar_w + 7, bar_y + 2, 0.9, BLUSH))

    # Feste Spalten mit rechtsbuendiger Prozentzahl - eine geschaetzte
    # Textbreite (Zeichen * Pixel) laesst lange Namen ueberlappen.
    for i, (lang, n) in enumerate(order):
        col_x = 40 + (i % 2) * 186
        y = 150 + (i // 2) * 28
        col = LANG_COLORS.get(lang, PASTELS[i % len(PASTELS)])
        body.append(f'<circle cx="{col_x + 6}" cy="{y - 4}" r="5.5" '
                    f'fill="{col}"/>')
        body.append(f'<text x="{col_x + 20}" y="{y}" class="b">'
                    f'{escape(lang)}</text>')
        body.append(f'<text x="{col_x + 166}" y="{y}" class="s" '
                    f'text-anchor="end">{100 * n / total:.0f}%  ({n})</text>')
    body.append(f'<text x="40" y="198" class="s">aus {len(d["repos"])} '
                f'Repositories  \u00b7  {total} mit erkannter Sprache</text>')
    return card(460, 214, "Sprachen", "\u3010 \u8a00\u8a9e \u3011",
                "\n".join(body), mascot=bunny(412, 104, 0.95))


def card_recent(d):
    repos = sorted(d["repos"], key=lambda r: r["pushed_at"], reverse=True)[:5]
    # Wurzelskala: ein einzelnes 640-KB-Repo wuerde linear alle anderen
    # Balken auf unsichtbare Striche zusammendruecken.
    mx = max(r["size"] for r in repos) or 1
    body = []
    for i, r in enumerate(repos):
        y = 100 + i * 25
        dt = r["pushed_at"][:10]
        col = PASTELS[i % len(PASTELS)]
        body.append(heart(40, y - 8, 0.75, col))
        body.append(f'<text x="57" y="{y}" class="b">'
                    f'{escape(r["name"])}</text>')
        body.append(f'<text x="486" y="{y}" class="s">'
                    f'{dt[8:10]}.{dt[5:7]}.{dt[0:4]}</text>')
        body.append(f'<rect x="576" y="{y - 9}" width="230" height="9" '
                    f'rx="4.5" fill="{TRACK}"/>')
        body.append(f'<rect x="576" y="{y - 9}" '
                    f'width="{8 + 222 * (r["size"] / mx) ** 0.5:.1f}" '
                    f'height="9" rx="4.5" fill="{col}"/>')
        body.append(f'<text x="884" y="{y}" class="s" text-anchor="end">'
                    f'{r["size"]} KB</text>')
    body.append(sparkle(470, 58, 3.4, SPARK, 2.1, .7))
    body.append(sparkle(300, 64, 2.6, SPARK, 1.3, .55))
    return card(930, 224,
                "Zuletzt aktualisiert  \u00b7  Balken = Repo-Gr\u00f6\u00dfe",
                "\u3010 \u6700\u8fd1\u306e\u66f4\u65b0 \u3011",
                "\n".join(body), mascot=bear(862, 58, 0.92))


# GitHub bietet fuer die eigenen Profil-Achievements keine API - diese
# Liste bildet nur nach, was tatsaechlich auf https://github.com/adblocker-1
# unter "Achievements" steht, und muss von Hand nachgezogen werden, wenn
# ein neues Abzeichen dazukommt.
ACHIEVEMENTS = [
    ("shark", "Pull Shark", 2),
    ("yolo",  "YOLO",       None),
    ("vault", "Arctic Vault", None),
]


def card_achievements(d):
    body = []
    n = len(ACHIEVEMENTS)
    step = 460 / (n + 1)
    for i, (icon, title, count) in enumerate(ACHIEVEMENTS):
        x = step * (i + 1)
        body.append(achievement_badge(x, 118, icon, title, count, r=28))

    body.append(heart(40, 58, 0.7, SPARK))
    body.append(heart(420, 58, 0.7, SPARK))
    body.append('<text x="230" y="185" class="s" text-anchor="middle">'
                'echte GitHub-Achievements \u00b7 von Hand gepflegt</text>')

    return card(460, 210, "Errungenschaften",
                "\u3010 \u6210\u5c31 \u3011",
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
    ("unifi", "\U0001F4E1"),         # Satellitenschuessel
    ("firewall", "\U0001F525"),      # Feuer
    ("migration", "\U0001F504"),     # Pfeile im Kreis
    ("sophos", "\U0001F6E1\uFE0F"),  # Schild
    ("365", "\U0001F4BE"),           # Diskette
    ("backup", "\u2601\uFE0F"),      # Wolke
    ("cove", "\U0001F5C4\uFE0F"),    # Aktenschrank
    ("mail", "\u2709\uFE0F"),        # Briefumschlag
    ("hyperv", "\U0001F5A5\uFE0F"),  # Bildschirm
    ("flappy", "\U0001F426"),        # Vogel
    ("prtg", "\U0001F4CA"),          # Diagramm
]
FALLBACK_EMOJI = "\u2728"            # Funkeln

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
    new = f"{head}{MARK_START}\n{project_table(d)}\n{MARK_END}{tail}"
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
                      ("recent", card_recent(d)),
                      ("achievements", card_achievements(d))):
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"assets/{name}.svg geschrieben ({len(svg)} Zeichen)")
    update_readme(d)


if __name__ == "__main__":
    main()
