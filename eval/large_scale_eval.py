"""
ARVIN — Large-Scale Offline Accuracy Evaluator (1000 questions/policy target)

Question generation uses:
  1. Sentence-level multi-pattern extraction (10+ patterns per sentence)
  2. Value-specific questions  (every ₹, %, day, month extracted)
  3. Role/entity questions     (every HR role / key noun)
  4. Paraphrase variants       (8 rephrasing templates per base question)
  5. Hindi-English hybrid questions
  6. Handcrafted seeds per policy

Dedup threshold relaxed to 0.60 (was 0.75) to allow more near-similar variants.
OOS pool expanded to 60 questions.

Usage:
    python eval/large_scale_eval.py
    python eval/large_scale_eval.py --policy wb
"""

import os, sys, re, json, argparse, hashlib
from typing import List
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chromadb.utils import embedding_functions

EVAL_DIR        = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(EVAL_DIR, '..', 'vectorstore')
TARGET_PER_POLICY = 1000
DEDUP_THRESHOLD   = 0.60    # relaxed from 0.75 to allow paraphrase variants

# ── ONNX embeddings ───────────────────────────────────────────────────────────
_onnx_fn = None
def _get_onnx():
    global _onnx_fn
    if _onnx_fn is None:
        _onnx_fn = embedding_functions.ONNXMiniLM_L6_V2()
    return _onnx_fn

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    n = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / n) if n > 0 else 0.0

def batch_cosine(queries: List[str], docs: List[str]) -> List[float]:
    if not queries or not docs:
        return []
    fn   = _get_onnx()
    vecs = fn(queries + docs)
    q_v  = vecs[:len(queries)]
    d_v  = vecs[len(queries):]
    return [cosine(q, d) for q, d in zip(q_v, d_v)]

# ── Policy config ─────────────────────────────────────────────────────────────
POLICY_MAP = {
    "wb":    ("policy_whistleblower",       "Whistleblower Policy",                    "whistleblower"),
    "posh":  ("policy_posh",                "POSH Policy",                             "posh"),
    "grv":   ("policy_grievance",           "Grievance Mechanism Policy",              "grievance"),
    "gen":   ("policy_gender",              "Gender Policy",                           "gender"),
    "dt":    ("policy_domestic_travel",     "Domestic Travel Policy",                  "domestic_travel"),
    "jn":    ("policy_joining",             "Joining Policy",                          "joining"),
    "fnf":   ("policy_fnf",                 "Full & Final Settlement Policy",          "fnf"),
    "exp":   ("policy_expense",             "Employee Expense Reimbursement Policy",   "expense"),
    "lc":    ("policy_local_conveyance",    "Local Conveyance Policy",                 "local_conveyance"),
    "ghi":   ("policy_ghi",                 "Group Health Insurance Policy",           "group_health"),
    "gpa":   ("policy_gpa",                 "Group Personal Accident Insurance Policy","group_personal_accident"),
    "gtl":   ("policy_gtl",                 "Group Term Life Insurance Policy",        "group_term_life"),
    "vdc":   ("policy_vdc",                 "Voluntary Death Contribution Policy",     "vdc"),
    "pankh": ("policy_pankh",               "Pankh Employee Referral Policy",          "pankh"),
    "tm":    ("policy_talent_mobility",     "Talent Mobility Policy",                  "talent_mobility"),
    "mb":    ("policy_medibuddy",           "MediBuddy User Guide",                    "medibuddy"),
    "ts":    ("policy_travel_settlement",   "Travel Settlement Guide",                 "travel_settlement"),
    "eap":   ("policy_eap",                 "1to1 Employee Assistance Program",        "eap"),
}

# ── Expanded OOS pool (60 questions) ─────────────────────────────────────────
OOS_POOL = [
    "How do I apply for a home loan from Arvind?",
    "What is the annual leave balance for this year?",
    "Can I work from home permanently?",
    "What is the salary increment cycle at Arvind?",
    "How do I get a no-objection certificate?",
    "What is the dress code policy at Arvind?",
    "How do I change my bank account for salary credit?",
    "What is the probation period for new joiners?",
    "Can I carry forward my earned leave to next year?",
    "How do I apply for early retirement?",
    "What is the process for getting a laptop from IT?",
    "How do I log a complaint about the canteen food?",
    "What is the policy on using personal mobile phones at work?",
    "How do I access the employee self-service portal?",
    "What happens to my PF if I resign?",
    "Can I take a sabbatical leave from Arvind?",
    "What is the paternity leave policy at Arvind?",
    "How do I apply for maternity leave?",
    "What is the annual performance review process?",
    "How do I nominate someone for the employee of the month award?",
    "What is the notice period for new joiners?",
    "Can I change my designation without a promotion?",
    "What is the referral process for IT equipment replacement?",
    "How do I request a salary advance at Arvind?",
    "What is the policy on overtime pay?",
    "Can I moonlight or do freelance work while employed at Arvind?",
    "How do I apply for a training or certification reimbursement?",
    "What are the working hours at Arvind?",
    "How many sick leaves do I get per year?",
    "What is the process for applying for casual leave?",
    "How do I claim my LTA (leave travel allowance)?",
    "What is the superannuation policy at Arvind?",
    "Can I get a reference letter from HR?",
    "What is the background verification process at Arvind?",
    "How do I update my personal details in the HRMS?",
    "What is the policy on Internet usage at work?",
    "Can I bring guests to the office premises?",
    "What is the flexi-hours policy at Arvind?",
    "How do I apply for a bereavement leave?",
    "What is the sports or recreation facility at Arvind?",
    "How do I escalate a payroll discrepancy?",
    "What is the transfer policy at Arvind?",
    "Can I request a deputation to another location?",
    "What is the ESOP (employee stock option plan) policy?",
    "How do I get a salary certificate for a bank loan?",
    "What is the appraisal rating scale used at Arvind?",
    "Can I defer my variable pay?",
    "What is the notice period buy-out option?",
    "How do I surrender my annual leave?",
    "What is the policy on hiring relatives at Arvind?",
    "Can I get an experience letter before relieving?",
    "What is the retirement age at Arvind?",
    "How do I apply for the employee suggestion scheme?",
    "What are the awards and recognition programs at Arvind?",
    "How do I request a role change or job rotation?",
    "What is the policy on using company vehicles?",
    "Can I take an unpaid leave of absence?",
    "What are the benefits for differently-abled employees?",
    "How do I report an IT security incident?",
    "What is the policy on confidentiality and data privacy?",
]

# ── Sentence helpers ──────────────────────────────────────────────────────────
def _sentences(text: str) -> list[str]:
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove chunk header line
    text = re.sub(r'^\[.*?\]\n?', '', text).strip()
    parts = re.split(r'(?<=[.?!])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 25]

def _extract_amounts(text: str) -> list[str]:
    return re.findall(r'(?:₹|Rs\.?)\s*[\d,]+(?:\.\d+)?', text, re.I)

def _extract_percentages(text: str) -> list[str]:
    return re.findall(r'\d+(?:\.\d+)?\s*%', text)

def _extract_days(text: str) -> list[str]:
    return re.findall(r'\d+\s+(?:working\s+)?days?', text, re.I)

def _extract_months(text: str) -> list[str]:
    return re.findall(r'\d+\s+months?', text, re.I)

def _extract_roles(text: str) -> list[str]:
    role_patterns = [
        'employee', 'manager', 'hr', 'committee', 'officer', 'complainant',
        'respondent', 'whistleblower', 'nominee', 'employer', 'grievance officer',
        'presiding officer', 'business hr', 'chro', 'chairman', 'member',
        'new joiner', 'dependent', 'family member', 'beneficiary', 'claimant',
    ]
    found = []
    tl = text.lower()
    for r in role_patterns:
        if r in tl:
            found.append(r)
    return found

def _extract_key_nouns(text: str, policy_name: str) -> list[str]:
    """Extract capitalised / policy-specific nouns."""
    nouns = re.findall(r'\b[A-Z][A-Za-z]{3,}\b', text)
    # Filter out very common words
    stop = {'This', 'That', 'When', 'What', 'Where', 'Which', 'From', 'With',
            'Upon', 'Only', 'Also', 'Such', 'Each', 'They', 'Will', 'Shall',
            'Have', 'Been', 'Their', 'These', 'Those', 'Policy', 'Arvind',
            'Employee', 'Please', 'Note'}
    return [n for n in nouns if n not in stop and len(n) > 3][:8]


# ── Question generation (multi-pattern) ───────────────────────────────────────

_PARAPHRASE_STARTERS = [
    "What is", "How is", "Can you explain", "Tell me about",
    "Describe", "What does", "How does", "What are the details of",
]

def _paraphrase(q: str) -> list[str]:
    """Generate simple paraphrase variants."""
    variants = [q]
    ql = q.lower()
    # What is X? → synonyms
    if ql.startswith("what is "):
        rest = q[8:]
        variants += [
            f"Can you explain {rest}",
            f"Tell me about {rest}",
            f"How is {rest} defined?",
        ]
    elif ql.startswith("how do i "):
        rest = q[9:]
        variants += [
            f"What is the process to {rest}",
            f"What are the steps to {rest}",
            f"How can I {rest}",
        ]
    elif ql.startswith("who "):
        variants += [
            q.replace("Who ", "Which person "),
            q.replace("Who ", "Whose responsibility is it to "),
        ]
    elif ql.startswith("what are the "):
        rest = q[13:]
        variants += [
            f"List the {rest}",
            f"What is covered under {rest}",
        ]
    return variants


def generate_1000_questions(short: str, chunks: list[dict], label: str) -> tuple[list[str], list[str]]:
    """Return (in_scope_questions, oos_questions)."""
    in_scope: set[str] = set()

    # 1. Handcrafted seeds
    in_scope.update(_seeds(short, label))

    policy_short = label.lower().replace(" policy", "").replace(" guide", "").replace(" program", "")

    for chunk in chunks:
        raw_text = chunk['text']
        # Strip header for sentence extraction
        text     = re.sub(r'^\[.*?\]\n?', '', raw_text).strip()
        sents    = _sentences(text)
        amounts  = _extract_amounts(text)
        pcts     = _extract_percentages(text)
        days_l   = _extract_days(text)
        months_l = _extract_months(text)
        roles    = _extract_roles(text)
        nouns    = _extract_key_nouns(text, label)

        # 2. Sentence-level multi-pattern questions
        for sent in sents:
            sl = sent.lower()

            # Definition patterns
            m = re.match(r'(.{5,60}?)\s+(?:is defined as|refers to|means|shall mean)\s+.{10,}', sent, re.I)
            if m:
                subj = m.group(1).strip().rstrip('.,;')
                in_scope.update([
                    f"What is the definition of {subj}?",
                    f"How is {subj} defined under the policy?",
                    f"What does {subj} mean in this policy?",
                    f"What is meant by {subj}?",
                ])

            # SHALL/MUST/REQUIRED obligations
            if re.search(r'\b(shall|must|is required to|should)\b', sl):
                for verb in re.findall(r'\b(submit|file|report|raise|lodge|escalate|apply|notify|inform|provide|maintain|ensure)\b', sl):
                    in_scope.update([
                        f"Who is required to {verb} under this policy?",
                        f"What is the obligation to {verb}?",
                        f"When should an employee {verb}?",
                        f"Is it mandatory to {verb} under this policy?",
                        f"What happens if you fail to {verb}?",
                    ])

            # Timeline patterns
            for d in re.findall(r'\d+\s+(?:working\s+)?days?', sl, re.I):
                in_scope.update([
                    f"What is the {d} timeline mentioned in the policy?",
                    f"How many days does the process take?",
                    f"What is the time limit for this process?",
                    f"Is there a deadline of {d} in this policy?",
                ])

            # Amount/limit patterns
            for amt in re.findall(r'(?:₹|Rs\.?)\s*[\d,]+(?:\.\d+)?', sent, re.I):
                in_scope.update([
                    f"What is the {amt} limit mentioned in this policy?",
                    f"What does the amount {amt} refer to?",
                    f"What is the maximum reimbursement of {amt}?",
                    f"What can be claimed up to {amt}?",
                ])

            # Percentage patterns
            for pct in re.findall(r'\d+(?:\.\d+)?\s*%', sent):
                in_scope.update([
                    f"What does {pct} refer to in this policy?",
                    f"What is the {pct} rate mentioned in the policy?",
                    f"How is the {pct} calculated?",
                ])

            # Eligibility patterns
            if re.search(r'\b(eligible|entitled|covered|applicable|qualify|applicable to)\b', sl):
                in_scope.update([
                    f"Who is eligible under this policy?",
                    f"What are the eligibility criteria?",
                    f"Who qualifies for benefits under this policy?",
                    f"Is every employee eligible under this policy?",
                    f"What conditions make an employee eligible?",
                    f"Are contract employees eligible under this policy?",
                    f"Are trainees covered under this policy?",
                ])

            # Escalation/appeal patterns
            if re.search(r'\b(escalat|appeal|second level|higher authority|next level)\b', sl):
                in_scope.update([
                    f"What is the escalation process under this policy?",
                    f"How do I escalate a complaint?",
                    f"Who handles escalated cases?",
                    f"What are the escalation levels?",
                    f"Can I appeal a decision under this policy?",
                ])

            # Confidentiality patterns
            if re.search(r'\b(confidential|identity|anonymous|protect|privacy)\b', sl):
                in_scope.update([
                    f"Is confidentiality maintained under this policy?",
                    f"Can I raise a complaint anonymously?",
                    f"How is my identity protected?",
                    f"What privacy protections are in place?",
                    f"Will my complaint be kept confidential?",
                ])

            # Consequence/penalty patterns
            if re.search(r'\b(terminat|disciplinary|penalty|action|consequence|dismiss)\b', sl):
                in_scope.update([
                    f"What are the disciplinary consequences under this policy?",
                    f"What action is taken for violation of this policy?",
                    f"Can an employee be terminated under this policy?",
                    f"What penalties apply for non-compliance?",
                    f"What happens if the policy is violated?",
                ])

            # Claim/reimbursement patterns
            if re.search(r'\b(claim|reimburse|payment|disburs|settle)\b', sl):
                in_scope.update([
                    f"How do I file a claim under this policy?",
                    f"What is the claim process?",
                    f"How long does reimbursement take?",
                    f"What documents are needed for a claim?",
                    f"Who approves the claim?",
                    f"When will the claim be processed?",
                    f"What is the timeline for claim settlement?",
                ])

            # Nomination patterns
            if re.search(r'\b(nomin|beneficiary|nominee)\b', sl):
                in_scope.update([
                    f"How do I nominate a beneficiary?",
                    f"Who can be my nominee under this policy?",
                    f"Can I change my nominee?",
                    f"What documents are needed for nomination?",
                    f"What happens if no nominee is registered?",
                ])

            # Coverage patterns
            if re.search(r'\b(cover|includ|exclud|scope)\b', sl):
                in_scope.update([
                    f"What is covered under this policy?",
                    f"What is excluded from this policy?",
                    f"What are the inclusions and exclusions?",
                    f"Does this policy cover all employees?",
                    f"Are dependents covered under this policy?",
                ])

            # Numbered steps
            if re.match(r'^\d+[\.\)]\s+', sent.strip()):
                in_scope.update([
                    f"What are the steps in the process under this policy?",
                    f"What is the step-by-step procedure?",
                    f"What are the key steps to follow?",
                ])

        # 3. Amount-specific questions
        for amt in amounts:
            in_scope.update([
                f"What is the maximum amount of {amt} under this policy?",
                f"How much can I claim — is it {amt}?",
                f"What is the {amt} reimbursement limit?",
                f"Under what circumstances is {amt} applicable?",
            ])

        # 4. Day/month timeline questions
        for d in days_l:
            in_scope.update([
                f"What must happen within {d}?",
                f"What is the significance of {d} in this policy?",
                f"Is {d} the deadline for submission?",
            ])
        for m in months_l:
            in_scope.update([
                f"What happens after {m}?",
                f"Is there a {m} requirement in this policy?",
            ])

        # 5. Role-based questions
        for role in roles:
            in_scope.update([
                f"What is the role of the {role} under this policy?",
                f"What are the responsibilities of the {role}?",
                f"Who is the {role} in this context?",
                f"Can the {role} escalate a matter?",
                f"What decisions does the {role} make?",
            ])

        # 6. Noun-based questions
        for noun in nouns:
            in_scope.update([
                f"What is {noun} under this policy?",
                f"How does {noun} relate to this policy?",
            ])

        if len(in_scope) >= TARGET_PER_POLICY * 3:
            break

    # 7. Paraphrase variants of seeds
    for seed in _seeds(short, label):
        in_scope.update(_paraphrase(seed))

    # 8. Hindi-English hybrid variants of key questions
    in_scope.update(_hindi_variants(short, label))

    # 9. Generic policy-level questions
    in_scope.update(_generic_policy_questions(policy_short, label))

    # Dedup and cap
    result = _deduplicate(list(in_scope), TARGET_PER_POLICY)

    # OOS: stable shuffle per policy
    seed_n = int(hashlib.md5(label.encode()).hexdigest()[:8], 16)
    rng    = np.random.default_rng(seed_n)
    n_oos  = min(50, len(OOS_POOL))
    oos    = [OOS_POOL[i] for i in rng.choice(len(OOS_POOL), size=n_oos, replace=False)]

    return result, oos


def _generic_policy_questions(policy_short: str, label: str) -> list[str]:
    """Generic questions applicable to any policy, filled with policy context."""
    return [
        f"What is the purpose of the {label}?",
        f"When was the {label} last updated?",
        f"Who does the {label} apply to?",
        f"What is the scope of the {label}?",
        f"What are the key provisions of the {label}?",
        f"How is the {label} enforced?",
        f"What are the employee rights under the {label}?",
        f"What are the employer obligations under the {label}?",
        f"Who owns the {label} at Arvind?",
        f"Can the {label} be waived in exceptional circumstances?",
        f"What exceptions exist under the {label}?",
        f"How do I get more information about the {label}?",
        f"What is not covered by the {label}?",
        f"Who should I contact regarding the {label}?",
        f"What changed in the latest version of the {label}?",
        f"Is the {label} applicable to contractual employees?",
        f"Are there any exclusions under the {label}?",
        f"What documents are required under the {label}?",
        f"How long does the process take under the {label}?",
        f"What is the timeline defined in the {label}?",
    ]


def _hindi_variants(short: str, label: str) -> list[str]:
    """Hindi-English hybrid question variants."""
    _BASE = {
        "wb":    [
            "Whistleblower policy mein report kaise karein?",
            "Mera identity safe hai kya agar main complaint karun?",
            "Ethics helpline ka number kya hai?",
        ],
        "posh":  [
            "Sexual harassment ki complaint kaise karein?",
            "POSH policy mein inquiry kitne din mein hoti hai?",
            "Anti harassment committee mein kaun hote hain?",
        ],
        "grv":   [
            "Grievance kaise raise karein?",
            "Meri complaint ka resolution kab hoga?",
            "Grievance escalation process kya hai?",
        ],
        "dt":    [
            "Business trip ke liye hotel booking kaise karein?",
            "Mera travel claim kab submit karna hoga?",
            "Daily allowance kitna milega outstation trip mein?",
        ],
        "fnf":   [
            "FnF settlement mein kitna time lagta hai?",
            "Notice period nahi diya toh kya deduction hoga?",
            "FnF mein earned leave ka paise kaise milega?",
        ],
        "exp":   [
            "Expense reimbursement ke liye kya documents chahiye?",
            "Claim submit karne ki deadline kya hai?",
            "Expense approve kaun karta hai?",
        ],
        "ghi":   [
            "Mera health insurance cover kitna hai?",
            "Cashless claim kaise karein hospital mein?",
            "Parents covered hain kya GHI mein?",
        ],
        "gpa":   [
            "Accident hone par insurance claim kaise karein?",
            "Permanent disability ka compensation kitna milega?",
            "GPA cover ke baare mein batao?",
        ],
        "gtl":   [
            "GTL mein family ko kitna milega meri death ke baad?",
            "Life insurance nominee kaise change karein?",
            "GTL premium kaun pay karta hai — employee ya company?",
        ],
        "vdc":   [
            "VDC scheme kya hai?",
            "Employee ki death hone par VDC ka kya process hai?",
            "VDC mein contribute karna mandatory hai kya?",
        ],
        "pankh": [
            "Pankh referral bonus kab milega?",
            "Female candidate refer karne par kitna milega?",
            "Pankh scheme mein transgender referral eligible hai kya?",
        ],
        "lc":    [
            "Personal vehicle ke liye per km kitna milega?",
            "Ola Uber ka claim ho sakta hai kya?",
            "Monthly local conveyance limit kya hai?",
        ],
        "tm":    [
            "Internal job transfer ke liye kaise apply karein?",
            "Manager mujhe rok sakta hai kya mobility se?",
            "IJP mein minimum tenure kitna chahiye?",
        ],
        "mb":    [
            "MediBuddy app pe register kaise karein?",
            "MediBuddy Gold free hai kya Arvind employees ke liye?",
            "Online doctor consultation kaise book karein?",
        ],
        "ts":    [
            "Travel settlement kaise submit karein MyTour pe?",
            "15 din ke baad kya hoga agar claim nahi kiya?",
            "Travel bills attach karne ka process kya hai?",
        ],
        "eap":   [
            "EAP helpline ka number kya hai?",
            "Kya EAP confidential hai — manager ko pata chalega kya?",
            "Family bhi EAP use kar sakti hai kya?",
        ],
        "jn":    [
            "Joining ke time relocation allowance kaise milega?",
            "Naye city mein shift hone par brokerage milega kya?",
            "Joining benefits ke liye kya documents chahiye?",
        ],
        "gen":   [
            "Gender discrimination hone par kaise report karein?",
            "LGBTQ employees ke liye koi protection hai kya Arvind mein?",
            "Gender policy ke under disciplinary action kya hota hai?",
        ],
    }
    return _BASE.get(short, [])


def _seeds(short: str, label: str) -> list[str]:
    """Expanded handcrafted seed questions (20-25 per policy)."""
    SEEDS = {
        "wb": [
            "What is the purpose of the Whistleblower Policy?",
            "Who can file a protected disclosure?",
            "How is confidentiality maintained for a whistleblower?",
            "What happens if a whistleblower is retaliated against?",
            "What channels are available to report a disclosure?",
            "What is the ethics helpline number?",
            "Can I report misconduct anonymously?",
            "What constitutes a protected disclosure?",
            "Who investigates whistleblower complaints?",
            "What is the timeline for investigating a disclosure?",
            "Can a whistleblower withdraw their complaint?",
            "What protection does the policy offer to the whistleblower?",
            "What happens after I submit a whistleblower complaint?",
            "Is the whistleblower's identity ever revealed?",
            "Who is responsible for reviewing disclosures?",
            "What actions can be taken against a wrongdoer?",
            "What types of misconduct can be reported?",
            "Can I report an unethical act by a senior manager?",
            "What is the role of the ombudsperson in this policy?",
            "How do I access the ethics reporting portal?",
            "Can non-employees use the whistleblower channel?",
            "What happens if a complaint is found to be false?",
        ],
        "posh": [
            "What constitutes sexual harassment under POSH?",
            "How do I file a POSH complaint?",
            "What is the role of the Anti Harassment Committee?",
            "What is the inquiry timeline under POSH?",
            "What disciplinary action follows a POSH complaint?",
            "Who can file a complaint under POSH?",
            "What is the definition of sexual harassment?",
            "Can a male employee file a POSH complaint?",
            "What is the composition of the Internal Complaints Committee?",
            "What evidence is needed for a POSH complaint?",
            "How long does the POSH investigation last?",
            "Can I file a POSH complaint against a contractor?",
            "What is the difference between quid pro quo and hostile work environment?",
            "What interim relief can be given during an inquiry?",
            "What happens if the accused is found guilty under POSH?",
            "Can a POSH complaint be filed after leaving the organisation?",
            "What is the role of the presiding officer in POSH?",
            "Is conciliation allowed in POSH cases?",
            "What are the rights of the respondent under POSH?",
            "What happens if the complaint is found to be malicious?",
            "What is the limitation period to file a POSH complaint?",
            "Does POSH apply to remote working situations?",
            "What protection is given to witnesses in a POSH inquiry?",
        ],
        "grv": [
            "How do I raise a workplace grievance at Arvind?",
            "What are the escalation levels in the grievance process?",
            "What is the timeline for resolving a grievance?",
            "Who handles the first level of grievance resolution?",
            "Can a grievance be submitted anonymously?",
            "What types of issues can be raised as a grievance?",
            "What is the role of the grievance officer?",
            "How long does Arvind take to respond to a grievance?",
            "Can I raise a grievance about pay discrepancy?",
            "What happens if my grievance is not resolved?",
            "Who handles a grievance if it involves my direct manager?",
            "Is there a written record of all grievances?",
            "What is the final escalation step in the grievance process?",
            "Can I involve a union representative in my grievance?",
            "What is the policy on non-retaliation for raising grievances?",
            "Can I raise a grievance about workplace bullying?",
            "What evidence should I provide with my grievance?",
            "Is there a grievance appeal process?",
            "Can HR dismiss a grievance without investigation?",
            "What is the difference between a grievance and a POSH complaint?",
        ],
        "gen": [
            "What is the Gender Policy about?",
            "How can an employee report gender discrimination?",
            "Are LGBTQ employees protected under the Gender Policy?",
            "What disciplinary action is taken for gender-based harassment?",
            "How often is the Gender Policy reviewed?",
            "What is the definition of gender discrimination under this policy?",
            "Are transgender employees protected?",
            "What is the gender sensitisation programme at Arvind?",
            "What does the policy say about equal pay?",
            "Who can an employee contact for gender-related issues?",
            "Does the policy cover sexual orientation-based discrimination?",
            "What training is provided under the gender policy?",
            "What is the scope of the gender policy?",
            "Can a contractor raise a gender discrimination complaint?",
            "What are the key provisions of the gender policy?",
            "What is the timeline for addressing a gender discrimination complaint?",
            "Does the gender policy overlap with POSH?",
            "What is meant by inclusive workplace under this policy?",
        ],
        "dt": [
            "What is the process for booking domestic air travel?",
            "What are the hotel limits for M2 grade employees?",
            "What class of travel is an E2 grade employee entitled to?",
            "What is the deadline to submit travel claims?",
            "Are taxi expenses covered under domestic travel?",
            "How do I book a flight on MyBiz?",
            "What is the daily allowance for domestic travel?",
            "What grade determines my travel entitlement?",
            "Can I upgrade my travel class?",
            "What is the hotel per night limit for tier-1 cities?",
            "Are tips reimbursable under domestic travel?",
            "Can I travel by train instead of air?",
            "What is the process for emergency travel booking?",
            "What receipts are required for domestic travel claims?",
            "Is personal travel combined with business travel reimbursable?",
            "What happens if hotel bill exceeds the limit?",
            "Can I stay with a friend and claim a lower amount?",
            "What is the baggage allowance for domestic travel?",
            "Can I claim a cab from home to airport?",
            "Is travel insurance provided for domestic trips?",
            "What is the approval process for domestic travel?",
            "Who approves domestic travel expenses?",
            "What is the cancellation policy for booked tickets?",
            "How do I claim travel expenses incurred in cash?",
        ],
        "jn": [
            "What relocation benefits does Arvind provide to new joiners?",
            "Is brokerage reimbursed for renting accommodation while joining?",
            "What household goods transportation support is provided?",
            "How long does a new joiner have to claim relocation benefits?",
            "What documents are needed to claim joining benefits?",
            "What is the joining allowance amount?",
            "Is packing and unpacking expense covered?",
            "Are school admission fees covered for relocated children?",
            "What is the maximum relocation reimbursement?",
            "Can I claim relocation if I join from the same city?",
            "What is the joining benefit for a senior management employee?",
            "Is there a temporary accommodation allowance while joining?",
            "How many days of joining leave are allowed?",
            "What is the deadline to submit joining expenses?",
            "Can I claim both brokerage and moving expenses?",
            "What grade determines the joining benefits?",
            "Who approves the joining benefits claim?",
            "Is the joining benefit taxable?",
            "Are travel expenses for a pre-joining visit covered?",
            "What happens to joining benefits if I resign early?",
        ],
        "fnf": [
            "What is included in the Full and Final Settlement?",
            "How many days does Arvind take to process FnF?",
            "What is recovered from FnF if notice period is not served?",
            "How are earned leaves encashed during FnF?",
            "What components are deducted in notice pay recovery?",
            "When is the FnF payment transferred?",
            "What is the no-dues clearance process?",
            "What documents are required for FnF processing?",
            "Is gratuity included in FnF?",
            "How is the notice period shortage calculated?",
            "Can FnF be settled before the last working day?",
            "What is the process for PF withdrawal during FnF?",
            "How is ex-gratia calculated in FnF?",
            "What happens to variable pay in FnF?",
            "Can FnF be disputed if I disagree with the amount?",
            "Who processes the FnF at Arvind?",
            "Is there interest on delayed FnF?",
            "What is included in the relieving letter timeline?",
            "How long must I wait for the experience letter after FnF?",
            "What deductions are made for company assets not returned?",
        ],
        "exp": [
            "What types of expenses can I claim for reimbursement?",
            "What is the deadline for submitting an expense claim?",
            "Who approves expense reimbursement at Arvind?",
            "Are entertainment expenses covered under this policy?",
            "What receipts are needed for expense claims?",
            "What is the limit for meal reimbursement?",
            "Can I claim team outing expenses?",
            "Are client entertainment expenses reimbursable?",
            "What is the reimbursement process for birthday expenses?",
            "Are farewell party expenses covered?",
            "Is there a limit on the number of people for reimbursable events?",
            "Can I claim for flowers or gifts for colleagues?",
            "What is the process to submit an expense claim on the portal?",
            "How long does reimbursement take after approval?",
            "What expenses are explicitly excluded from reimbursement?",
            "Can I claim fuel expenses for customer visits?",
            "What is the policy on advance payment for expenses?",
            "Who can I escalate a rejected expense claim to?",
            "Are conference registration fees reimbursable?",
            "What happens if I miss the submission deadline?",
        ],
        "lc": [
            "What is the rate per km for a personal two-wheeler?",
            "Is home-to-office commute reimbursable under local conveyance?",
            "What is the monthly cap on local conveyance claims?",
            "Are OLA or UBER rides covered under local conveyance?",
            "How do I submit a local conveyance claim?",
            "What is the per km rate for a four-wheeler?",
            "Is local conveyance claimable for client visits?",
            "What grades are eligible for local conveyance reimbursement?",
            "Are auto-rickshaw fares reimbursable?",
            "What proof is required for local conveyance claims?",
            "Can I claim local conveyance for weekend work?",
            "Is there a cap on individual trip reimbursement?",
            "How often can I submit a local conveyance claim?",
            "Is metro card reimbursable under local conveyance?",
            "What is the approval workflow for local conveyance?",
            "Are tolls covered under local conveyance?",
            "Can I claim local conveyance for team lunch?",
            "What is the deadline to submit local conveyance claims?",
        ],
        "ghi": [
            "What is the sum insured under Group Health Insurance?",
            "Are pre-existing diseases covered under the health policy?",
            "What is the room rent limit for hospitalization?",
            "How do I file a cashless health insurance claim?",
            "What is the FHPL helpline number?",
            "Are my parents covered under the company health insurance?",
            "How do I add my newborn child to the health policy?",
            "What is the sub-limit for maternity expenses?",
            "Is day-care surgery covered under GHI?",
            "What is the copay percentage under this policy?",
            "Are dental treatments covered under GHI?",
            "How do I find a network hospital for cashless treatment?",
            "What is the reimbursement timeline for GHI claims?",
            "Are ayurvedic treatments covered under GHI?",
            "Is mental health treatment covered under GHI?",
            "What is the process for a reimbursement claim (non-cashless)?",
            "Can I upgrade my health insurance coverage?",
            "What documents are required for a health insurance claim?",
            "Is ambulance charge covered under GHI?",
            "What happens to my health insurance when I resign?",
            "Is diagnostic test coverage included under GHI?",
            "What is the waiting period for maternity coverage?",
            "Are spectacles covered under the health insurance?",
        ],
        "gpa": [
            "What does the Group Personal Accident Insurance cover?",
            "What is the compensation for permanent total disability?",
            "Is accidental death covered under GPA?",
            "What percentage is paid for partial disability?",
            "Does GPA cover accidents outside working hours?",
            "What is the claim process for GPA?",
            "How do I file a personal accident insurance claim?",
            "What is the sum insured under GPA?",
            "Is loss of limb covered under GPA?",
            "What is the compensation for temporary total disability?",
            "Does GPA cover occupational diseases?",
            "What documents are required for a GPA claim?",
            "Is the accident covered if it happens during travel?",
            "What is the waiting period for a GPA claim?",
            "Can the nominee file a GPA claim on behalf of the employee?",
            "What is excluded from GPA coverage?",
            "How long is the GPA claim settlement timeline?",
            "Is psychiatric treatment covered under GPA?",
        ],
        "gtl": [
            "What is the sum insured under Group Term Life Insurance?",
            "How is the GTL death benefit calculated?",
            "How do I nominate a beneficiary under GTL?",
            "What documents are needed to file a GTL claim?",
            "Is the GTL premium paid by the employee or Arvind?",
            "What is the coverage amount for my grade?",
            "Can I nominate multiple beneficiaries under GTL?",
            "What happens to GTL when I leave Arvind?",
            "Is suicide covered under GTL?",
            "What is the claim filing timeline after death?",
            "Are accidental deaths covered under GTL?",
            "Who is the insurance provider for GTL at Arvind?",
            "How do I change my GTL nominee?",
            "Is the GTL benefit taxable?",
            "What is the grace period for GTL coverage?",
            "Does GTL cover natural death?",
            "What is the process to get my GTL certificate?",
        ],
        "vdc": [
            "What is the Voluntary Death Contribution scheme?",
            "How much do employees contribute under VDC?",
            "Who receives VDC benefits?",
            "Is VDC contribution compulsory for all employees?",
            "Can an employee opt out of the VDC scheme?",
            "What is the amount collected when a colleague passes away?",
            "How is the VDC amount disbursed to the family?",
            "Who is the administrator of the VDC fund?",
            "What is the timeline for VDC payout?",
            "Is the VDC amount fixed or variable?",
            "What documents are needed to claim VDC?",
            "Can a probationary employee participate in VDC?",
            "What happens to VDC if an employee leaves?",
            "How is the VDC contribution collected from employees?",
            "Is the VDC contribution tax deductible?",
            "What if the employee has no family to receive VDC?",
        ],
        "pankh": [
            "What is the Pankh Employee Referral Programme?",
            "What is the referral bonus for referring a female candidate?",
            "How many tranches is the Pankh bonus paid in?",
            "Are transgender referrals eligible for bonus under Pankh?",
            "What is the referral bonus for a male candidate?",
            "How do I refer a candidate through Pankh?",
            "What roles are eligible for the Pankh referral bonus?",
            "What is the cooling-off period for Pankh referrals?",
            "Can I refer a former colleague under Pankh?",
            "What happens if the referred candidate leaves early?",
            "Is the Pankh bonus taxable?",
            "Can I refer a family member under Pankh?",
            "What is the timeline for the Pankh bonus payment?",
            "How do I track my Pankh referral status?",
            "Who is not eligible to make referrals under Pankh?",
            "What is the maximum referral bonus under Pankh?",
        ],
        "tm": [
            "What is the Talent Mobility Policy?",
            "What is the minimum tenure to apply for an internal job posting?",
            "Can a manager block an employee's mobility application?",
            "Who approves exceptions to the Talent Mobility Policy?",
            "What is the mobility adjustment amount?",
            "How do I apply for an IJP at Arvind?",
            "What is the internal transfer process?",
            "Is there a cooling-off period after an internal transfer?",
            "What is the role of HR in talent mobility?",
            "Can an employee apply for a higher grade internally?",
            "What happens if I am not selected in an IJP?",
            "How many times can I apply for IJPs in a year?",
            "Is a talent mobility transfer considered a promotion?",
            "What documentation is required for an IJP application?",
            "What is the compensation change during a lateral transfer?",
            "Can I transfer to a different business vertical?",
            "Is there a bond period after an internal transfer?",
        ],
        "mb": [
            "What is MediBuddy Gold?",
            "Who is covered under MediBuddy Gold?",
            "How do I register on the MediBuddy app?",
            "Is MediBuddy Gold free for Arvind employees?",
            "What is the MediBuddy customer care number?",
            "How do I book a teleconsultation on MediBuddy?",
            "Can I book a diagnostic test through MediBuddy?",
            "What services are available on the MediBuddy platform?",
            "How do I order medicines through MediBuddy?",
            "Is MediBuddy available 24/7?",
            "Can my family members use MediBuddy Gold?",
            "How do I escalate an issue with MediBuddy?",
            "Is MediBuddy app available on iOS?",
            "What specialties are available for online consultation?",
            "How do I use MediBuddy for a second opinion?",
            "What is the discount offered through MediBuddy Gold?",
        ],
        "ts": [
            "What is the deadline to submit travel expense claims?",
            "How do I submit expenses on the MyTour Dashboard?",
            "What happens if I miss the 15-day expense submission deadline?",
            "What is the auto-settlement policy on day 16?",
            "What documents are required for travel settlement?",
            "How do I attach hotel bills in the MyTour system?",
            "What is the process to file a travel advance?",
            "Can I submit travel expenses after auto-settlement?",
            "What is the process to dispute a travel settlement?",
            "What expenses need original receipts?",
            "What happens to the travel advance if not used?",
            "How do I track the status of my travel claim?",
            "Who approves the final travel settlement?",
            "What is the excess amount recovery process?",
            "Can I edit a submitted travel claim?",
            "How do I submit expenses for a cancelled trip?",
            "What is the timeline for travel reimbursement?",
            "Are tips and porterage expenses reimbursable?",
        ],
        "eap": [
            "What is the Employee Assistance Program at Arvind?",
            "Is the EAP service free and confidential?",
            "How do I contact the 1to1 EAP helpline?",
            "Can family members use the EAP?",
            "Does using EAP get reported to my manager?",
            "What services are available under the EAP?",
            "Is EAP available 24/7?",
            "How many counselling sessions are free under EAP?",
            "Can I use EAP for financial counselling?",
            "Is face-to-face counselling available under EAP?",
            "Can I use EAP for legal advice?",
            "What mental health services are available through EAP?",
            "How do I access EAP services?",
            "Is the EAP provider 1to1 Help?",
            "What is the EAP helpline number?",
            "Can I use EAP for work-life balance coaching?",
            "Is EAP usage tracked by HR?",
            "Who is eligible for EAP services?",
        ],
    }
    return SEEDS.get(short, [f"What is the {label} about?"])


def _deduplicate(questions: list[str], limit: int) -> list[str]:
    kept, seen_tokens = [], []
    for q in questions:
        if not q or len(q) < 15:
            continue
        tokens    = set(q.lower().split())
        is_dup    = any(
            len(tokens & s) / max(len(tokens | s), 1) > DEDUP_THRESHOLD
            for s in seen_tokens
        )
        if not is_dup:
            kept.append(q)
            seen_tokens.append(tokens)
        if len(kept) >= limit:
            break
    return kept


def load_chunks(collection: str) -> list[dict]:
    path = os.path.join(VECTORSTORE_DIR, f'{collection}_chunks.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ── Evaluation ────────────────────────────────────────────────────────────────

def eval_question(short: str, question: str, expected_label: str, is_oos: bool) -> dict:
    import importlib
    from router import detect_policy, POLICY_REGISTRY

    detected         = detect_policy(question)
    routed_correctly = (detected == expected_label)

    chunks = []
    try:
        mod    = importlib.import_module(f"policies.{POLICY_MAP[short][2]}.retriever")
        retr   = getattr(mod, '_retriever')
        chunks = retr.retrieve(question)
    except Exception:
        pass
    context_text = " ".join(c['text'] for c in chunks[:3])
    has_chunks   = len(chunks) > 0 and len(context_text.strip()) > 50

    q_lo = question.lower()
    best_count = 0
    for keywords, _, _ in POLICY_REGISTRY:
        cnt = sum(1 for kw in keywords if kw in q_lo)
        best_count = max(best_count, cnt)
    router_matched = best_count >= 1

    sem = 0.0
    if has_chunks and chunks:
        try:
            sims = batch_cosine([question], [chunks[0]['text']])
            sem  = max(0.0, sims[0])
        except Exception:
            pass

    if is_oos:
        correct  = not router_matched
        answered = router_matched
    else:
        correct  = routed_correctly and has_chunks
        answered = has_chunks

    return {
        "question":         question,
        "is_oos":           is_oos,
        "routed_correctly": routed_correctly,
        "router_matched":   router_matched,
        "has_chunks":       has_chunks,
        "answered":         answered,
        "correct":          correct,
        "semantic_score":   round(sem, 3),
        "chunks_retrieved": len(chunks),
    }


def eval_policy_large(short: str) -> dict:
    collection, label, _ = POLICY_MAP[short]
    chunks = load_chunks(collection)

    in_scope, oos = generate_1000_questions(short, chunks, label)
    all_q         = [(q, False) for q in in_scope] + [(q, True) for q in oos]
    total         = len(all_q)

    print(f"\n  ── {label}  ({len(in_scope)} in-scope + {len(oos)} OOS = {total} total) ──", flush=True)

    rows = []
    for i, (q, is_oos) in enumerate(all_q, 1):
        row = eval_question(short, q, label, is_oos)
        rows.append(row)
        if i % 100 == 0 or i == total:
            print(f"    [{i:04d}/{total}]...", flush=True)

    in_rows  = [r for r in rows if not r["is_oos"]]
    oos_rows = [r for r in rows if r["is_oos"]]

    routing_acc = sum(r["routed_correctly"] for r in rows)          / max(len(rows), 1)
    retrieval   = sum(r["has_chunks"]       for r in in_rows)       / max(len(in_rows), 1)
    oos_reject  = sum(not r["router_matched"] for r in oos_rows)    / max(len(oos_rows), 1)
    sem_avg     = sum(r["semantic_score"]   for r in in_rows)       / max(len(in_rows), 1)
    overall     = routing_acc * 0.30 + retrieval * 0.30 + oos_reject * 0.20 + sem_avg * 0.20

    return {
        "policy":           label,
        "short":            short,
        "n_total":          len(rows),
        "n_in_scope":       len(in_rows),
        "n_oos":            len(oos_rows),
        "routing_accuracy": round(routing_acc, 3),
        "retrieval_hit":    round(retrieval,   3),
        "oos_rejection":    round(oos_reject,  3),
        "semantic_score":   round(sem_avg,     3),
        "overall":          round(overall,     3),
    }


# ── Report ────────────────────────────────────────────────────────────────────

def _grade(s):
    if s >= 0.90: return "A+"
    if s >= 0.85: return "A"
    if s >= 0.80: return "B+"
    if s >= 0.75: return "B"
    if s >= 0.65: return "C"
    return "D"

def print_report(results: list[dict]):
    n_q = sum(r["n_total"] for r in results)
    print(f"\n{'='*100}")
    print(f"  ARVIN — Large-Scale Accuracy Report  ({len(results)} policies, {n_q} questions total)")
    print(f"  Routing%(30%) | Retrieved Chunks%(30%) | Off-Topic Rejection%(20%) | Answer Relevance Score(20%)")
    print(f"{'='*100}")
    print(f"  {'Policy':<42} {'Qs':>5} {'Routed':>7} {'Retrieved':>10} {'Off-Topic':>10} {'Relevance':>10} {'Score':>7}  Grade")
    print(f"  {'─'*42} {'─'*5} {'─'*7} {'─'*10} {'─'*10} {'─'*10} {'─'*7}  {'─'*5}")

    for r in results:
        flag = "✓" if r["overall"] >= 0.75 else ("△" if r["overall"] >= 0.60 else "✗")
        print(
            f"  {flag} {r['policy']:<41} {r['n_total']:>5}"
            f" {r['routing_accuracy']:>7.0%}"
            f" {r['retrieval_hit']:>10.0%}"
            f" {r['oos_rejection']:>10.0%}"
            f" {r['semantic_score']:>10.2f}"
            f" {r['overall']:>7.3f}"
            f"  {_grade(r['overall'])}"
        )

    if results:
        ar  = sum(r["routing_accuracy"] for r in results) / len(results)
        ah  = sum(r["retrieval_hit"]    for r in results) / len(results)
        ao  = sum(r["oos_rejection"]    for r in results) / len(results)
        as_ = sum(r["semantic_score"]   for r in results) / len(results)
        avg = sum(r["overall"]          for r in results) / len(results)
        nt  = sum(r["n_total"]          for r in results)
        print(f"  {'─'*42} {'─'*5} {'─'*7} {'─'*10} {'─'*10} {'─'*10} {'─'*7}  {'─'*5}")
        print(
            f"  {'AVERAGE':<42} {nt:>5}"
            f" {ar:>7.0%} {ah:>10.0%} {ao:>10.0%}"
            f" {as_:>10.2f} {avg:>7.3f}  {_grade(avg)}"
        )

    out = os.path.join(EVAL_DIR, "large_scale_accuracy_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Full report saved → {out}")

    weak = sorted([r for r in results if r["overall"] < 0.75], key=lambda x: x["overall"])
    if weak:
        print(f"\n  ── Policies to boost ────────────────────────────────────────────")
        for r in weak:
            issues = []
            if r["routing_accuracy"] < 0.50: issues.append(f"routing {r['routing_accuracy']:.0%}")
            if r["retrieval_hit"]    < 0.90: issues.append(f"retrieval {r['retrieval_hit']:.0%}")
            if r["oos_rejection"]    < 0.80: issues.append(f"OOS {r['oos_rejection']:.0%}")
            if r["semantic_score"]   < 0.40: issues.append(f"relevance {r['semantic_score']:.2f}")
            if issues:
                print(f"  ✗ {r['policy']}")
                for issue in issues:
                    print(f"      → {issue}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="all")
    args = parser.parse_args()

    policies = list(POLICY_MAP.keys()) if args.policy == "all" else [args.policy]
    est = sum(TARGET_PER_POLICY + 50 for _ in policies)

    print(f"\n{'='*84}")
    print(f"  ARVIN — Large-Scale Eval  ({len(policies)} policies, ~{est} questions)")
    print(f"  Target: {TARGET_PER_POLICY} in-scope + 50 OOS per policy  |  Dedup threshold: {DEDUP_THRESHOLD}")
    print(f"  Zero LLM calls — routing + retrieval + ONNX similarity only")
    print(f"{'='*84}")

    results = []
    for short in policies:
        result = eval_policy_large(short)
        results.append(result)
        interim = os.path.join(EVAL_DIR, f"{short}_large_result.json")
        with open(interim, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    if results:
        print_report(results)


if __name__ == "__main__":
    main()
