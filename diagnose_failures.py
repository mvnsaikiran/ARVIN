import json
from collections import Counter

data = json.load(open("full18_failures.json"))

for policy in ["Local Conveyance Policy", "Group Personal Accident Insurance Scheme"]:
    cases = [c for c in data if c["source"] == policy]
    print(f"=== {policy} ({len(cases)} failures in top-500) ===")
    cats = Counter(c["category"] for c in cases)
    for cat, n in cats.most_common():
        print(f"  {n:3d}  {cat}")
    print("\n  --- Sample failing queries ---")
    for c in cases[:10]:
        print(f"  Q:       {c['query']}")
        print(f"  Missing: {c['missing']}")
        print()
    print()
