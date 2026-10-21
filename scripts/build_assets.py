#!/usr/bin/env python3
"""Generate the SVG graphics used in the profile README.

Every graphic is written in a light and a dark variant so the README can
switch between them with <picture> and prefers-color-scheme.

Usage: python3 scripts/build_assets.py
"""

from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

THEMES = {
    "dark": {
        "bg1": "#0d1117", "bg2": "#111d2e", "panel": "#161b22", "border": "#30363d",
        "grid": "#1f2a37", "text": "#e6edf3", "muted": "#8b949e", "ok": "#3fb950",
        "accent1": "#58a6ff", "accent2": "#3fb950", "chip": "#1c2431", "key": "#21262d",
    },
    "light": {
        "bg1": "#ffffff", "bg2": "#eef4ff", "panel": "#ffffff", "border": "#d0d7de",
        "grid": "#e4e9f0", "text": "#1f2328", "muted": "#59636e", "ok": "#1a7f37",
        "accent1": "#0969da", "accent2": "#1a7f37", "chip": "#f6f8fa", "key": "#eaeef2",
    },
}

CATEGORY_COLORS = {
    "Backup": "#2da44e",
    "Mail": "#e16f24",
    "Security": "#2f81f7",
    "Cloud": "#1b9bd1",
    "Virtualization": "#8250df",
    "Network": "#14a39a",
    "Admin tool": "#bf3989",
}

POWERSHELL = "#5391fe"

PROJECTS = [
    ("Veeam-backup-PRTG", "Backup", "PRTG sensor",
     "Job status and repository usage for Veeam Backup & Replication."),
    ("Veeam-Backup365-PRTG", "Backup", "PRTG sensor",
     "Job status and object counts for Veeam Backup for Microsoft 365."),
    ("Cove-Data-Protection-PRTG", "Backup", "PRTG sensor",
     "Backup status, errors and backup age for N-able Cove Data Protection."),
    ("MailStore-PRTG", "Mail", "PRTG sensor",
     "Archiving profiles and job status for MailStore Server."),
    ("Sophos-Central-PRTG", "Security", "PRTG sensor",
     "Endpoints, servers and mobile devices in Sophos Central, with health and alerts."),
    ("entra-Health-Check-PRTG", "Cloud", "PRTG sensor",
     "Device inventory, compliance and sync status for Microsoft Intune and Entra ID."),
    ("HyperVReplicaHealth-PRTG", "Virtualization", "PRTG push sensor",
     "Replication health of every Hyper-V virtual machine."),
    ("UnifiController-PRTG", "Network", "PRTG sensor",
     "UniFi devices across platforms, via API key or local login."),
    ("Sophos-api-device-migration", "Admin tool", "GUI tool",
     "Moves Sophos Central devices between tenants with a few clicks."),
    ("Sophos-Firewall-API-Documentation", "Admin tool", "Export tool",
     "Exports a Sophos Firewall configuration to Excel, JSON and XML."),
]


def svg(width, height, title, body, style=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; }}
  @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .25; }} }}
  .pulse {{ animation: pulse 2s ease-in-out infinite; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
{style}</style>
{body}
</svg>
"""


def header(t):
    w, h = 1200, 320
    # Heartbeat line inside the status panel.
    px, py, pw = 790, 46, 350
    base = py + 88
    pts, x = [], px + 20
    beat = [(0, 0), (40, 0), (50, -10), (58, 0), (66, 0), (74, 26), (84, -52), (94, 14), (102, 0), (140, 0)]
    while x < px + pw - 20:
        for dx, dy in beat:
            if x + dx <= px + pw - 20:
                pts.append(f"{x + dx},{base + dy}")
        x += 140
    ecg = " ".join(pts)

    rows = [("Backup jobs", "OK"), ("Firewalls", "OK"), ("Replication", "OK")]
    row_svg = ""
    for i, (name, state) in enumerate(rows):
        y = py + 150 + i * 25
        row_svg += f"""
  <circle cx="{px + 26}" cy="{y - 4}" r="4" fill="{t['ok']}" class="pulse" style="animation-delay:{i * .4}s"/>
  <text x="{px + 40}" y="{y}" class="mono" font-size="13" fill="{t['muted']}">{name}</text>
  <text x="{px + pw - 20}" y="{y}" class="mono" font-size="13" fill="{t['ok']}" text-anchor="end" font-weight="600">{state}</text>"""

    chips = ["8 PRTG sensors", "2 admin tools", "1 Linux suite"]
    chip_svg, cx = "", 64
    for c in chips:
        cw = 22 + len(c) * 8.2
        chip_svg += f"""
  <rect x="{cx}" y="226" width="{cw:.0f}" height="34" rx="17" fill="{t['chip']}" stroke="{t['border']}"/>
  <text x="{cx + cw / 2:.0f}" y="248" class="mono" font-size="14" fill="{t['text']}" text-anchor="middle">{c}</text>"""
        cx += cw + 12

    body = f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t['bg1']}"/><stop offset="1" stop-color="{t['bg2']}"/>
  </linearGradient>
  <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{t['accent1']}"/><stop offset="1" stop-color="{t['accent2']}"/>
  </linearGradient>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M32 0H0V32" fill="none" stroke="{t['grid']}" stroke-width="1"/>
  </pattern>
  <clipPath id="frame"><rect width="{w}" height="{h}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#frame)">
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)" opacity=".6"/>
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="none" stroke="{t['border']}"/>

<rect x="64" y="52" width="250" height="30" rx="15" fill="{t['chip']}" stroke="{t['border']}"/>
<circle cx="84" cy="67" r="5" fill="{t['ok']}" class="pulse"/>
<text x="98" y="72" class="mono" font-size="12" fill="{t['ok']}" letter-spacing="1.5" font-weight="600">ALL SYSTEMS OPERATIONAL</text>

<text x="62" y="152" class="sans" font-size="58" font-weight="700" fill="{t['text']}">Hi, I'm <tspan fill="url(#name)">Adblocker</tspan></text>
<text x="64" y="196" class="sans" font-size="22" fill="{t['muted']}">Systems Engineer  ·  Monitoring  ·  PowerShell Automation</text>
{chip_svg}

<rect x="{px}" y="{py}" width="{pw}" height="{h - 2 * py}" rx="14" fill="{t['panel']}" stroke="{t['border']}"/>
<circle cx="{px + 22}" cy="{py + 22}" r="5" fill="#ff5f57"/>
<circle cx="{px + 38}" cy="{py + 22}" r="5" fill="#febc2e"/>
<circle cx="{px + 54}" cy="{py + 22}" r="5" fill="#28c840"/>
<text x="{px + pw - 20}" y="{py + 27}" class="mono" font-size="12" fill="{t['muted']}" text-anchor="end">prtg://uptime</text>
<line x1="{px}" y1="{py + 42}" x2="{px + pw}" y2="{py + 42}" stroke="{t['border']}"/>
<polyline points="{ecg}" fill="none" stroke="{t['grid']}" stroke-width="2.5" stroke-linejoin="round"/>
<polyline points="{ecg}" fill="none" stroke="{t['ok']}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" class="ecg"/>
<line x1="{px + 20}" y1="{py + 120}" x2="{px + pw - 20}" y2="{py + 120}" stroke="{t['border']}" stroke-dasharray="3 4"/>
{row_svg}"""
    style = """  .ecg { stroke-dasharray: 380 1200; animation: ecg 3.2s linear infinite; }
  @keyframes ecg { from { stroke-dashoffset: 1200; } to { stroke-dashoffset: -380; } }
"""
    return svg(w, h, "Hi, I'm Adblocker: Systems Engineer, Monitoring, PowerShell Automation", body, style)


def card(t, name, category, kind, desc, delay):
    w, h = 460, 156
    color = CATEGORY_COLORS[category]
    # Narrowest width that keeps the line count, so the lines come out balanced.
    n = len(wrap(desc, 54))
    lines = wrap(desc, min(c for c in range(20, 55) if len(wrap(desc, c)) == n))[:2]
    desc_svg = "".join(
        f'\n  <text x="24" y="{92 + i * 21}" class="sans" font-size="14" fill="{t["muted"]}">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t['panel']}" stroke="{t['border']}"/>
<rect x="24" y="20" width="{len(category) * 7.6 + 20:.0f}" height="22" rx="11" fill="{color}" fill-opacity=".14"/>
<text x="{24 + (len(category) * 7.6 + 20) / 2:.0f}" y="35" class="sans" font-size="11.5" font-weight="600" fill="{color}" text-anchor="middle" letter-spacing=".6">{category.upper()}</text>
<circle cx="{w - 30}" cy="31" r="5" fill="{t['ok']}" class="pulse" style="animation-delay:{delay:.1f}s"/>
<text x="24" y="68" class="sans" font-size="19" font-weight="700" fill="{t['accent1']}">{escape(name)}</text>{desc_svg}
<circle cx="30" cy="{h - 22}" r="6" fill="{POWERSHELL}"/>
<text x="43" y="{h - 17}" class="sans" font-size="13" fill="{t['muted']}">PowerShell</text>
<text x="{w - 24}" y="{h - 17}" class="mono" font-size="12" fill="{t['muted']}" text-anchor="end">{escape(kind)}</text>"""
    return svg(w, h, f"{name}: {desc}", body)


def spotlight(t):
    w, h = 1200, 300
    keys = ""
    kx, ky, ks, gap = 690, 74, 46, 10
    for r in range(3):
        for c in range(5):
            i = r * 5 + c
            x, y = kx + c * (ks + gap), ky + r * (ks + gap)
            keys += f'\n  <rect x="{x}" y="{y}" width="{ks}" height="{ks}" rx="9" fill="{t["key"]}" stroke="{t["border"]}"/>'
            keys += (f'\n  <rect x="{x + 3}" y="{y + 3}" width="{ks - 6}" height="{ks - 6}" rx="7" '
                     f'fill="{t["accent1"]}" class="key" style="animation-delay:{(i * 7 % 15) * .25:.2f}s"/>')

    faders = ""
    fx0 = 1000
    for i, (label, lvl) in enumerate([("PERS", 0), ("STRM", 1), ("CHAT", 2)]):
        fx = fx0 + i * 56
        faders += f"""
  <rect x="{fx + 14}" y="74" width="8" height="150" rx="4" fill="{t['key']}" stroke="{t['border']}"/>
  <rect x="{fx + 14}" y="74" width="8" height="150" rx="4" fill="{t['ok']}" class="meter m{lvl}"/>
  <rect x="{fx}" y="130" width="36" height="16" rx="4" fill="{t['text']}" class="fader f{lvl}"/>
  <text x="{fx + 18}" y="250" class="mono" font-size="11" fill="{t['muted']}" text-anchor="middle">{label}</text>"""

    body = f"""<defs>
  <linearGradient id="sbg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t['bg1']}"/><stop offset="1" stop-color="{t['bg2']}"/>
  </linearGradient>
  <linearGradient id="sname" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{t['accent1']}"/><stop offset="1" stop-color="{t['accent2']}"/>
  </linearGradient>
</defs>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#sbg)" stroke="{t['border']}"/>
<text x="64" y="72" class="mono" font-size="14" font-weight="600" fill="{t['ok']}" letter-spacing="2">OPEN SOURCE · LINUX</text>
<text x="62" y="128" class="sans" font-size="50" font-weight="700" fill="url(#sname)">FreeStream</text>
<text x="64" y="166" class="sans" font-size="22" fill="{t['text']}">Stream Deck and Wave Link for Linux</text>
<text x="64" y="208" class="sans" font-size="16.5" fill="{t['muted']}"><tspan font-weight="700" fill="{t['text']}">FreeDeck</tspan>  runs every Stream Deck with your original profiles</text>
<text x="64" y="236" class="sans" font-size="16.5" fill="{t['muted']}"><tspan font-weight="700" fill="{t['text']}">FreeWave</tspan>  PipeWire mixer with Personal, Stream and Chat mixes</text>
<text x="64" y="266" class="mono" font-size="14" fill="{t['muted']}">Python  ·  PipeWire  ·  Debian &amp; Ubuntu</text>
<rect x="672" y="56" width="298" height="190" rx="16" fill="{t['panel']}" stroke="{t['border']}"/>{keys}
<text x="821" y="268" class="mono" font-size="11" fill="{t['muted']}" text-anchor="middle">FreeDeck</text>
<rect x="990" y="56" width="178" height="210" rx="16" fill="{t['panel']}" stroke="{t['border']}"/>{faders}"""
    style = """  .key { opacity: 0; animation: key 3.75s ease-in-out infinite; }
  @keyframes key { 0%, 70%, 100% { opacity: 0; } 8%, 20% { opacity: .9; } }
  .meter { transform-box: fill-box; transform-origin: bottom; animation: meter 1.4s ease-in-out infinite alternate; }
  .m1 { animation-duration: 1.1s; } .m2 { animation-duration: 1.7s; }
  @keyframes meter { from { transform: scaleY(.25); } to { transform: scaleY(.85); } }
  .fader { animation: fader 6s ease-in-out infinite alternate; }
  .f1 { animation-duration: 7.5s; animation-delay: -2s; } .f2 { animation-duration: 5s; animation-delay: -4s; }
  @keyframes fader { from { transform: translateY(-40px); } to { transform: translateY(50px); } }
"""
    return svg(w, h, "FreeStream: Stream Deck and Wave Link for Linux", body, style)


def main():
    OUT.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        (OUT / f"header-{theme}.svg").write_text(header(t))
        (OUT / f"freestream-{theme}.svg").write_text(spotlight(t))
        for i, (name, cat, kind, desc) in enumerate(PROJECTS):
            (OUT / f"card-{name.lower()}-{theme}.svg").write_text(card(t, name, cat, kind, desc, i * .3))
    print(f"Wrote {len(list(OUT.glob('*.svg')))} SVGs to {OUT}")


if __name__ == "__main__":
    main()
