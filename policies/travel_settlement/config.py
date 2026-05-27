import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Travel Settlement - Arvind Limited.pdf')
POLICY_NAME = "Travel Settlement Guide"
COLLECTION  = "policy_travel_settlement"
MAX_CHUNK   = 1200  # for slides, this is ignored (full page per chunk)
SKIP_PAGES  = {1, 23}
SEM_WEIGHT  = 1.5
TOP_K       = 6
MODE        = "slides"
DOC_TYPE    = "Guide"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Travel Settlement Guide..." when referencing the guide.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Travel Settlement Guide. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "travel settlement", "travel claim submission", "travel expense claim",
    "onearvind travel", "submit travel expenses", "travel settlement request",
    "travel claim form", "travel reimbursement claim", "domestic travel settlement",
]
