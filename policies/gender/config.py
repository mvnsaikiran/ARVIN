import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'arvind-gender-policy-2025.pdf')
POLICY_NAME = "Gender Policy"
COLLECTION  = "policy_gender"
MAX_CHUNK   = 1200
SKIP_PAGES  = {1}
SEM_WEIGHT  = 3.0
TOP_K       = 4
MODE        = "prose"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Gender Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Gender Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "gender policy", "gender equality", "gender inclusion", "gender bias",
    "gender discrimination", "gender identity", "lgbtq", "transgender",
    "equal opportunity gender", "gender diversity", "inclusive workplace gender",
    "gender neutral", "gender based discrimination", "gender sensitization",
]
