#!/usr/bin/env python3
"""Zeichnet alle Grafiken des Profils (assets/*.svg) und traegt die
Projekttabelle im README nach.

Jede Grafik gibt es zweimal: *-light.svg (Tag, Washi-Papier) und
*-dark.svg (Nacht, Indigo). Das README waehlt per <picture> passend zum
GitHub-Theme des Besuchers.

  python3 scripts/generate.py                   # Daten von der GitHub-API
  python3 scripts/generate.py --snapshot x.json # Daten aus einer Datei
  python3 scripts/generate.py --save-snapshot x.json

Die Karten liegen im Repo statt von Gratis-Diensten zu kommen: Die sind
regelmaessig ueberlastet und GitHub zeigt dann ein kaputtes Bild.
"""

import argparse
import json
import math
import os
import random
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wafu import (BOLD, FALLBACK_COLORS, LANG_COLORS, MEDIUM, THEMES, Svg,
                  blossom, card_bg, hanko, num, petal_path, seigaiha)

USER = "adblocker-1"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"


# =================================================================== Daten
def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": f"{USER}-profile"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    return {
        "user": {k: user[k] for k in ("followers", "created_at")},
        # Forks und das Profil-Repo selbst sind keine eigenen Projekte.
        "repos": [{"name": r["name"], "language": r["language"],
                   "description": r["description"],
                   "stars": r["stargazers_count"],
                   "pushed_at": r["pushed_at"]}
                  for r in repos
                  if not r["fork"] and not r.get("archived")
                  and r["name"] != USER],
    }


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ================================================================== Header
def fuji_x(y, left=True):
    """x-Koordinate der Fuji-Flanke auf Hoehe y (Bezier per Bisektion)."""
    p0, p1, p2 = (600, 340), (800, 322), (870, 150)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        ym = (1 - m) ** 2 * p0[1] + 2 * (1 - m) * m * p1[1] + m * m * p2[1]
        lo, hi = (m, hi) if ym > y else (lo, m)
    x = (1 - lo) ** 2 * p0[0] + 2 * (1 - lo) * lo * p1[0] + lo * lo * p2[0]
    return x if left else 1800 - x


def torii(cx, base, w, h, t):
    """Torii (鳥居) mit geschwungenem Kasagi und leicht schraegen Pfosten."""
    top = base - h
    lx, rx = cx - w * .31, cx + w * .31
    return (
        f'<g fill="{t["shu"]}">'
        # Pfosten, unten etwas nach aussen gestellt
        f'<path d="M{num(lx - 3)} {num(top + 10)}H{num(lx + 3)}'
        f'L{num(lx + 1)} {num(base)}H{num(lx - 7)}Z"/>'
        f'<path d="M{num(rx - 3)} {num(top + 10)}H{num(rx + 3)}'
        f'L{num(rx + 7)} {num(base)}H{num(rx - 1)}Z"/>'
        # Nuki (unterer Balken) und Gakuzuka (Mittelstuetze)
        f'<rect x="{num(cx - w / 2)}" y="{num(top + 26)}" width="{w}" '
        f'height="5"/>'
        f'<rect x="{num(cx - 2.5)}" y="{num(top + 12)}" width="5" height="15"/>'
        # Shimaki und Kasagi: oberer Balken, an den Enden hochgezogen
        f'<rect x="{num(cx - w / 2 + 2)}" y="{num(top + 8)}" '
        f'width="{w - 4}" height="5"/>'
        f'<path d="M{num(cx - w / 2 - 9)} {num(top - 3)}'
        f'Q{num(cx)} {num(top + 9)} {num(cx + w / 2 + 9)} {num(top - 3)}'
        f'L{num(cx + w / 2 + 6)} {num(top + 5)}'
        f'Q{num(cx)} {num(top + 14)} {num(cx - w / 2 - 6)} {num(top + 5)}Z"/>'
        '</g>')


def header(theme):
    t = THEMES[theme]
    night = theme == "dark"
    W, H, G = 1200, 420, 340                 # G = Wasserlinie
    s = Svg(W, H, "Adblocker - PowerShell, PRTG, Monitoring und "
                  "Automatisierung",
            "Berg Fuji vor " + ("dem Mond" if night else "der Sonne") +
            ", Torii, Kirschblueten und Seigaiha-Wellen")
    rnd = random.Random(7)                  # fester Seed = stabile Dateien
    card_bg(s, t, radius=20, clip_id="hc")

    sky = ("#0B1322", "#1B2944") if night else ("#F7F1E6", "#EFDCC6")
    s.defs.append(
        f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{sky[0]}"/>'
        f'<stop offset="1" stop-color="{sky[1]}"/></linearGradient>')
    s.css.append(
        ".pf{animation:fall linear infinite;opacity:0}"
        "@keyframes fall{0%{transform:translate(0,0) rotate(0deg);opacity:0}"
        "10%{opacity:.95}85%{opacity:.85}"
        "100%{transform:translate(-150px,380px) rotate(400deg);opacity:0}}"
        ".tw{animation:tw ease-in-out infinite alternate}"
        "@keyframes tw{from{opacity:.25}to{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.pf{animation:none}"
        ".tw{animation:none}}")
    s.add('<g clip-path="url(#hc)">',
          f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    # --- Sterne (nur nachts)
    if night:
        for i in range(70):
            x, y = rnd.uniform(20, W - 20), rnd.uniform(14, G - 90)
            if math.hypot(x - 900, y - 180) < 130:
                continue
            r = rnd.choice((.7, .9, 1.1, 1.4, 1.8))
            tw = (f' class="tw" style="animation-duration:'
                  f'{rnd.uniform(2.5, 6):.1f}s"') if i % 4 == 0 else ""
            s.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" '
                  f'fill="#F2E7C9"{tw} opacity=".8"/>')

    # --- Sonne bzw. Mond
    if night:
        s.add('<circle cx="900" cy="180" r="150" fill="#F2E7C9" '
              'opacity=".05"/>',
              '<circle cx="900" cy="180" r="118" fill="#F2E7C9" '
              'opacity=".08"/>',
              '<circle cx="900" cy="180" r="92" fill="#F2E7C9"/>',
              '<circle cx="872" cy="160" r="16" fill="#D9CCA8" opacity=".5"/>',
              '<circle cx="925" cy="205" r="11" fill="#D9CCA8" opacity=".45"/>',
              '<circle cx="930" cy="150" r="7" fill="#D9CCA8" opacity=".4"/>')
    else:
        s.add(f'<circle cx="900" cy="180" r="112" fill="{t["shu"]}"/>')

    # --- Goldene Wolkenbaender (Suyari-gasumi) hinter dem Berg
    band = t["gold"]
    op_back, op_front = (.14, .22) if night else (.3, .45)
    for x, y, w, h in ((640, 98, 210, 20), (1000, 128, 210, 20),
                       (640, 218, 170, 18)):
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" '
              f'fill="{band}" opacity="{op_back}"/>')

    # --- Fuji
    s.add(f'<path d="M600 {G}Q800 322 870 150L884 158L900 147L916 158'
          f'L930 150Q1000 322 1200 {G}Z" fill="{t["fuji"]}"/>')
    snow_y = 212
    pts = [(fuji_x(y), y) for y in range(snow_y, 150, -8)]
    pts += [(870, 150), (884, 158), (900, 147), (916, 158), (930, 150)]
    pts += [(fuji_x(y, False), y) for y in range(152, snow_y + 1, 8)]
    # gezackte Schneegrenze, von rechts nach links
    xr, xl = fuji_x(snow_y, False), fuji_x(snow_y)
    drips = (0, 18, 4, 30, 8, 22, 2, 34, 6, 16, 0)
    n = len(drips) - 1
    for i, d in enumerate(drips[1:-1], 1):
        pts.append((xr - (xr - xl) * i / n, snow_y + d))
    s.add('<path d="M' + "L".join(f"{num(x)} {num(y)}" for x, y in pts) +
          f'Z" fill="{t["snow"]}"/>')
    # Grate unterhalb der Schneekappe
    for x0, x1 in ((848, 790), (880, 850), (905, 915), (930, 975),
                   (955, 1030)):
        s.add(f'<path d="M{x0} 236Q{(x0 + x1) / 2} 270 {x1} 318" fill="none" '
              f'stroke="{t["hills2"]}" stroke-width="1.6" opacity=".35"/>')

    # --- Wolkenband vor dem Berg
    s.add(f'<rect x="700" y="262" width="190" height="18" rx="9" '
          f'fill="{band}" opacity="{op_front}"/>',
          f'<rect x="990" y="286" width="150" height="16" rx="8" '
          f'fill="{band}" opacity="{op_front}"/>')

    # --- Huegel vor dem Fuss des Berges
    s.add(f'<path d="M520 {G + 6}C600 300 660 304 730 322S850 300 930 318'
          f'S1100 296 1200 312L1200 {G + 20}L520 {G + 20}Z" '
          f'fill="{t["hills"]}"/>')

    s.add(torii(662, G + 2, 70, 82, t))

    # --- Wellen
    s.add(seigaiha(s, t, 0, G + 18, W, H, r=22))

    # --- Kirschzweig oben rechts
    br = t["branch"]
    for d, w in (("M1215 18C1150 28 1098 46 1040 84", 10),
                 ("M1122 38C1102 68 1086 96 1060 122", 6),
                 ("M1066 68C1034 72 1004 64 976 48", 5),
                 ("M1172 24C1166 48 1170 70 1182 96", 5),
                 ("M1040 84C1020 96 1006 112 998 130", 4)):
        s.add(f'<path d="{d}" fill="none" stroke="{br}" stroke-width="{w}" '
              'stroke-linecap="round"/>')
    for x, y, r, rot in ((1040, 84, 17, 10), (1060, 122, 15, 40),
                         (976, 48, 14, 20), (1182, 96, 15, 5),
                         (1122, 40, 16, 30), (1006, 66, 11, 50),
                         (1150, 30, 13, 15), (1090, 100, 12, 60),
                         (998, 130, 13, 25), (1200, 50, 12, 45)):
        s.add(blossom(x, y, r, rot, t))
    for x, y in ((1028, 108), (1110, 70), (962, 40), (1170, 118)):
        s.add(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{t["sakura_in"]}"/>')

    # --- Fallende Bluetenblaetter
    for i in range(16):
        x = rnd.uniform(640, 1190)
        y = rnd.uniform(-20, 60)
        dur = rnd.uniform(9, 16)
        delay = -rnd.uniform(0, dur)
        size = rnd.uniform(4, 6.5)
        s.add(f'<g transform="translate({num(x)} {num(y)})">'
              f'<path class="pf" d="{petal_path(size)}" fill="{t["sakura"]}" '
              f'style="animation-duration:{dur:.1f}s;'
              f'animation-delay:{delay:.1f}s"/></g>')

    # --- Titelblock links
    s.add(f'<rect x="64" y="86" width="36" height="3" fill="{t["shu"]}"/>')
    s.text("ようこそ", 114, 96, 20, BOLD, t["shu"], spacing=.25)
    s.text("WILLKOMMEN", 114 + BOLD.width("ようこそ", 20, .25) + 16, 95, 13,
           MEDIUM, t["muted"], spacing=.3)
    w = s.text("Adblocker", 62, 184, 84, BOLD, t["ink"])
    hanko(s, 62 + w + 20, 114, 62, "監視", t)
    s.text("アドブロッカー", 66, 228, 24, MEDIUM, t["ink2"], spacing=.45)
    s.add(f'<rect x="66" y="250" width="420" height="1.2" fill="{t["line"]}"/>')
    s.text("PowerShell · PRTG · Monitoring · Automatisierung", 66, 286, 19,
           MEDIUM, t["ink2"])
    s.text("監視と自動化、一行ずつ。", 66, 318, 17, MEDIUM, t["muted"],
           spacing=.2)

    s.add("</g>")
    return s.render()


# ======================================================== Abschnittskoepfe
SECTIONS = [
    # Datei, Nummer, Kanji, Lesung, Deutsch
    ("about", "一", "自己紹介", "jiko shōkai", "Über mich"),
    ("tools", "二", "道具箱", "dōgubako", "Werkzeugkasten"),
    ("works", "三", "作品", "sakuhin", "Projekte"),
    ("stats", "四", "統計", "tōkei", "Statistiken"),
    ("trail", "五", "足跡", "ashiato", "Spuren"),
    ("contact", "六", "連絡", "renraku", "Kontakt"),
]


def section(theme, nr, kanji, reading, german):
    t = THEMES[theme]
    s = Svg(900, 96, f"{kanji} - {german}")
    s.add(f'<circle cx="42" cy="48" r="29" fill="{t["shu"]}"/>')
    # CJK-Zeichen sitzen von -120 bis 880 Einheiten: Mitte = 0.38 em
    s.text(nr, 42, 48 + 28 * .38, 28, BOLD, t["on_shu"], anchor="middle")
    x = 92
    x += s.text(kanji, x, 48 + 42 * .38, 42, BOLD, t["ink"], spacing=.08)
    x += 22
    s.add(f'<rect x="{num(x)}" y="28" width="1.4" height="40" '
          f'fill="{t["line"]}"/>')
    x += 20
    w1 = s.text(german, x, 45, 22, BOLD, t["ink"])
    w2 = s.text(reading, x, 70, 14, MEDIUM, t["muted"], spacing=.14)
    x += max(w1, w2) + 26
    s.add(f'<rect x="{num(x)}" y="47.4" width="{num(866 - x)}" height="1.2" '
          f'fill="{t["line"]}"/>',
          f'<rect x="872" y="42" width="9" height="9" fill="{t["shu"]}" '
          f'transform="rotate(45 876.5 46.5)"/>')
    return s.render()


# =================================================================== Haiku
HAIKU = ["夜の番", "静かに光る", "緑の灯"]
HAIKU_DE = ["Nachtwache –", "still leuchten sie,", "die grünen Lichter."]


def haiku(theme):
    t = THEMES[theme]
    s = Svg(900, 300, "Haiku: " + " / ".join(HAIKU) + " - " +
            " ".join(HAIKU_DE))
    card_bg(s, t)
    # Enso: offener Pinselkreis hinter dem senkrechten Text
    a0, a1, cx, cy, r = math.radians(-60), math.radians(255), 758, 150, 112
    s.add(f'<path d="M{num(cx + r * math.cos(a0))} {num(cy + r * math.sin(a0))}'
          f'A{r} {r} 0 1 1 {num(cx + r * math.cos(a1))} '
          f'{num(cy + r * math.sin(a1))}" fill="none" stroke="{t["ink"]}" '
          f'stroke-width="11" stroke-linecap="round" opacity=".08"/>')
    # Tategaki: Spalten von rechts nach links, leicht versetzt
    size = 34
    for i, (line, top) in enumerate(zip(HAIKU, (58, 86, 114))):
        s.vtext(line, 812 - i * 54, top, size, BOLD, t["ink"], spacing=.12)
    hanko(s, 610, 196, 46, "俳句", t, rot=3)

    s.add(f'<rect x="56" y="62" width="28" height="3" fill="{t["shu"]}"/>')
    s.text("俳句", 96, 71, 18, BOLD, t["shu"], spacing=.2)
    s.text("HAIKU", 146, 70, 13, MEDIUM, t["muted"], spacing=.3)
    for i, line in enumerate(HAIKU_DE):
        w = s.text(line, 56, 124 + i * 40, 27, MEDIUM, t["ink"])
    # drei gruene Sensoren - alles in Ordnung
    for j in range(3):
        x = 56 + w + 22 + j * 18
        s.add(f'<circle cx="{num(x)}" cy="195" r="7" fill="#5DAE5B" '
              f'opacity=".25"/>',
              f'<circle cx="{num(x)}" cy="195" r="4" fill="#4E9A4B"/>')
    s.text("Wenn nachts alle Sensoren grün sind, ist Ruhe.", 56, 250, 16,
           MEDIUM, t["muted"])
    return s.render()


# ============================================================ Werkzeugkasten
TOOLS = [
    ("言語", "Sprachen", ["PowerShell", "Python", "JavaScript", "HTML",
                         "JSON"]),
    ("監視", "Monitoring", ["PRTG", "UniFi", "Sophos Central",
                           "Sophos Firewall", "Veeam", "MailStore", "Cove",
                           "Hyper-V", "Intune", "Entra ID"]),
    ("道具", "Werkzeuge", ["Git", "GitHub Actions", "VS Code", "REST-APIs",
                          "Windows Server", "Claude"]),
]


def tools(theme):
    t = THEMES[theme]
    TAG_H, GAP, LEFT, RIGHT, FS = 38, 10, 200, 864, 16
    rows = []                         # (label, de, [(x, y, text, w)])
    y = 36
    for kanji, de, items in TOOLS:
        x, placed, top = LEFT, [], y
        for it in items:
            w = MEDIUM.width(it, FS) + 44
            if x + w > RIGHT:
                x, y = LEFT, y + TAG_H + GAP
            placed.append((x, y, it, w))
            x += w + GAP
        rows.append((kanji, de, top, y + TAG_H, placed))
        y += TAG_H + 36
    H = y - 36 + 34

    s = Svg(900, H, "Werkzeugkasten: " + "; ".join(
        f"{de}: {', '.join(i)}" for _, de, i in TOOLS))
    card_bg(s, t)
    for n, (kanji, de, top, bottom, placed) in enumerate(rows):
        mid = (top + bottom) / 2
        s.text(kanji, 40, mid + 2, 30, BOLD, t["shu"], spacing=.1)
        s.text(de, 41, mid + 26, 13, MEDIUM, t["muted"], spacing=.12)
        if n:
            s.add(f'<path d="M40 {num(top - 18)}H860" stroke="{t["line"]}" '
                  f'stroke-dasharray="2 6" stroke-linecap="round"/>')
        for x, ty, it, w in placed:
            # Holztafel (名札) mit Nagelloch
            s.add(f'<rect x="{num(x)}" y="{ty}" width="{num(w)}" '
                  f'height="{TAG_H}" rx="5" fill="{t["wood"]}" '
                  f'stroke="{t["wood_edge"]}" stroke-width="1.2"/>',
                  f'<path d="M{num(x + 6)} {ty + 5}H{num(x + w - 6)}" '
                  f'stroke="{t["wood_edge"]}" stroke-width=".8" '
                  f'opacity=".45"/>',
                  f'<circle cx="{num(x + 14)}" cy="{ty + TAG_H / 2}" r="3" '
                  f'fill="{t["wood_edge"]}"/>')
            s.text(it, x + 26, ty + TAG_H / 2 + 5.5, FS, MEDIUM,
                   t["wood_ink"])
    return s.render()


# ================================================================ Statistik
def stats(theme, d):
    t = THEMES[theme]
    repos = d["repos"]
    since = parse_time(d["user"]["created_at"])
    last = max(parse_time(r["pushed_at"]) for r in repos)
    counts = Counter(r["language"] for r in repos if r["language"])
    total = sum(counts.values())

    cells = [
        ("作品", str(len(repos)), "Repositories"),
        ("言語", str(len(counts)), "Sprachen"),
        ("星", str(sum(r["stars"] for r in repos)), "Sterne"),
        ("仲間", str(d["user"]["followers"]), "Follower"),
        ("開始", since.strftime("%Y"), "Dabei seit"),
        ("更新", last.strftime("%d.%m.%Y"), "Letzter Push"),
    ]
    themes = Counter(category(r["name"]) for r in repos)

    s = Svg(900, 320, "Statistiken: " + ", ".join(
        f"{de} {v}" for _, v, de in cells) + "; Sprachen: " + ", ".join(
        f"{lang} {n}" for lang, n in counts.most_common()) + "; Themen: " +
        ", ".join(f"{de} {n}" for (_, de), n in themes.most_common()))
    card_bg(s, t)

    for i, (kanji, value, de) in enumerate(cells):
        x = 44 + (i % 3) * 138
        y = 48 + (i // 3) * 118
        s.text(kanji, x, y + 16, 16, BOLD, t["shu"], spacing=.15)
        size = 24 if len(value) > 6 else 40
        s.text(value, x, y + 62, size, BOLD, t["ink"])
        s.text(de, x, y + 86, 13, MEDIUM, t["muted"], spacing=.06)
    s.text("Aktualisiert sich alle 6 Stunden per GitHub Action.", 44, 290,
           12, MEDIUM, t["muted"], spacing=.04)

    s.add(f'<rect x="466" y="44" width="1.2" height="232" fill="{t["line"]}"/>')

    # Sprachen: Balken + Legende
    X0, X1 = 500, 858
    s.text("言語", X0, 62, 16, BOLD, t["shu"], spacing=.15)
    s.text("Sprachen nach Repositories", X0 + 48, 61, 13, MEDIUM,
           t["muted"])
    s.defs.append(f'<clipPath id="bar"><rect x="{X0}" y="76" '
                  f'width="{X1 - X0}" height="14" rx="7"/></clipPath>')
    s.add(f'<rect x="{X0}" y="76" width="{X1 - X0}" height="14" rx="7" '
          f'fill="{t["track"]}"/>', '<g clip-path="url(#bar)">')
    colors, x = {}, X0
    for i, (lang, n) in enumerate(counts.most_common()):
        colors[lang] = LANG_COLORS[theme].get(
            lang, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        w = (X1 - X0) * n / total
        s.add(f'<rect x="{num(x)}" y="76" width="{num(w)}" height="14" '
              f'fill="{colors[lang]}"/>')
        if x > X0:
            s.add(f'<rect x="{num(x - 1)}" y="76" width="2" height="14" '
                  f'fill="{t["bg"]}"/>')
        x += w
    s.add("</g>")
    for i, (lang, n) in enumerate(counts.most_common(4)):
        cx = X0 + (i % 2) * 188
        cy = 120 + (i // 2) * 26
        s.add(f'<circle cx="{cx + 6}" cy="{cy - 5}" r="5.5" '
              f'fill="{colors[lang]}"/>')
        s.text(MEDIUM.safe(lang), cx + 20, cy, 15, MEDIUM, t["ink"])
        s.text(f"{100 * n / total:.0f} %", cx + 168, cy, 13, MEDIUM,
               t["muted"], anchor="end")

    # Themen der Projekte (gleiche Einteilung wie in der Projekttabelle)
    s.text("分野", X0, 186, 16, BOLD, t["shu"], spacing=.15)
    s.text("Themen der Projekte", X0 + 48, 185, 13, MEDIUM, t["muted"])
    top = max(themes.values())
    # bei Gleichstand alphabetisch, damit die Reihenfolge stabil bleibt
    ranked = sorted(themes.items(), key=lambda kv: (-kv[1], kv[0][1]))
    for i, ((jp, de), n) in enumerate(ranked[:8]):
        cx = X0 + (i % 2) * 188
        cy = 214 + (i // 2) * 24
        s.text(de, cx, cy, 13, MEDIUM, t["ink"])
        bw = 44 * n / top
        s.add(f'<rect x="{num(cx + 150 - bw)}" y="{cy - 8}" width="{num(bw)}" '
              f'height="7" rx="3.5" fill="{t["gold"]}" opacity=".7"/>')
        s.text(str(n), cx + 168, cy, 13, BOLD, t["shu"], anchor="end")
    return s.render()


# ================================================================= Buttons
BUTTONS = [
    ("repos", "作", "作品を見る", "Repositories"),
    ("follow", "縁", "フォローする", "Folgen"),
]


def button(seal, jp, de):
    """Zinnoberroter Knopf - auf hellem wie dunklem Grund gut lesbar, daher
    nur eine Fassung (ein <img> im Link statt <picture>)."""
    t = THEMES["light"]
    s = Svg(280, 64, f"{de} ({jp})")
    s.add(f'<rect width="280" height="64" rx="12" fill="{t["shu"]}"/>',
          f'<rect x="12" y="12" width="40" height="40" rx="5" '
          f'fill="{t["on_shu"]}"/>')
    s.text(seal, 32, 32 + 24 * .38, 24, BOLD, t["shu"], anchor="middle")
    s.text(jp, 68, 28, 13, BOLD, t["on_shu"], spacing=.15,
           attrs='opacity=".85"')
    s.text(de, 68, 50, 19, BOLD, t["on_shu"])
    return s.render()


# ================================================================== Fusszeile
def footer(theme):
    t = THEMES[theme]
    W, H = 1200, 300
    s = Svg(W, H, "一期一会 - ichi-go ichi-e: Jede Begegnung ist einmalig. "
                  "Danke fürs Vorbeischauen!")
    card_bg(s, t, radius=20, clip_id="fc")
    s.add('<g clip-path="url(#fc)">')
    s.add(blossom(90, 70, 20, 12, t), blossom(128, 104, 14, 40, t),
          blossom(1110, 76, 18, 30, t), blossom(1072, 112, 12, 5, t))
    s.vtext("またね", 200, 50, 26, BOLD, t["ink2"], spacing=.1)
    s.text("一期一会", 600, 118, 66, BOLD, t["ink"], anchor="middle",
           spacing=.22)
    s.text("ichi-go ichi-e", 600, 152, 15, MEDIUM, t["muted"],
           anchor="middle", spacing=.35)
    s.text("Jede Begegnung ist einmalig – danke fürs Vorbeischauen.", 600,
           190, 20, MEDIUM, t["ink2"], anchor="middle")
    hanko(s, 960, 54, 58, "感謝", t, rot=5)
    s.add(seigaiha(s, t, 0, 244, W, H, r=18))
    s.add("</g>")
    return s.render()


# ========================================================= Projekttabelle
MARK_START = "<!-- PROJEKTE:START -->"
MARK_END = "<!-- PROJEKTE:ENDE -->"
# Erster Treffer im Repo-Namen gewinnt - Reihenfolge ist Absicht.
CATEGORIES = [
    ("migration", "移行", "Migration"),
    ("firewall", "防御", "Firewall"),
    ("sophos", "防御", "Security"),
    ("unifi", "ネットワーク", "Netzwerk"),
    ("365", "バックアップ", "Backup"),
    ("veeam", "バックアップ", "Backup"),
    ("cove", "バックアップ", "Backup"),
    ("mail", "メール", "E-Mail"),
    ("hyperv", "仮想化", "Virtualisierung"),
    ("entra", "クラウド", "Cloud"),
    ("intune", "クラウド", "Cloud"),
]
FALLBACK_CATEGORY = ("道具", "Werkzeug")
MAX_DESC = 160


def category(name):
    low = name.lower().replace("-", "")
    for key, jp, de in CATEGORIES:
        if key in low:
            return jp, de
    return FALLBACK_CATEGORY


def describe(r):
    text = (r.get("description") or "").strip().replace("\n", " ")
    if not text:
        return "&nbsp;"
    if len(text) > MAX_DESC:
        text = text[:MAX_DESC].rsplit(" ", 1)[0].rstrip(" .,;-") + " …"
    # Ein rohes | wuerde die Markdown-Tabelle sprengen, < und > HTML.
    return (text.replace("|", "\\|").replace("<", "&lt;")
            .replace(">", "&gt;"))


def project_table(d):
    rows = ["| 作品 · Projekt | 分野 · Thema und Beschreibung |",
            "| :-- | :-- |"]
    for r in sorted(d["repos"], key=lambda x: x["pushed_at"], reverse=True):
        jp, de = category(r["name"])
        url = f"https://github.com/{USER}/{r['name']}"
        rows.append(f"| **[{r['name']}]({url})** "
                    f"| <sub>{jp} · {de}</sub><br>{describe(r)} |")
    return "\n".join(rows)


def update_readme(d):
    """Ersetzt nur den Bereich zwischen den Markern. Fehlen sie, bleibt das
    README unangetastet - lieber unveraendert als halb zerstoert."""
    text = README.read_text(encoding="utf-8")
    if MARK_START not in text or MARK_END not in text:
        print("README.md: Marker fehlen - unveraendert gelassen.")
        return
    head, rest = text.split(MARK_START, 1)
    _, tail = rest.split(MARK_END, 1)
    new = f"{head}{MARK_START}\n{project_table(d)}\n{MARK_END}{tail}"
    if new != text:
        README.write_text(new, encoding="utf-8")
        print(f"README.md: Projekttabelle aktualisiert "
              f"({len(d['repos'])} Repos)")
    else:
        print("README.md: Projekttabelle ist aktuell")


# ==================================================================== Main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", help="Daten aus JSON-Datei statt API")
    ap.add_argument("--save-snapshot", help="API-Daten zusaetzlich speichern")
    a = ap.parse_args()

    if a.snapshot:
        d = json.loads(Path(a.snapshot).read_text(encoding="utf-8"))
    else:
        d = fetch()
    if a.save_snapshot:
        Path(a.save_snapshot).write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    if not d["repos"]:
        sys.exit("Keine Repositories gefunden - Abbruch, damit keine leeren "
                 "Karten committet werden.")

    out = {}
    for theme in THEMES:
        out[f"header-{theme}"] = header(theme)
        out[f"haiku-{theme}"] = haiku(theme)
        out[f"tools-{theme}"] = tools(theme)
        out[f"stats-{theme}"] = stats(theme, d)
        out[f"footer-{theme}"] = footer(theme)
        for key, *args in SECTIONS:
            out[f"section-{key}-{theme}"] = section(theme, *args)

    for key, *args in BUTTONS:
        out[f"button-{key}"] = button(*args)

    ASSETS.mkdir(exist_ok=True)
    for name, svg in out.items():
        path = ASSETS / f"{name}.svg"
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8")
            print(f"assets/{name}.svg geschrieben")
    update_readme(d)


if __name__ == "__main__":
    main()
