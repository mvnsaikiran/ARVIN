import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Group Term Life Insurance - Arvind Limited.pdf')
POLICY_NAME = "Group Term Life Insurance Policy"
COLLECTION  = "policy_gtl"
MAX_CHUNK   = 1000
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.3
TOP_K       = 4
MODE        = "tables"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Group Term Life Insurance Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Group Term Life Insurance Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    # exact policy phrases
    "group term life", "term life insurance", "gtl", "life cover",
    "death benefit insurance", "life insurance", "nominee life insurance",
    "death claim insurance", "gtl scheme", "life insurance benefit arvind",
    # broader triggers employees actually type
    "death", "death benefit", "nominee", "life policy", "term insurance",
    "gtl policy", "death claim", "life cover arvind", "employee death",
    "death compensation", "life benefit", "insurance nominee",
    "death of employee", "natural death", "accidental death life",
]
