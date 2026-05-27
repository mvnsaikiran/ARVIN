import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Group Personal Accident Insurance Scheme - Arvind Ltd.pdf')
POLICY_NAME = "Group Personal Accident Insurance Policy"
COLLECTION  = "policy_gpa"
MAX_CHUNK   = 1000
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.5
TOP_K       = 4
MODE        = "prose"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Group Personal Accident Insurance Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Group Personal Accident Insurance Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    # exact policy phrases
    "personal accident insurance", "gpa", "accidental death benefit",
    "disability benefit", "accident insurance", "permanent disability",
    "temporary disability", "accident claim", "group personal accident",
    "accident compensation",
    # broader triggers employees actually type
    "accident", "accidental", "injured", "injury", "pa insurance",
    "pa policy", "pa cover", "disability claim", "accident benefit",
    "accident policy", "personal accident", "accident cover",
    "loss of limb", "loss of sight", "partial disability",
]
