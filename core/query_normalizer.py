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


def normalise(query: str) -> str:
    """
    Return a normalised version of `query` suitable for routing.
    The original query is unchanged; only the returned string is used
    for routing/embedding decisions.
    """
    text = query.strip().lower()

    # 1. Expand policy abbreviations (before word-splitting to catch "GHI" etc.)
    for pattern, replacement in _ABBR_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 2. Replace Hindi words with English equivalents
    words = text.split()
    expanded = []
    for word in words:
        # strip punctuation for lookup but preserve in output if no substitution
        clean = re.sub(r"[^\w]", "", word)
        replacement = _HINDI_MAP.get(clean, "")
        if replacement == "":
            # empty string means drop the word (filler)
            if clean in _HINDI_MAP:
                continue   # explicitly mapped to "", drop it
            expanded.append(word)  # not in map, keep as-is
        else:
            expanded.append(replacement)

    text = " ".join(expanded)

    # 3. Collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else query.lower()
