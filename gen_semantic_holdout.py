"""
Method 3 — Semantic similarity holdout split.

Clusters all existing test queries by semantic embedding similarity using KMeans.
Holds out the 20% most semantically distant clusters — these are truly different
from the majority and act as a harder, unseen test set.

Output:
  semantic_holdout.json   — the held-out queries (~20%)
  semantic_train.json     — the remaining queries (~80%)
  semantic_split_info.json — cluster metadata / which clusters are held out
"""

import json, os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from chromadb.utils import embedding_functions

SUITES = [
    ("enterprise_test_suite.json",   "old"),
    ("new_policies_test_suite.json", "old"),
    ("batch2_test_suite.json",       "old"),
    ("medibuddy_test_suite.json",    "new"),
]

OUTPUT_HOLDOUT     = "semantic_holdout.json"
OUTPUT_TRAIN       = "semantic_train.json"
OUTPUT_SPLIT_INFO  = "semantic_split_info.json"

N_CLUSTERS         = 50   # K in KMeans
HOLDOUT_FRAC       = 0.20 # fraction of clusters to hold out
MODEL_NAME         = "ONNXMiniLM-L6-V2 (local)"


def load_all_cases() -> list[dict]:
    cases = []
    for path, fmt in SUITES:
        try:
            data = json.load(open(path))
        except FileNotFoundError:
            print(f"  SKIP (not found): {path}")
            continue
        for c in data:
            c["_fmt"] = fmt
            # normalise key fields
            if fmt == "old":
                c["_query"]    = c["query"]
                c["_policy"]   = c.get("source", "?")
                c["_key_facts"] = c.get("keyFacts", [])
            else:
                c["_query"]    = c["query"]
                c["_policy"]   = c.get("policy", "?")
                c["_key_facts"] = c.get("key_facts", [])
        cases.extend(data)
        print(f"  Loaded {len(data)} cases from {path}")
    return cases


def embed_queries(queries: list[str]) -> np.ndarray:
    print(f"\nEmbedding {len(queries)} queries with {MODEL_NAME} …")
    ef = embedding_functions.ONNXMiniLM_L6_V2()
    BATCH = 256
    all_embs = []
    for start in range(0, len(queries), BATCH):
        batch = queries[start:start + BATCH]
        all_embs.extend(ef(batch))
        done = min(start + BATCH, len(queries))
        print(f"  {done}/{len(queries)} embedded", end="\r", flush=True)
    print()
    embs = np.array(all_embs, dtype=np.float32)
    return normalize(embs, norm="l2")


def cluster_and_split(embs: np.ndarray, cases: list[dict]):
    n_clusters = min(N_CLUSTERS, len(cases) // 5)
    print(f"\nKMeans clustering into {n_clusters} clusters …")
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(embs)

    # Compute centroid of ALL embeddings → grand mean
    grand_centroid = embs.mean(axis=0)

    # For each cluster, compute distance of its centroid from the grand mean
    cluster_centroids = km.cluster_centers_
    dists = np.linalg.norm(cluster_centroids - grand_centroid, axis=1)

    # Sort clusters by distance descending, hold out top HOLDOUT_FRAC
    n_holdout = max(1, round(n_clusters * HOLDOUT_FRAC))
    sorted_by_dist = np.argsort(dists)[::-1]
    holdout_clusters = set(sorted_by_dist[:n_holdout].tolist())

    print(f"Holding out {n_holdout} clusters (most distant from grand centroid)")
    print("Held-out cluster IDs:", sorted(holdout_clusters))

    holdout_cases, train_cases = [], []
    for i, case in enumerate(cases):
        if labels[i] in holdout_clusters:
            holdout_cases.append(case)
        else:
            train_cases.append(case)

    # Build split metadata
    split_info = {
        "n_total":         len(cases),
        "n_clusters":      n_clusters,
        "n_holdout_clusters": n_holdout,
        "holdout_cluster_ids": sorted(holdout_clusters),
        "n_holdout":       len(holdout_cases),
        "n_train":         len(train_cases),
        "cluster_distances": [
            {"cluster_id": int(cid), "dist_from_grand": float(dists[cid])}
            for cid in sorted_by_dist
        ],
    }

    return holdout_cases, train_cases, labels, split_info


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Loading test cases …")
    cases   = load_all_cases()
    queries = [c["_query"] for c in cases]

    embs = embed_queries(queries)

    holdout_cases, train_cases, labels, split_info = cluster_and_split(embs, cases)

    # Save outputs — strip internal _* fields before writing
    def clean(c):
        return {k: v for k, v in c.items() if not k.startswith("_")}

    with open(OUTPUT_HOLDOUT, "w") as f:
        json.dump([clean(c) for c in holdout_cases], f, indent=2)
    with open(OUTPUT_TRAIN, "w") as f:
        json.dump([clean(c) for c in train_cases], f, indent=2)
    with open(OUTPUT_SPLIT_INFO, "w") as f:
        json.dump(split_info, f, indent=2)

    print(f"\nSplit complete:")
    print(f"  Train   : {len(train_cases):5d} cases → {OUTPUT_TRAIN}")
    print(f"  Holdout : {len(holdout_cases):5d} cases → {OUTPUT_HOLDOUT}")
    print(f"  Info    : {OUTPUT_SPLIT_INFO}")

    # Policy breakdown of holdout set
    from collections import Counter
    pol_counts = Counter(c["_policy"] for c in holdout_cases)
    print(f"\nHoldout set policy breakdown:")
    for pol, cnt in sorted(pol_counts.items(), key=lambda x: -x[1]):
        print(f"  {pol:<55} {cnt}")


if __name__ == "__main__":
    main()
