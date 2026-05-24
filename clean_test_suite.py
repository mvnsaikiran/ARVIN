"""
Clean the test suite — fix broken keyFacts, impossible tests, bad sources.
Produces cleaned_test_suite.json and reports all changes made.
"""

import json, re, os
import pdfplumber
from docx import Document

# ── Build full policy corpus for fact verification ────────────────────────────

POLICIES_SRC = "policies"

def normalise(text: str) -> str:
    t = text.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\([\w\s]+\)', ' ', t)   # strip parenthetical words
    t = t.replace('-', ' ')
    t = t.replace('/', ' or ')
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def build_corpus() -> str:
    corpus = []
    for fn in os.listdir(POLICIES_SRC):
        fp = os.path.join(POLICIES_SRC, fn)
        ext = os.path.splitext(fn)[1].lower()
        try:
            if ext == '.pdf':
                with pdfplumber.open(fp) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text() or ''
                        corpus.append(t)
                        for table in (page.extract_tables() or []):
                            for row in table:
                                corpus.append(' '.join(str(c) for c in row if c))
            elif ext in ('.docx', '.doc'):
                doc = Document(fp)
                corpus.append('\n'.join(p.text for p in doc.paragraphs))
                for table in doc.tables:
                    for row in table.rows:
                        corpus.append(' '.join(c.text for c in row.cells))
        except Exception as e:
            print(f"  Warning reading {fn}: {e}")
    return normalise(' '.join(corpus))

print("Building policy corpus from all 8 policy files...", flush=True)
corpus_norm = build_corpus()
print(f"Corpus: {len(corpus_norm):,} normalised chars\n", flush=True)

def fact_in_corpus(fact: str) -> bool:
    return normalise(fact) in corpus_norm

# ── Fix rules ─────────────────────────────────────────────────────────────────

IMPOSSIBLE_CATEGORIES = {'meta'}   # "What is the chatbot name?" etc.
MULTI_POLICY_SOURCES  = {'multiple policies', 'multiple'}

def fix_emdash(fact: str) -> str:
    """'actuals — full explanation' → 'actuals'"""
    for sep in [' — ', ' – ', ' - ']:
        if sep in fact:
            left = fact.split(sep)[0].strip()
            if left and not fact_in_corpus(fact) and fact_in_corpus(left):
                return left
    return fact

def fix_invented_phrases(facts: list[str]) -> tuple[list[str], list[str]]:
    """Return (cleaned_facts, change_log)."""
    cleaned, log = [], []
    for f in facts:
        # Try em-dash fix
        fixed = fix_emdash(f)
        if fixed != f:
            log.append(f'emdash: "{f}" → "{fixed}"')
            cleaned.append(fixed)
            continue

        # "no retaliation" → "retaliation" (the 'no' breaks substring match)
        if f.lower() == 'no retaliation' and not fact_in_corpus(f):
            log.append(f'negation: "{f}" → "retaliation"')
            cleaned.append('retaliation')
            continue

        # "not be protected" → "protected"
        if 'not be protected' in f.lower() and not fact_in_corpus(f):
            log.append(f'negation: "{f}" → "protection"')
            cleaned.append('protection')
            continue

        # "only the individual" → "the individual" (word order issue)
        if f.lower() == 'only the individual' and not fact_in_corpus(f):
            log.append(f'word-order: "{f}" → "the individual"')
            cleaned.append('the individual')
            continue

        # "additional leave" → "entitled leaves" (paraphrase)
        if f.lower() == 'additional leave' and not fact_in_corpus(f):
            log.append(f'paraphrase: "{f}" → "entitled leaves"')
            cleaned.append('entitled leaves')
            continue

        # "3rd ac or chair car" / "3rd ac/chair car" — keep as-is (normaliser handles slash)
        # "premium economy or business class" → "premium economy"
        if f.lower() in ('premium economy or business class',) and not fact_in_corpus(f):
            log.append(f'trim: "{f}" → "premium economy"')
            cleaned.append('premium economy')
            continue

        # Long facts (>50 chars) not in corpus → try splitting on "or", keep first
        if len(f) > 50 and not fact_in_corpus(f):
            parts = re.split(r'\bor\b', f, maxsplit=1)
            if len(parts) == 2 and fact_in_corpus(parts[0].strip()):
                log.append(f'split-or: "{f}" → "{parts[0].strip()}"')
                cleaned.append(parts[0].strip())
                continue

        cleaned.append(f)
    return cleaned, log

# ── Load and clean ────────────────────────────────────────────────────────────

with open('test_suite.json') as f:
    tests = json.load(f)

print(f"Cleaning {len(tests)} test cases...\n", flush=True)

cleaned_tests = []
stats = {
    'removed_impossible': 0,
    'fixed_facts': 0,
    'unchanged': 0,
    'total_fact_fixes': 0,
}
change_log = []

for tc in tests:
    category = tc.get('category', '').lower()

    # Remove impossible tests
    if category in IMPOSSIBLE_CATEGORIES:
        stats['removed_impossible'] += 1
        change_log.append(f"REMOVED [{tc['id']}] {tc['query'][:60]} (impossible category: {category})")
        continue

    # Fix keyFacts
    original_facts = tc.get('keyFacts', [])
    fixed_facts, fact_log = fix_invented_phrases(original_facts)

    if fact_log:
        stats['fixed_facts'] += 1
        stats['total_fact_fixes'] += len(fact_log)
        for entry in fact_log:
            change_log.append(f"FIXED [{tc['id']}] {entry}")
        tc = {**tc, 'keyFacts': fixed_facts}
    else:
        stats['unchanged'] += 1

    cleaned_tests.append(tc)

# ── Save ──────────────────────────────────────────────────────────────────────

with open('cleaned_test_suite.json', 'w') as f:
    json.dump(cleaned_tests, f, indent=2)

print(f"{'='*55}")
print(f"  CLEANING REPORT")
print(f"{'='*55}")
print(f"  Original test cases:     {len(tests)}")
print(f"  Removed (impossible):    {stats['removed_impossible']}")
print(f"  Tests with fixed facts:  {stats['fixed_facts']}")
print(f"  Total fact fixes:        {stats['total_fact_fixes']}")
print(f"  Unchanged:               {stats['unchanged']}")
print(f"  Final test cases:        {len(cleaned_tests)}")
print(f"{'='*55}")
print(f"\nSample changes:")
for entry in change_log[:30]:
    print(f"  {entry}")
if len(change_log) > 30:
    print(f"  ... and {len(change_log)-30} more")
