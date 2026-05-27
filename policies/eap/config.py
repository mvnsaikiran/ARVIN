import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', '1to1 help Arvind.pdf')
POLICY_NAME = "1to1 Employee Assistance Program"
COLLECTION  = "policy_eap"
MAX_CHUNK   = 1200  # for slides, this is ignored (full page per chunk)
SKIP_PAGES  = {1, 23}
SEM_WEIGHT  = 1.5
TOP_K       = 6
MODE        = "slides"
DOC_TYPE    = "Program"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the 1to1 Employee Assistance Program..." when referencing the program.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the 1to1 Employee Assistance Program. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "1to1", "one to one help", "eap", "employee assistance program",
    "counselling service", "mental health support", "stress support",
    "eap helpline", "arvind eap", "employee counselling",
    "professional counselling", "confidential counselling",
]
