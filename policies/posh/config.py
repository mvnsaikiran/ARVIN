"""
Policy 2: POSH — Prevention of Sexual Harassment Policy
File: posh-policy-arvind-limited.pdf
"""

import os

PDF_PATH    = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Final_Policies',
    'posh-policy-arvind-limited.pdf'
)
POLICY_NAME = "POSH Policy"
COLLECTION  = "policy_posh"
MAX_CHUNK   = 1200
# Pages 11-14 are AIC member contact directories — not policy content
SKIP_PAGES  = {11, 12, 13, 14}
SEM_WEIGHT  = 1.5
TOP_K       = 6

SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.

Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the POSH Policy..." when referencing the policy.
- If the context does not cover the question, say exactly:
  "This specific detail is not covered in the POSH Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""

KEYWORDS = [
    # core topic
    "posh", "sexual harassment", "harassment at workplace",
    "prevention of sexual harassment",
    # key terms
    "aggrieved woman", "aggrieved employee",
    "unwelcome", "sexually determined behaviour",
    "hostile work environment", "intimidating",
    # committee
    "aic", "anti incidence committee", "anti-incidence committee",
    "internal committee", "presiding officer", "external member",
    # complaint / process
    "file a complaint", "lodge a complaint", "raise a complaint",
    "complaint against", "sexual harassment complaint",
    "complaint procedure", "inquiry", "investigation",
    "60 days", "90 days", "10 days",
    # outcome
    "disciplinary action", "written warning", "written apology",
    "reprimand", "withholding of promotion", "termination",
    # protection
    "confidentiality posh", "false complaint posh",
    "interim relief", "interim action",
    # workplace definition
    "extended workplace", "office parties", "outbound training",
    "travel for office", "client meetings",
    # contact
    "contact officer", "posh contact",
]
