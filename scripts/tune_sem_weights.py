"""
Grid search for optimal SEM_WEIGHT (BM25 vs semantic fusion) per policy.

For each policy, tries sem_weight in [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
and picks the value that maximises mean cosine similarity between the query and
the top retrieved chunk across the policy's eval questions.

No LLM calls. Run from repo root:
    python scripts/tune_sem_weights.py
"""

import os, sys, re, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chromadb.utils import embedding_functions
from eval.offline_accuracy import POLICY_MAP, generate_questions_from_chunks, load_chunks
from core.base_retriever import PolicyRetriever

REPO            = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORSTORE_DIR = os.path.join(REPO, 'vectorstore')

WEIGHTS = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]

_onnx = None
def _get_onnx():
    global _onnx
    if _onnx is None:
        _onnx = embedding_functions.ONNXMiniLM_L6_V2()
    return _onnx

def cosine(a, b):
    a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    n = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / n) if n > 0 else 0.0

def eval_weight(retriever: PolicyRetriever, questions: list[str]) -> float:
    """Return mean cosine(query, top-chunk) over all questions."""
    fn = _get_onnx()
    sims = []
    for q in questions:
        try:
            chunks = retriever.retrieve(q)
            if chunks:
                q_vec  = fn([q])[0]
                c_vec  = fn([chunks[0]['text']])[0]
                sims.append(cosine(q_vec, c_vec))
        except Exception:
            pass
    return float(np.mean(sims)) if sims else 0.0


def tune_policy(short: str) -> tuple[float, float]:
    """Return (best_weight, best_score)."""
    collection, label, subdir = POLICY_MAP[short]
    import importlib
    mod = importlib.import_module(f"policies.{subdir}.config")
    sys_prompt = mod.SYSTEM_PROMPT
    top_k      = mod.TOP_K

    chunks     = load_chunks(collection)
    in_scope, _ = generate_questions_from_chunks(short, chunks, label)
    # Use up to 30 questions for speed
    questions  = in_scope[:30]

    best_w, best_s = WEIGHTS[0], -1.0
    results = []
    for w in WEIGHTS:
        retr = PolicyRetriever(
            collection      = collection,
            system_prompt   = sys_prompt,
            policy_name     = label,
            top_k           = top_k,
            sem_weight      = w,
            vectorstore_dir = VECTORSTORE_DIR,
        )
        score = eval_weight(retr, questions)
        results.append((w, score))
        if score > best_s:
            best_s, best_w = score, w

    scores_str = "  ".join(f"{w:.1f}→{s:.3f}" for w, s in results)
    print(f"  {short:<6} best={best_w:.1f} (score={best_s:.3f})  [{scores_str}]")
    return best_w, best_s


def main():
    print(f"\n{'='*80}")
    print("  ARVIN — BM25/Semantic Weight Grid Search")
    print(f"  Weights tested: {WEIGHTS}")
    print(f"{'='*80}\n")

    best_weights: dict[str, float] = {}

    for short in POLICY_MAP:
        print(f"Tuning {short}...")
        w, s = tune_policy(short)
        best_weights[short] = w

    print(f"\n{'='*80}")
    print("  Recommended sem_weight updates:")
    print(f"{'='*80}")

    # Load current values for comparison
    for short, new_w in best_weights.items():
        _, _, subdir = POLICY_MAP[short]
        try:
            import importlib
            mod = importlib.import_module(f"policies.{subdir}.config")
            old_w = mod.SEM_WEIGHT
        except Exception:
            old_w = "?"
        change = f"  ({old_w} → {new_w})" if old_w != new_w else "  (no change)"
        print(f"  {short:<8} {new_w}{change}")

    # Save results
    out = os.path.join(REPO, 'eval', 'sem_weight_tuning.json')
    with open(out, 'w') as f:
        json.dump(best_weights, f, indent=2)
    print(f"\n  Results saved → {out}")
    return best_weights


if __name__ == "__main__":
    main()
