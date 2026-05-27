import os
PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Full & Final Settlement Policy_Arvind (1).pdf')
POLICY_NAME = "Full & Final Settlement Policy"
COLLECTION  = "policy_fnf"
MAX_CHUNK   = 1000
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.2
TOP_K       = 6
MODE        = "tables"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Full & Final Settlement Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Full & Final Settlement Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "full and final", "fnf", "full and final settlement", "exit process",
    "resignation dues", "relieving letter", "no dues clearance", "gratuity",
    "pf withdrawal", "last working day", "exit formalities", "fnf settlement",
    "settlement amount", "pf transfer", "exit checklist",
]
