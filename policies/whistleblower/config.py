"""
Policy 1: Whistleblower Policy
File: whistleblower-policy-arvind-limited.pdf
"""

import os

PDF_PATH       = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Final_Policies',
    'whistleblower-policy-arvind-limited.pdf'
)
POLICY_NAME    = "Whistleblower Policy"
COLLECTION     = "policy_whistleblower"
MAX_CHUNK      = 1500   # pure prose, larger chunks keep full sections together
SKIP_TABLES    = True   # this policy has zero tables — skip table extraction
SKIP_PAGES     = {1}    # page 1 is a cover image with no real content
SEM_WEIGHT     = 3.0    # semantic > BM25 for meaning-heavy prose
TOP_K          = 5      # 12 chunks total; 5 ensures no section is missed
DOC_TYPE       = "Policy"

SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.

Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Whistleblower Policy..." when referencing the policy.
- If the context does not cover the question, say exactly:
  "This specific detail is not covered in the Whistleblower Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""

# Keywords that identify this policy in a query (used by router)
KEYWORDS = [
    "whistleblower", "whistle blower", "whistle-blower",
    "protected disclosure", "ethics helpline",
    "bribery", "corruption", "fraud", "kickback",
    "false invoicing", "procurement fraud",
    "reportable concern", "blow the whistle",
    "report misconduct", "report wrongdoing",
    "non-victimization", "confidential complaint",
    "whistleblower identity", "retaliation after reporting",
    "retaliation",
    "victimization",
    "victimized",
    "face retaliation",
    "protect me",
    "am i protected",
    "safe to report",
    # investigation / process — keep specific to whistleblower context
    "whistleblower committee",
    "whistleblower investigation",
    "wrongdoing",
    "wrongful conduct",
    "false complaint whistleblower",
    "frivolous complaint",
    "grievance redressal",
    # confidentiality
    "whistleblower identity",
    "whistleblower confidential",
    # applicability
    "who can report",
    "business associate",
    "stakeholder",
    # reporting channels
    "toll-free",
    "toll free",
    "ethics helpline",
    "18002008301",
    "arvind@ethicshelpline.in",
    "web portal",
    "how to report",
    "where to report",
    "report a concern",
    # espionage / other reportables
    "corporate espionage",
    "embezzlement",
    "misappropriation",
    "unethical",
    "illegal activity",
]
