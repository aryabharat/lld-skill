#!/usr/bin/env python3
"""Builds the README benchmark charts (light + dark SVG) from the raw judge JSON.
Run from the repo root:  python3 evals/bench/charts.py
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets")
os.makedirs(OUT, exist_ok=True)

NAMES = {"arm-lld": "lld (this repo)", "arm-qfz": "qfzhao670", "arm-malay": "malay44/lld-skills",
         "arm-sds": "tylerpayne", "arm-sdp": "software-design-philosophy", "base": "no skill"}

def ranks(folder):
    key = json.load(open(os.path.join(folder, "key.json")))
    per_arm, per_task = collections.defaultdict(list), collections.defaultdict(lambda: collections.defaultdict(list))
    for kid, mapping in key.items():
        p = os.path.join(folder, f"{kid}.json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p))
        for i, letter in enumerate(j["ranking"]):
            arm = mapping[letter]
            per_arm[arm].append(i + 1)
            per_task[kid.split("-")[0]][arm].append(i + 1)
    mean = lambda xs: sum(xs) / len(xs)
    return ({a: mean(v) for a, v in per_arm.items()},
            {t: {a: mean(v) for a, v in d.items()} for t, d in per_task.items()})

r1, _ = ranks(os.path.join(HERE, "round1"))
r2, r2_task = ranks(os.path.join(HERE, "round2"))

THEMES = {
    "light": dict(surface="#fcfcfb", text="#0b0b0b", text2="#52514e", muted="#8a8984", grid="#e4e3df",
                  r1="#86b6ef", r2="#1c5cab", line="#b7d3f6",
                  # ordinal ramp, best rank first; validated with validate_palette.js --ordinal
                  ramp=["#0d366b", "#1c5cab", "#2a78d6", "#5598e7", "#86b6ef"]),
    "dark": dict(surface="#1a1a19", text="#f0efec", text2="#c3c2b7", muted="#8f8e88", grid="#33332f",
                 r1="#256abf", r2="#86b6ef", line="#2b4a73",
                 ramp=["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab"]),
}
BUCKET = lambda v: 0 if v <= 1.5 else 1 if v <= 2.5 else 2 if v <= 3.5 else 3 if v <= 4.5 else 4
FONT = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ink_on(fill, t):
    # pick the text ink with the higher contrast against the cell fill
    def cr(a, b):
        la, lb = lum(a), lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
    return "#0b0b0b" if cr(fill, "#0b0b0b") >= cr(fill, "#ffffff") else "#ffffff"

def dumbbell(mode):
    t = THEMES[mode]
    order = sorted(r2, key=lambda a: r2[a])
    W, left, right, top, row = 760, 210, 40, 78, 40
    H = top + row * len(order) + 56
    lo, hi = 1.0, 5.0
    x = lambda v: left + (v - lo) / (hi - lo) * (W - left - right)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="{FONT}">',
         f'<rect width="{W}" height="{H}" rx="8" fill="{t["surface"]}"/>',
         f'<text x="20" y="30" font-size="16" font-weight="600" fill="{t["text"]}">Mean rank across 8 tasks, 16 blind judges (lower is better)</text>',
         f'<circle cx="26" cy="52" r="5" fill="{t["r1"]}"/><text x="36" y="56" font-size="12" fill="{t["text2"]}">Round 1</text>',
         f'<circle cx="106" cy="52" r="5" fill="{t["r2"]}"/><text x="116" y="56" font-size="12" fill="{t["text2"]}">Round 2 (after one round of fixes to lld)</text>']
    for v in range(1, 6):
        s.append(f'<line x1="{x(v):.1f}" y1="{top - 8}" x2="{x(v):.1f}" y2="{top + row * len(order) - 12}" stroke="{t["grid"]}" stroke-width="1"/>')
        s.append(f'<text x="{x(v):.1f}" y="{top + row * len(order) + 6}" font-size="11" text-anchor="middle" fill="{t["muted"]}">{v}</text>')
    s.append(f'<text x="{x(1):.1f}" y="{H - 14}" font-size="11" fill="{t["muted"]}">&#8592; better</text>')
    for i, a in enumerate(order):
        y = top + i * row + 8
        bold = ' font-weight="700"' if a == "arm-lld" else ""
        s.append(f'<text x="{left - 14}" y="{y + 4}" font-size="13" text-anchor="end" fill="{t["text"]}"{bold}>{NAMES[a]}</text>')
        a1, a2 = r1[a], r2[a]
        s.append(f'<line x1="{x(a1):.1f}" y1="{y}" x2="{x(a2):.1f}" y2="{y}" stroke="{t["line"]}" stroke-width="2" stroke-linecap="round"/>')
        s.append(f'<circle cx="{x(a1):.1f}" cy="{y}" r="6" fill="{t["r1"]}" stroke="{t["surface"]}" stroke-width="2"/>')
        s.append(f'<circle cx="{x(a2):.1f}" cy="{y}" r="6" fill="{t["r2"]}" stroke="{t["surface"]}" stroke-width="2"/>')
        lab_x = max(x(a1), x(a2)) + 12
        s.append(f'<text x="{lab_x:.1f}" y="{y + 4}" font-size="11" fill="{t["text2"]}">{a1:.2f} &#8594; {a2:.2f}</text>')
    s.append("</svg>")
    return "\n".join(s)

def heatmap(mode):
    t = THEMES[mode]
    order = sorted(r2, key=lambda a: r2[a])
    tasks = sorted(r2_task)
    labels = {"T1": "Parking lot", "T2": "Add rule", "T3": "Builder?", "T4": "State?", "T5": "Review",
              "T6": "Cache", "T7": "Schema", "T8": "Refactor"}
    left, top, cw, ch, gap = 210, 92, 64, 34, 2
    W = left + len(tasks) * cw + 30
    H = top + len(order) * ch + 60
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="{FONT}">',
         f'<rect width="{W}" height="{H}" rx="8" fill="{t["surface"]}"/>',
         f'<text x="20" y="30" font-size="16" font-weight="600" fill="{t["text"]}">Round 2: mean rank per task (1 = best of 6, {'darker' if mode == 'light' else 'lighter'} is better)</text>']
    for j, T in enumerate(tasks):
        cx = left + j * cw + cw / 2
        s.append(f'<text x="{cx:.1f}" y="{top - 26}" font-size="11" font-weight="600" text-anchor="middle" fill="{t["text2"]}">{T}</text>')
        s.append(f'<text x="{cx:.1f}" y="{top - 12}" font-size="10" text-anchor="middle" fill="{t["muted"]}">{labels[T]}</text>')
    for i, a in enumerate(order):
        y = top + i * ch
        bold = ' font-weight="700"' if a == "arm-lld" else ""
        s.append(f'<text x="{left - 14}" y="{y + ch / 2 + 4:.1f}" font-size="13" text-anchor="end" fill="{t["text"]}"{bold}>{NAMES[a]}</text>')
        for j, T in enumerate(tasks):
            v = r2_task[T][a]
            fill = t["ramp"][BUCKET(v)]
            xx = left + j * cw
            s.append(f'<rect x="{xx + gap / 2}" y="{y + gap / 2}" width="{cw - gap}" height="{ch - gap}" rx="4" fill="{fill}"/>')
            s.append(f'<text x="{xx + cw / 2:.1f}" y="{y + ch / 2 + 4:.1f}" font-size="12" text-anchor="middle" fill="{ink_on(fill, t)}">{v:.1f}</text>')
    s.append(f'<text x="20" y="{H - 16}" font-size="11" fill="{t["muted"]}">Each cell averages two judges. T5 was later re-checked after a review fix: lld ranked 1st from both judges.</text>')
    s.append("</svg>")
    return "\n".join(s)

for mode in THEMES:
    open(os.path.join(OUT, f"bench-rank-{mode}.svg"), "w").write(dumbbell(mode))
    open(os.path.join(OUT, f"bench-tasks-{mode}.svg"), "w").write(heatmap(mode))
print({NAMES[a]: (round(r1[a], 2), round(r2[a], 2)) for a in r2})
