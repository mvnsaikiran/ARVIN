import os
PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'local-conveyance-policy-arvind-limited.pdf')
POLICY_NAME = "Local Conveyance Policy"
COLLECTION  = "policy_local_conveyance"
MAX_CHUNK   = 800
SKIP_PAGES  = set()
SEM_WEIGHT  = 1.2
TOP_K       = 4
MODE        = "tables"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Local Conveyance Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Local Conveyance Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "local conveyance", "conveyance allowance", "petrol reimbursement",
    "mileage claim", "local travel allowance", "cab allowance",
    "conveyance claim", "daily conveyance", "own vehicle allowance",
    "local conveyance policy",
]
