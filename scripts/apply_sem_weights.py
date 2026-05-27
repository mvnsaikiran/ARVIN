"""
Apply optimal SEM_WEIGHT values from grid search to all policy configs.
Run from repo root:  python scripts/apply_sem_weights.py
"""
import os, sys, re, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# From grid search results
BEST_WEIGHTS = {
    "wb":    3.0,
    "posh":  2.5,
    "grv":   3.0,
    "gen":   3.0,
    "dt":    3.0,
    "jn":    3.0,
    "fnf":   1.2,
    "exp":   2.0,
    "lc":    1.5,
    "ghi":   3.0,
    "gpa":   1.0,
    "gtl":   1.0,
    "vdc":   1.0,
    "pankh": 0.5,
    "tm":    3.0,
    "mb":    1.0,
    "ts":    1.0,
    "eap":   2.5,
}

from eval.offline_accuracy import POLICY_MAP

def main():
    for short, new_w in BEST_WEIGHTS.items():
        _, _, subdir = POLICY_MAP[short]
        cfg_path = os.path.join(REPO, 'policies', subdir, 'config.py')
        with open(cfg_path, encoding='utf-8') as f:
            src = f.read()

        # Replace SEM_WEIGHT = X.X  (handles int or float)
        new_src = re.sub(
            r'(SEM_WEIGHT\s*=\s*)[\d\.]+',
            lambda m: m.group(1) + str(new_w),
            src,
        )
        if new_src == src:
            print(f"  {short:<8} SEM_WEIGHT not found in {cfg_path}")
            continue

        with open(cfg_path, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print(f"  {short:<8} SEM_WEIGHT updated → {new_w}  ({cfg_path.split('policies/')[1]})")

if __name__ == "__main__":
    main()
