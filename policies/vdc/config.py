import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Voluntary Death Contribution Policy - Arvind Ltd.pdf')
POLICY_NAME = "Voluntary Death Contribution Policy"
COLLECTION  = "policy_vdc"
MAX_CHUNK   = 600
SKIP_PAGES  = set()
SEM_WEIGHT  = 1.2
TOP_K       = 3
MODE        = "tables"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Voluntary Death Contribution Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Voluntary Death Contribution Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "voluntary death contribution", "vdc", "death contribution scheme",
    "death benefit contribution", "employee death fund",
    "compassionate contribution", "death of employee contribution",
]
