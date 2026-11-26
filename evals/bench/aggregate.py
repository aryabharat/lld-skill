#!/usr/bin/env python3
# Unblinds judge JSON and aggregates per arm: checklist %, mean scores, mean rank, wins.
import json, os, glob, collections, re
B = os.path.dirname(os.path.abspath(__file__))
key = json.load(open(f"{B}/judge/key.json"))
names = {"arm-lld": "lld (this repo)", "arm-malay": "malay44/lld-skills", "arm-sdp": "software-design-philosophy",
         "arm-sds": "tylerpayne/system-design-skill", "arm-qfz": "qfzhao670/low-level-design-skill", "base": "no skill"}
agg = collections.defaultdict(lambda: collections.defaultdict(list))
per_task = collections.defaultdict(lambda: collections.defaultdict(list))
errors = collections.defaultdict(list)
missing = []
for kid, mapping in key.items():
    f = f"{B}/judge/{kid}.json"
    if not os.path.exists(f): missing.append(kid); continue
    txt = open(f).read()
    j = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    T = kid.split("-")[0]
    n = len(j["ranking"])
    for L, a in j["answers"].items():
        arm = mapping[L]
        cl = a["checklist"]
        agg[arm]["check"].append(sum(cl) / len(cl))
        for k in ("correctness", "design", "clarity", "proportionality"):
            agg[arm][k].append(a[k])
        r = j["ranking"].index(L) + 1
        agg[arm]["rank"].append(r)
        agg[arm]["win"].append(1 if r == 1 else 0)
        per_task[T][arm].append((sum(cl) / len(cl), r))
        for e in a.get("errors", []): errors[arm].append(f"{T}: {e}")
words = {arm: sum(len(open(p).read().split()) for p in glob.glob(f"{B}/answers/{arm}/T*.md")) for arm in names}
mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
rows = sorted(agg, key=lambda a: mean(agg[a]["rank"]))
out = ["| Setup | Mean rank (1 best) | Wins | Checklist | Correctness | Design | Decision clarity | Proportionality | Errors flagged | Words (8 tasks) |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for a in rows:
    d = agg[a]
    out.append(f"| {names[a]} | {mean(d['rank']):.2f} | {sum(d['win'])}/{len(d['win'])} | {100*mean(d['check']):.0f}% | {mean(d['correctness']):.1f} | {mean(d['design']):.1f} | {mean(d['clarity']):.1f} | {mean(d['proportionality']):.1f} | {len(errors[a])} | {words[a]} |")
out.append("\nPer task (checklist %, mean rank):\n")
out.append("| Task | " + " | ".join(names[a] for a in rows) + " |")
out.append("|---|" + "---|" * len(rows))
for T in sorted(per_task):
    cells = []
    for a in rows:
        v = per_task[T][a]
        cells.append(f"{100*mean([x[0] for x in v]):.0f}% / {mean([x[1] for x in v]):.1f}" if v else "-")
    out.append(f"| {T} | " + " | ".join(cells) + " |")
open(f"{B}/summary.md", "w").write("\n".join(out) + "\n")
json.dump(errors, open(f"{B}/errors.json", "w"), indent=1)
print("\n".join(out)); print("missing:", missing)
