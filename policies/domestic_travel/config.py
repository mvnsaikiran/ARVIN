import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'domestic-travel-policy-arvind-limited.pdf')
POLICY_NAME = "Domestic Travel Policy"
COLLECTION  = "policy_domestic_travel"
MAX_CHUNK   = 1000
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.2
TOP_K       = 7
MODE        = "tables"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Domestic Travel Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Domestic Travel Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "domestic travel policy", "travel allowance", "hotel allowance", "flight booking policy",
    "travel approval", "per diem", "travel advance", "ta da", "travel entitlement",
    "grade wise travel", "travel class entitlement", "business travel policy",
    "travel norms", "hotel entitlement", "travel reimbursement policy",
]
