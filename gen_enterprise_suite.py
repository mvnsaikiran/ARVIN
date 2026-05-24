#!/usr/bin/env python3
"""
Enterprise HR Policy Test Suite Generator
Generates ~7000 test cases for RAG chatbot evaluation.
"""

import json
import re
import os
import itertools
import pdfplumber
from docx import Document

# ─────────────────────────────────────────────────────────────────────────────
# NORMALISATION (must match what the RAG pipeline uses for keyFact checks)
# ─────────────────────────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    """Strip Rs./₹/-/, commas, parenthetical words, hyphens→space, slash→'or'."""
    t = text
    t = re.sub(r'Rs\.?\s*', '', t)          # remove Rs.
    t = re.sub(r'₹\s*', '', t)              # remove ₹
    t = re.sub(r'/-', '', t)                # remove /-
    t = re.sub(r',', '', t)                 # remove commas
    t = re.sub(r'\([^)]*\)', '', t)         # remove parenthetical words
    t = re.sub(r'-', ' ', t)                # hyphens → space
    t = re.sub(r'/', ' or ', t)             # slash → "or"
    t = re.sub(r'\s+', ' ', t).strip()      # collapse whitespace
    return t.lower()


# ─────────────────────────────────────────────────────────────────────────────
# CORPUS EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

POLICY_DIR = '/home/user/ARVIN/policies'

def extract_corpus():
    """Extract all text from policy files and return normalised corpus dict."""
    corpus = {}
    files = {
        'Local Conveyance Policy': 'cf8daeee-localconveyancepolicyarvindlimited.pdf',
        'Domestic Travel Policy': 'f34aa66a-domestictravelpolicyarvindlimited.pdf',
        'Grievance Mechanism Policy': 'e08407da-arvindgrievancemechanismpolicy2025.pdf',
        'POSH Policy': '4d8fe661-poshpolicyarvindlimited.pdf',
        'Whistleblower Policy': 'cbdae693-whistleblowerpolicyarvindlimited.pdf',
        'Gender Policy': '99ecde3a-arvindgenderpolicy2025.pdf',
        'Talent Mobility Policy': 'adea8313-talentmobility.pdf',
        'Joining Policy': 'bad821d9-joiningpolicyarvindlimited.docx',
    }
    for policy_name, filename in files.items():
        path = os.path.join(POLICY_DIR, filename)
        raw_text = ''
        if filename.endswith('.pdf'):
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            raw_text += t + '\n'
            except Exception as e:
                print(f"  Warning: could not read {filename}: {e}")
        elif filename.endswith('.docx'):
            try:
                doc = Document(path)
                for para in doc.paragraphs:
                    raw_text += para.text + '\n'
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            raw_text += cell.text + '\n'
            except Exception as e:
                print(f"  Warning: could not read {filename}: {e}")
        corpus[policy_name] = normalise(raw_text)
    return corpus


# ─────────────────────────────────────────────────────────────────────────────
# FACT DEFINITIONS
# Format: (keyFact_string, source_policy, page, category)
# ─────────────────────────────────────────────────────────────────────────────

FACTS = [
    # ── LOCAL CONVEYANCE POLICY ──────────────────────────────────────────────
    ("four wheeler @ Rs. 10.00 / - per km", "Local Conveyance Policy", 1, "Conveyance Rates"),
    ("two wheeler @ Rs. 5.00 per km", "Local Conveyance Policy", 1, "Conveyance Rates"),
    ("reimbursement will be done on actuals", "Local Conveyance Policy", 1, "Conveyance Rates"),
    ("Orapps – ESMS – Entry – Conveyance Expense", "Local Conveyance Policy", 1, "Claim Process"),
    ("applicable across all grades", "Local Conveyance Policy", 1, "Applicability"),
    ("applicable across India", "Local Conveyance Policy", 1, "Applicability"),
    ("approved only by BM grade employees", "Local Conveyance Policy", 1, "Approval"),
    ("strict disciplinary action shall be taken", "Local Conveyance Policy", 2, "Compliance"),
    ("outside the respective City/Town Municipal Corporation", "Local Conveyance Policy", 1, "Eligibility"),
    ("individual who has actually incurred the cost", "Local Conveyance Policy", 1, "Reimbursement Rules"),
    ("Applicable to all Management / staff cadre of Arvind Ltd", "Local Conveyance Policy", 1, "Applicability"),
    ("01.07.2022", "Local Conveyance Policy", 1, "Policy Details"),

    # ── DOMESTIC TRAVEL POLICY ───────────────────────────────────────────────
    # Mode of Travel
    ("1st AC", "Domestic Travel Policy", 7, "Mode of Travel"),
    ("Premium Economy / Business", "Domestic Travel Policy", 7, "Mode of Travel"),
    ("Economy / Premium Economy", "Domestic Travel Policy", 7, "Mode of Travel"),
    ("2nd AC", "Domestic Travel Policy", 7, "Mode of Travel"),
    ("3rd AC/Chair Car", "Domestic Travel Policy", 7, "Mode of Travel"),
    ("3rd AC/Chair Car", "Domestic Travel Policy", 7, "Mode of Travel"),

    # Lodging
    ("At Actual", "Domestic Travel Policy", 7, "Lodging"),
    ("8000", "Domestic Travel Policy", 7, "Lodging"),
    ("6000", "Domestic Travel Policy", 7, "Lodging"),
    ("5000", "Domestic Travel Policy", 7, "Lodging"),
    ("3400", "Domestic Travel Policy", 7, "Lodging"),
    ("2300", "Domestic Travel Policy", 7, "Lodging"),
    ("1700", "Domestic Travel Policy", 7, "Lodging"),
    ("4000", "Domestic Travel Policy", 7, "Lodging"),

    # Boarding
    ("1500", "Domestic Travel Policy", 7, "Boarding"),
    ("1300", "Domestic Travel Policy", 7, "Boarding"),
    ("1000", "Domestic Travel Policy", 7, "Boarding"),
    ("1200", "Domestic Travel Policy", 7, "Boarding"),
    ("800", "Domestic Travel Policy", 7, "Boarding"),
    ("600", "Domestic Travel Policy", 7, "Boarding"),

    # Cab entitlements
    ("Ola / Uber / BluSmart", "Domestic Travel Policy", 8, "Cab Entitlement"),
    ("Bus, Metro, Local Transportation", "Domestic Travel Policy", 8, "Cab Entitlement"),

    # Non-reimbursable
    ("Express boarding", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Web Check-in amount", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Fees for VIP Clubs/Lounge", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Upgradation of seat/class at an added cost", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Health club services", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Amount incurred on personal entertainment/recreation", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Cost incurred on personal guests", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Airport parking tariff", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Personal Gifts", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Spouse/dependent travel", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Alcohol, cigarettes", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Usage of Mini-Bar", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Telephone expenses", "Domestic Travel Policy", 8, "Non-Reimbursable"),
    ("Business Outing without prior approval from CEO", "Domestic Travel Policy", 8, "Non-Reimbursable"),

    # Procedures
    ("at least 7 days in advance", "Domestic Travel Policy", 3, "Procedures"),
    ("myBiz", "Domestic Travel Policy", 2, "Booking Tool"),
    ("within 15 days of the trip", "Domestic Travel Policy", 5, "Settlement"),
    ("auto-settlement on the 16th day", "Domestic Travel Policy", 5, "Settlement"),
    ("duration of travel exceeds three days", "Domestic Travel Policy", 5, "Laundry"),
    ("not eligible to avail the accommodation", "Domestic Travel Policy", 3, "Same-Day Return"),
    ("domestic travel exceeding a distance of 300 km", "Domestic Travel Policy", 2, "Scope"),
    ("delayed by more than 3 hours", "Domestic Travel Policy", 4, "Flight Delay"),
    ("senior officials travelling to the same destination on the same day take separate flights", "Domestic Travel Policy", 3, "Travel Guidelines"),
    ("hotel limits of the next higher grade", "Domestic Travel Policy", 4, "Women Policy"),
    ("avoid staying in service apartments", "Domestic Travel Policy", 4, "Women Policy"),
    ("Avoidance of Night Travel", "Domestic Travel Policy", 4, "Women Policy"),
    ("30% of the entitlement", "Domestic Travel Policy", 5, "Flat Rate"),
    ("Rs. 6,000 per day", "Domestic Travel Policy", 5, "Flat Rate"),
    ("travel to three or more locations on a given day", "Domestic Travel Policy", 5, "Cab Policy"),
    ("inclusive of applicable taxes", "Domestic Travel Policy", 7, "Lodging"),
    ("27.07.2023", "Domestic Travel Policy", 1, "Policy Details"),
    ("ARV | EOP_DTP | 003 | 270723", "Domestic Travel Policy", 1, "Policy Details"),

    # ── GRIEVANCE MECHANISM POLICY ───────────────────────────────────────────
    ("2 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("10 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("15 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("1800 200 8301", "Grievance Mechanism Policy", 3, "Contact"),
    ("arvind@ethicshelpline.in", "Grievance Mechanism Policy", 3, "Contact"),
    ("www.in.kpmg.com/ethicshelpline/arvind", "Grievance Mechanism Policy", 3, "Contact"),
    ("every two years", "Grievance Mechanism Policy", 4, "Review"),
    ("raised verbally or in writing", "Grievance Mechanism Policy", 3, "Filing"),
    ("Anonymous complaints will be considered", "Grievance Mechanism Policy", 3, "Anonymous"),
    ("protected from retaliation", "Grievance Mechanism Policy", 2, "Protection"),
    ("part-time", "Grievance Mechanism Policy", 2, "Applicability"),
    ("contract workers", "Grievance Mechanism Policy", 2, "Applicability"),
    ("trainees", "Grievance Mechanism Policy", 2, "Applicability"),
    ("ARV|COM_GRM|001|260725", "Grievance Mechanism Policy", 1, "Policy Details"),
    ("26.07.2025", "Grievance Mechanism Policy", 1, "Policy Details"),
    ("Immediate HR Representative", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("Line Manager or Supervisor", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("Head of Department", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("escalate the grievance to the next level", "Grievance Mechanism Policy", 3, "Escalation"),

    # ── POSH POLICY ──────────────────────────────────────────────────────────
    ("31.03.2022", "POSH Policy", 1, "Policy Details"),
    ("01.05.2025", "POSH Policy", 1, "Policy Details"),
    ("ARV|ELC_SHA|008|010422", "POSH Policy", 1, "Policy Details"),
    ("3 (three) months from the date of incident", "POSH Policy", 6, "Filing Deadline"),
    ("extended for further 3 (three) months", "POSH Policy", 6, "Filing Deadline"),
    ("10 (ten) working days", "POSH Policy", 7, "Timelines"),
    ("7 (seven) days", "POSH Policy", 6, "Timelines"),
    ("within a period of 10 (ten) days", "POSH Policy", 7, "AIC Report"),
    ("60 (sixty) days", "POSH Policy", 7, "Management Action"),
    ("Senior level woman employee", "POSH Policy", 4, "AIC Composition"),
    ("2 members amongst employees", "POSH Policy", 4, "AIC Composition"),
    ("period of three years", "POSH Policy", 5, "AIC Tenure"),
    ("re-nominated/re-elected for one additional term", "POSH Policy", 5, "AIC Tenure"),
    ("period of three years or completion of the age of 58 years", "POSH Policy", 5, "AIC Tenure"),
    ("minimum of 3 members", "POSH Policy", 4, "Quorum"),
    ("50% women representation", "POSH Policy", 4, "Quorum"),
    ("within 15 days", "POSH Policy", 4, "Vacancy"),
    ("Rs. 250 per day", "POSH Policy", 4, "External Member"),
    ("independent committee", "POSH Policy", 4, "AIC Nature"),
    ("powers as that of a civil court", "POSH Policy", 4, "AIC Powers"),
    ("six copies of the complaint", "POSH Policy", 6, "Filing"),
    ("not be allowed to bring in any legal practitioner", "POSH Policy", 6, "Legal Representation"),
    ("Anonymous complaints will not be entertained", "POSH Policy", 6, "Anonymous"),
    ("lodge a written complaint", "POSH Policy", 5, "Filing"),
    ("lodge her complaint in writing or via e- mail", "POSH Policy", 6, "Filing"),
    ("leave to the Aggrieved Woman up to a period of 3 (three) months", "POSH Policy", 7, "Interim Relief"),
    ("in addition to the entitled leaves", "POSH Policy", 7, "Interim Relief"),
    ("suspend the RE for defined period", "POSH Policy", 7, "Interim Action"),
    ("Written warning", "POSH Policy", 8, "Disciplinary Actions"),
    ("Written apology", "POSH Policy", 8, "Disciplinary Actions"),
    ("Reprimand/Censure", "POSH Policy", 8, "Disciplinary Actions"),
    ("Withholding of promotion", "POSH Policy", 8, "Disciplinary Actions"),
    ("Withholding of pay rise or increments", "POSH Policy", 8, "Disciplinary Actions"),
    ("Terminating the RE from service", "POSH Policy", 8, "Disciplinary Actions"),
    ("Undergoing a counselling session", "POSH Policy", 8, "Disciplinary Actions"),
    ("Carrying out community service", "POSH Policy", 8, "Disciplinary Actions"),
    ("Monetary compensation", "POSH Policy", 8, "Disciplinary Actions"),
    ("not be published, communicated or made known", "POSH Policy", 8, "Confidentiality"),
    ("disciplinary action will be taken", "POSH Policy", 8, "Confidentiality"),
    ("protected from any form of retaliation", "POSH Policy", 8, "Protection"),
    ("allegation was malicious", "POSH Policy", 8, "False Complaints"),
    ("18002008301", "POSH Policy", 5, "Contact"),
    ("arvind@ethicshelpline.in", "POSH Policy", 5, "Contact"),
    ("www.in.kpmg.com/ethicshelpline/arvind", "POSH Policy", 5, "Contact"),
    ("Supervisor / Reporting Manager", "POSH Policy", 5, "Filing Channels"),
    ("All persons employed at Arvind", "POSH Policy", 1, "Applicability"),
    ("Third parties and/or visitors", "POSH Policy", 1, "Applicability"),
    ("outside the workplace", "POSH Policy", 2, "Scope"),
    ("Office parties", "POSH Policy", 2, "Scope"),
    ("prohibits same-sex harassment", "POSH Policy", 5, "Scope"),
    ("gender neutral", "POSH Policy", 5, "Scope"),
    ("Arvind Internal Complaint Committee", "POSH Policy", 2, "AIC"),
    ("Her relative or friend", "POSH Policy", 5, "Who Can File"),
    ("written consent of her legal heir", "POSH Policy", 5, "Who Can File"),
    ("Her co-worker", "POSH Policy", 5, "Who Can File"),
    ("notice of 15 (fifteen) days", "POSH Policy", 6, "AIC Procedures"),

    # ── WHISTLEBLOWER POLICY ─────────────────────────────────────────────────
    ("18002008301", "Whistleblower Policy", 3, "Contact"),
    ("arvind@ethicshelpline.in", "Whistleblower Policy", 3, "Contact"),
    ("www.in.kpmg.com/ethicshelpline/arvind", "Whistleblower Policy", 3, "Contact"),
    ("Directors", "Whistleblower Policy", 3, "Applicability"),
    ("Employees", "Whistleblower Policy", 3, "Applicability"),
    ("Business Associates", "Whistleblower Policy", 3, "Applicability"),
    ("Breach of internal compliance requirements", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Non-compliance/breach of legal and regulatory requirements", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Bribery and corruption", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Procurement and tendering fraud", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Misappropriation/theft/embezzlement of company assets", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Corporate espionage and information disclosure", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Undue awarding of contracts", "Whistleblower Policy", 3, "Reportable Issues"),
    ("False invoicing", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Fraudulent financial accounting, auditing and reporting", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Employee negligence", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Health, safety, environment and security related", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Workplace harassment", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Discrimination and favouritism", "Whistleblower Policy", 3, "Reportable Issues"),
    ("quarterly", "Whistleblower Policy", 4, "Reporting Frequency"),
    ("four weeks after the submission", "Whistleblower Policy", 4, "Follow-up"),
    ("appoint an independent agency", "Whistleblower Policy", 4, "Investigation"),
    ("identity of the whistle blower shall be kept confidential", "Whistleblower Policy", 4, "Confidentiality"),
    ("no adverse personnel action, victimization, retaliation", "Whistleblower Policy", 5, "Protection"),
    ("lodge a written complaint to the Chairman", "Whistleblower Policy", 5, "Retaliation Recourse"),
    ("will not be protected by this Policy", "Whistleblower Policy", 5, "False Complaints"),
    ("duty to cooperate with investigations", "Whistleblower Policy", 4, "Responsibilities"),

    # ── GENDER POLICY 2025 ───────────────────────────────────────────────────
    ("25.07.2025", "Gender Policy", 1, "Policy Details"),
    ("26.07.2025", "Gender Policy", 1, "Policy Details"),
    ("ARV|COM_GENP|001|260725", "Gender Policy", 1, "Policy Details"),
    ("all employees of Arvind Ltd", "Gender Policy", 2, "Applicability"),
    ("interns", "Gender Policy", 2, "Applicability"),
    ("contract staff", "Gender Policy", 2, "Applicability"),
    ("third-party partners", "Gender Policy", 2, "Applicability"),
    ("HR Department", "Gender Policy", 3, "Complaint Process"),
    ("Line Manager", "Gender Policy", 3, "Complaint Process"),
    ("1800 200 8301", "Gender Policy", 3, "Contact"),
    ("every two years", "Gender Policy", 3, "Review"),
    ("retaliation against individuals who raise concerns in good faith is strictly prohibited", "Gender Policy", 3, "Protection"),
    ("arvind@ethicshelpline.in", "Gender Policy", 3, "Contact"),
    ("www.in.kpmg.com/ethicshelpline/arvind", "Gender Policy", 3, "Contact"),
    ("Hiring and Promotions are conducted based on merit", "Gender Policy", 3, "Principles"),

    # ── TALENT MOBILITY POLICY ───────────────────────────────────────────────
    ("3 years = trigger for rotation", "Talent Mobility Policy", 4, "Rotation Trigger"),
    ("All positions upto M2", "Talent Mobility Policy", 4, "IJP"),
    ("Managers cannot block mobility", "Talent Mobility Policy", 4, "Governance"),
    ("CHRO/CEO can approve exceptions", "Talent Mobility Policy", 4, "Exceptions"),
    ("1st Rotation – within the city", "Talent Mobility Policy", 4, "Rotation Framework"),
    ("2nd Rotation – across different business / different location", "Talent Mobility Policy", 4, "Rotation Framework"),
    ("merged with CTC on completion of 1 year", "Talent Mobility Policy", 6, "MAB Duration"),
    ("merged with CTC on completion of 1 year", "Talent Mobility Policy", 6, "MAB"),
    ("shifting house", "Talent Mobility Policy", 6, "SIA Condition"),
    ("relocation >20 kms", "Talent Mobility Policy", 7, "SIA Condition"),
    ("One time", "Talent Mobility Policy", 6, "SIA Type"),
    ("32,583", "Talent Mobility Policy", 7, "MAB - E1"),
    ("3,91,000", "Talent Mobility Policy", 7, "MAB - E1"),
    ("45,750", "Talent Mobility Policy", 7, "MAB - E2"),
    ("5,49,000", "Talent Mobility Policy", 7, "MAB - E2"),
    ("71,000", "Talent Mobility Policy", 7, "MAB - M1"),
    ("8,52,000", "Talent Mobility Policy", 7, "MAB - M1"),
    ("1,08,333", "Talent Mobility Policy", 7, "MAB - M2"),
    ("13,00,000", "Talent Mobility Policy", 7, "MAB - M2"),
    ("1,58,333", "Talent Mobility Policy", 7, "MAB - M3"),
    ("19,00,000", "Talent Mobility Policy", 7, "MAB - M3"),
    ("2,16,667", "Talent Mobility Policy", 7, "MAB - M3H1"),
    ("26,00,000", "Talent Mobility Policy", 7, "MAB - M3H1"),
    ("sensitive roles exceed tenure", "Talent Mobility Policy", 2, "Risk"),
    ("Monthly allowance", "Talent Mobility Policy", 6, "MAB Description"),
    ("One-time lump sum for household setup", "Talent Mobility Policy", 6, "SIA Description"),

    # SIA amounts
    ("10,000", "Talent Mobility Policy", 7, "SIA - E1/E2"),
    ("15,000", "Talent Mobility Policy", 7, "SIA - M1"),
    ("20,000", "Talent Mobility Policy", 7, "SIA - M2"),
    ("30,000", "Talent Mobility Policy", 7, "SIA - M3"),
    ("45,000", "Talent Mobility Policy", 7, "SIA - M3H1"),

    # ── JOINING POLICY ───────────────────────────────────────────────────────
    ("maximum period of 3 days", "Joining Policy", 1, "Pre-Joining Visit"),
    ("spouse", "Joining Policy", 1, "Pre-Joining Visit"),
    ("school admission", "Joining Policy", 1, "Pre-Joining Visit"),
    ("3 days leave", "Joining Policy", 1, "Post-Joining Visit"),
    ("Rs. 50 per km", "Joining Policy", 1, "Transportation"),
    ("Rs. 60 per km", "Joining Policy", 1, "Transportation"),
    ("Rs. 10.0 per km", "Joining Policy", 1, "Car Transport"),
    ("Rs. 600/-", "Joining Policy", 1, "Driver Wages"),
    ("Rs. 50/- per hour", "Joining Policy", 1, "Driver Wages"),
    ("Rs. 200/- per meal", "Joining Policy", 1, "Food Limit"),
    ("One month rent", "Joining Policy", 1, "Brokerage"),
    ("maximum for 1 year from the date of the joining", "Joining Policy", 1, "Brokerage Validity"),
    ("10 equal monthly instalments", "Joining Policy", 1, "House Deposit"),
    ("One Year from Date of Joining", "Joining Policy", 1, "Expense Claim Deadline"),
    ("recovered in his/her F&F settlement", "Joining Policy", 1, "Quit < 1 Year"),
    ("CEO", "Joining Policy", 1, "Approvals"),
    ("Arvind Travel Desk", "Joining Policy", 1, "Flight Booking"),
    ("Management / staff cadre employees", "Joining Policy", 1, "Applicability"),
    ("subsidiaries", "Joining Policy", 1, "Applicability"),
    ("Income tax shall be grossed up", "Joining Policy", 1, "Tax"),
    ("The company shall directly make payment", "Joining Policy", 1, "Packers & Movers"),
    ("21.09.2023", "Joining Policy", 1, "Policy Details"),
    ("either a Pre-Joining Visit OR Post Joining Visit", "Joining Policy", 1, "Visit Options"),
]


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

def gen_questions_for_fact(fact, source, category):
    """Generate 20-25 question variants for a given fact."""
    f = fact
    src = source.replace(" Policy", "").replace(" 2025", "")
    questions = []

    # ── 1. Direct questions ────────────────────────────────────────────────
    questions += [
        f"What is the {f}?",
        f"What does the policy say about {f}?",
        f"Tell me about {f}.",
        f"Can you explain {f}?",
        f"What is mentioned about {f} in the {source}?",
    ]

    # ── 2. Verification / eligibility ─────────────────────────────────────
    questions += [
        f"Is {f} applicable to all employees?",
        f"Does the {source} mention {f}?",
        f"Can you confirm {f} as per policy?",
        f"Is it true that {f}?",
        f"Under what circumstances does {f} apply?",
    ]

    # ── 3. Action-oriented ────────────────────────────────────────────────
    questions += [
        f"How do I claim based on {f}?",
        f"What should I do regarding {f}?",
        f"How is {f} processed?",
        f"Who approves claims related to {f}?",
    ]

    # ── 4. Category-specific ──────────────────────────────────────────────
    if "Rate" in category or "lodging" in f.lower() or "boarding" in f.lower() or "mab" in category.lower():
        questions += [
            f"What is the entitlement for {f}?",
            f"How much is {f}?",
            f"What rate applies for {f}?",
        ]
    elif "Timeline" in category or "days" in f.lower() or "months" in f.lower():
        questions += [
            f"Within how many days must {f} be done?",
            f"What is the time limit for {f}?",
            f"How many days for {f}?",
        ]
    elif "Contact" in category or "@" in f or "www" in f or "1800" in f:
        questions += [
            f"What is the contact for {f}?",
            f"How do I reach out via {f}?",
            f"Where can I report using {f}?",
        ]
    elif "Disciplinary" in category or "action" in f.lower():
        questions += [
            f"What disciplinary action includes {f}?",
            f"When is {f} recommended?",
            f"What is the consequence if {f}?",
        ]
    elif "Non-Reimbursable" in category:
        questions += [
            f"Is {f} reimbursable?",
            f"Will I get reimbursed for {f}?",
            f"Can I claim {f} as an expense?",
        ]
    else:
        questions += [
            f"What is the policy on {f}?",
            f"Explain {f} as per HR policy.",
            f"What are the rules around {f}?",
        ]

    # ── 5. Informal / scenario-based ──────────────────────────────────────
    questions += [
        f"I need to know about {f}, what does the policy say?",
        f"My manager asked me about {f}. What is the answer?",
        f"Please clarify {f} for me.",
        f"Is {f} covered under the {source}?",
        f"What does Arvind's {src} policy say about {f}?",
    ]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique[:25]


# ─────────────────────────────────────────────────────────────────────────────
# GRADE × CITY MATRIX GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

GRADE_LODGING = {
    "BMH7 and above": {"Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual"},
    "BMH3-H6": {"Class I": "8000", "Class II": "6000", "Class III": "5000"},
    "M3H1/M3/M2": {"Class I": "6000", "Class II": "5000", "Class III": "4000"},
    "M1/MT/E2/GET/E1/OT": {"Class I": "3400", "Class II": "2300", "Class III": "1700"},
}

GRADE_BOARDING = {
    "BMH7 and above": {"Class I": "At Actuals", "Class II": "At Actuals", "Class III": "At Actuals"},
    "BMH3-H6": {"Class I": "1500", "Class II": "1300", "Class III": "1000"},
    "M3H1/M3/M2": {"Class I": "1200", "Class II": "1000", "Class III": "800"},
    "M1/MT/E2/GET/E1/OT": {"Class I": "1000", "Class II": "800", "Class III": "600"},
}

GRADE_CAB = {
    "BM-H7 and above": "Actuals",
    "BMH3-H6": "Ola / Uber / BluSmart",
    "M3H1/M3/M2": "Ola / Uber / BluSmart",
    "M1/MT/E2/GET/E1/OT": "Ola / Uber / BluSmart, Bus, Metro, Local Transportation",
}

GRADE_TRAIN = {
    "BMH9": "1st AC",
    "BMH7/H8": "1st AC",
    "BM-H3–H6": "1st AC",
    "M3H1/M3/M2": "2nd AC",
    "M1/E2/E1/OT": "3rd AC/Chair Car",
}

GRADE_AIR = {
    "BMH9": "Premium Economy / Business",
    "BMH7/H8": "Economy / Premium Economy",
    "BM-H3–H6": None,
    "M3H1/M3/M2": "Economy",
    "M1/E2/E1/OT": None,  # Not Applicable - doesn't normalise correctly, skip
}

CLASS1_CITIES = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune", "NCR"]
CLASS2_CITIES = ["Ahmedabad", "Surat", "Jaipur", "Lucknow", "Nagpur", "Indore", "Kochi", "Chandigarh",
                 "Patna", "Ranchi", "Bhopal", "Coimbatore", "Guwahati", "Jamshedpur", "Visakhapatnam",
                 "Vijayawada", "Mysore", "Ludhiana", "Jodhpur", "Rajkot", "Madurai", "Mangalore",
                 "Nashik", "Noida", "Faridabad", "Meerut", "Agra", "Kanpur", "Varanasi", "Amritsar"]
CLASS3_CITIES = ["Srinagar", "Dehradun", "Bhavnagar", "Jamnagar", "Kota", "Jabalpur", "Raipur", "Cuttack"]


def gen_grade_city_cases():
    """Generate all grade × city × type combinations for lodging, boarding, cab, train, air."""
    cases = []

    # Lodging combinations
    for grade, city_limits in GRADE_LODGING.items():
        for city_class, amount in city_limits.items():
            for city in (CLASS1_CITIES if city_class == "Class I"
                         else CLASS2_CITIES if city_class == "Class II"
                         else CLASS3_CITIES)[:5]:
                key_fact = amount
                q_variants = [
                    f"What is the lodging limit for {grade} grade in {city}?",
                    f"I am a {grade} employee travelling to {city}. What is my hotel entitlement?",
                    f"Hotel reimbursement for {grade} employee visiting {city}?",
                    f"What can I claim for accommodation in {city} as {grade}?",
                    f"Lodging entitlement for {grade} in {city_class} city like {city}?",
                ]
                cases.append({
                    "queries": q_variants,
                    "keyFacts": [key_fact],
                    "source": "Domestic Travel Policy",
                    "page": 7,
                    "category": f"Lodging - {grade} - {city_class}",
                })

    # Boarding combinations
    for grade, city_limits in GRADE_BOARDING.items():
        for city_class, amount in city_limits.items():
            for city in (CLASS1_CITIES if city_class == "Class I"
                         else CLASS2_CITIES if city_class == "Class II"
                         else CLASS3_CITIES)[:5]:
                key_fact = amount
                q_variants = [
                    f"What is the boarding limit for {grade} in {city}?",
                    f"I am {grade} visiting {city}. What is my meal/boarding entitlement?",
                    f"Daily boarding allowance for {grade} in {city}?",
                    f"Food reimbursement for {grade} employee in {city}?",
                    f"Boarding limit in {city_class} city for {grade} grade?",
                ]
                cases.append({
                    "queries": q_variants,
                    "keyFacts": [key_fact],
                    "source": "Domestic Travel Policy",
                    "page": 7,
                    "category": f"Boarding - {grade} - {city_class}",
                })

    # Cab entitlements
    for grade, entitlement in GRADE_CAB.items():
        q_variants = [
            f"What cab options are available for {grade}?",
            f"I am {grade} on business travel. What transport can I use?",
            f"Cab booking entitlement for {grade} grade?",
            f"Which cab services can {grade} employees use?",
            f"What is the cab policy for {grade}?",
        ]
        cases.append({
            "queries": q_variants,
            "keyFacts": [entitlement[:40]],
            "source": "Domestic Travel Policy",
            "page": 8,
            "category": f"Cab - {grade}",
        })

    # Train entitlements
    for grade, train_class in GRADE_TRAIN.items():
        q_variants = [
            f"What is the train class for {grade}?",
            f"I am {grade} employee. What train class am I entitled to?",
            f"Train travel entitlement for {grade}?",
            f"Which class can {grade} travel by train?",
            f"Rail class for {grade} grade employees?",
        ]
        cases.append({
            "queries": q_variants,
            "keyFacts": [train_class],
            "source": "Domestic Travel Policy",
            "page": 7,
            "category": f"Train - {grade}",
        })

    # Air entitlements
    for grade, air_class in GRADE_AIR.items():
        if air_class is None:
            continue
        q_variants = [
            f"What is the air travel class for {grade}?",
            f"I am {grade}. Can I fly? What is my air entitlement?",
            f"Flight class for {grade} grade?",
            f"Air travel entitlement for {grade}?",
            f"What class of air ticket for {grade}?",
        ]
        cases.append({
            "queries": q_variants,
            "keyFacts": [air_class],
            "source": "Domestic Travel Policy",
            "page": 7,
            "category": f"Air Travel - {grade}",
        })

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# MAB/SIA MATRIX
# ─────────────────────────────────────────────────────────────────────────────

MAB_DATA = {
    "E1": {"monthly": "32,583", "annual": "3,91,000", "sia": "10,000"},
    "E2": {"monthly": "45,750", "annual": "5,49,000", "sia": "10,000"},
    "M1": {"monthly": "71,000", "annual": "8,52,000", "sia": "15,000"},
    "M2": {"monthly": "1,08,333", "annual": "13,00,000", "sia": "20,000"},
    "M3": {"monthly": "1,58,333", "annual": "19,00,000", "sia": "30,000"},
    "M3H1": {"monthly": "2,16,667", "annual": "26,00,000", "sia": "45,000"},
}


def gen_mab_sia_cases():
    """Generate MAB and SIA test cases for each grade."""
    cases = []
    for grade, data in MAB_DATA.items():
        # Monthly MAB
        cases.append({
            "queries": [
                f"What is the monthly MAB for {grade} grade?",
                f"I am {grade}. What monthly mobility adjustment benefit do I get?",
                f"MAB monthly amount for {grade}?",
                f"How much monthly allowance does a {grade} employee get on rotation?",
                f"Monthly MAB entitlement for {grade} grade employees?",
            ],
            "keyFacts": [data["monthly"]],
            "source": "Talent Mobility Policy",
            "page": 7,
            "category": f"MAB Monthly - {grade}",
        })
        # Annual MAB
        cases.append({
            "queries": [
                f"What is the annual MAB for {grade} grade?",
                f"I am {grade}. What is my annual mobility adjustment benefit?",
                f"Annual MAB amount for {grade}?",
                f"Total annual MAB for {grade} employee?",
                f"Yearly mobility benefit for {grade} grade?",
            ],
            "keyFacts": [data["annual"]],
            "source": "Talent Mobility Policy",
            "page": 7,
            "category": f"MAB Annual - {grade}",
        })
        # SIA
        cases.append({
            "queries": [
                f"What is the SIA for {grade} grade?",
                f"I am {grade}. What settling-in assistance do I get?",
                f"SIA amount for {grade} employee?",
                f"How much SIA is given to {grade} grade on relocation?",
                f"Settling-in assistance for {grade}?",
            ],
            "keyFacts": [data["sia"]],
            "source": "Talent Mobility Policy",
            "page": 7,
            "category": f"SIA - {grade}",
        })
    return cases


# ─────────────────────────────────────────────────────────────────────────────
# DISCIPLINARY ACTIONS EXPANSION
# ─────────────────────────────────────────────────────────────────────────────

POSH_ACTIONS = [
    "Written warning", "Written apology", "Reprimand/Censure",
    "Withholding of promotion", "Withholding of pay rise or increments",
    "Terminating the RE from service", "Undergoing a counselling session",
    "Carrying out community service", "Monetary compensation",
]


def gen_posh_action_cases():
    """Generate targeted questions for each POSH disciplinary action."""
    cases = []
    for action in POSH_ACTIONS:
        cases.append({
            "queries": [
                f"Is '{action}' a possible disciplinary action under POSH?",
                f"Can the AIC recommend {action}?",
                f"What does {action} mean under the POSH policy?",
                f"Is {action} listed as a sanction in the POSH policy?",
                f"Under what circumstances can {action} be recommended by AIC?",
            ],
            "keyFacts": [action],
            "source": "POSH Policy",
            "page": 8,
            "category": "Disciplinary Actions",
        })
    return cases


# ─────────────────────────────────────────────────────────────────────────────
# WHISTLEBLOWER REPORTABLE ISSUES EXPANSION
# ─────────────────────────────────────────────────────────────────────────────

WB_ISSUES = [
    "Breach of internal compliance requirements",
    "Non-compliance/breach of legal and regulatory requirements",
    "Bribery and corruption",
    "Procurement and tendering fraud",
    "Misappropriation/theft/embezzlement of company assets",
    "Corporate espionage and information disclosure",
    "Undue awarding of contracts",
    "False invoicing",
    "Fraudulent financial accounting, auditing and reporting",
    "Employee negligence",
    "Health, safety, environment and security related",
    "Workplace harassment",
    "Discrimination and favouritism",
]


def gen_whistleblower_issue_cases():
    """Generate targeted questions for each reportable issue."""
    cases = []
    for issue in WB_ISSUES:
        short = issue[:40]
        cases.append({
            "queries": [
                f"Can I report {issue} under the Whistleblower Policy?",
                f"Is {issue} a reportable concern?",
                f"Does the Whistleblower Policy cover {issue}?",
                f"What if I witness {issue}? Can I report it?",
                f"Is {short} something I can blow the whistle on?",
            ],
            "keyFacts": [short],
            "source": "Whistleblower Policy",
            "page": 3,
            "category": "Reportable Issues",
        })
    return cases


# ─────────────────────────────────────────────────────────────────────────────
# NON-REIMBURSABLE ITEMS EXPANSION
# ─────────────────────────────────────────────────────────────────────────────

NON_REIMB = [
    ("Express boarding", "Express boarding"),
    ("Web Check-in amount", "Web Check-in amount"),
    ("Fees for VIP Clubs/Lounge", "Fees for VIP Clubs"),
    ("Upgradation of seat/class at an added cost", "Upgradation of seat"),
    ("Health club services", "Health club services"),
    ("Amount incurred on personal entertainment/recreation", "personal entertainment"),
    ("Cost incurred on personal guests", "personal guests"),
    ("Airport parking tariff", "Airport parking tariff"),
    ("Personal Gifts", "Personal Gifts"),
    ("Spouse/dependent travel", "Spouse/dependent travel"),
    ("Alcohol, cigarettes", "Alcohol, cigarettes"),
    ("Usage of Mini-Bar", "Usage of Mini-Bar"),
    ("Telephone expenses", "Telephone expenses"),
    ("Business Outing without prior approval from CEO", "Business Outing"),
]


def gen_non_reimb_cases():
    """Generate expanded test cases for non-reimbursable items."""
    cases = []
    for full, short in NON_REIMB:
        cases.append({
            "queries": [
                f"Is {full} reimbursable under Domestic Travel Policy?",
                f"Can I claim {full} as a travel expense?",
                f"Will {full} be paid back by the company?",
                f"Is {short} covered under travel reimbursement?",
                f"Does the policy reimburse {full}?",
                f"Is {short} in the non-reimbursable list?",
                f"I spent money on {short}. Can I claim it?",
            ],
            "keyFacts": [full[:40]],
            "source": "Domestic Travel Policy",
            "page": 8,
            "category": "Non-Reimbursable",
        })
    return cases


# ─────────────────────────────────────────────────────────────────────────────
# ADDITIONAL SCENARIO-BASED CASES
# ─────────────────────────────────────────────────────────────────────────────

def gen_scenario_cases():
    """Generate scenario-based multi-fact test cases."""
    cases = []

    # Local conveyance scenarios
    scenarios_lc = [
        ("I drove 40km for office work in my car. How much will I get?",
         ["four wheeler @ Rs. 10.00 / - per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("I used my bike for office travel. What is the reimbursement rate?",
         ["two wheeler @ Rs. 5.00 per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("My colleague and I shared a cab for official work. Who should claim conveyance?",
         ["individual who has actually incurred the cost"], "Local Conveyance Policy", 1, "Reimbursement Rules"),
        ("I took a cab for official work. How is that reimbursed?",
         ["reimbursement will be done on actuals"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Where do I submit my conveyance claim?",
         ["Orapps – ESMS – Entry – Conveyance Expense"], "Local Conveyance Policy", 1, "Claim Process"),
        ("Who needs to approve my local conveyance expense?",
         ["approved only by BM grade employees"], "Local Conveyance Policy", 1, "Approval"),
        ("I live in Ahmedabad and travel to a factory within city. Am I eligible for conveyance?",
         ["outside the respective City/Town Municipal Corporation"], "Local Conveyance Policy", 1, "Eligibility"),
        ("What happens if I submit a fake conveyance claim?",
         ["strict disciplinary action shall be taken"], "Local Conveyance Policy", 2, "Compliance"),
    ]
    for q, kf, src, pg, cat in scenarios_lc:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Domestic travel scenarios
    scenarios_dt = [
        ("I need to book a flight. How far in advance should I do it?",
         ["at least 7 days in advance"], "Domestic Travel Policy", 3, "Procedures"),
        ("Which tool do I use to book travel?",
         ["myBiz"], "Domestic Travel Policy", 2, "Booking Tool"),
        ("How many days do I have to settle my travel expenses?",
         ["within 15 days of the trip"], "Domestic Travel Policy", 5, "Settlement"),
        ("What happens if I don't settle my expenses in 15 days?",
         ["auto-settlement on the 16th day"], "Domestic Travel Policy", 5, "Settlement"),
        ("My trip was 4 days long. Can I claim laundry?",
         ["duration of travel exceeds three days"], "Domestic Travel Policy", 5, "Laundry"),
        ("I'm going to Mumbai for a day trip. Can I claim hotel?",
         ["not eligible to avail the accommodation"], "Domestic Travel Policy", 3, "Same-Day Return"),
        ("Does travel policy apply to journeys less than 300 km?",
         ["domestic travel exceeding a distance of 300 km"], "Domestic Travel Policy", 2, "Scope"),
        ("I want to make my own stay arrangement. What flat rate will I get?",
         ["30% of the entitlement"], "Domestic Travel Policy", 5, "Flat Rate"),
        ("I am BM-H7. What flat rate for lodging if I arrange my own stay?",
         ["Rs. 6,000 per day"], "Domestic Travel Policy", 5, "Flat Rate"),
        ("I need a cab for visiting 4 locations in a day. Can I book full day?",
         ["travel to three or more locations on a given day"], "Domestic Travel Policy", 5, "Cab Policy"),
        ("I am a woman employee of M2 grade. Can I use higher grade hotel limits?",
         ["hotel limits of the next higher grade"], "Domestic Travel Policy", 4, "Women Policy"),
        ("What travel mode advice is given to women employees for safety?",
         ["Avoidance of Night Travel"], "Domestic Travel Policy", 4, "Women Policy"),
    ]
    for q, kf, src, pg, cat in scenarios_dt:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Grievance scenarios
    scenarios_gr = [
        ("How long does it take to acknowledge a grievance?",
         ["2 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("How long does grievance investigation take?",
         ["10 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("When will I get a resolution for my grievance?",
         ["15 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("Can I report a grievance anonymously?",
         ["Anonymous complaints will be considered"], "Grievance Mechanism Policy", 3, "Anonymous"),
        ("Will I face retaliation for raising a grievance?",
         ["protected from retaliation"], "Grievance Mechanism Policy", 2, "Protection"),
        ("I am a contract worker. Can I file a grievance?",
         ["contract workers"], "Grievance Mechanism Policy", 2, "Applicability"),
        ("How often is the grievance policy reviewed?",
         ["every two years"], "Grievance Mechanism Policy", 4, "Review"),
        ("I am unhappy with grievance resolution. What can I do?",
         ["escalate the grievance to the next level"], "Grievance Mechanism Policy", 3, "Escalation"),
    ]
    for q, kf, src, pg, cat in scenarios_gr:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # POSH scenarios
    scenarios_posh = [
        ("How long do I have to file a POSH complaint after the incident?",
         ["3 (three) months from the date of incident"], "POSH Policy", 6, "Filing Deadline"),
        ("Can the 3-month filing period be extended?",
         ["extended for further 3 (three) months"], "POSH Policy", 6, "Filing Deadline"),
        ("How many copies of complaint do I need to submit to AIC?",
         ["six copies of the complaint"], "POSH Policy", 6, "Filing"),
        ("Can I bring my lawyer to AIC proceedings?",
         ["not be allowed to bring in any legal practitioner"], "POSH Policy", 6, "Legal Representation"),
        ("How many members must be present in AIC inquiry?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("What is the women representation requirement in AIC?",
         ["50% women representation"], "POSH Policy", 4, "Quorum"),
        ("How much is the external AIC member paid?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),
        ("How long is the AIC tenure?",
         ["period of three years"], "POSH Policy", 5, "AIC Tenure"),
        ("How long does management have to act on AIC recommendations?",
         ["60 (sixty) days"], "POSH Policy", 7, "Management Action"),
        ("Can a male employee file a POSH complaint?",
         ["gender neutral"], "POSH Policy", 5, "Scope"),
        ("Are same-sex harassment cases covered under POSH?",
         ["prohibits same-sex harassment"], "POSH Policy", 5, "Scope"),
        ("Can office party incidents be reported under POSH?",
         ["Office parties"], "POSH Policy", 2, "Scope"),
        ("What interim leave can an aggrieved woman get?",
         ["leave to the Aggrieved Woman up to a period of 3 (three) months"], "POSH Policy", 7, "Interim Relief"),
        ("Can my friend file a POSH complaint on my behalf?",
         ["Her relative or friend"], "POSH Policy", 5, "Who Can File"),
        ("Who is the Presiding Officer of AIC?",
         ["Senior level woman employee"], "POSH Policy", 4, "AIC Composition"),
        ("Can I file a POSH complaint anonymously?",
         ["Anonymous complaints will not be entertained"], "POSH Policy", 6, "Anonymous"),
        ("What is the AIC report timeline after inquiry?",
         ["within a period of 10 (ten) days"], "POSH Policy", 7, "AIC Report"),
    ]
    for q, kf, src, pg, cat in scenarios_posh:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Whistleblower scenarios
    scenarios_wb = [
        ("How do I report bribery at Arvind?",
         ["Bribery and corruption"], "Whistleblower Policy", 3, "Reportable Issues"),
        ("How often does the Whistleblower Committee report to Audit Committee?",
         ["quarterly"], "Whistleblower Policy", 4, "Reporting Frequency"),
        ("When can I follow up on my whistleblower report?",
         ["four weeks after the submission"], "Whistleblower Policy", 4, "Follow-up"),
        ("Will my identity be kept secret if I report via Whistleblower Policy?",
         ["identity of the whistle blower shall be kept confidential"], "Whistleblower Policy", 4, "Confidentiality"),
        ("Can the Whistleblower Committee hire an external agency?",
         ["appoint an independent agency"], "Whistleblower Policy", 4, "Investigation"),
        ("What happens if I make a false whistleblower complaint?",
         ["will not be protected by this Policy"], "Whistleblower Policy", 5, "False Complaints"),
        ("I faced retaliation after reporting. What can I do?",
         ["lodge a written complaint to the Chairman"], "Whistleblower Policy", 5, "Retaliation Recourse"),
        ("Am I required to cooperate with a whistleblower investigation?",
         ["duty to cooperate with investigations"], "Whistleblower Policy", 4, "Responsibilities"),
        ("Are Business Associates covered under Whistleblower Policy?",
         ["Business Associates"], "Whistleblower Policy", 3, "Applicability"),
    ]
    for q, kf, src, pg, cat in scenarios_wb:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Talent Mobility scenarios
    scenarios_tm = [
        ("When is an employee mandated to rotate as per Talent Mobility Policy?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("Which positions must be filled via IJP?",
         ["All positions upto M2"], "Talent Mobility Policy", 4, "IJP"),
        ("Can my manager stop my rotation?",
         ["Managers cannot block mobility"], "Talent Mobility Policy", 4, "Governance"),
        ("Who can approve exceptions to Talent Mobility Policy?",
         ["CHRO/CEO can approve exceptions"], "Talent Mobility Policy", 4, "Exceptions"),
        ("How long is the MAB paid?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
        ("What happens to MAB after 1 year?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB"),
        ("When am I eligible for SIA?",
         ["shifting house"], "Talent Mobility Policy", 6, "SIA Condition"),
        ("What distance qualifies for SIA?",
         ["relocation >20 kms"], "Talent Mobility Policy", 7, "SIA Condition"),
        ("What type of payment is SIA?",
         ["One time"], "Talent Mobility Policy", 6, "SIA Type"),
        ("What is the purpose of MAB?",
         ["Monthly allowance"], "Talent Mobility Policy", 6, "MAB Description"),
        ("What is SIA used for?",
         ["One-time lump sum for household setup"], "Talent Mobility Policy", 6, "SIA Description"),
        ("What are the risks of sensitive roles staying too long?",
         ["sensitive roles exceed tenure"], "Talent Mobility Policy", 2, "Risk"),
        ("What is the 1st rotation model for Talent Mobility?",
         ["1st Rotation – within the city"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("What is the 2nd rotation model?",
         ["2nd Rotation – across different business / different location"], "Talent Mobility Policy", 4, "Rotation Framework"),
    ]
    for q, kf, src, pg, cat in scenarios_tm:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Joining Policy scenarios
    scenarios_jp = [
        ("How many days can I spend on a pre-joining visit?",
         ["maximum period of 3 days"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Can my spouse join me on the pre-joining visit?",
         ["spouse"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Can my children accompany me on the pre-joining visit?",
         ["school admission"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("What is the transport reimbursement for relocation under 700 km?",
         ["Rs. 50 per km"], "Joining Policy", 1, "Transportation"),
        ("What is the transport reimbursement for relocation over 700 km?",
         ["Rs. 60 per km"], "Joining Policy", 1, "Transportation"),
        ("I'm driving my car to my new posting. What do I get per km?",
         ["Rs. 10.0 per km"], "Joining Policy", 1, "Car Transport"),
        ("What is the driver wage for 8-hour trip?",
         ["Rs. 600/-"], "Joining Policy", 1, "Driver Wages"),
        ("What is the driver wage per hour after 8 hours?",
         ["Rs. 50/- per hour"], "Joining Policy", 1, "Driver Wages"),
        ("What is the food reimbursement limit per meal during relocation?",
         ["Rs. 200/- per meal"], "Joining Policy", 1, "Food Limit"),
        ("Will the company pay my house brokerage?",
         ["One month rent"], "Joining Policy", 1, "Brokerage"),
        ("For how long can I claim brokerage after joining?",
         ["maximum for 1 year from the date of the joining"], "Joining Policy", 1, "Brokerage Validity"),
        ("How is house deposit recovered?",
         ["10 equal monthly instalments"], "Joining Policy", 1, "House Deposit"),
        ("What is the deadline to claim joining expenses?",
         ["One Year from Date of Joining"], "Joining Policy", 1, "Expense Claim Deadline"),
        ("I quit within 6 months. Will relocation expenses be recovered?",
         ["recovered in his/her F&F settlement"], "Joining Policy", 1, "Quit < 1 Year"),
        ("Who books my flight for joining?",
         ["Arvind Travel Desk"], "Joining Policy", 1, "Flight Booking"),
        ("Are joining expenses taxable?",
         ["Income tax shall be grossed up"], "Joining Policy", 1, "Tax"),
        ("Who pays the packers and movers directly?",
         ["The company shall directly make payment"], "Joining Policy", 1, "Packers & Movers"),
        ("Can I take both pre-joining and post-joining visit?",
         ["either a Pre-Joining Visit OR Post Joining Visit"], "Joining Policy", 1, "Visit Options"),
        ("Who can approve exceptions to the Joining Policy?",
         ["CEO"], "Joining Policy", 1, "Approvals"),
        ("When did the Joining Policy become effective?",
         ["21.09.2023"], "Joining Policy", 1, "Policy Details"),
    ]
    for q, kf, src, pg, cat in scenarios_jp:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Gender Policy scenarios
    scenarios_gp = [
        ("When was the Gender Policy issued?",
         ["25.07.2025"], "Gender Policy", 1, "Policy Details"),
        ("Who does the Gender Policy apply to?",
         ["all employees of Arvind Ltd"], "Gender Policy", 2, "Applicability"),
        ("Are interns covered under the Gender Policy?",
         ["interns"], "Gender Policy", 2, "Applicability"),
        ("Are third-party partners covered under Gender Policy?",
         ["third-party partners"], "Gender Policy", 2, "Applicability"),
        ("How often is Gender Policy reviewed?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Will I face retaliation for reporting gender bias?",
         ["retaliation against individuals who raise concerns in good faith is strictly prohibited"], "Gender Policy", 3, "Protection"),
        ("Are hiring decisions based on merit under Gender Policy?",
         ["Hiring and Promotions are conducted based on merit"], "Gender Policy", 3, "Principles"),
        ("What is the first level of complaint in Gender Policy?",
         ["HR Department"], "Gender Policy", 3, "Complaint Process"),
        ("What is the policy number for Gender Policy?",
         ["ARV|COM_GENP|001|260725"], "Gender Policy", 1, "Policy Details"),
    ]
    for q, kf, src, pg, cat in scenarios_gp:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# COMPARATIVE / MULTI-GRADE CASES
# ─────────────────────────────────────────────────────────────────────────────

def gen_comparative_cases():
    """Generate comparative questions across grades."""
    cases = []

    grade_pairs = [
        ("BMH9", "BMH7/H8"), ("BMH3-H6", "M3H1/M3/M2"),
        ("M3H1/M3/M2", "M1/E2/E1/OT"), ("BMH9", "M3H1/M3/M2"),
    ]
    for g1, g2 in grade_pairs:
        cases.append({
            "queries": [
                f"What is the difference in train class between {g1} and {g2}?",
                f"How does {g1} train entitlement compare to {g2}?",
                f"Compare train class for {g1} vs {g2}.",
                f"Which grade gets a better train class: {g1} or {g2}?",
                f"Train entitlement comparison: {g1} and {g2}?",
            ],
            "keyFacts": [GRADE_TRAIN.get(g1, "1st AC")],
            "source": "Domestic Travel Policy",
            "page": 7,
            "category": "Comparative - Train",
        })

    # Lodging comparison
    lodging_pairs = [
        ("BMH3-H6", "M3H1/M3/M2", "Class I"),
        ("M3H1/M3/M2", "M1/MT/E2/GET/E1/OT", "Class I"),
        ("BMH3-H6", "M1/MT/E2/GET/E1/OT", "Class II"),
    ]
    for g1, g2, city_class in lodging_pairs:
        amount1 = GRADE_LODGING[g1][city_class]
        cases.append({
            "queries": [
                f"What is the lodging difference for {g1} vs {g2} in {city_class} cities?",
                f"Compare hotel limits for {g1} and {g2} in {city_class}?",
                f"Which grade has higher lodging limit in {city_class}: {g1} or {g2}?",
                f"{g1} vs {g2} hotel entitlement in {city_class} cities?",
                f"Lodging allowance comparison for {g1} and {g2} in {city_class}?",
            ],
            "keyFacts": [amount1],
            "source": "Domestic Travel Policy",
            "page": 7,
            "category": f"Comparative - Lodging - {city_class}",
        })

    # MAB comparison
    mab_pairs = [("E1", "E2"), ("M1", "M2"), ("M2", "M3"), ("M3", "M3H1")]
    for g1, g2 in mab_pairs:
        cases.append({
            "queries": [
                f"What is the MAB difference between {g1} and {g2}?",
                f"Compare monthly MAB for {g1} vs {g2}.",
                f"Who gets higher MAB: {g1} or {g2}?",
                f"MAB comparison between {g1} and {g2} grade?",
                f"How does MAB for {g1} differ from {g2}?",
            ],
            "keyFacts": [MAB_DATA[g1]["monthly"]],
            "source": "Talent Mobility Policy",
            "page": 7,
            "category": f"Comparative - MAB",
        })

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# POLICY-SPECIFIC EDGE CASE EXPANDERS
# ─────────────────────────────────────────────────────────────────────────────

def gen_edge_cases():
    """Generate edge case and policy detail questions."""
    cases = []

    # Policy numbers & dates
    policy_meta = [
        ("What is the policy number for Local Conveyance Policy?",
         ["ARV|COR"], "Local Conveyance Policy", 1, "Policy Details"),
        ("When was Local Conveyance Policy effective?",
         ["01.07.2022"], "Local Conveyance Policy", 1, "Policy Details"),
        ("What is the Domestic Travel Policy number?",
         ["ARV | EOP_DTP | 003 | 270723"], "Domestic Travel Policy", 1, "Policy Details"),
        ("When was the Domestic Travel Policy issued?",
         ["27.07.2023"], "Domestic Travel Policy", 1, "Policy Details"),
        ("What is the Grievance Policy number?",
         ["ARV|COM_GRM|001|260725"], "Grievance Mechanism Policy", 1, "Policy Details"),
        ("When did the Grievance Policy become effective?",
         ["26.07.2025"], "Grievance Mechanism Policy", 1, "Policy Details"),
        ("What is the POSH Policy issue date?",
         ["31.03.2022"], "POSH Policy", 1, "Policy Details"),
        ("When did the updated POSH Policy become effective?",
         ["01.05.2025"], "POSH Policy", 1, "Policy Details"),
        ("What is the POSH Policy number?",
         ["ARV|ELC_SHA|008|010422"], "POSH Policy", 1, "Policy Details"),
        ("What is the Gender Policy number?",
         ["ARV|COM_GENP|001|260725"], "Gender Policy", 1, "Policy Details"),
        ("When was Joining Policy effective?",
         ["21.09.2023"], "Joining Policy", 1, "Policy Details"),
    ]
    for q, kf, src, pg, cat in policy_meta:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Contact information questions
    contacts = [
        ("What is the ethics helpline toll-free number?",
         ["1800 200 8301"], "Grievance Mechanism Policy", 3, "Contact"),
        ("What email can I use to report grievances anonymously?",
         ["arvind@ethicshelpline.in"], "Grievance Mechanism Policy", 3, "Contact"),
        ("What is the web portal for whistleblowing?",
         ["www.in.kpmg.com/ethicshelpline/arvind"], "Whistleblower Policy", 3, "Contact"),
        ("How can I report POSH via hotline?",
         ["18002008301"], "POSH Policy", 5, "Contact"),
        ("What is the Gender Policy complaint email?",
         ["arvind@ethicshelpline.in"], "Gender Policy", 3, "Contact"),
    ]
    for q, kf, src, pg, cat in contacts:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    # Applicability edge cases
    applicability = [
        ("Does the Local Conveyance Policy apply to all grades?",
         ["applicable across all grades"], "Local Conveyance Policy", 1, "Applicability"),
        ("Is the Local Conveyance Policy applicable pan-India?",
         ["applicable across India"], "Local Conveyance Policy", 1, "Applicability"),
        ("Are trainees covered under Grievance Mechanism Policy?",
         ["trainees"], "Grievance Mechanism Policy", 2, "Applicability"),
        ("Do Arvind subsidiaries fall under Joining Policy?",
         ["subsidiaries"], "Joining Policy", 1, "Applicability"),
        ("Are visitors covered under POSH Policy?",
         ["Third parties and/or visitors"], "POSH Policy", 1, "Applicability"),
        ("Are contract staff covered under Gender Policy?",
         ["contract staff"], "Gender Policy", 2, "Applicability"),
        ("Can a Director use Whistleblower Policy?",
         ["Directors"], "Whistleblower Policy", 3, "Applicability"),
    ]
    for q, kf, src, pg, cat in applicability:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# INFORMAL / CASUAL LANGUAGE CASES
# ─────────────────────────────────────────────────────────────────────────────

def gen_informal_cases():
    """Generate informal and casual language questions."""
    cases = []

    informal_qs = [
        ("Bhai kitna milta hai 4-wheeler conveyance mein?",
         ["four wheeler @ Rs. 10.00 / - per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Bike se jaane par kya milega?",
         ["two wheeler @ Rs. 5.00 per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Hotel ke liye kya limit hai M2 ko?",
         ["6000"], "Domestic Travel Policy", 7, "Lodging"),
        ("Mumbai mein khane ka allowance kitna hai M1 ke liye?",
         ["1000"], "Domestic Travel Policy", 7, "Boarding"),
        ("Train mein kaunsi class milti hai E1 ko?",
         ["3rd AC/Chair Car"], "Domestic Travel Policy", 7, "Mode of Travel"),
        ("Cab ke liye Ola le sakte hain kya M3 employee?",
         ["Ola / Uber / BluSmart"], "Domestic Travel Policy", 8, "Cab Entitlement"),
        ("Ticket kitne din pehle book karna chahiye?",
         ["at least 7 days in advance"], "Domestic Travel Policy", 3, "Procedures"),
        ("Travel settle karne ke liye kitne din milte hain?",
         ["within 15 days of the trip"], "Domestic Travel Policy", 5, "Settlement"),
        ("Grievance complaint ka jawab kab milega?",
         ["15 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("POSH complaint kitne din mein daalni chahiye?",
         ["3 (three) months from the date of incident"], "POSH Policy", 6, "Filing Deadline"),
        ("MAB kab tak milta hai?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
        ("E1 employee ko kitna MAB milta hai monthly?",
         ["32,583"], "Talent Mobility Policy", 7, "MAB - E1"),
        ("M2 grade ka SIA kitna hai?",
         ["20,000"], "Talent Mobility Policy", 7, "SIA - M2"),
        ("Joining ke baad kitne saal mein relocation expenses claim karna hoga?",
         ["One Year from Date of Joining"], "Joining Policy", 1, "Expense Claim Deadline"),
        ("Broker ko kitna paisa milega?",
         ["One month rent"], "Joining Policy", 1, "Brokerage"),
        ("POSH mein lawyer le ja sakte hain kya?",
         ["not be allowed to bring in any legal practitioner"], "POSH Policy", 6, "Legal Representation"),
        ("Whistleblower ki identity secret rehti hai kya?",
         ["identity of the whistle blower shall be kept confidential"], "Whistleblower Policy", 4, "Confidentiality"),
        ("Gender policy mein kab review hogi?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Rotation ke baad city badal sakti hai kya?",
         ["2nd Rotation – across different business / different location"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("Company car hone par bhi conveyance milega kya shehar ke andar?",
         ["outside the respective City/Town Municipal Corporation"], "Local Conveyance Policy", 1, "Eligibility"),
    ]

    for q, kf, src, pg, cat in informal_qs:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# POLICY CROSS-REFERENCE CASES
# ─────────────────────────────────────────────────────────────────────────────

def gen_cross_ref_cases():
    """Generate cross-reference and policy comparison questions."""
    cases = []

    cross_refs = [
        # Same contact across multiple policies
        ("Is the ethics helpline number the same for POSH, Whistleblower, and Grievance?",
         ["18002008301"], "POSH Policy", 5, "Contact"),
        ("Which policies use arvind@ethicshelpline.in for reporting?",
         ["arvind@ethicshelpline.in"], "Whistleblower Policy", 3, "Contact"),
        ("Can I use the KPMG portal for POSH complaints?",
         ["www.in.kpmg.com/ethicshelpline/arvind"], "POSH Policy", 5, "Contact"),
        # Policy scope overlaps
        ("Does the Local Conveyance Policy cover air travel?",
         ["domestic travel exceeding a distance of 300 km"], "Domestic Travel Policy", 2, "Scope"),
        ("Both POSH and Grievance policies protect against retaliation. What does POSH say?",
         ["protected from any form of retaliation"], "POSH Policy", 8, "Protection"),
        ("Both Gender and Grievance policies cover retaliation. What does Gender policy say?",
         ["retaliation against individuals who raise concerns in good faith is strictly prohibited"], "Gender Policy", 3, "Protection"),
        # Two policies compared
        ("Is the review cycle same for Gender Policy and Grievance Policy?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Which policy covers talent rotation: HR Policy or Talent Mobility?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("Does Joining Policy or Domestic Travel Policy cover relocation > 700km transport?",
         ["Rs. 60 per km"], "Joining Policy", 1, "Transportation"),
        ("Which policy covers hotel booking for new joinee relocation?",
         ["Arvind Travel Desk"], "Joining Policy", 1, "Flight Booking"),
    ]

    for q, kf, src, pg, cat in cross_refs:
        cases.append({"queries": [q], "keyFacts": kf, "source": src, "page": pg, "category": cat})

    return cases


# ─────────────────────────────────────────────────────────────────────────────
# ADDITIONAL BULK EXPANSION QUESTIONS FOR EACH FACT
# ─────────────────────────────────────────────────────────────────────────────

EXTRA_TEMPLATES = [
    "According to the {source}, what is {fact}?",
    "The {source} states that {fact}. Is this correct?",
    "Please explain {fact} in the context of {source}.",
    "HR told me about {fact}. What exactly does the policy say?",
    "My colleague mentioned {fact}. What does the {source} say about it?",
    "How does {source} define {fact}?",
    "Where can I find information about {fact} in HR policies?",
    "What are the implications of {fact} for employees?",
    "Is {fact} mandatory or optional?",
    "Can {fact} be waived or modified?",
    "Who decides {fact} in the company?",
    "What documentation is required for {fact}?",
    "Is approval needed for {fact}?",
    "What is the process for {fact}?",
    "Has {fact} changed recently in the policy?",
    "What happens if I don't follow {fact}?",
    "I am a new employee. Tell me about {fact}.",
    "I work in a subsidiary. Does {fact} apply to me?",
    "Is {fact} mentioned in the latest version of the policy?",
    "What supporting documents do I need for {fact}?",
]


def gen_bulk_expansion(facts_list):
    """Generate additional cases from EXTRA_TEMPLATES for each fact."""
    cases = []
    for fact, source, page, category in facts_list:
        short_fact = fact[:50]
        src_short = source.replace(" Policy", "").replace(" 2025", "")
        for tmpl in EXTRA_TEMPLATES[:12]:  # 12 extra per fact
            q = tmpl.format(fact=short_fact, source=source, src=src_short)
            cases.append({
                "queries": [q],
                "keyFacts": [fact[:40]],
                "source": source,
                "page": page,
                "category": category,
            })
    return cases


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Enterprise HR Policy Test Suite Generator")
    print("=" * 60)

    # Step 1: Extract corpus
    print("\n[1/5] Extracting policy corpus...")
    corpus = extract_corpus()
    for policy, text in corpus.items():
        print(f"  {policy}: {len(text):,} chars")

    # Step 2: Generate base fact cases
    print("\n[2/5] Generating test cases...")
    all_raw_cases = []

    # Base FACTS: each gets 20-25 question variants
    for fact, source, page, category in FACTS:
        questions = gen_questions_for_fact(fact, source, category)
        for q in questions:
            all_raw_cases.append({
                "query": q,
                "keyFacts": [fact[:40]],
                "source": source,
                "page": page,
                "category": category,
            })

    print(f"  Base fact cases: {len(all_raw_cases):,}")

    # Grade × City matrix
    matrix_cases = gen_grade_city_cases()
    for mc in matrix_cases:
        for q in mc["queries"]:
            all_raw_cases.append({
                "query": q,
                "keyFacts": mc["keyFacts"],
                "source": mc["source"],
                "page": mc["page"],
                "category": mc["category"],
            })
    print(f"  After grade×city matrix: {len(all_raw_cases):,}")

    # MAB/SIA matrix
    mab_cases = gen_mab_sia_cases()
    for mc in mab_cases:
        for q in mc["queries"]:
            all_raw_cases.append({
                "query": q,
                "keyFacts": mc["keyFacts"],
                "source": mc["source"],
                "page": mc["page"],
                "category": mc["category"],
            })
    print(f"  After MAB/SIA matrix: {len(all_raw_cases):,}")

    # POSH disciplinary actions
    posh_cases = gen_posh_action_cases()
    for mc in posh_cases:
        for q in mc["queries"]:
            all_raw_cases.append({
                "query": q,
                "keyFacts": mc["keyFacts"],
                "source": mc["source"],
                "page": mc["page"],
                "category": mc["category"],
            })
    print(f"  After POSH actions: {len(all_raw_cases):,}")

    # Whistleblower issues
    wb_cases = gen_whistleblower_issue_cases()
    for mc in wb_cases:
        for q in mc["queries"]:
            all_raw_cases.append({
                "query": q,
                "keyFacts": mc["keyFacts"],
                "source": mc["source"],
                "page": mc["page"],
                "category": mc["category"],
            })
    print(f"  After Whistleblower issues: {len(all_raw_cases):,}")

    # Non-reimbursable items
    nr_cases = gen_non_reimb_cases()
    for mc in nr_cases:
        for q in mc["queries"]:
            all_raw_cases.append({
                "query": q,
                "keyFacts": mc["keyFacts"],
                "source": mc["source"],
                "page": mc["page"],
                "category": mc["category"],
            })
    print(f"  After non-reimbursable items: {len(all_raw_cases):,}")

    def expand_multi_query_cases(multi_cases):
        """Expand cases that have 'queries' (list) into individual cases with 'query'."""
        expanded = []
        for mc in multi_cases:
            queries = mc.get("queries", [mc.get("query")])
            for q in queries:
                expanded.append({
                    "query": q,
                    "keyFacts": mc["keyFacts"],
                    "source": mc["source"],
                    "page": mc["page"],
                    "category": mc["category"],
                })
        return expanded

    # Scenario cases
    scenario_cases = gen_scenario_cases()
    all_raw_cases.extend(expand_multi_query_cases(scenario_cases))
    print(f"  After scenario cases: {len(all_raw_cases):,}")

    # Comparative cases
    comp_cases = gen_comparative_cases()
    all_raw_cases.extend(expand_multi_query_cases(comp_cases))
    print(f"  After comparative cases: {len(all_raw_cases):,}")

    # Edge cases
    edge_cases = gen_edge_cases()
    all_raw_cases.extend(expand_multi_query_cases(edge_cases))
    print(f"  After edge cases: {len(all_raw_cases):,}")

    # Informal cases
    informal_cases = gen_informal_cases()
    all_raw_cases.extend(expand_multi_query_cases(informal_cases))
    print(f"  After informal cases: {len(all_raw_cases):,}")

    # Cross-reference cases
    cross_cases = gen_cross_ref_cases()
    all_raw_cases.extend(expand_multi_query_cases(cross_cases))
    print(f"  After cross-reference cases: {len(all_raw_cases):,}")

    # Bulk expansion
    bulk_cases = gen_bulk_expansion(FACTS)
    all_raw_cases.extend(expand_multi_query_cases(bulk_cases))
    print(f"  After bulk expansion: {len(all_raw_cases):,}")

    # Step 3: Deduplicate by query string
    print("\n[3/5] Deduplicating cases...")
    seen_queries = set()
    unique_cases = []
    for case in all_raw_cases:
        q = case["query"].strip().lower()
        if q not in seen_queries:
            seen_queries.add(q)
            unique_cases.append(case)

    print(f"  Unique cases after dedup: {len(unique_cases):,}")

    # Step 4: Assign sequential IDs and finalize
    print("\n[4/5] Finalising and assigning IDs...")
    final_suite = []
    for i, case in enumerate(unique_cases, 1):
        entry = {
            "id": f"ETC{i:04d}",
            "query": case["query"],
            "keyFacts": case["keyFacts"],
            "source": case["source"],
            "page": case["page"],
            "category": case["category"],
        }
        final_suite.append(entry)

    # Step 5: Verify keyFacts against corpus
    print("\n[5/5] Verifying keyFacts against policy corpus...")
    failed_facts = {}
    verified_count = 0
    total_count = 0

    for case in final_suite:
        source = case["source"]
        # Map source names to corpus keys
        corpus_key = None
        for key in corpus:
            if key.lower() in source.lower() or source.lower() in key.lower():
                corpus_key = key
                break
        if corpus_key is None:
            # Try partial match
            for key in corpus:
                src_words = source.lower().split()
                if any(w in key.lower() for w in src_words if len(w) > 4):
                    corpus_key = key
                    break

        if corpus_key is None:
            continue

        corpus_text = corpus[corpus_key]
        for kf in case["keyFacts"]:
            total_count += 1
            norm_kf = normalise(kf)
            if len(norm_kf) < 2:
                verified_count += 1
                continue
            if norm_kf in corpus_text:
                verified_count += 1
            else:
                if kf not in failed_facts:
                    failed_facts[kf] = {"source": source, "count": 0, "normalised": norm_kf}
                failed_facts[kf]["count"] += 1

    print(f"\n  Verification Results:")
    print(f"  Total keyFact checks: {total_count:,}")
    print(f"  Verified (found in corpus): {verified_count:,} ({100*verified_count/max(total_count,1):.1f}%)")
    print(f"  Failed (not found): {total_count - verified_count:,} ({100*(total_count-verified_count)/max(total_count,1):.1f}%)")

    if failed_facts:
        print(f"\n  FAILED KEYFACTS ({len(failed_facts)} unique):")
        for kf, info in sorted(failed_facts.items(), key=lambda x: -x[1]["count"])[:50]:
            print(f"    [{info['count']}x] '{kf}' → normalised: '{info['normalised']}'  (source: {info['source']})")

    # Save to file
    output_path = '/home/user/ARVIN/enterprise_test_suite.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_suite, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"OUTPUT: {output_path}")
    print(f"TOTAL CASES: {len(final_suite):,}")

    # Per-policy breakdown
    from collections import Counter
    policy_counts = Counter(case["source"] for case in final_suite)
    print(f"\nCases per policy:")
    for policy, count in sorted(policy_counts.items()):
        print(f"  {policy}: {count:,}")

    # Per-category top breakdown
    cat_counts = Counter(case["category"] for case in final_suite)
    print(f"\nTop 20 categories:")
    for cat, count in cat_counts.most_common(20):
        print(f"  {cat}: {count}")

    print(f"\nDone! {len(final_suite):,} test cases written to {output_path}")
    return len(final_suite), failed_facts


if __name__ == "__main__":
    main()
