"""Render the profile card as dark_mode.svg and light_mode.svg.

The numbers come from stats.json in this repo, the one shared source that
widebluesound.com and nathanrightnour.com also read. A GitHub Action runs this
whenever stats.json changes. Standard library only. Fails loudly if a number
is missing.
"""
import base64
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
LOGIN = "NathanR-85"

# Layout (px). JetBrains Mono advance width is 0.6 em.
PAD = 30
ART_FONT, ART_LINE = 9, 11.25
INFO_FONT, INFO_LINE = 14, 22.5
GAP = 44
KEY_COL = 15  # characters before the value starts

THEMES = {
    "dark": {
        "bg": "#0d1117", "card": "#111723", "border": "#222b3b",
        "art": ("#93c4ff", "#a98bff", "#e391f8"),
        "rule": ("#6daeff", "#c957f3"),
        "title": "#e6ebf5", "section": "#a98bff", "key": "#7cb4ff",
        "value": "#d5dcea", "dots": "#3a4458", "live": "#7ee2b8",
    },
    "light": {
        "bg": "#ffffff", "card": "#f7f8fc", "border": "#e1e5ef",
        "art": ("#2d6ad8", "#6a3ad8", "#a52fc4"),
        "rule": ("#2d6ad8", "#a52fc4"),
        "title": "#141a26", "section": "#6a3ad8", "key": "#2459c2",
        "value": "#2a3140", "dots": "#c3c9d6", "live": "#127a52",
    },
}


KEYS = ("plays", "productions", "founded", "studios", "countries")


def load_stats() -> dict:
    n = json.loads((ROOT / "stats.json").read_text())
    missing = [k for k in KEYS if not str(n.get(k, "")).strip()]
    if missing:
        raise RuntimeError(f"stats.json is missing: {', '.join(missing)}")
    return n


def info_lines(n: dict):
    """Rows: ("title", text) | ("section", text) | ("kv", key, value, live) | ("gap",)."""
    return [
        ("title", "nathan@rightnour"),
        ("kv", "OS", "macOS", False),
        ("kv", "Role", "Music Producer, CEO of Wide Blue Sound", False),
        ("gap",),
        ("section", "Music"),
        ("kv", "Plays", f"{n['plays']} on TV and streaming", False),
        ("kv", "Heard on", "Apple, the Olympics, Monday Night Football", False),
        ("kv", "Productions", n["productions"], False),
        ("gap",),
        ("section", "Software"),
        ("kv", "Since", n["founded"], False),
        ("kv", "Studios", f"{n['studios']} in {n['countries']} countries", False),
        ("gap",),
        ("section", "Contact"),
        ("kv", "Web", "nathanrightnour.com", False),
    ]


def font_face(weight: str, file: str) -> str:
    data = base64.b64encode((ROOT / "assets" / file).read_bytes()).decode()
    return (f"@font-face{{font-family:'JBM';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")


def render(theme: dict, art: list[str], n: dict) -> str:
    cw_art = ART_FONT * 0.6
    cw = INFO_FONT * 0.6
    art_w = max(len(r) for r in art) * cw_art
    art_h = len(art) * ART_LINE
    info_x = PAD + art_w + GAP
    rows = info_lines(n)
    info_w = max(KEY_COL + len(r[2]) for r in rows if r[0] == "kv") * cw
    info_w = max(info_w, 40 * cw)
    width = round(info_x + info_w + PAD)
    info_h = len(rows) * INFO_LINE
    height = round(max(art_h, info_h) + 2 * PAD)
    info_top = PAD + (height - 2 * PAD - info_h) / 2 + INFO_FONT
    art_top = PAD + (height - 2 * PAD - art_h) / 2 + ART_FONT

    t = theme
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Nathan Rightnour</title>",
        "<defs>",
        f'<linearGradient id="art" x1="0" y1="0" x2="0.35" y2="1">'
        f'<stop offset="0" stop-color="{t["art"][0]}"/><stop offset="0.55" stop-color="{t["art"][1]}"/>'
        f'<stop offset="1" stop-color="{t["art"][2]}"/></linearGradient>',
        f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["rule"][0]}" stop-opacity="0.9"/>'
        f'<stop offset="1" stop-color="{t["rule"][1]}" stop-opacity="0"/></linearGradient>',
        "<style>",
        font_face("400", "jbm-Regular.woff2"),
        font_face("700", "jbm-Bold.woff2"),
        f"text{{font-family:'JBM',monospace;white-space:pre;}}"
        f".a{{font-size:{ART_FONT}px;}}"
        f".i{{font-size:{INFO_FONT}px;fill:{t['value']};}}"
        f".t{{fill:{t['title']};font-weight:700;}}"
        f".s{{fill:{t['section']};font-weight:700;}}"
        f".k{{fill:{t['key']};}}.d{{fill:{t['dots']};}}.l{{fill:{t['live']};}}",
        "</style>",
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{t["card"]}" stroke="{t["border"]}"/>',
        f'<text class="a" fill="url(#art)" xml:space="preserve">',
    ]
    for i, row in enumerate(art):
        out.append(f'<tspan x="{PAD}" y="{art_top + i * ART_LINE:.2f}">{escape(row)}</tspan>')
    out.append("</text>")

    for i, row in enumerate(rows):
        y = info_top + i * INFO_LINE
        kind = row[0]
        if kind == "gap":
            continue
        if kind in ("title", "section"):
            cls = "t" if kind == "title" else "s"
            text = row[1]
            out.append(f'<text class="i {cls}" x="{info_x:.2f}" y="{y:.2f}">{escape(text)}</text>')
            line_x = info_x + (len(text) + 1) * cw
            out.append(f'<rect x="{line_x:.2f}" y="{y - INFO_FONT * 0.32:.2f}" width="{info_x + info_w - line_x:.2f}" height="1" fill="url(#rule)"/>')
            continue
        _, key, value, live = row
        dots = " " + "." * (KEY_COL - len(key) - 2) + " "
        vcls = ' class="l"' if live else ""
        out.append(
            f'<text class="i" x="{info_x:.2f}" y="{y:.2f}" xml:space="preserve">'
            f'<tspan class="k">{escape(key)}</tspan><tspan class="d">{dots}</tspan>'
            f'<tspan{vcls}>{escape(value)}</tspan></text>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    art = (ROOT / "assets" / "portrait.txt").read_text().split("\n")
    n = load_stats()
    for name, theme in THEMES.items():
        (ROOT / f"{name}_mode.svg").write_text(render(theme, art, n))
    print(n)


if __name__ == "__main__":
    main()
