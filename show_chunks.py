"""
Print actual chunk text for a given policy so we can fix keyFacts.
Usage: python show_chunks.py "Local Conveyance Policy"
       python show_chunks.py "Group Personal Accident Insurance Scheme"
"""
import json, sys

chunks = json.load(open("vectorstore/chunks.json"))
target = sys.argv[1] if len(sys.argv) > 1 else "Local Conveyance Policy"

pol_chunks = [c for c in chunks if c["policy_name"] == target]
print(f"{target} — {len(pol_chunks)} chunks\n")
for i, c in enumerate(pol_chunks, 1):
    print(f"{'='*60}")
    print(f"Chunk {i} | Page {c['page']} | type={c.get('chunk_type','prose')}")
    print(f"{'='*60}")
    print(c["text"])
    print()
