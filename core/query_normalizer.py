"""
Query normalisation for ARVIN's routing layer.

Handles:
  1. Hindi/Hinglish → English word substitution
  2. Policy abbreviation expansion
  3. Noise stripping (filler words, repeated punctuation)
"""

import re

# ---------------------------------------------------------------------------
# Hindi / Hinglish → English word map
# ---------------------------------------------------------------------------
_HINDI_MAP: dict[str, str] = {
    # pronouns / determiners
    "mera": "my", "meri": "my", "mere": "my", "apna": "my", "apni": "my",
    "mujhe": "me", "hum": "we",
    # "main" is NOT mapped — it is an English word (main purpose, main office)
    "yeh": "this", "woh": "that", "iss": "this",
    # "is" and "the" are intentionally NOT mapped — they are common English words
    # interrogatives
    "kya": "what", "kaisa": "how", "kaisi": "how", "kaise": "how",
    "kitna": "how much", "kitni": "how much", "kitne": "how many",
    "kab": "when", "kahan": "where", "kyun": "why", "kyunki": "because",
    "kon": "who", "kaun": "who", "konsa": "which", "kaunsa": "which",
    # verbs / auxiliaries
    "hai": "is", "hain": "are", "tha": "was",
    # "the" is NOT mapped — it is the English definite article
    "hoga": "will be", "hogi": "will be", "honge": "will be",
    "milega": "will i get", "milegi": "will i get", "milenge": "will get",
    "milta": "available", "milti": "available",
    "chahiye": "required", "chaiye": "required",
    "kar": "do", "karo": "do", "karein": "do", "karna": "to do",
    "sakta": "can", "sakti": "can", "sakte": "can",
    "bata": "tell", "batao": "tell me", "bataye": "please tell",
    "dekho": "see", "dekhna": "to see",
    "submit": "submit", "apply": "apply", "claim": "claim",
    # prepositions / conjunctions
    "ka": "", "ki": "", "ke": "", "se": "from",
    "mein": "in", "pe": "on", "par": "on",
    "aur": "and", "ya": "or", "nahi": "not", "nahin": "not",
    "ko": "to", "tak": "till",
    # common HR filler
    "bhai": "", "yaar": "", "please": "please", "plz": "please",
    "bro": "", "sir": "", "ma'am": "", "madam": "",
    "help": "help", "batao": "tell me",
    # common expressions
    "allowance": "allowance",   # already English — kept for completeness
}

# ---------------------------------------------------------------------------
# Policy abbreviation → descriptive expansion
# (expand so semantic router can match intent anchors)
# ---------------------------------------------------------------------------
_ABBR_MAP: dict[str, str] = {
    # insurance
    r"\bghi\b":  "group health insurance",
    r"\bgpa\b":  "group personal accident insurance",
    r"\bgtl\b":  "group term life insurance",
    r"\bvdc\b":  "voluntary death contribution",
    # HR policies
    r"\bwb\b":   "whistleblower",
    r"\bposh\b": "sexual harassment prevention posh",
    r"\bfnf\b":  "full and final settlement",
    r"\bf&f\b":  "full and final settlement",
    r"\beap\b":  "employee assistance program",
    r"\blc\b":   "local conveyance",
    r"\btm\b":   "talent mobility internal transfer",
    r"\bijp\b":  "internal job posting talent mobility",
    # travel
    r"\bdt\b":         "domestic travel",
    r"\bta\s*/?da\b":  "travel allowance daily allowance",
    r"\bta/da\b":      "travel allowance daily allowance",
    r"\bta\b":         "travel allowance",
    r"\bda\b":         "daily allowance",
    r"\bmybiz\b":      "mybiz travel booking",
    # finance / exit
    r"\bpf\b":   "provident fund",
    r"\bgratuity\b": "gratuity full final settlement",
    # health / benefits
    r"\bmedibuddy\b": "medibuddy teleconsultation",
    r"\bfhpl\b":      "fhpl health insurance tpa",
    r"\bpankh\b":     "pankh employee referral",
    r"\b1to1\b":      "1to1 employee assistance counselling",
}

# ---------------------------------------------------------------------------
# Domain slang / casual speech → routing-friendly terms
# Maps informal employee phrasing to keywords the router recognises.
# Order matters: longer / more specific patterns first.
# ---------------------------------------------------------------------------
_SLANG_MAP: list[tuple[str, str]] = [
    # ── Exit / separation ────────────────────────────────────────────────────
    (r"\b(got fired|was fired|been fired|getting fired|termination pay)\b",
     "full and final settlement"),
    (r"\b(leaving (the )?company|leaving (the )?job|quitting|quit (the )?job|put in (my )?papers|resigned?|resignation)\b",
     "full and final settlement"),
    (r"\b(last (day|working day)|exit formalities|relieving (letter|process)|clearance (form|process))\b",
     "full and final settlement"),
    (r"\b(notice period (pay|buyout|waiver)|serve (my )?notice)\b",
     "full and final settlement"),

    # ── Travel ───────────────────────────────────────────────────────────────
    (r"\b(bus ride|bus fare|auto fare|auto ride|rickshaw|rick(shaw)? fare)\b",
     "local conveyance"),
    (r"\b(cab (to|from) (office|work|home)|ola|uber|rapido|taxi (to|from) (office|work))\b",
     "local conveyance"),
    (r"\b(petrol (bill|money|reimbursement)|fuel (cost|expense|reimbursement)|per km)\b",
     "local conveyance"),
    (r"\b(outstation|out(-| )station|business trip|official trip|work trip|tour (advance|expenses?))\b",
     "domestic travel"),
    (r"\b(hotel (bill|stay|booking|limit)|flight (booking|ticket|claim)|air ticket)\b",
     "domestic travel"),
    (r"\b(travel (bills?|receipts?|claims?|settlement|expenses?))\b",
     "travel settlement"),
    (r"\b(mytour|my tour dashboard|tour claim|tour settlement)\b",
     "travel settlement"),

    # ── Insurance ────────────────────────────────────────────────────────────
    (r"\b(hospitaliz(ed?|ation)|admitted (to )?hospital|hospital (bill|claim|expenses?))\b",
     "group health insurance"),
    (r"\b(mediclaim|cashless (treatment|claim|card)|tpa card|insurance card)\b",
     "group health insurance"),
    (r"\b(doctor (visit|consultation|fees?)|medical (bill|reimbursement|claim))\b",
     "group health insurance"),
    (r"\b(met with (an )?accident|accident (claim|insurance|cover)|road accident)\b",
     "group personal accident insurance"),
    (r"\b(disability (cover|benefit|compensation)|lost (a )?(limb|finger|eye|hand))\b",
     "group personal accident insurance"),
    (r"\b(life (cover|insurance|policy)|death (benefit|claim|cover)|nominee (for )?insurance)\b",
     "group term life insurance"),
    (r"\b(family (gets?|receives?|entitled)|dependents? (benefit|cover|insurance))\b",
     "group term life insurance"),
    (r"\b(colleague (died|passed away|death)|co-?worker (died|death))\b",
     "voluntary death contribution"),
    (r"\b(condolence (fund|amount)|death fund|solidarity (fund|contribution))\b",
     "voluntary death contribution"),

    # ── Complaints / misconduct ───────────────────────────────────────────────
    (r"\b(sexually harassed?|harassment (at work|complaint)|unwanted (advances|touching|behaviour))\b",
     "posh sexual harassment"),
    (r"\b(inappropriate (behaviour|conduct|comments?)|hostile work environment)\b",
     "posh sexual harassment"),
    (r"\b(report (fraud|corruption|bribery|misconduct|wrongdoing|unethical))\b",
     "whistleblower ethics disclosure"),
    (r"\b(blowing (the )?whistle|ethics (helpline|hotline|complaint))\b",
     "whistleblower ethics disclosure"),
    (r"\b(complain (about )?my (manager|boss|supervisor)|workplace (complaint|issue|dispute))\b",
     "grievance mechanism"),
    (r"\b(gender (discrimination|bias|inequality)|lgbtq|transgender (employee|rights))\b",
     "gender policy"),

    # ── Joining / onboarding ─────────────────────────────────────────────────
    (r"\b(first day (at work)?|joining (formalities|documents|kit)|onboarding)\b",
     "joining policy relocation"),
    (r"\b(relocation (allowance|support|expense|benefit)|shifting (cities|to (a )?new city))\b",
     "joining policy relocation"),
    (r"\b(packers? (and )?movers?|household (goods|shifting)|brokerage (reimbursement|for rent))\b",
     "joining policy relocation"),

    # ── Referral ─────────────────────────────────────────────────────────────
    (r"\b(refer (a |my )?(friend|someone|candidate|person)|employee referral (bonus|reward|program))\b",
     "pankh employee referral"),
    (r"\b(referral (bonus|money|amount|incentive)|hiring bonus for referral)\b",
     "pankh employee referral"),

    # ── Internal transfer ─────────────────────────────────────────────────────
    (r"\b(switch (departments?|teams?|roles?|divisions?)|move (to )?another (departments?|teams?|roles?))\b",
     "talent mobility internal job posting"),
    (r"\b(internal (transfer|move|application|posting)|apply (for )?internal (role|job|position))\b",
     "talent mobility internal job posting"),
    (r"\b(job rotation|lateral (move|transfer)|cross(-| )functional (move|transfer))\b",
     "talent mobility internal job posting"),

    # ── Expenses / reimbursement ──────────────────────────────────────────────
    (r"\b(get (my )?money back|claim (back )?my (money|expenses?)|reimburs(e|ement))\b",
     "expense reimbursement claim"),
    (r"\b(birthday (party|celebration) (expense|cost|reimbursement)|team (lunch|dinner) (expense|claim))\b",
     "employee expense reimbursement"),
    (r"\b(puja (expense|celebration)|farewell (expense|party cost))\b",
     "employee expense reimbursement"),

    # ── Health / wellness ─────────────────────────────────────────────────────
    (r"\b(stressed? (at work|out)|mental health (support|help)|anxiety|counsell?ing)\b",
     "employee assistance program counselling eap"),
    (r"\b(talk (to )?someone|need (help|support) (at work|personally)|feeling (low|burnout|overwhelmed))\b",
     "employee assistance program counselling eap"),
    (r"\b(teleconsult(ation)?|online doctor|virtual (doctor|consultation)|book (a )?doctor)\b",
     "medibuddy teleconsultation"),
]


def normalise(query: str) -> str:
    """
    Return a normalised version of `query` suitable for routing.
    The original query is unchanged; only the returned string is used
    for routing/embedding decisions.

    Pipeline:
      1. Slang / casual-speech → official HR terms
      2. Policy abbreviation expansion
      3. Hindi/Hinglish word substitution
      4. Whitespace collapse
    """
    text = query.strip().lower()

    # 1. Slang expansion (longest/most-specific patterns are listed first)
    for pattern, replacement in _SLANG_MAP:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 2. Expand policy abbreviations
    for pattern, replacement in _ABBR_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 3. Replace Hindi words with English equivalents
    words = text.split()
    expanded = []
    for word in words:
        clean = re.sub(r"[^\w]", "", word)
        replacement = _HINDI_MAP.get(clean, "")
        if replacement == "":
            if clean in _HINDI_MAP:
                continue   # explicitly mapped to "", drop filler
            expanded.append(word)
        else:
            expanded.append(replacement)

    text = " ".join(expanded)

    # 4. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else query.lower()
