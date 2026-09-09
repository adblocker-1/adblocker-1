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
                   "size": r["size"], "stars": r["stargazers_count"],
                   "forks": r["forks_count"], "pushed_at": r["pushed_at"],
                   "created_at": r["created_at"]}
                  for r in repos if not r["fork"]],
    }


# -------------------------------------------------------------- Bausteine
def card(w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<style>
  .t {{ font: 600 15px {FONT}; fill: {TITLE}; }}
  .n {{ font: 700 22px {FONT}; fill: {NUMBER}; }}
  .l {{ font: 400 11px {FONT}; fill: {MUTED}; letter-spacing:.4px; }}
  .b {{ font: 400 12.5px {FONT}; fill: {TEXT}; }}
  .s {{ font: 400 11px {FONT}; fill: {MUTED}; }}
</style>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14"
      fill="{BG}" stroke="{BORDER}"/>
<text x="22" y="32" class="t">{escape(title)}</text>
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
    body = [heart(410, 20, 1.5, "#FFC9D6")]
    for i, (num, lab) in enumerate(cells):
        x = 24 + (i % 3) * 145
        y = 80 + (i // 3) * 58
        body.append(f'<text x="{x}" y="{y}" class="n">{num}</text>')
        body.append(f'<text x="{x}" y="{y + 17}" class="l">{lab}</text>')
    return card(450, 170, "Adblocker  ·  GitHub", "\n".join(body))


def card_langs(d):
    counts = Counter(r["language"] for r in d["repos"] if r["language"])
    total = sum(counts.values())
    order = counts.most_common()

    bar_x, bar_y, bar_w, bar_h, gap = 24, 70, 402, 12, 2
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
        col_x = 24 + (i % 2) * 213
        y = 118 + (i // 2) * 28
        col = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        pct = 100 * n / total
        body.append(f'<circle cx="{col_x + 6}" cy="{y - 4}" r="5.5" fill="{col}"/>')
        body.append(f'<text x="{col_x + 20}" y="{y}" class="b">{escape(lang)}</text>')
        body.append(f'<text x="{col_x + 189}" y="{y}" class="s" '
                    f'text-anchor="end">{pct:.0f}%  ({n})</text>')
    return card(450, 170, "Repositories nach Sprache", "\n".join(body))


def card_recent(d):
    repos = sorted(d["repos"], key=lambda r: r["pushed_at"], reverse=True)[:5]
    # Wurzelskala: ein einzelnes 640-KB-Repo wuerde linear alle anderen
    # Balken auf unsichtbare Striche zusammendruecken.
    mx = max(r["size"] for r in repos) or 1
    body = []
    for i, r in enumerate(repos):
        y = 64 + i * 26
        d = r["pushed_at"][:10]
        date = f"{d[8:10]}.{d[5:7]}.{d[0:4]}"
        w = 8 + 232 * (r["size"] / mx) ** 0.5
        col = FALLBACK[i % len(FALLBACK)]
        body.append(f'<text x="24" y="{y}" class="b">{escape(r["name"])}</text>')
        body.append(f'<text x="470" y="{y}" class="s">{date}</text>')
        body.append(f'<rect x="560" y="{y - 9}" width="240" height="9" '
                    f'rx="4.5" fill="{TRACK}"/>')
        body.append(f'<rect x="560" y="{y - 9}" width="{w:.1f}" height="9" '
                    f'rx="4.5" fill="{col}"/>')
        body.append(f'<text x="890" y="{y}" class="s" text-anchor="end">'
                    f'{r["size"]} KB</text>')
    return card(914, 188, "Zuletzt aktualisiert  ·  Balken = Repo-Gr\u00f6\u00dfe",
                "\n".join(body))


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


if __name__ == "__main__":
    main()
