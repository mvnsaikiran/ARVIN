import os

PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'arvind-grievance-mechanism-policy-2025.pdf')
POLICY_NAME = "Grievance Mechanism Policy"
COLLECTION  = "policy_grievance"
MAX_CHUNK   = 1200
SKIP_PAGES  = {1}
SEM_WEIGHT  = 1.5
TOP_K       = 5
MODE        = "prose"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Grievance Mechanism Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Grievance Mechanism Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "grievance", "workplace grievance", "raise a grievance", "lodge a grievance",
    "grievance committee", "grievance redressal mechanism", "employee grievance",
    "grievance form", "escalate grievance", "unfair treatment", "grievance resolution",
    "grievance timeline", "grievance procedure", "file a grievance",
]
