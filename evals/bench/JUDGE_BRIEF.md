# Judge brief

Read `<BENCH_DIR>/rubric.md`, then your packet. Grade every answer in the packet strictly by the rubric for that task. You must not open any other file in the bench folder (no answers/, no key.json, no other packets).

Be a demanding senior reviewer: verify code and concurrency claims yourself, and do not reward length, headings or confident tone. A short answer that is fully right beats a long one with an error.

Write your result as JSON to the path given in your task, exactly this shape:

```json
{
  "task": "T1",
  "answers": {
    "A": {"checklist": [1,0,1,...], "correctness": 7, "design": 8, "clarity": 6, "proportionality": 5, "errors": ["..."], "note": "one sentence"},
    "B": {...}
  },
  "ranking": ["C","A","B","F","E","D"]
}
```

The checklist array follows the order of that task's checklist items in the rubric. Reply with just the output path.
