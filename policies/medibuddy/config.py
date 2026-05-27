import os
FAQ_PATH    = os.path.join(os.path.dirname(__file__), 'faq.txt')
POLICY_NAME = "MediBuddy User Guide"
COLLECTION  = "policy_medibuddy"
MAX_CHUNK   = 800
SKIP_PAGES  = set()
SEM_WEIGHT  = 1.5
TOP_K       = 4
MODE        = "faq"
DOC_TYPE    = "Guide"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the MediBuddy User Guide..." when referencing the guide.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the MediBuddy User Guide. Please contact MediBuddy support at 9999991555 or hello@medibuddy.in"
- Be concise and professional.
- Use bullet points for lists of steps."""
KEYWORDS = [
    "medibuddy", "medi buddy", "teleconsultation", "online doctor consultation",
    "medibuddy app", "online consultation medibuddy", "medibuddy gold",
    "medibuddy registration", "book doctor online", "medibuddy benefit",
]
