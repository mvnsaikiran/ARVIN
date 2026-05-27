"""
Run all 18 policy ingestions in sequence.
Usage:  python ingest_all.py
"""

import sys
import time
import importlib

POLICIES = [
    ("policies.whistleblower.ingest",        "Whistleblower Policy"),
    ("policies.posh.ingest",                  "POSH Policy"),
    ("policies.grievance.ingest",             "Grievance Mechanism Policy"),
    ("policies.gender.ingest",                "Gender Policy"),
    ("policies.domestic_travel.ingest",       "Domestic Travel Policy"),
    ("policies.joining.ingest",               "Joining Policy"),
    ("policies.fnf.ingest",                   "Full & Final Settlement Policy"),
    ("policies.expense.ingest",               "Employee Expense Reimbursement Policy"),
    ("policies.local_conveyance.ingest",      "Local Conveyance Policy"),
    ("policies.group_health.ingest",          "Group Health Insurance Policy"),
    ("policies.group_personal_accident.ingest", "Group Personal Accident Insurance Policy"),
    ("policies.group_term_life.ingest",       "Group Term Life Insurance Policy"),
    ("policies.vdc.ingest",                   "Voluntary Death Contribution Policy"),
    ("policies.pankh.ingest",                 "Pankh Employee Referral Policy"),
    ("policies.talent_mobility.ingest",       "Talent Mobility Policy"),
    ("policies.medibuddy.ingest",             "MediBuddy User Guide"),
    ("policies.travel_settlement.ingest",     "Travel Settlement Guide"),
    ("policies.eap.ingest",                   "1to1 Employee Assistance Program"),
]


def main():
    total   = len(POLICIES)
    passed  = []
    failed  = []

    print("=" * 60)
    print(f"  ARVIN — Ingesting all {total} policies")
    print("=" * 60)

    for i, (module_path, label) in enumerate(POLICIES, 1):
        print(f"\n[{i:02d}/{total}] {label}")
        print("-" * 40)
        t0 = time.time()
        try:
            mod = importlib.import_module(module_path)
            mod.run()
            elapsed = time.time() - t0
            print(f"  ✓ Done in {elapsed:.1f}s")
            passed.append(label)
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ✗ FAILED in {elapsed:.1f}s: {e}")
            failed.append((label, str(e)))

    print("\n" + "=" * 60)
    print(f"  SUMMARY: {len(passed)}/{total} succeeded")
    print("=" * 60)
    if failed:
        print("\nFailed policies:")
        for label, err in failed:
            print(f"  ✗ {label}: {err}")
        sys.exit(1)
    else:
        print("\nAll policies ingested successfully. ARVIN is ready.")


if __name__ == "__main__":
    main()
