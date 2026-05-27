"""
Re-ingest all 18 policies in sequence.
Run from repo root:  python scripts/ingest_all.py
"""

import os, sys, subprocess, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

POLICIES = [
    "whistleblower",
    "posh",
    "grievance",
    "gender",
    "domestic_travel",
    "joining",
    "fnf",
    "expense",
    "local_conveyance",
    "group_health",
    "group_personal_accident",
    "group_term_life",
    "vdc",
    "pankh",
    "talent_mobility",
    "medibuddy",
    "travel_settlement",
    "eap",
]

def main():
    total = len(POLICIES)
    failed = []
    for i, policy in enumerate(POLICIES, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total}] Ingesting: {policy}")
        print('='*60)
        t0 = time.time()
        result = subprocess.run(
            [sys.executable, "-m", f"policies.{policy}.ingest"],
            cwd=REPO,
            capture_output=False,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"  ERROR: {policy} failed (exit {result.returncode})")
            failed.append(policy)
        else:
            print(f"  OK — {elapsed:.1f}s")

    print(f"\n{'='*60}")
    print(f"Ingest complete: {total - len(failed)}/{total} succeeded")
    if failed:
        print(f"FAILED: {failed}")

if __name__ == "__main__":
    main()
