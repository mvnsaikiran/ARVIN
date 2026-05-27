import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'talent-mobility.pdf')
POLICY_NAME = "Talent Mobility Policy"
COLLECTION  = "policy_talent_mobility"
MAX_CHUNK   = 1200  # for slides, this is ignored (full page per chunk)
SKIP_PAGES  = {1, 10}
SEM_WEIGHT  = 1.5
TOP_K       = 6
MODE        = "slides"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Talent Mobility Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Talent Mobility Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "talent mobility", "internal transfer", "job rotation", "internal job posting",
    "mobility policy", "cross functional move", "role rotation",
    "career mobility", "internal movement", "lateral transfer",
    "internal career", "mobility eligibility",
]
