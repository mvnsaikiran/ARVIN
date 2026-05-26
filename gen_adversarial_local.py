"""
Method 2 (local, no external API) — Adversarial paraphrase generation.

Extracts key facts from policy chunks and generates plain-English questions
that deliberately avoid policy jargon. Tests vocabulary gap failures.

Strategy:
  1. Parse chunks to extract (value, context) pairs using regex
  2. Map policy jargon → everyday language via substitution table
  3. Generate questions from multiple templates, using everyday language
  4. Verify each question's key_fact is actually in the source chunk

Output: adversarial_holdout.json
"""

import json, re, random
from collections import defaultdict

CHUNKS_FILE = "vectorstore/chunks.json"
OUTPUT_FILE = "adversarial_holdout.json"
random.seed(42)

# ── Jargon → plain English substitution table ──────────────────────────────────
# Policy word (regex pattern) → everyday replacement
JARGON_MAP = [
    # Financial terms
    (r"\breimburs\w*\b",           ["money back", "get paid back", "claim back", "refund"]),
    (r"\ballowance\b",             ["money", "monthly pay", "fixed amount", "payment"]),
    (r"\bentitlement\b",           ["what I get", "amount allowed", "my share"]),
    (r"\bCTC\b",                   ["salary package", "total pay", "annual salary"]),
    (r"\bper diem\b",              ["daily money", "daily pay"]),
    (r"\bactuals?\b",              ["real cost", "actual bill", "whatever I spend"]),
    (r"\bex-gratia\b",             ["bonus payment", "extra money"]),
    (r"\bgross(?:ed)? up\b",       ["company pays tax", "tax covered", "before-tax amount"]),
    (r"\bfixed pay\b",             ["base salary", "monthly salary"]),
    (r"\bvariable pay\b",          ["bonus", "performance pay"]),

    # Grade/level terms
    (r"\bgrade\b",                 ["level", "band", "job level", "rank"]),
    (r"\bcadre\b",                 ["level", "category", "type of employee"]),
    (r"\bmanagement\b",            ["senior staff", "managers", "leadership"]),
    (r"\bstaff\b",                 ["workers", "employees", "team members"]),

    # Leave/absence
    (r"\bleave\b",                 ["time off", "day off", "break from work"]),
    (r"\babsence\b",               ["not at work", "away from office"]),

    # Policy procedure terms
    (r"\bintimate\b",              ["inform", "notify", "tell", "let them know"]),
    (r"\bintimation\b",            ["notification", "informing", "telling"]),
    (r"\bapplicab(?:le|ility)\b",  ["valid for", "applies to", "who gets this", "covered"]),
    (r"\bengagement\b",            ["working", "employment", "job"]),
    (r"\bsettlement\b",            ["payment", "getting money back", "clearing dues"]),
    (r"\bdischarge\b",             ["leaving hospital", "checkout", "released"]),
    (r"\btermination\b",           ["leaving the job", "fired", "employment ended"]),
    (r"\bseparation\b",            ["leaving company", "quitting", "exit"]),
    (r"\bfull and final\b",        ["last payment", "final money", "exit payment"]),

    # Travel terms
    (r"\blodging\b",               ["hotel", "stay", "place to sleep"]),
    (r"\baccommodation\b",         ["hotel", "place to stay", "where to stay"]),
    (r"\bconveyance\b",            ["travel", "getting around", "transport"]),
    (r"\btransportation\b",        ["travel cost", "getting there", "moving"]),
    (r"\brelocation\b",            ["shifting cities", "moving to new place", "job transfer"]),
    (r"\bjoining\b",               ["first day", "starting the job", "when I join"]),

    # Insurance/health
    (r"\bpremium\b",               ["insurance fee", "monthly cost", "insurance payment"]),
    (r"\bcashless\b",              ["no upfront payment", "hospital bills paid directly"]),
    (r"\breimbursement claim\b",   ["claiming money back", "getting refund"]),
    (r"\bTPA\b",                   ["insurance handler", "middle company", "claim processor"]),
    (r"\bhospitalisation\b",       ["hospital stay", "being admitted", "going to hospital"]),

    # HR process terms
    (r"\bgrievance\b",             ["complaint", "issue", "problem", "concern"]),
    (r"\bescalat\w*\b",            ["taking it higher", "reporting up", "raising further"]),
    (r"\bcomplaints? committee\b", ["complaints team", "HR committee", "the panel"]),
    (r"\bIC\b",                    ["complaints team", "the panel"]),
    (r"\brespondent\b",            ["the person accused", "the other person"]),
    (r"\bcomplainant\b",           ["the person complaining", "who filed complaint"]),
    (r"\binquiry\b",               ["investigation", "looking into it", "checking facts"]),
    (r"\bwhistleblower\b",         ["person who reports", "informer", "reporter"]),
    (r"\bposh\b",                  ["workplace harassment", "sexual harassment"]),
    (r"\bsexual harassment\b",     ["inappropriate behavior", "harassment at work"]),

    # Death / life events
    (r"\bdeceased\b",              ["passed away", "dead colleague", "who died"]),
    (r"\bnominee\b",               ["family member", "named person", "beneficiary"]),
    (r"\bdependan(?:t|ts?)\b",     ["family", "kids and spouse", "people depending on me"]),
    (r"\bbeneficiar\w*\b",         ["who gets the money", "family member who receives"]),
]


def apply_jargon_map(text: str) -> str:
    """Replace policy jargon with everyday language (pick random alternative)."""
    for pattern, replacements in JARGON_MAP:
        def replacer(m):
            return random.choice(replacements)
        text = re.sub(pattern, replacer, text, flags=re.IGNORECASE)
    return text


# ── Fact extractors ────────────────────────────────────────────────────────────
def extract_amounts(text: str) -> list[dict]:
    """Extract monetary amounts with surrounding context."""
    facts = []
    # Rs. X / ₹X / X per km / X per day patterns
    for m in re.finditer(
        r'(?:Rs\.?\s*|₹\s*)(\d[\d,]*(?:\.\d+)?)\s*(?:/-)?(?:\s*(?:per\s+\w+|lakh|lakhs?))?',
        text, re.IGNORECASE
    ):
        raw = m.group().strip().rstrip('/-').strip()
        facts.append({"type": "amount", "value": raw, "raw_num": m.group(1).replace(",","")})
    return facts


def extract_grades(text: str) -> list[dict]:
    """Extract grade/level references."""
    facts = []
    for m in re.finditer(r'\b(E[1-9]|M[1-9]H?\d*|OT|Staff|BMH\d+|Grade\s+[A-Z]\d*)\b', text):
        facts.append({"type": "grade", "value": m.group().strip()})
    return facts


def extract_days_hours(text: str) -> list[dict]:
    """Extract time-period facts."""
    facts = []
    for m in re.finditer(r'(\d+)\s*(days?|hours?|months?|years?|weeks?)', text, re.IGNORECASE):
        facts.append({"type": "time", "value": m.group().strip()})
    return facts


def extract_percentages(text: str) -> list[dict]:
    facts = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*%', text):
        facts.append({"type": "pct", "value": m.group().strip()})
    return facts


def extract_contacts(text: str) -> list[dict]:
    facts = []
    for m in re.finditer(r'(\d[\d\s\-]{8,}\d)', text):
        facts.append({"type": "phone", "value": m.group().strip()})
    for m in re.finditer(r'[\w.+-]+@[\w.-]+\.\w+', text):
        facts.append({"type": "email", "value": m.group().strip()})
    return facts


def extract_facts(chunk: dict) -> list[dict]:
    text = chunk.get("text", "")
    facts = []
    facts.extend(extract_amounts(text))
    facts.extend(extract_grades(text))
    facts.extend(extract_days_hours(text))
    facts.extend(extract_percentages(text))
    facts.extend(extract_contacts(text))
    return facts


# ── Question templates ─────────────────────────────────────────────────────────
AMOUNT_TEMPLATES = [
    "How much money can I get back for this?",
    "What is the maximum I can spend?",
    "How much will the company pay me?",
    "What's the most money I can claim?",
    "Is there a ceiling on how much I get?",
    "How much can I get for {context}?",
    "What is the money limit for {context}?",
]

GRADE_TEMPLATES = [
    "I am a {grade} level employee — what do I get?",
    "What is the benefit for someone at {grade}?",
    "How does the amount differ if I'm at {grade}?",
    "What is the {grade} entitlement?",
    "For a {grade} grade, how much money am I allowed?",
]

TIME_TEMPLATES = [
    "How many {unit} do I have to submit the claim?",
    "What is the time limit to apply?",
    "How long do I have to do this?",
    "Is there a deadline for submitting documents?",
    "What happens if I miss the {value} window?",
]

CONTACT_TEMPLATES = [
    "Who should I call for this?",
    "What is the helpline number?",
    "Where do I send the documents?",
    "How do I contact them?",
    "What email should I use to report this?",
]

GENERIC_TEMPLATES = [
    "What are the rules around this?",
    "Can you explain this policy in simple words?",
    "Am I covered for this situation?",
    "What happens if I don't follow this?",
    "Who is eligible for this benefit?",
    "How does this work for a new joiner?",
    "What is the process to apply for this?",
    "Is there any paperwork I need to fill?",
    "Does my family also get this benefit?",
    "What if my case is different from what's written?",
]


def make_questions(chunk: dict) -> list[dict]:
    """Generate adversarial questions for a chunk."""
    pol  = chunk.get("policy_name", "")
    text = chunk.get("text", "")
    if len(text) < 80:
        return []

    facts = extract_facts(chunk)
    qs    = []

    # Paraphrase a slice of the chunk text as context
    snippet = text[:300]
    context_plain = apply_jargon_map(snippet[:80].rstrip())

    # Amount-based questions
    amounts = [f for f in facts if f["type"] == "amount"]
    if amounts:
        amt = random.choice(amounts)
        tmpl = random.choice(AMOUNT_TEMPLATES)
        q = tmpl.format(context=context_plain)
        qs.append({"query": q, "key_facts": [amt["raw_num"]], "policy": pol, "chunk_id": chunk.get("id","")})

    # Grade-based questions
    grades = [f for f in facts if f["type"] == "grade"]
    if grades:
        grade = random.choice(grades)
        tmpl  = random.choice(GRADE_TEMPLATES)
        q = tmpl.format(grade=grade["value"])
        # key_fact = something from the chunk that mentions this grade
        grade_context = re.search(
            rf'{re.escape(grade["value"])}.{{0,80}}', text
        )
        kf = grade_context.group() if grade_context else grade["value"]
        qs.append({"query": q, "key_facts": [kf[:60]], "policy": pol, "chunk_id": chunk.get("id","")})

    # Time-based questions
    times = [f for f in facts if f["type"] == "time"]
    if times:
        t    = random.choice(times)
        unit = re.search(r'[a-zA-Z]+', t["value"])
        unit_str = unit.group() if unit else "days"
        tmpl = random.choice(TIME_TEMPLATES)
        q = tmpl.format(unit=unit_str, value=t["value"])
        qs.append({"query": q, "key_facts": [t["value"]], "policy": pol, "chunk_id": chunk.get("id","")})

    # Contact questions
    contacts = [f for f in facts if f["type"] in ("phone", "email")]
    if contacts:
        c = random.choice(contacts)
        tmpl = random.choice(CONTACT_TEMPLATES)
        q = tmpl
        qs.append({"query": q, "key_facts": [c["value"]], "policy": pol, "chunk_id": chunk.get("id","")})

    # Always add 1-2 generic paraphrased questions
    n_generic = random.randint(1, 2)
    for tmpl in random.sample(GENERIC_TEMPLATES, min(n_generic, len(GENERIC_TEMPLATES))):
        plain_q = apply_jargon_map(tmpl)
        # key_fact = first sentence of chunk that contains a number or name
        kf_match = re.search(r'[^.!?]*\d+[^.!?]*[.!?]', text)
        kf = kf_match.group().strip()[:60] if kf_match else text[:60]
        qs.append({"query": plain_q, "key_facts": [kf], "policy": pol, "chunk_id": chunk.get("id","")})

    return qs


def main():
    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks")

    # Sample chunks per policy
    by_policy: dict[str, list] = defaultdict(list)
    for c in chunks:
        if len(c.get("text","")) > 150:
            by_policy[c["policy_name"]].append(c)

    SAMPLE = 5
    sampled = []
    for pol, pol_chunks in sorted(by_policy.items()):
        chosen = random.sample(pol_chunks, min(SAMPLE, len(pol_chunks)))
        sampled.extend(chosen)

    print(f"Sampled {len(sampled)} chunks across {len(by_policy)} policies\n")

    results = []
    for chunk in sampled:
        qs = make_questions(chunk)
        results.extend(qs)

    # Shuffle to mix policies
    random.shuffle(results)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Generated {len(results)} adversarial questions")
    print(f"Saved → {OUTPUT_FILE}\n")

    from collections import Counter
    counts = Counter(r["policy"] for r in results)
    for pol, cnt in sorted(counts.items()):
        print(f"  {pol:<55} {cnt}")

    print(f"\nSample questions:")
    for q in random.sample(results, min(8, len(results))):
        print(f"  [{q['policy'][:30]}]  {q['query']}")
        print(f"    key_fact: {q['key_facts'][0][:50]}")


if __name__ == "__main__":
    main()
