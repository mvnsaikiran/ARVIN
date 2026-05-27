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
MAX_CHUNK      = 1000   # prose-heavy doc, medium chunks work well

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
]
