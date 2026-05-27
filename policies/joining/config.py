import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Joining Policy- Arvind Ltd.pdf')
POLICY_NAME = "Joining Policy"
COLLECTION  = "policy_joining"
MAX_CHUNK   = 1000
SKIP_PAGES  = {1}
SEM_WEIGHT  = 3.0
TOP_K       = 5
MODE        = "tables"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Joining Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Joining Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "joining policy", "joining bonus", "relocation allowance", "onboarding allowance",
    "joining kit", "new joinee", "joining formalities", "notice pay buyout",
    "joining expenses", "accommodation joining", "new employee joining",
    "joining reimbursement", "relocation benefit", "joining travel",
]
