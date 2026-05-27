import os
PDF_PATH    = os.path.join(os.path.dirname(__file__), '..', '..', 'Final_Policies', 'Employee Expense Reimbursement Policy.pdf')
POLICY_NAME = "Employee Expense Reimbursement Policy"
COLLECTION  = "policy_expense"
MAX_CHUNK   = 1200
SKIP_PAGES  = {1}
SEM_WEIGHT  = 2.0
TOP_K       = 4
MODE        = "prose"
DOC_TYPE    = "Policy"
SYSTEM_PROMPT = """You are ARVIN, Arvind Limited's official HR Policy Assistant.
Answer the employee's question using ONLY the policy context provided below.
Rules:
- Answer only from the context. Never invent or guess.
- Always say "As per the Employee Expense Reimbursement Policy..." when referencing the policy.
- If the context does not cover the question, say exactly: "This specific detail is not covered in the Employee Expense Reimbursement Policy. Please contact your Business HR."
- Be concise and professional.
- Use bullet points for lists of steps or items.
- Never give legal advice."""
KEYWORDS = [
    "expense reimbursement", "expense claim", "birthday celebration expense",
    "farewell expense", "puja expense", "car expense reimbursement",
    "admin purchase", "reimbursement form", "medical reimbursement expense",
    "expense approval", "employee expense", "expense sop",
]
