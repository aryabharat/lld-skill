#!/usr/bin/env python3
# Builds blind judge packets: per task, per judge, answers shuffled under letters A-F.
import json, os, random, re, sys
B = os.path.dirname(os.path.abspath(__file__))
arms = sorted(d for d in os.listdir(f"{B}/answers") if os.path.isdir(f"{B}/answers/{d}"))
tasks = open(f"{B}/tasks.md").read()
task_text = {m.group(1): m.group(0) for m in re.finditer(r"## (T\d)[^\n]*\n.*?(?=\n## T\d|\Z)", tasks, re.S)}
os.makedirs(f"{B}/judge", exist_ok=True)
key = {}

def scrub(t):
    t = re.sub(r"\s*\[(?:L\d+[^\]]*|inf(?:erred)?)\]", "", t)          # lesson refs
    t = re.sub(r"\((?:inferred|inf)\)", "", t)
    t = re.sub(r"(?i)\b(the )?(lld|lld-review|lld-patterns|lld-build|lld-concurrency|software-design-philosophy|system-design-interview|low-level-design) skill\b", "the guidance", t)
    t = re.sub(r"(?i)per the (skill|guidance|reference)[^.,;]*", "", t)
    return t.strip()

for judge in (1, 2):
    for n in range(1, 9):
        T = f"T{n}"
        rng = random.Random(f"{T}-{judge}-lld-bench-r2")
        order = arms[:]
        rng.shuffle(order)
        letters = "ABCDEFGH"[: len(order)]
        key[f"{T}-j{judge}"] = dict(zip(letters, order))
        parts = [f"# Judge packet {T} (judge {judge})\n\n## The task\n\n{task_text[T]}\n"]
        for L, arm in zip(letters, order):
            p = f"{B}/answers/{arm}/{T}.md"
            body = scrub(open(p).read()) if os.path.exists(p) else "(no answer)"
            parts.append(f"\n\n=============== ANSWER {L} ===============\n\n{body}\n")
        open(f"{B}/judge/{T}-j{judge}.md", "w").write("".join(parts))
json.dump(key, open(f"{B}/judge/key.json", "w"), indent=1)
print("arms:", arms)
