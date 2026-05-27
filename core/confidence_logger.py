"""
HITL confidence logger.

Every routing event is appended to logs/routing_confidence.jsonl.
Review weekly: the "oos" and "clarification" entries are your roadmap
for missing intent anchors and gaps in keyword coverage.

Fields:
  ts      — UTC ISO timestamp
  query   — raw user query
  policy  — routed policy label (None if unrouted)
  score   — semantic confidence 0-1 (1.0 for keyword routes)
  method  — "keyword" | "semantic" | "clarification" | "oos"
"""
import json, os, datetime

_LOG_DIR  = os.path.join(os.path.dirname(__file__), '..', 'logs')
_LOG_FILE = os.path.join(_LOG_DIR, 'routing_confidence.jsonl')


def log_routing_event(
    query: str,
    routed_policy: "str | None",
    confidence: float,
    method: str,
) -> None:
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        entry = {
            "ts":     datetime.datetime.utcnow().isoformat(),
            "query":  query,
            "policy": routed_policy,
            "score":  round(confidence, 4),
            "method": method,
        }
        with open(_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass  # never crash the main flow due to logging


def load_log() -> list[dict]:
    """Return all log entries for analysis / threshold calibration."""
    if not os.path.exists(_LOG_FILE):
        return []
    entries = []
    with open(_LOG_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def compute_10th_percentile_threshold() -> float:
    """
    Compute the 10th percentile confidence score across all successful
    semantic routes — use as a dynamic minimum confidence threshold.
    Returns 0.45 as a safe default when fewer than 20 entries exist.
    """
    entries = load_log()
    sem_scores = [
        e["score"] for e in entries
        if e.get("method") == "semantic" and e.get("policy") is not None
    ]
    if len(sem_scores) < 20:
        return 0.45
    sem_scores.sort()
    idx = max(0, int(len(sem_scores) * 0.10) - 1)
    return round(sem_scores[idx], 4)
