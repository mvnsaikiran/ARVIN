import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Pankh - Employee Referral.pdf')
POLICY_NAME = "Pankh Employee Referral Policy"
COLLECTION  = "policy_pankh"
MAX_CHUNK   = 800
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.2
TOP_K       = 4
MODE        = "tables"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Pankh Employee Referral Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Pankh Employee Referral Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "pankh", "employee referral", "referral bonus", "refer a candidate",
    "employee referral program", "referral reward", "candidate referral",
    "job referral", "pankh referral", "refer friend for job",
]
