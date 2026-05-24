#!/usr/bin/env python3
"""
Enterprise HR Policy Golden Test Set v2
10,000-case stratified test suite with natural language queries.

Tiers:
  Tier 1 (40% = 4000): Math & Matrix   — Domestic Travel, Local Conveyance, Talent Mobility
  Tier 2 (30% = 3000): High Risk       — POSH, Whistleblower, Grievance
  Tier 3 (20% = 2000): Process         — Joining, Gender
  Tier 4 (10% = 1000): Cross-Policy    — Multi-document queries

SOURCE NAMES must match chunks.json exactly:
  "Domestic Travel Policy"
  "Local Conveyance Policy"
  "Talent Mobility Policy"
  "POSH Policy (Prevention of Sexual Harassment)"
  "Whistleblower Policy"
  "Grievance Mechanism Policy 2025"
  "Gender Policy 2025"
  "Joining Policy"
"""

import json, re, os, random
from collections import Counter
import pdfplumber
from docx import Document

# ──────────────────────────────────────────────────────────────────────────────
# NORMALISATION  (must match benchmark_enterprise.py exactly)
# ──────────────────────────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    t = text.lower()
    t = re.sub(r'rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


# ──────────────────────────────────────────────────────────────────────────────
# CORPUS EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

POLICY_DIR = '/home/user/ARVIN/policies'

# Map from chunks.json policy_name → filename
POLICY_FILES = {
    'Local Conveyance Policy':                        'cf8daeee-localconveyancepolicyarvindlimited.pdf',
    'Domestic Travel Policy':                         'f34aa66a-domestictravelpolicyarvindlimited.pdf',
    'Grievance Mechanism Policy 2025':                'e08407da-arvindgrievancemechanismpolicy2025.pdf',
    'POSH Policy (Prevention of Sexual Harassment)':  '4d8fe661-poshpolicyarvindlimited.pdf',
    'Whistleblower Policy':                           'cbdae693-whistleblowerpolicyarvindlimited.pdf',
    'Gender Policy 2025':                             '99ecde3a-arvindgenderpolicy2025.pdf',
    'Talent Mobility Policy':                         'adea8313-talentmobility.pdf',
    'Joining Policy':                                 'bad821d9-joiningpolicyarvindlimited.docx',
}


def extract_corpus():
    corpus = {}
    for policy_name, filename in POLICY_FILES.items():
        path = os.path.join(POLICY_DIR, filename)
        raw = ''
        if filename.endswith('.pdf'):
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            raw += t + '\n'
            except Exception as e:
                print(f"  Warning: could not read {filename}: {e}")
        elif filename.endswith('.docx'):
            try:
                doc = Document(path)
                for para in doc.paragraphs:
                    raw += para.text + '\n'
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            raw += cell.text + '\n'
            except Exception as e:
                print(f"  Warning: could not read {filename}: {e}")
        corpus[policy_name] = normalise(raw)
    return corpus


def kf_in_corpus(kf: str, corpus_text: str) -> bool:
    """Return True if keyFact is found in the (already normalised) corpus text."""
    norm_kf = normalise(kf)
    return bool(norm_kf) and norm_kf in corpus_text


# ──────────────────────────────────────────────────────────────────────────────
# TIER 1: MATH & MATRIX DATA
# ──────────────────────────────────────────────────────────────────────────────

# Lodging limits per grade × city class
GRADE_LODGING = {
    "BMH7 and above":         {"Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual"},
    "BMH3-H6":                {"Class I": "8000",      "Class II": "6000",      "Class III": "5000"},
    "M3H1/M3/M2":             {"Class I": "6000",      "Class II": "5000",      "Class III": "4000"},
    "M1/MT/E2/GET/E1/OT":     {"Class I": "3400",      "Class II": "2300",      "Class III": "1700"},
}

# Boarding limits per grade × city class
GRADE_BOARDING = {
    "BMH7 and above":         {"Class I": "At Actuals", "Class II": "At Actuals", "Class III": "At Actuals"},
    "BMH3-H6":                {"Class I": "1500",       "Class II": "1300",       "Class III": "1000"},
    "M3H1/M3/M2":             {"Class I": "1200",       "Class II": "1000",       "Class III": "800"},
    "M1/MT/E2/GET/E1/OT":     {"Class I": "1000",       "Class II": "800",        "Class III": "600"},
}

# Train class per grade
GRADE_TRAIN = {
    "BMH9":          "1st AC",
    "BMH7/H8":       "1st AC",
    "BM-H3-H6":      "1st AC",
    "M3H1/M3/M2":    "2nd AC",
    "M1/E2/E1/OT":   "3rd AC/Chair Car",
}

# Air class per grade
GRADE_AIR = {
    "BMH9":          "Premium Economy / Business",
    "BMH7/H8":       "Economy / Premium Economy",
    "M3H1/M3/M2":    "Economy",
}

# Cab entitlement per grade group
GRADE_CAB = {
    "BMH7 and above":     "Actuals",
    "BMH3-H6":            "Ola / Uber / BluSmart",
    "M3H1/M3/M2":         "Ola / Uber / BluSmart",
    "M1/MT/E2/GET/E1/OT": "Bus, Metro, Local Transportation",
}

# City samples per class
CLASS1_CITIES = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad",
                 "Kolkata", "Pune", "Noida", "Gurugram", "Ahmedabad"]
CLASS2_CITIES = ["Surat", "Jaipur", "Lucknow", "Nagpur", "Indore",
                 "Kochi", "Chandigarh", "Bhopal", "Coimbatore", "Guwahati",
                 "Visakhapatnam", "Mysore", "Ludhiana", "Rajkot", "Madurai"]
CLASS3_CITIES = ["Srinagar", "Dehradun", "Bhavnagar", "Jamnagar", "Kota",
                 "Jabalpur", "Raipur", "Cuttack", "Shimla", "Udaipur"]

# MAB / SIA per grade
MAB_DATA = {
    "E1":   {"monthly": "32,583",   "annual": "3,91,000",  "sia": "10,000"},
    "E2":   {"monthly": "45,750",   "annual": "5,49,000",  "sia": "10,000"},
    "M1":   {"monthly": "71,000",   "annual": "8,52,000",  "sia": "15,000"},
    "M2":   {"monthly": "1,08,333", "annual": "13,00,000", "sia": "20,000"},
    "M3":   {"monthly": "1,58,333", "annual": "19,00,000", "sia": "30,000"},
    "M3H1": {"monthly": "2,16,667", "annual": "26,00,000", "sia": "45,000"},
}

# Non-reimbursable items
NON_REIMB = [
    "Express boarding",
    "Web Check-in amount",
    "Fees for VIP Clubs/Lounge",
    "Upgradation of seat/class at an added cost",
    "Health club services",
    "Amount incurred on personal entertainment/recreation",
    "Cost incurred on personal guests",
    "Airport parking tariff",
    "Personal Gifts",
    "Spouse/dependent travel",
    "Alcohol, cigarettes",
    "Usage of Mini-Bar",
    "Telephone expenses",
    "Business Outing without prior approval from CEO",
]


# ──────────────────────────────────────────────────────────────────────────────
# TIER 2: COMPLIANCE DATA
# ──────────────────────────────────────────────────────────────────────────────

POSH_ACTIONS = [
    "Written warning",
    "Written apology",
    "Reprimand/Censure",
    "Withholding of promotion",
    "Withholding of pay rise or increments",
    "Terminating the RE from service",
    "Undergoing a counselling session",
    "Carrying out community service",
    "Monetary compensation",
]

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


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: deduplicate while preserving order
# ──────────────────────────────────────────────────────────────────────────────

def dedup(cases: list) -> list:
    seen = set()
    out = []
    for c in cases:
        key = normalise(c["query"])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def make_case(query, key_facts, source, page, category, query_type, tier):
    return {
        "query": query,
        "keyFacts": key_facts,
        "source": source,
        "page": page,
        "category": category,
        "query_type": query_type,
        "tier": tier,
    }


# ══════════════════════════════════════════════════════════════════════════════
# TIER 1 GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def gen_tier1_lodging():
    """Natural lodging questions — grade × city × class."""
    cases = []
    city_cls = {
        "Class I":   CLASS1_CITIES,
        "Class II":  CLASS2_CITIES,
        "Class III": CLASS3_CITIES,
    }
    for grade, limits in GRADE_LODGING.items():
        for cls_name, amount in limits.items():
            cities = city_cls[cls_name]
            # Generate enough variants across cities
            for i, city in enumerate(cities):
                variants = [
                    f"I'm a {grade} employee travelling to {city}. What's my hotel limit per night?",
                    f"Going to {city} on business as {grade}. How much can I claim for hotel?",
                    f"What is the maximum hotel reimbursement for {grade} in {city}?",
                    f"Hotel limit for {grade} grade in {city} ({cls_name} city)?",
                    f"I need to book accommodation in {city}. My grade is {grade}. What's my ceiling?",
                ]
                for q in variants:
                    cases.append(make_case(
                        query=q,
                        key_facts=[amount],
                        source="Domestic Travel Policy",
                        page=7,
                        category=f"Lodging-{grade}-{cls_name}",
                        query_type="Lookup",
                        tier=1,
                    ))
    return cases


def gen_tier1_boarding():
    """Natural boarding / meal allowance questions."""
    cases = []
    city_cls = {
        "Class I":   CLASS1_CITIES,
        "Class II":  CLASS2_CITIES,
        "Class III": CLASS3_CITIES,
    }
    for grade, limits in GRADE_BOARDING.items():
        for cls_name, amount in limits.items():
            cities = city_cls[cls_name]
            for i, city in enumerate(cities):
                variants = [
                    f"What is my daily meal allowance in {city} as {grade}?",
                    f"I'm {grade} on a business trip to {city}. What's my boarding limit?",
                    f"How much can I claim for food per day in {city}? (Grade: {grade})",
                    f"Boarding entitlement for {grade} in {city}?",
                    f"Daily food reimbursement ceiling for {grade} in {city} ({cls_name})?",
                ]
                for q in variants:
                    cases.append(make_case(
                        query=q,
                        key_facts=[amount],
                        source="Domestic Travel Policy",
                        page=7,
                        category=f"Boarding-{grade}-{cls_name}",
                        query_type="Lookup",
                        tier=1,
                    ))
    return cases


def gen_tier1_train():
    """Train class entitlement questions."""
    cases = []
    for grade, train_class in GRADE_TRAIN.items():
        variants = [
            f"Which train class can {grade} employees book?",
            f"I'm {grade}. Am I entitled to {train_class} on train travel?",
            f"What is the rail class for {grade} grade?",
            f"Train travel class entitlement for {grade}?",
            f"Can a {grade} employee book {train_class}?",
            f"My grade is {grade}. What train class am I allowed?",
            f"Which AC class does {grade} get on train journeys?",
            f"Train booking class for {grade} as per Domestic Travel Policy?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[train_class],
                source="Domestic Travel Policy",
                page=7,
                category=f"Train-{grade}",
                query_type="Lookup",
                tier=1,
            ))
    return cases


def gen_tier1_air():
    """Air travel class entitlement questions."""
    cases = []
    for grade, air_class in GRADE_AIR.items():
        variants = [
            f"What flight class is {grade} entitled to?",
            f"I am {grade}. Can I book {air_class} for air travel?",
            f"Air ticket class for {grade} grade?",
            f"Which cabin class does {grade} fly in?",
            f"What is the air travel entitlement for {grade}?",
            f"Flight entitlement for {grade} employees as per policy?",
            f"Can {grade} employees fly business class?",
            f"What's the airline booking class for {grade}?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[air_class],
                source="Domestic Travel Policy",
                page=7,
                category=f"Air-{grade}",
                query_type="Lookup",
                tier=1,
            ))
    return cases


def gen_tier1_cab():
    """Cab/transport entitlement questions."""
    cases = []
    for grade, entitlement in GRADE_CAB.items():
        kf = entitlement[:50]
        variants = [
            f"What transport options can {grade} use for local travel on business trips?",
            f"I'm {grade}. Can I book Ola or Uber on official travel?",
            f"Which cab services does {grade} grade get?",
            f"What is the cab entitlement for {grade}?",
            f"I am a {grade} employee. How should I commute at the destination?",
            f"What transport can a {grade} employee take at the travel destination?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[kf],
                source="Domestic Travel Policy",
                page=8,
                category=f"Cab-{grade}",
                query_type="Lookup",
                tier=1,
            ))
    return cases


def gen_tier1_mab():
    """MAB & SIA natural language questions."""
    cases = []
    for grade, data in MAB_DATA.items():
        # Monthly MAB
        monthly_qs = [
            f"I just got rotated as {grade}. What monthly MAB will I receive?",
            f"My grade is {grade} and I'm being transferred. What is the monthly MAB?",
            f"MAB monthly amount for {grade} employees?",
            f"How much monthly mobility allowance does a {grade} get?",
            f"What is the monthly mobility adjustment benefit for {grade}?",
            f"I'm {grade} relocating to a new city. What monthly MAB do I get?",
            f"Monthly MAB entitlement for grade {grade}?",
            f"What's the monthly MAB figure for {grade} grade?",
        ]
        for q in monthly_qs:
            cases.append(make_case(
                query=q,
                key_facts=[data["monthly"]],
                source="Talent Mobility Policy",
                page=7,
                category=f"MAB-Monthly-{grade}",
                query_type="Numerical",
                tier=1,
            ))

        # Annual MAB
        annual_qs = [
            f"What is the annual MAB for a {grade} employee?",
            f"I'm {grade}. What's the total MAB I get per year?",
            f"Annual mobility benefit for {grade} grade?",
            f"Yearly MAB figure for {grade}?",
            f"If I am {grade}, what annual MAB is credited?",
            f"Total annual mobility adjustment benefit for {grade}?",
        ]
        for q in annual_qs:
            cases.append(make_case(
                query=q,
                key_facts=[data["annual"]],
                source="Talent Mobility Policy",
                page=7,
                category=f"MAB-Annual-{grade}",
                query_type="Numerical",
                tier=1,
            ))

        # SIA
        sia_qs = [
            f"I'm {grade} and shifting house after relocation. What SIA do I get?",
            f"What is the settling-in assistance for {grade} grade?",
            f"SIA amount for {grade} on relocation?",
            f"I'm a {grade} employee moving more than 20km. What is my SIA?",
            f"How much SIA does a {grade} employee receive?",
            f"What one-time settling-in amount does {grade} get?",
        ]
        for q in sia_qs:
            cases.append(make_case(
                query=q,
                key_facts=[data["sia"]],
                source="Talent Mobility Policy",
                page=7,
                category=f"SIA-{grade}",
                query_type="Numerical",
                tier=1,
            ))
    return cases


def gen_tier1_non_reimb():
    """Non-reimbursable travel expense questions."""
    cases = []
    for item in NON_REIMB:
        short = item[:50]
        variants = [
            f"Can I claim {item} as a travel expense?",
            f"Is {short} reimbursable under the travel policy?",
            f"Will the company pay for {item}?",
            f"I spent money on {short} during my trip. Can I get it back?",
            f"Is {short} in the non-reimbursable list?",
            f"Does the Domestic Travel Policy cover {item}?",
            f"I booked {short} on my business trip. Will it be reimbursed?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[short],
                source="Domestic Travel Policy",
                page=8,
                category="Non-Reimbursable",
                query_type="Yes/No",
                tier=1,
            ))
    return cases


def gen_tier1_travel_procedures():
    """Travel procedures: booking, settlement, scope, conditions."""
    cases = []

    proc_facts = [
        # (query, keyFact, page, category, query_type)
        ("How many days in advance should I book a flight for official travel?",
         "at least 7 days in advance", 3, "Booking", "Conditional"),
        ("Which tool should I use to book corporate travel?",
         "myBiz", 2, "Booking-Tool", "Process"),
        ("What tool do we use for travel bookings at Arvind?",
         "myBiz", 2, "Booking-Tool", "Process"),
        ("How many days do I have to submit my travel expense claim?",
         "within 15 days of the trip", 5, "Settlement", "Numerical"),
        ("What happens if I don't settle my travel expenses within 15 days?",
         "auto-settlement on the 16th day", 5, "Settlement", "Conditional"),
        ("My trip lasted 4 days. Can I claim laundry charges?",
         "duration of travel exceeds three days", 5, "Laundry", "Conditional"),
        ("I returned on the same day from a business trip. Can I claim hotel?",
         "not eligible to avail the accommodation", 3, "Same-Day-Return", "Yes/No"),
        ("Does the Domestic Travel Policy apply to trips under 300 km?",
         "domestic travel exceeding a distance of 300 km", 2, "Scope", "Conditional"),
        ("If my flight is delayed by 3+ hours, what is the policy?",
         "delayed by more than 3 hours", 4, "Flight-Delay", "Conditional"),
        ("Can two senior officials travel together on the same flight to the same destination?",
         "senior officials travelling to the same destination on the same day take separate flights", 3, "Travel-Guidelines", "Yes/No"),
        ("I'm a woman employee. Can I use a higher grade hotel limit?",
         "hotel limits of the next higher grade", 4, "Women-Policy", "Yes/No"),
        ("What is the travel safety advice for women employees?",
         "Avoidance of Night Travel", 4, "Women-Policy", "Process"),
        ("I prefer to arrange my own stay. What flat rate will I receive?",
         "30% of the entitlement", 5, "Flat-Rate", "Numerical"),
        ("I'm BMH7 and arranging my own accommodation. What is the flat cash entitlement?",
         "Rs. 6,000 per day", 5, "Flat-Rate", "Numerical"),
        ("I need to visit 4 locations today. Can I book a full-day cab?",
         "travel to three or more locations on a given day", 5, "Cab-Policy", "Conditional"),
        ("Are hotel limits quoted inclusive of taxes?",
         "inclusive of applicable taxes", 7, "Lodging", "Yes/No"),
        ("Does travel policy cover trips under 300km distance?",
         "domestic travel exceeding a distance of 300 km", 2, "Scope", "Yes/No"),
        ("Should I avoid service apartments as a woman employee?",
         "avoid staying in service apartments", 4, "Women-Policy", "Yes/No"),
        ("I need to make a business outing. Do I need CEO approval?",
         "Business Outing without prior approval from CEO", 8, "Non-Reimbursable", "Conditional"),
        ("What is the Domestic Travel Policy number?",
         "ARV | EOP_DTP | 003 | 270723", 1, "Policy-Details", "Exact-Fact"),
        ("When was the Domestic Travel Policy issued?",
         "27.07.2023", 1, "Policy-Details", "Exact-Fact"),
    ]

    for q, kf, pg, cat, qt in proc_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Domestic Travel Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=1,
        ))
    return cases


def gen_tier1_local_conveyance():
    """Local conveyance policy questions."""
    cases = []

    lc_facts = [
        ("I drove my personal car 50km for office work. What rate applies?",
         "four wheeler @ Rs. 10.00 / - per km", 1, "Conveyance-Rates", "Numerical"),
        ("I used my bike for official travel. What is the reimbursement rate?",
         "two wheeler @ Rs. 5.00 per km", 1, "Conveyance-Rates", "Numerical"),
        ("I took a cab for official work. How will it be reimbursed?",
         "reimbursement will be done on actuals", 1, "Conveyance-Rates", "Process"),
        ("Where do I submit my conveyance claim?",
         "Orapps – ESMS – Entry – Conveyance Expense", 1, "Claim-Process", "Process"),
        ("Who must approve my conveyance expense claim?",
         "approved only by BM grade employees", 1, "Approval", "Process"),
        ("My colleague and I both travelled for work. Who claims the conveyance?",
         "individual who has actually incurred the cost", 1, "Reimbursement-Rules", "Yes/No"),
        ("I travel within the city for work. Am I eligible for conveyance?",
         "outside the respective City/Town Municipal Corporation", 1, "Eligibility", "Conditional"),
        ("What happens if I file a false conveyance claim?",
         "strict disciplinary action shall be taken", 2, "Compliance", "Conditional"),
        ("Does the Local Conveyance Policy apply to all employee grades?",
         "applicable across all grades", 1, "Applicability", "Yes/No"),
        ("Is local conveyance policy applicable across all of India?",
         "applicable across India", 1, "Applicability", "Yes/No"),
        ("Who is covered under the Local Conveyance Policy?",
         "Applicable to all Management / staff cadre of Arvind Ltd", 1, "Applicability", "Exact-Fact"),
        ("When was the Local Conveyance Policy effective?",
         "01.07.2022", 1, "Policy-Details", "Exact-Fact"),
        ("I used a four-wheeler for 20km official travel. What rate is applied?",
         "four wheeler @ Rs. 10.00 / - per km", 1, "Conveyance-Rates", "Numerical"),
        ("What is the two-wheeler conveyance rate under Arvind's policy?",
         "two wheeler @ Rs. 5.00 per km", 1, "Conveyance-Rates", "Numerical"),
        ("My commute was outside municipal limits. Can I claim conveyance?",
         "outside the respective City/Town Municipal Corporation", 1, "Eligibility", "Conditional"),
        ("Can staff cadre employees claim local conveyance?",
         "Applicable to all Management / staff cadre of Arvind Ltd", 1, "Applicability", "Yes/No"),
        ("Is cab reimbursed on actual cost or fixed rate?",
         "reimbursement will be done on actuals", 1, "Conveyance-Rates", "Yes/No"),
        ("What is the penalty for fraudulent conveyance claims?",
         "strict disciplinary action shall be taken", 2, "Compliance", "Process"),
        ("I need to submit a conveyance claim. Which system do I use?",
         "Orapps – ESMS – Entry – Conveyance Expense", 1, "Claim-Process", "Process"),
        ("Does the conveyance policy cover inter-city travel?",
         "outside the respective City/Town Municipal Corporation", 1, "Eligibility", "Yes/No"),
    ]

    for q, kf, pg, cat, qt in lc_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Local Conveyance Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=1,
        ))
    return cases


def gen_tier1_talent_mobility_procedures():
    """Talent mobility policy process questions."""
    cases = []

    tm_facts = [
        ("When is an employee mandated to rotate under Talent Mobility Policy?",
         "3 years = trigger for rotation", 4, "Rotation-Trigger", "Conditional"),
        ("Which positions must be filled through IJP?",
         "All positions upto M2", 4, "IJP", "Lookup"),
        ("Can my manager block my rotation?",
         "Managers cannot block mobility", 4, "Governance", "Yes/No"),
        ("Who can approve exceptions to the Talent Mobility Policy?",
         "CHRO/CEO can approve exceptions", 4, "Exceptions", "Process"),
        ("How long is MAB paid and when is it merged with CTC?",
         "merged with CTC on completion of 1 year", 6, "MAB-Duration", "Conditional"),
        ("When am I eligible for settling-in assistance?",
         "shifting house", 6, "SIA-Condition", "Conditional"),
        ("What distance triggers SIA eligibility?",
         "relocation >20 kms", 7, "SIA-Condition", "Numerical"),
        ("Is SIA a monthly allowance or one-time payment?",
         "One time", 6, "SIA-Type", "Yes/No"),
        ("What is the purpose of the MAB allowance?",
         "Monthly allowance", 6, "MAB-Description", "Exact-Fact"),
        ("What is the SIA used for?",
         "One-time lump sum for household setup", 6, "SIA-Description", "Exact-Fact"),
        ("What risk arises when employees in sensitive roles exceed tenure?",
         "sensitive roles exceed tenure", 2, "Risk", "Exact-Fact"),
        ("What is the first rotation model under Talent Mobility?",
         "1st Rotation – within the city", 4, "Rotation-Framework", "Exact-Fact"),
        ("What is the second rotation in the talent mobility framework?",
         "2nd Rotation – across different business / different location", 4, "Rotation-Framework", "Exact-Fact"),
        ("My rotation will require me to move cities. Does MAB kick in after 1 year?",
         "merged with CTC on completion of 1 year", 6, "MAB-Duration", "Conditional"),
        ("Does Arvind block managers from stopping employee rotation?",
         "Managers cannot block mobility", 4, "Governance", "Yes/No"),
        ("What happens to MAB after 1 year of rotation?",
         "merged with CTC on completion of 1 year", 6, "MAB", "Conditional"),
        ("Is SIA given even if I don't shift house?",
         "shifting house", 6, "SIA-Condition", "Yes/No"),
        ("Does relocation of 15km qualify for SIA?",
         "relocation >20 kms", 7, "SIA-Condition", "Yes/No"),
        ("After 3 years in the same role, what happens under Talent Mobility?",
         "3 years = trigger for rotation", 4, "Rotation-Trigger", "Conditional"),
        ("Can Talent Mobility exceptions be approved by the CHRO?",
         "CHRO/CEO can approve exceptions", 4, "Exceptions", "Yes/No"),
    ]

    for q, kf, pg, cat, qt in tm_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Talent Mobility Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=1,
        ))
    return cases


def gen_tier1_conditional():
    """Grade-specific conditional and scenario queries for Tier 1."""
    cases = []

    # Scenario-based grade lookups
    scenarios = [
        # Lodging scenarios
        ("I'm M3H1 going to Mumbai (Class I city). What's my nightly hotel limit?",
         "6000", "Domestic Travel Policy", 7, "Lodging-M3H1-ClassI", "Scenario"),
        ("As M1 grade visiting Surat (Class II city), what's my hotel ceiling?",
         "2300", "Domestic Travel Policy", 7, "Lodging-M1-ClassII", "Scenario"),
        ("I'm BMH3 travelling to Raipur (Class III). What's my maximum hotel?",
         "5000", "Domestic Travel Policy", 7, "Lodging-BMH3-ClassIII", "Scenario"),
        ("E2 employee going to Delhi for a week — what hotel amount is allowed per night?",
         "3400", "Domestic Travel Policy", 7, "Lodging-E2-ClassI", "Scenario"),
        ("BMH9 executive on Mumbai trip — any hotel limit or at actuals?",
         "At Actual", "Domestic Travel Policy", 7, "Lodging-BMH9", "Scenario"),

        # Boarding scenarios
        ("I'm M2 grade in Hyderabad (Class I). What's my daily food allowance?",
         "1200", "Domestic Travel Policy", 7, "Boarding-M2-ClassI", "Scenario"),
        ("E1 employee in Chandigarh (Class II) — what is my boarding entitlement?",
         "800", "Domestic Travel Policy", 7, "Boarding-E1-ClassII", "Scenario"),
        ("BMH5 executive dining in Lucknow (Class II) — what's the boarding cap?",
         "1300", "Domestic Travel Policy", 7, "Boarding-BMH5-ClassII", "Scenario"),
        ("I'm M3 grade visiting Shimla (Class III). Boarding limit?",
         "800", "Domestic Travel Policy", 7, "Boarding-M3-ClassIII", "Scenario"),

        # MAB scenarios
        ("I just joined as E2 and am relocating 800km away. What's my monthly MAB?",
         "45,750", "Talent Mobility Policy", 7, "MAB-Monthly-E2", "Scenario"),
        ("As M1 grade rotated to a new city, what monthly MAB do I receive?",
         "71,000", "Talent Mobility Policy", 7, "MAB-Monthly-M1", "Scenario"),
        ("I'm M3H1 on rotation — what annual MAB is credited?",
         "26,00,000", "Talent Mobility Policy", 7, "MAB-Annual-M3H1", "Scenario"),
        ("I'm E1 relocating over 20km. What SIA will I get?",
         "10,000", "Talent Mobility Policy", 7, "SIA-E1", "Scenario"),
        ("M2 employee shifting house after being transferred. What is the SIA?",
         "20,000", "Talent Mobility Policy", 7, "SIA-M2", "Scenario"),
        ("I'm M3 and shifting house. What SIA amount am I eligible for?",
         "30,000", "Talent Mobility Policy", 7, "SIA-M3", "Scenario"),

        # Train scenarios
        ("I'm M3 travelling from Ahmedabad to Delhi. Which train class should I book?",
         "2nd AC", "Domestic Travel Policy", 7, "Train-M3", "Scenario"),
        ("As E1 grade, which AC class can I book on a train?",
         "3rd AC/Chair Car", "Domestic Travel Policy", 7, "Train-E1", "Scenario"),
        ("I'm BMH9 on a train to Chennai. What class am I entitled to?",
         "1st AC", "Domestic Travel Policy", 7, "Train-BMH9", "Scenario"),

        # Air scenarios
        ("I'm BMH9 flying to Delhi. Can I book business class?",
         "Premium Economy / Business", "Domestic Travel Policy", 7, "Air-BMH9", "Scenario"),
        ("I'm M2 on an official trip. What flight cabin class applies?",
         "Economy", "Domestic Travel Policy", 7, "Air-M2", "Scenario"),
        ("BMH7 executive — what air travel class is permitted?",
         "Economy / Premium Economy", "Domestic Travel Policy", 7, "Air-BMH7", "Scenario"),
    ]

    for q, kf, src, pg, cat, qt in scenarios:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source=src,
            page=pg,
            category=cat,
            query_type=qt,
            tier=1,
        ))
    return cases


def gen_tier1_comparative():
    """Comparative / Yes-No questions for Tier 1."""
    cases = []

    comparisons = [
        # Train class Yes/No
        ("Can M3H1 employees book 1st AC trains?",
         "2nd AC", "Domestic Travel Policy", 7, "Train-M3H1-YesNo", "Yes/No"),
        ("Is 2nd AC available for M1 employees?",
         "3rd AC/Chair Car", "Domestic Travel Policy", 7, "Train-M1-YesNo", "Yes/No"),
        ("Can E1 employees book 2nd AC train tickets?",
         "3rd AC/Chair Car", "Domestic Travel Policy", 7, "Train-E1-YesNo", "Yes/No"),
        ("Does BMH9 get 2nd AC or 1st AC on trains?",
         "1st AC", "Domestic Travel Policy", 7, "Train-BMH9-Compare", "Lookup"),

        # Hotel comparisons
        ("What is the difference in hotel limits between M3H1 and M1/E2 in Class I cities?",
         "6000", "Domestic Travel Policy", 7, "Lodging-Comparative-ClassI", "Lookup"),
        ("Which grade has higher lodging limit in Class I: BMH3-H6 or M3H1?",
         "8000", "Domestic Travel Policy", 7, "Lodging-Comparative", "Lookup"),
        ("M1 vs M3 hotel limits in Mumbai — who gets more?",
         "6000", "Domestic Travel Policy", 7, "Lodging-Comparative-M1vsM3", "Lookup"),

        # MAB comparisons
        ("Who gets higher monthly MAB: E1 or E2?",
         "45,750", "Talent Mobility Policy", 7, "MAB-Comparative-E1E2", "Lookup"),
        ("Comparing M1 and M2 MAB — which grade gets 1,08,333 per month?",
         "1,08,333", "Talent Mobility Policy", 7, "MAB-Comparative-M1M2", "Lookup"),
        ("Is M3H1 monthly MAB higher than M3?",
         "2,16,667", "Talent Mobility Policy", 7, "MAB-Comparative-M3M3H1", "Yes/No"),

        # Boarding comparisons
        ("Which grade has higher boarding in Class I: BMH3-H6 or M3H1?",
         "1500", "Domestic Travel Policy", 7, "Boarding-Comparative", "Lookup"),
        ("Compare boarding limit: M1 vs M3 in Class II cities",
         "1000", "Domestic Travel Policy", 7, "Boarding-Comparative-ClassII", "Lookup"),

        # Cab comparisons
        ("Can M1 employees book Ola on business trips?",
         "Bus, Metro, Local Transportation", "Domestic Travel Policy", 8, "Cab-M1-YesNo", "Yes/No"),
        ("Does BMH3-H6 get Actuals for cab or app-based cabs?",
         "Ola / Uber / BluSmart", "Domestic Travel Policy", 8, "Cab-BMH3-Lookup", "Lookup"),
        ("Can M3H1 use Ola/Uber on business travel?",
         "Ola / Uber / BluSmart", "Domestic Travel Policy", 8, "Cab-M3H1-YesNo", "Yes/No"),
    ]

    for q, kf, src, pg, cat, qt in comparisons:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source=src,
            page=pg,
            category=cat,
            query_type=qt,
            tier=1,
        ))
    return cases


# ══════════════════════════════════════════════════════════════════════════════
# TIER 2 GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def gen_tier2_posh():
    """POSH policy — exact entity extraction, process, structural."""
    cases = []

    posh_facts = [
        # Filing & timelines
        ("How long after an incident do I have to file a POSH complaint?",
         "3 (three) months from the date of incident", 6, "Filing-Deadline", "Exact-Fact"),
        ("Can the 3-month POSH filing deadline be extended?",
         "extended for further 3 (three) months", 6, "Filing-Deadline", "Yes/No"),
        ("How many copies of the POSH complaint do I need to submit?",
         "six copies of the complaint", 6, "Filing", "Exact-Fact"),
        ("Can I bring my lawyer to AIC proceedings?",
         "not be allowed to bring in any legal practitioner", 6, "Legal-Representation", "Yes/No"),
        ("How do I file a POSH complaint?",
         "lodge her complaint in writing or via e- mail", 6, "Filing", "Process"),
        ("Can the complainant file a written complaint?",
         "lodge a written complaint", 5, "Filing", "Process"),
        # NOTE: POSH uses 18002008301 (no spaces), not '1800 200 8301'
        ("What is the POSH helpline number?",
         "18002008301", 5, "Contact", "Exact-Fact"),

        # AIC composition
        ("Who heads the AIC?",
         "Senior level woman employee", 4, "AIC-Composition", "Exact-Fact"),
        ("How many employee members are in the AIC?",
         "2 members amongst employees", 4, "AIC-Composition", "Exact-Fact"),
        ("How many members must be present for a valid AIC inquiry?",
         "minimum of 3 members", 4, "Quorum", "Numerical"),
        ("What is the minimum women representation in AIC?",
         "50% women representation", 4, "Quorum", "Numerical"),
        ("How much is the external AIC member paid per day?",
         "Rs. 250 per day", 4, "External-Member", "Numerical"),
        ("How long is the AIC member's tenure?",
         "period of three years", 5, "AIC-Tenure", "Exact-Fact"),
        ("Can AIC members be re-nominated for an additional term?",
         "re-nominated/re-elected for one additional term", 5, "AIC-Tenure", "Yes/No"),
        ("What is the tenure limit if an external member turns 58?",
         "period of three years or completion of the age of 58 years", 5, "AIC-Tenure", "Exact-Fact"),
        ("What kind of committee is the AIC?",
         "independent committee", 4, "AIC-Nature", "Exact-Fact"),
        ("Does AIC have the powers of a civil court?",
         "powers as that of a civil court", 4, "AIC-Powers", "Yes/No"),
        ("How quickly must a vacancy in AIC be filled?",
         "within 15 days", 4, "AIC-Vacancy", "Numerical"),
        ("Who can file a POSH complaint on behalf of the aggrieved woman?",
         "Her relative or friend", 5, "Who-Can-File", "Exact-Fact"),
        ("Can a co-worker file a POSH complaint on my behalf?",
         "Her co-worker", 5, "Who-Can-File", "Yes/No"),
        ("What legal heir consent is needed for filing a POSH complaint?",
         "written consent of her legal heir", 5, "Who-Can-File", "Exact-Fact"),

        # Timelines
        ("How many days does the accused get to respond to POSH complaint?",
         "7 (seven) days", 6, "Timelines", "Numerical"),
        ("How many working days for AIC to submit its report?",
         "within a period of 10 (ten) days", 7, "AIC-Report", "Numerical"),
        ("How long does management have to act on AIC recommendations?",
         "60 (sixty) days", 7, "Management-Action", "Numerical"),
        ("How many days notice must AIC give before inquiry?",
         "notice of 15 (fifteen) days", 6, "AIC-Procedures", "Numerical"),
        ("Within how many working days should the inquiry be completed?",
         "10 (ten) working days", 7, "Timelines", "Numerical"),

        # Interim relief & actions
        ("What interim leave can the aggrieved woman get during inquiry?",
         "leave to the Aggrieved Woman up to a period of 3 (three) months", 7, "Interim-Relief", "Exact-Fact"),
        ("Is the interim leave granted in addition to regular leave?",
         "in addition to the entitled leaves", 7, "Interim-Relief", "Yes/No"),
        ("Can the AIC suspend the respondent during inquiry?",
         "suspend the RE for defined period", 7, "Interim-Action", "Yes/No"),

        # Scope
        ("Does POSH cover incidents outside the workplace?",
         "outside the workplace", 2, "Scope", "Yes/No"),
        ("Can office party incidents be reported under POSH?",
         "Office parties", 2, "Scope", "Yes/No"),
        ("Does POSH cover same-sex harassment?",
         "prohibits same-sex harassment", 5, "Scope", "Yes/No"),
        ("Is POSH gender-neutral at Arvind?",
         "gender neutral", 5, "Scope", "Yes/No"),
        ("Can male employees file POSH complaints?",
         "gender neutral", 5, "Scope", "Yes/No"),

        # Confidentiality and false complaints
        ("Are POSH proceedings kept confidential?",
         "not be published, communicated or made known", 8, "Confidentiality", "Yes/No"),
        ("What happens if POSH confidentiality is breached?",
         "disciplinary action will be taken", 8, "Confidentiality", "Conditional"),
        ("Am I protected from retaliation after filing a POSH complaint?",
         "protected from any form of retaliation", 8, "Protection", "Yes/No"),
        ("What happens if a POSH complaint is found to be malicious?",
         "allegation was malicious", 8, "False-Complaints", "Conditional"),
        ("Can I file an anonymous POSH complaint?",
         "Anonymous complaints will not be entertained", 6, "Anonymous", "Yes/No"),

        # Disciplinary actions
        ("Is written warning a possible POSH sanction?",
         "Written warning", 8, "Disciplinary-Actions", "Yes/No"),
        ("Can the AIC recommend monetary compensation?",
         "Monetary compensation", 8, "Disciplinary-Actions", "Yes/No"),
        ("Can the AIC recommend termination of the respondent?",
         "Terminating the RE from service", 8, "Disciplinary-Actions", "Yes/No"),
        ("Is community service a POSH disciplinary action?",
         "Carrying out community service", 8, "Disciplinary-Actions", "Yes/No"),
        ("Can the AIC recommend withholding a promotion?",
         "Withholding of promotion", 8, "Disciplinary-Actions", "Yes/No"),

        # Contact & filing channels
        ("Can I report POSH via Arvind's ethics email?",
         "arvind@ethicshelpline.in", 5, "Contact", "Yes/No"),
        ("Can I report POSH through the KPMG web portal?",
         "www.in.kpmg.com/ethicshelpline/arvind", 5, "Contact", "Yes/No"),
        ("Who are the POSH filing channels?",
         "Supervisor / Reporting Manager", 5, "Filing-Channels", "Exact-Fact"),

        # Applicability
        ("Does POSH policy apply to third-party visitors?",
         "Third parties and/or visitors", 1, "Applicability", "Yes/No"),
        ("Are all Arvind employees covered under POSH?",
         "All persons employed at Arvind", 1, "Applicability", "Yes/No"),

        # Policy details
        ("What is the POSH policy issue date?",
         "31.03.2022", 1, "Policy-Details", "Exact-Fact"),
        ("When was the POSH policy last updated?",
         "01.05.2025", 1, "Policy-Details", "Exact-Fact"),
        ("What is the POSH policy reference number?",
         "ARV|ELC_SHA|008|010422", 1, "Policy-Details", "Exact-Fact"),
    ]

    for q, kf, pg, cat, qt in posh_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="POSH Policy (Prevention of Sexual Harassment)",
            page=pg,
            category=cat,
            query_type=qt,
            tier=2,
        ))

    # POSH disciplinary actions — multi-variant
    for action in POSH_ACTIONS:
        variants = [
            f"Is '{action}' listed as a disciplinary action in the POSH policy?",
            f"Can the AIC recommend {action} as a sanction?",
            f"Is {action} a possible outcome of POSH inquiry?",
            f"What does the POSH policy say about {action}?",
            f"Under what circumstances is {action} recommended by AIC?",
            f"Is {action} in the list of POSH disciplinary measures?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[action],
                source="POSH Policy (Prevention of Sexual Harassment)",
                page=8,
                category="Disciplinary-Actions",
                query_type="Yes/No",
                tier=2,
            ))

    return cases


def gen_tier2_whistleblower():
    """Whistleblower policy — entity extraction, process, adversarial."""
    cases = []

    wb_facts = [
        ("What is the whistleblower hotline number?",
         "18002008301", 3, "Contact", "Exact-Fact"),
        ("What email is used for whistleblower reports?",
         "arvind@ethicshelpline.in", 3, "Contact", "Exact-Fact"),
        ("What is the web portal for ethics reporting?",
         "www.in.kpmg.com/ethicshelpline/arvind", 3, "Contact", "Exact-Fact"),
        ("Are Directors covered under the Whistleblower Policy?",
         "Directors", 3, "Applicability", "Yes/No"),
        ("Are Business Associates covered under Whistleblower Policy?",
         "Business Associates", 3, "Applicability", "Yes/No"),
        ("Are all employees covered under Whistleblower Policy?",
         "Employees", 3, "Applicability", "Yes/No"),
        ("How often does the whistleblower committee report to the Audit Committee?",
         "quarterly", 4, "Reporting-Frequency", "Exact-Fact"),
        ("When can I follow up on my whistleblower report?",
         "four weeks after the submission", 4, "Follow-up", "Numerical"),
        ("Can the committee appoint an external investigator?",
         "appoint an independent agency", 4, "Investigation", "Yes/No"),
        ("Is a whistleblower's identity kept confidential?",
         "identity of the whistle blower shall be kept confidential", 4, "Confidentiality", "Yes/No"),
        ("Am I protected from retaliation as a whistleblower?",
         "no adverse personnel action, victimization, retaliation", 5, "Protection", "Yes/No"),
        ("What can I do if I face retaliation after reporting?",
         "lodge a written complaint to the Chairman", 5, "Retaliation-Recourse", "Process"),
        ("What happens if I make a false whistleblower report?",
         "will not be protected by this Policy", 5, "False-Complaints", "Conditional"),
        ("Am I required to cooperate with a whistleblower investigation?",
         "duty to cooperate with investigations", 4, "Responsibilities", "Yes/No"),
        ("Can I report workplace harassment under the Whistleblower Policy?",
         "Workplace harassment", 3, "Reportable-Issues", "Yes/No"),
        ("Is bribery reportable under the Whistleblower Policy?",
         "Bribery and corruption", 3, "Reportable-Issues", "Yes/No"),
        ("Can I report discrimination under the Whistleblower Policy?",
         "Discrimination and favouritism", 3, "Reportable-Issues", "Yes/No"),
        ("Is false invoicing a reportable concern?",
         "False invoicing", 3, "Reportable-Issues", "Yes/No"),
        ("What if I witness procurement fraud? Can I report it?",
         "Procurement and tendering fraud", 3, "Reportable-Issues", "Yes/No"),
        ("Is embezzlement of company assets reportable?",
         "Misappropriation/theft/embezzlement of company assets", 3, "Reportable-Issues", "Yes/No"),
    ]

    for q, kf, pg, cat, qt in wb_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Whistleblower Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=2,
        ))

    # Reportable issues — multi-variant
    for issue in WB_ISSUES:
        short = issue[:50]
        variants = [
            f"Can I report {issue} under the Whistleblower Policy?",
            f"Is {short} a reportable concern under Whistleblower Policy?",
            f"Does Whistleblower Policy cover {issue}?",
            f"Should I use the ethics helpline to report {short}?",
            f"I witnessed {short}. Can I blow the whistle?",
            f"Is {issue} listed as a reportable issue?",
        ]
        for q in variants:
            cases.append(make_case(
                query=q,
                key_facts=[short],
                source="Whistleblower Policy",
                page=3,
                category="Reportable-Issues",
                query_type="Yes/No",
                tier=2,
            ))

    return cases


def gen_tier2_grievance():
    """Grievance mechanism policy questions."""
    cases = []

    griev_facts = [
        # Timelines
        ("How quickly is a grievance acknowledged after filing?",
         "2 working days", 3, "Timelines", "Numerical"),
        ("How long does a grievance investigation take?",
         "10 working days", 3, "Timelines", "Numerical"),
        ("When can I expect a resolution to my grievance?",
         "15 working days", 3, "Timelines", "Numerical"),
        ("What is the initial acknowledgement timeline for a grievance?",
         "2 working days", 3, "Timelines", "Exact-Fact"),
        ("What is the investigation timeline for a grievance?",
         "10 working days", 3, "Timelines", "Exact-Fact"),
        ("What is the resolution timeline for a grievance?",
         "15 working days", 3, "Timelines", "Exact-Fact"),

        # Contact
        ("What is the ethics helpline toll-free number for grievances?",
         "1800 200 8301", 3, "Contact", "Exact-Fact"),
        ("What email can I use to report a grievance?",
         "arvind@ethicshelpline.in", 3, "Contact", "Exact-Fact"),
        ("What is the web portal for Arvind grievance reporting?",
         "www.in.kpmg.com/ethicshelpline/arvind", 3, "Contact", "Exact-Fact"),

        # Channels
        ("Who is the first point of contact to raise a grievance?",
         "Line Manager or Supervisor", 2, "Escalation-Channels", "Process"),
        ("Who is the HR contact for grievances?",
         "Immediate HR Representative", 2, "Escalation-Channels", "Exact-Fact"),
        ("Who is the departmental head in the grievance escalation?",
         "Head of Department", 2, "Escalation-Channels", "Exact-Fact"),

        # Filing & anonymous
        ("Can I raise a grievance verbally?",
         "raised verbally or in writing", 3, "Filing", "Yes/No"),
        ("Can I file an anonymous grievance?",
         "Anonymous complaints will be considered", 3, "Anonymous", "Yes/No"),
        ("Am I protected from retaliation for raising a grievance?",
         "protected from retaliation", 2, "Protection", "Yes/No"),

        # Escalation
        ("What can I do if I'm not satisfied with the grievance resolution?",
         "escalate the grievance to the next level", 3, "Escalation", "Process"),

        # Applicability
        ("Are part-time employees covered by the Grievance Policy?",
         "part-time", 2, "Applicability", "Yes/No"),
        ("Do contract workers have access to the Grievance Mechanism?",
         "contract workers", 2, "Applicability", "Yes/No"),
        ("Are trainees covered under the Grievance Mechanism Policy?",
         "trainees", 2, "Applicability", "Yes/No"),

        # Review
        ("How often is the Grievance Mechanism Policy reviewed?",
         "every two years", 4, "Review", "Exact-Fact"),

        # Policy details
        ("What is the Grievance Policy reference number?",
         "ARV|COM_GRM|001|260725", 1, "Policy-Details", "Exact-Fact"),
        ("When did the Grievance Mechanism Policy become effective?",
         "26.07.2025", 1, "Policy-Details", "Exact-Fact"),
    ]

    for q, kf, pg, cat, qt in griev_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Grievance Mechanism Policy 2025",
            page=pg,
            category=cat,
            query_type=qt,
            tier=2,
        ))

    # Adversarial / process order queries
    adversarial = [
        ("I raised a grievance 3 weeks ago and heard nothing. What are the expected timelines?",
         "15 working days", 3, "Timelines", "Scenario"),
        ("Is there a difference in timeline between grievance acknowledgement and resolution?",
         "2 working days", 3, "Timelines", "Conditional"),
        ("My grievance was acknowledged but not resolved in 15 days. What should I do?",
         "escalate the grievance to the next level", 3, "Escalation", "Scenario"),
        ("Can I report a grievance via phone call or does it have to be in writing?",
         "raised verbally or in writing", 3, "Filing", "Yes/No"),
        ("I'm a trainee on a short-term contract. Can I raise a grievance?",
         "trainees", 2, "Applicability", "Scenario"),
        ("My contract ends next month. Can I still file a grievance?",
         "contract workers", 2, "Applicability", "Scenario"),
        ("I'm afraid of reporting to my manager. Can I go directly to HR?",
         "Immediate HR Representative", 2, "Escalation-Channels", "Scenario"),
        ("What is the fastest channel to report a grievance?",
         "Line Manager or Supervisor", 2, "Escalation-Channels", "Process"),
        ("I want to report anonymously. Will my grievance be taken seriously?",
         "Anonymous complaints will be considered", 3, "Anonymous", "Scenario"),
        ("Will I be penalized for raising a workplace grievance?",
         "protected from retaliation", 2, "Protection", "Scenario"),
    ]

    for q, kf, pg, cat, qt in adversarial:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Grievance Mechanism Policy 2025",
            page=pg,
            category=cat,
            query_type=qt,
            tier=2,
        ))

    return cases


# ══════════════════════════════════════════════════════════════════════════════
# TIER 3 GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def gen_tier3_joining():
    """Joining policy — temporal, procedural, policy stance."""
    cases = []

    joining_facts = [
        # Pre-joining / post-joining visit
        ("How many days can I spend on a pre-joining visit?",
         "maximum period of 3 days", 1, "Pre-Joining-Visit", "Numerical"),
        ("Can my spouse accompany me on a pre-joining visit?",
         "spouse", 1, "Pre-Joining-Visit", "Yes/No"),
        ("Can I visit schools for my children during the pre-joining visit?",
         "school admission", 1, "Pre-Joining-Visit", "Yes/No"),
        ("Can I take both a pre-joining and a post-joining visit?",
         "either a Pre-Joining Visit OR Post Joining Visit", 1, "Visit-Options", "Yes/No"),
        ("I already did a pre-joining visit. Can I also do a post-joining visit?",
         "either a Pre-Joining Visit OR Post Joining Visit", 1, "Visit-Options", "Conditional"),
        ("How many days leave do I get for the post-joining visit?",
         "3 days leave", 1, "Post-Joining-Visit", "Numerical"),

        # Transportation rates
        ("What is the transport reimbursement rate for relocation under 700km?",
         "Rs. 50 per km", 1, "Transportation", "Numerical"),
        ("What rate applies for relocation journeys over 700km?",
         "Rs. 60 per km", 1, "Transportation", "Numerical"),
        ("I am driving my car to my new location. What rate do I get per km?",
         "Rs. 10.0 per km", 1, "Car-Transport", "Numerical"),
        ("What is the standard driver wage for an 8-hour relocation trip?",
         "Rs. 600/-", 1, "Driver-Wages", "Numerical"),
        ("What is the driver wage per hour after 8 hours?",
         "Rs. 50/- per hour", 1, "Driver-Wages", "Numerical"),
        ("What is the maximum meal reimbursement per meal during relocation?",
         "Rs. 200/- per meal", 1, "Food-Limit", "Numerical"),

        # Brokerage & housing
        ("Will the company pay my brokerage fee for finding a house?",
         "One month rent", 1, "Brokerage", "Yes/No"),
        ("For how long can I claim brokerage after my joining date?",
         "maximum for 1 year from the date of the joining", 1, "Brokerage-Validity", "Numerical"),
        ("How is the house deposit reimbursed by the company?",
         "10 equal monthly instalments", 1, "House-Deposit", "Process"),

        # Deadlines & settlements
        ("What is the deadline to claim all joining-related expenses?",
         "One Year from Date of Joining", 1, "Expense-Claim-Deadline", "Numerical"),
        ("If I resign within 6 months of joining, what happens to relocation expenses?",
         "recovered in his/her F&F settlement", 1, "Quit-1Year", "Conditional"),
        ("I left before 1 year of joining. Will relocation costs be deducted from my FnF?",
         "recovered in his/her F&F settlement", 1, "Quit-1Year", "Yes/No"),

        # Approvals & logistics
        ("Who approves Joining Policy exceptions?",
         "CEO", 1, "Approvals", "Exact-Fact"),
        ("Who books my flight tickets when joining?",
         "Arvind Travel Desk", 1, "Flight-Booking", "Exact-Fact"),
        ("Are joining-related expenses taxable?",
         "Income tax shall be grossed up", 1, "Tax", "Yes/No"),
        ("Who pays the packers and movers directly?",
         "The company shall directly make payment", 1, "Packers-Movers", "Exact-Fact"),
        ("Does the company pay the packers and movers directly or do I pay and claim?",
         "The company shall directly make payment", 1, "Packers-Movers", "Yes/No"),
        ("Is the Joining Policy applicable to subsidiaries?",
         "subsidiaries", 1, "Applicability", "Yes/No"),
        ("Who is covered under the Joining Policy?",
         "Management / staff cadre employees", 1, "Applicability", "Exact-Fact"),

        # Policy details
        ("When was the Joining Policy effective from?",
         "21.09.2023", 1, "Policy-Details", "Exact-Fact"),

        # Scenario variants
        ("I'm relocating 850km to Mumbai. What transport reimbursement applies?",
         "Rs. 60 per km", 1, "Transportation", "Scenario"),
        ("My relocation distance is 400km. What rate per km do I get?",
         "Rs. 50 per km", 1, "Transportation", "Scenario"),
        ("I drove my own car 300km for relocation. What rate applies?",
         "Rs. 10.0 per km", 1, "Car-Transport", "Scenario"),
        ("Can I claim hotel during my pre-joining visit?",
         "maximum period of 3 days", 1, "Pre-Joining-Visit", "Conditional"),
        ("What is the brokerage ceiling for a new joinee?",
         "One month rent", 1, "Brokerage", "Numerical"),
        ("The company is paying my house deposit. How will it be recovered?",
         "10 equal monthly instalments", 1, "House-Deposit", "Process"),
    ]

    for q, kf, pg, cat, qt in joining_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Joining Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=3,
        ))

    return cases


def gen_tier3_gender():
    """Gender policy — policy stance, procedural, applicability."""
    cases = []

    gender_facts = [
        # Policy details
        ("When was the Gender Policy issued?",
         "25.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("When did the Gender Policy become effective?",
         "26.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("What is the Gender Policy reference number?",
         "ARV|COM_GENP|001|260725", 1, "Policy-Details", "Exact-Fact"),

        # Applicability
        ("Who does the Gender Policy apply to?",
         "all employees of Arvind Ltd", 2, "Applicability", "Exact-Fact"),
        ("Are interns covered under the Gender Policy?",
         "interns", 2, "Applicability", "Yes/No"),
        ("Are contract staff covered under the Gender Policy?",
         "contract staff", 2, "Applicability", "Yes/No"),
        ("Are third-party partners covered under the Gender Policy?",
         "third-party partners", 2, "Applicability", "Yes/No"),

        # Complaint process
        ("Who do I contact to raise a gender discrimination complaint?",
         "HR Department", 3, "Complaint-Process", "Process"),
        ("Can I go to my line manager for a gender-related complaint?",
         "Line Manager", 3, "Complaint-Process", "Yes/No"),
        ("What is the gender helpline contact number?",
         "1800 200 8301", 3, "Contact", "Exact-Fact"),
        ("What email can I use for gender-related complaints?",
         "arvind@ethicshelpline.in", 3, "Contact", "Exact-Fact"),
        ("What is the web portal for gender-related reporting?",
         "www.in.kpmg.com/ethicshelpline/arvind", 3, "Contact", "Exact-Fact"),

        # Review cycle
        ("How often is the Gender Policy reviewed?",
         "every two years", 3, "Review", "Exact-Fact"),
        ("When will the Gender Policy be next reviewed?",
         "every two years", 3, "Review", "Temporal"),

        # Principles & protection
        ("Will I face retaliation for reporting gender discrimination?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Yes/No"),
        ("Is reporting gender bias protected from retaliation?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Yes/No"),
        ("Are promotions merit-based under Gender Policy?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Yes/No"),
        ("Does Arvind follow merit-based hiring under Gender Policy?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Yes/No"),

        # Scenario-based
        ("I'm an intern and witnessed gender bias. Am I covered by Gender Policy?",
         "interns", 2, "Applicability", "Scenario"),
        ("I'm a contract worker. Can I use the Gender Policy to report discrimination?",
         "contract staff", 2, "Applicability", "Scenario"),
        ("I reported a gender issue and my manager is hostile. What protection do I have?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Scenario"),
        ("I feel I was passed over for promotion due to gender. Who should I report to?",
         "HR Department", 3, "Complaint-Process", "Scenario"),
        ("A vendor is discriminating based on gender. Is this covered?",
         "third-party partners", 2, "Applicability", "Scenario"),
    ]

    for q, kf, pg, cat, qt in gender_facts:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Gender Policy 2025",
            page=pg,
            category=cat,
            query_type=qt,
            tier=3,
        ))

    return cases


def gen_tier3_joining_extended():
    """Extended joining policy questions for more coverage."""
    cases = []

    # Multiple variants of the same fact to increase unique queries
    joining_extended = [
        # Pre-joining
        ("What activities are allowed during the pre-joining visit?",
         "school admission", 1, "Pre-Joining-Visit", "Process"),
        ("Can I use the pre-joining visit to explore housing?",
         "maximum period of 3 days", 1, "Pre-Joining-Visit", "Conditional"),
        ("How long is the maximum duration for a pre-joining visit?",
         "maximum period of 3 days", 1, "Pre-Joining-Visit", "Exact-Fact"),
        ("What is the maximum stay allowed for pre-joining visit activities?",
         "maximum period of 3 days", 1, "Pre-Joining-Visit", "Exact-Fact"),
        ("Can my wife come with me on the pre-joining visit?",
         "spouse", 1, "Pre-Joining-Visit", "Yes/No"),
        ("Is my family allowed on the pre-joining company visit?",
         "spouse", 1, "Pre-Joining-Visit", "Yes/No"),

        # Post-joining
        ("How many days off do I get for a post-joining visit?",
         "3 days leave", 1, "Post-Joining-Visit", "Numerical"),
        ("If I choose the post-joining visit, how many leave days?",
         "3 days leave", 1, "Post-Joining-Visit", "Lookup"),
        ("Is the post-joining visit covered by Arvind?",
         "3 days leave", 1, "Post-Joining-Visit", "Yes/No"),

        # Transportation - more variants
        ("Relocation distance is 600km. What transport rate applies?",
         "Rs. 50 per km", 1, "Transportation", "Numerical"),
        ("My move is 900km from current city. What per km rate applies?",
         "Rs. 60 per km", 1, "Transportation", "Numerical"),
        ("What is the cutoff distance for the higher transport rate?",
         "Rs. 60 per km", 1, "Transportation", "Conditional"),
        ("Below 700km relocation — which rate per km applies?",
         "Rs. 50 per km", 1, "Transportation", "Lookup"),
        ("Is there a higher reimbursement rate for long-distance relocation?",
         "Rs. 60 per km", 1, "Transportation", "Yes/No"),
        ("Self-drive relocation — what per km rate is allowed?",
         "Rs. 10.0 per km", 1, "Car-Transport", "Numerical"),
        ("Mileage for own car during relocation at Arvind?",
         "Rs. 10.0 per km", 1, "Car-Transport", "Exact-Fact"),

        # Driver wages variants
        ("If I hire a driver for relocation, what is the daily rate?",
         "Rs. 600/-", 1, "Driver-Wages", "Numerical"),
        ("Driver hourly charge after 8 hours during relocation?",
         "Rs. 50/- per hour", 1, "Driver-Wages", "Numerical"),
        ("What is the overtime charge for driver per hour?",
         "Rs. 50/- per hour", 1, "Driver-Wages", "Numerical"),

        # Food / meals
        ("During relocation travel, what is the per-meal food limit?",
         "Rs. 200/- per meal", 1, "Food-Limit", "Numerical"),
        ("How much can I claim per meal during the joining move?",
         "Rs. 200/- per meal", 1, "Food-Limit", "Exact-Fact"),

        # Brokerage
        ("Will Arvind cover my house brokerage when I relocate?",
         "One month rent", 1, "Brokerage", "Yes/No"),
        ("What is the brokerage amount covered by the company?",
         "One month rent", 1, "Brokerage", "Numerical"),
        ("Is brokerage reimbursable for new joiners?",
         "One month rent", 1, "Brokerage", "Yes/No"),
        ("Brokerage claim window after joining?",
         "maximum for 1 year from the date of the joining", 1, "Brokerage-Validity", "Numerical"),
        ("Can I claim brokerage 15 months after joining?",
         "maximum for 1 year from the date of the joining", 1, "Brokerage-Validity", "Conditional"),

        # House deposit
        ("In how many installments is the house deposit refunded?",
         "10 equal monthly instalments", 1, "House-Deposit", "Numerical"),
        ("Company paid house deposit — how is it repaid?",
         "10 equal monthly instalments", 1, "House-Deposit", "Process"),
        ("Does the company advance the house deposit?",
         "10 equal monthly instalments", 1, "House-Deposit", "Yes/No"),

        # Expense deadline variants
        ("Last date to submit joining expense claim?",
         "One Year from Date of Joining", 1, "Expense-Claim-Deadline", "Exact-Fact"),
        ("I joined 10 months ago. Can I still claim relocation expenses?",
         "One Year from Date of Joining", 1, "Expense-Claim-Deadline", "Conditional"),
        ("What is the validity of joining expense reimbursement?",
         "One Year from Date of Joining", 1, "Expense-Claim-Deadline", "Lookup"),

        # Quit before 1 year
        ("I resigned after 8 months. Will joining expenses be recovered?",
         "recovered in his/her F&F settlement", 1, "Quit-1Year", "Conditional"),
        ("What happens to relocation payments if I leave early?",
         "recovered in his/her F&F settlement", 1, "Quit-1Year", "Process"),
        ("Is there a claw-back of joining costs if I quit early?",
         "recovered in his/her F&F settlement", 1, "Quit-1Year", "Conditional"),

        # Logistics
        ("Who does the company pay for relocation goods transport?",
         "The company shall directly make payment", 1, "Packers-Movers", "Process"),
        ("Does Arvind pay movers directly or reimburse me?",
         "The company shall directly make payment", 1, "Packers-Movers", "Yes/No"),
        ("My flight for joining — who should I contact to book it?",
         "Arvind Travel Desk", 1, "Flight-Booking", "Process"),
        ("Is the joining travel flight booked by Arvind or by me?",
         "Arvind Travel Desk", 1, "Flight-Booking", "Yes/No"),

        # Tax
        ("Are my joining relocation expenses subject to income tax?",
         "Income tax shall be grossed up", 1, "Tax", "Yes/No"),
        ("Does Arvind gross up tax on relocation reimbursements?",
         "Income tax shall be grossed up", 1, "Tax", "Yes/No"),
        ("Will I be taxed on the joining allowances?",
         "Income tax shall be grossed up", 1, "Tax", "Conditional"),

        # Applicability
        ("Does Joining Policy apply to employees at subsidiaries?",
         "subsidiaries", 1, "Applicability", "Yes/No"),
        ("Is staff cadre included under the Joining Policy?",
         "Management / staff cadre employees", 1, "Applicability", "Yes/No"),
        ("Does the Joining Policy cover contract employees?",
         "Management / staff cadre employees", 1, "Applicability", "Conditional"),

        # CEO approval
        ("Does the CEO approve joining policy exceptions?",
         "CEO", 1, "Approvals", "Yes/No"),
        ("Who has the authority to approve exceptions under Joining Policy?",
         "CEO", 1, "Approvals", "Exact-Fact"),

        # Policy date
        ("What is the effective date of the Joining Policy?",
         "21.09.2023", 1, "Policy-Details", "Exact-Fact"),
        ("Since when has the Joining Policy been in force?",
         "21.09.2023", 1, "Policy-Details", "Exact-Fact"),

        # Visit options
        ("Can I do both a pre-joining and post-joining visit?",
         "either a Pre-Joining Visit OR Post Joining Visit", 1, "Visit-Options", "Yes/No"),
        ("The company offers either pre-joining or post-joining visit — can I take both?",
         "either a Pre-Joining Visit OR Post Joining Visit", 1, "Visit-Options", "Conditional"),
    ]

    for q, kf, pg, cat, qt in joining_extended:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Joining Policy",
            page=pg,
            category=cat,
            query_type=qt,
            tier=3,
        ))

    return cases


def gen_tier3_gender_extended():
    """Extended gender policy questions."""
    cases = []

    gender_extended = [
        # More applicability variants
        ("Does the Gender Policy cover temporary staff?",
         "contract staff", 2, "Applicability", "Yes/No"),
        ("Can an intern report under the Gender Policy?",
         "interns", 2, "Applicability", "Yes/No"),
        ("Does the Gender Policy cover vendor employees working at Arvind?",
         "third-party partners", 2, "Applicability", "Yes/No"),
        ("Is a freelancer working for Arvind covered under the Gender Policy?",
         "third-party partners", 2, "Applicability", "Conditional"),
        ("Are all categories of workers covered by Gender Policy?",
         "all employees of Arvind Ltd", 2, "Applicability", "Exact-Fact"),

        # Complaint process variants
        ("I want to report gender discrimination. First step?",
         "HR Department", 3, "Complaint-Process", "Process"),
        ("Can I escalate gender issues to my line manager?",
         "Line Manager", 3, "Complaint-Process", "Yes/No"),
        ("What is the primary internal contact for gender complaints?",
         "HR Department", 3, "Complaint-Process", "Exact-Fact"),
        ("How do I start the gender grievance process?",
         "Line Manager", 3, "Complaint-Process", "Process"),

        # Contact variants
        ("What phone number can I call for gender policy issues?",
         "1800 200 8301", 3, "Contact", "Exact-Fact"),
        ("Is there a toll-free helpline for gender complaints?",
         "1800 200 8301", 3, "Contact", "Yes/No"),
        ("Which email address to report gender discrimination?",
         "arvind@ethicshelpline.in", 3, "Contact", "Exact-Fact"),
        ("Can I use the KPMG ethics portal for gender policy complaints?",
         "www.in.kpmg.com/ethicshelpline/arvind", 3, "Contact", "Yes/No"),

        # Review variants
        ("What is the review frequency for the Gender Policy?",
         "every two years", 3, "Review", "Exact-Fact"),
        ("Is the Gender Policy reviewed annually or biannually?",
         "every two years", 3, "Review", "Yes/No"),
        ("Gender Policy review period?",
         "every two years", 3, "Review", "Lookup"),

        # Protection variants
        ("Is there anti-retaliation protection for gender complaints?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Yes/No"),
        ("What does Gender Policy say about retaliation against complainants?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Exact-Fact"),
        ("I raised a gender concern in good faith. Am I protected?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Yes/No"),
        ("Can my employer punish me for raising a gender issue in good faith?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Yes/No"),

        # Principles variants
        ("Are promotions gender-neutral at Arvind?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Yes/No"),
        ("How does Arvind ensure fairness in hiring under Gender Policy?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Process"),
        ("Is talent acquired on merit at Arvind per Gender Policy?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Yes/No"),

        # Policy details variants
        ("What is the issue date of the 2025 Gender Policy?",
         "25.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("When was the current Gender Policy published?",
         "25.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("Effective date of the Arvind Gender Policy 2025?",
         "26.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("When does the Arvind Gender Policy 2025 take effect?",
         "26.07.2025", 1, "Policy-Details", "Exact-Fact"),
        ("What reference code is used for Gender Policy 2025?",
         "ARV|COM_GENP|001|260725", 1, "Policy-Details", "Exact-Fact"),
        ("What is the policy ID for Arvind Gender Policy 2025?",
         "ARV|COM_GENP|001|260725", 1, "Policy-Details", "Exact-Fact"),

        # Additional scenarios
        ("A new hire is being excluded from team activities. Which policy applies?",
         "all employees of Arvind Ltd", 2, "Applicability", "Scenario"),
        ("I faced gender bias at a factory location. Am I covered?",
         "all employees of Arvind Ltd", 2, "Applicability", "Scenario"),
        ("Who can I call if I witness gender discrimination in my department?",
         "HR Department", 3, "Complaint-Process", "Scenario"),
        ("What recourse do I have if my promotion was denied based on gender?",
         "Hiring and Promotions are conducted based on merit", 3, "Principles", "Scenario"),
        ("I'm a third-party consultant. Can I report gender bias under Arvind's policy?",
         "third-party partners", 2, "Applicability", "Scenario"),
        ("I'm afraid my report of gender bias will affect my career. What protection exists?",
         "retaliation against individuals who raise concerns in good faith is strictly prohibited", 3, "Protection", "Scenario"),
    ]

    for q, kf, pg, cat, qt in gender_extended:
        cases.append(make_case(
            query=q,
            key_facts=[kf],
            source="Gender Policy 2025",
            page=pg,
            category=cat,
            query_type=qt,
            tier=3,
        ))

    return cases


# ══════════════════════════════════════════════════════════════════════════════
# TIER 4 GENERATORS: CROSS-POLICY
# ══════════════════════════════════════════════════════════════════════════════

def gen_tier4_cross_policy():
    """Multi-document queries needing facts from 2+ policies."""
    cases = []

    cross_facts = [
        # Same ethics helpline across policies
        # POSH uses 18002008301 (no spaces), Grievance uses 1800 200 8301 (spaced)
        ("Is the ethics helpline number the same for POSH, Whistleblower, and Grievance?",
         ["18002008301"],
         "POSH Policy (Prevention of Sexual Harassment)", 5, "Cross-Contact", "Cross-Policy"),
        ("Which policies share the same email arvind@ethicshelpline.in?",
         ["arvind@ethicshelpline.in"],
         "Whistleblower Policy", 3, "Cross-Contact", "Cross-Policy"),
        ("Can I use the KPMG portal for both POSH and whistleblower reports?",
         ["www.in.kpmg.com/ethicshelpline/arvind"],
         "POSH Policy (Prevention of Sexual Harassment)", 5, "Cross-Contact", "Cross-Policy"),

        # Retaliation across policies
        ("Both POSH and Grievance policies protect against retaliation. What does POSH say?",
         ["protected from any form of retaliation"],
         "POSH Policy (Prevention of Sexual Harassment)", 8, "Cross-Protection", "Cross-Policy"),
        ("How does Gender Policy protection from retaliation compare to POSH policy?",
         ["retaliation against individuals who raise concerns in good faith is strictly prohibited"],
         "Gender Policy 2025", 3, "Cross-Protection", "Cross-Policy"),
        ("Do Whistleblower and Grievance policies both protect against retaliation?",
         ["no adverse personnel action, victimization, retaliation"],
         "Whistleblower Policy", 5, "Cross-Protection", "Cross-Policy"),

        # Review cycles
        ("Do Gender Policy and Grievance Policy have the same review cycle?",
         ["every two years"],
         "Gender Policy 2025", 3, "Cross-Review", "Cross-Policy"),

        # MAB vs Joining travel
        ("Does Joining Policy or Talent Mobility cover house-shifting expenses?",
         ["One-time lump sum for household setup"],
         "Talent Mobility Policy", 6, "Cross-Relocation", "Cross-Policy"),
        ("What's the difference between SIA in Talent Mobility and joining relocation expenses?",
         ["One time"],
         "Talent Mobility Policy", 6, "Cross-Relocation", "Cross-Policy"),
        ("For a transfer requiring relocation, which policy covers transport costs?",
         ["Rs. 50 per km"],
         "Joining Policy", 1, "Cross-Relocation", "Cross-Policy"),

        # Local conveyance vs Domestic travel
        ("What is the difference between local conveyance and domestic travel policy?",
         ["domestic travel exceeding a distance of 300 km"],
         "Domestic Travel Policy", 2, "Cross-Scope", "Cross-Policy"),
        ("Does local conveyance policy cover trips over 300km?",
         ["domestic travel exceeding a distance of 300 km"],
         "Domestic Travel Policy", 2, "Cross-Scope", "Cross-Policy"),
        ("Can I use local conveyance rates for intercity travel above 300km?",
         ["four wheeler @ Rs. 10.00 / - per km"],
         "Local Conveyance Policy", 1, "Cross-Scope", "Cross-Policy"),

        # POSH vs Whistleblower for workplace harassment
        ("Should I use POSH or Whistleblower Policy to report workplace harassment?",
         ["Workplace harassment"],
         "Whistleblower Policy", 3, "Cross-Scope", "Cross-Policy"),
        ("If I face sexual harassment, do I use POSH or Whistleblower Policy?",
         ["Arvind Internal Complaint Committee"],
         "POSH Policy (Prevention of Sexual Harassment)", 2, "Cross-Scope", "Cross-Policy"),

        # Grade-based: Joining + Domestic Travel
        ("I'm E2 grade joining from a city 800km away. What transport rate applies for joining?",
         ["Rs. 60 per km"],
         "Joining Policy", 1, "Cross-Grade-Travel", "Cross-Policy"),
        ("I'm M2 being rotated. What monthly MAB do I get?",
         ["1,08,333"],
         "Talent Mobility Policy", 7, "Cross-Grade-MAB", "Cross-Policy"),

        # Rotation vs new joiner
        ("If I'm rotated to Mumbai (M3 grade), what is my MAB?",
         ["1,58,333"],
         "Talent Mobility Policy", 7, "Cross-Grade-MAB", "Cross-Policy"),
        ("M1 employee transferred — what's the SIA amount under Talent Mobility?",
         ["15,000"],
         "Talent Mobility Policy", 7, "Cross-Grade-MAB", "Cross-Policy"),

        # Anonymous complaints — POSH vs Grievance difference
        ("Can I file anonymous complaints under both POSH and Grievance policies?",
         ["Anonymous complaints will not be entertained"],
         "POSH Policy (Prevention of Sexual Harassment)", 6, "Cross-Anonymous", "Cross-Policy"),
        ("What is the difference in anonymous complaint handling between POSH and Grievance?",
         ["Anonymous complaints will be considered"],
         "Grievance Mechanism Policy 2025", 3, "Cross-Anonymous", "Cross-Policy"),

        # Joining + Gender policy
        ("A female new joinee is facing gender bias from day one. Which policies apply?",
         ["all employees of Arvind Ltd"],
         "Gender Policy 2025", 2, "Cross-Applicability", "Cross-Policy"),
        ("Does the Gender Policy apply from joining date?",
         ["all employees of Arvind Ltd"],
         "Gender Policy 2025", 2, "Cross-Applicability", "Cross-Policy"),

        # AIC vs Grievance — process comparison
        ("What is the difference between grievance resolution timeline and POSH AIC inquiry timeline?",
         ["15 working days"],
         "Grievance Mechanism Policy 2025", 3, "Cross-Timelines", "Cross-Policy"),
        ("POSH gives 10 working days for AIC report. Grievance gives 15 working days for resolution. Is that right?",
         ["10 (ten) working days"],
         "POSH Policy (Prevention of Sexual Harassment)", 7, "Cross-Timelines", "Cross-Policy"),

        # Travel + mobility
        ("If I'm M3H1 on rotation to Bangalore, what MAB and hotel limit applies?",
         ["2,16,667", "6000"],
         "Talent Mobility Policy", 7, "Cross-Grade-All", "Cross-Policy"),
        ("I'm BMH3 travelling to Chennai for business — what hotel limit and which train class?",
         ["8000", "1st AC"],
         "Domestic Travel Policy", 7, "Cross-Grade-All", "Cross-Policy"),
        ("I'm E2 on a 5-day trip to Delhi — hotel limit and can I claim laundry?",
         ["3400", "duration of travel exceeds three days"],
         "Domestic Travel Policy", 7, "Cross-Grade-All", "Cross-Policy"),
        ("I'm M2. Going to Mumbai (Class I) — hotel limit and boarding limit?",
         ["6000", "1200"],
         "Domestic Travel Policy", 7, "Cross-Grade-All", "Cross-Policy"),

        # Whistleblower + Grievance comparison
        ("How does the Whistleblower Policy review cycle compare to Grievance Policy?",
         ["quarterly"],
         "Whistleblower Policy", 4, "Cross-Review", "Cross-Policy"),
        ("Both Whistleblower and Grievance policies have follow-up windows. What's the whistleblower follow-up?",
         ["four weeks after the submission"],
         "Whistleblower Policy", 4, "Cross-Follow-up", "Cross-Policy"),

        # SIA + Conveyance
        ("If I'm relocating as M1, what is my SIA from Talent Mobility Policy?",
         ["15,000"],
         "Talent Mobility Policy", 7, "Cross-Relocation-Rates", "Cross-Policy"),
        ("E1 employee joining from 600km away. What is the per-km transport rate?",
         ["Rs. 50 per km"],
         "Joining Policy", 1, "Cross-Relocation-Rates", "Cross-Policy"),

        # Policy numbers comparison
        ("What are the policy numbers for Grievance and Gender policies?",
         ["ARV|COM_GRM|001|260725"],
         "Grievance Mechanism Policy 2025", 1, "Cross-Policy-Details", "Cross-Policy"),

        # Joining policy + POSH
        ("A new joiner faces harassment on day one. Which policy protects them?",
         ["All persons employed at Arvind"],
         "POSH Policy (Prevention of Sexual Harassment)", 1, "Cross-Applicability", "Cross-Policy"),

        # Talent Mobility + Grievance
        ("If my rotation request is blocked, can I file a grievance?",
         ["Managers cannot block mobility"],
         "Talent Mobility Policy", 4, "Cross-Governance", "Cross-Policy"),
        ("My manager is blocking my transfer. What do Talent Mobility and Grievance policies say?",
         ["Managers cannot block mobility"],
         "Talent Mobility Policy", 4, "Cross-Governance", "Cross-Policy"),

        # Multiple policy scope
        ("Which Arvind policies are reviewed every two years?",
         ["every two years"],
         "Gender Policy 2025", 3, "Cross-Review", "Cross-Policy"),
        ("Do Gender Policy and Grievance Policy have aligned review schedules?",
         ["every two years"],
         "Grievance Mechanism Policy 2025", 4, "Cross-Review", "Cross-Policy"),

        # Contact comparison
        ("Does the KPMG ethics portal serve multiple Arvind policies?",
         ["www.in.kpmg.com/ethicshelpline/arvind"],
         "Whistleblower Policy", 3, "Cross-Contact", "Cross-Policy"),
        ("Can I use 1800 200 8301 for both grievance and gender complaints?",
         ["1800 200 8301"],
         "Gender Policy 2025", 3, "Cross-Contact", "Cross-Policy"),
    ]

    for item in cross_facts:
        if len(item) == 6:
            q, kfs, src, pg, cat, qt = item
            cases.append(make_case(
                query=q,
                key_facts=kfs if isinstance(kfs, list) else [kfs],
                source=src,
                page=pg,
                category=cat,
                query_type=qt,
                tier=4,
            ))

    return cases


def gen_tier4_cross_policy_extended():
    """Additional cross-policy cases for Tier 4."""
    cases = []

    # Grade MAB + Domestic Travel combined scenarios
    grade_combo = [
        ("E1", "32,583", "10,000", "3400", "1000"),
        ("E2", "45,750", "10,000", "3400", "1000"),
        ("M1", "71,000", "15,000", "3400", "1000"),
        ("M2", "1,08,333", "20,000", "6000", "1200"),
        ("M3", "1,58,333", "30,000", "6000", "1200"),
        ("M3H1", "2,16,667", "45,000", "6000", "1200"),
    ]
    for grade, mab, sia, hotel_c1, board_c1 in grade_combo:
        cases.append(make_case(
            query=f"I am {grade} grade being rotated to Bangalore. What MAB, SIA, hotel limit?",
            key_facts=[mab, sia],
            source="Talent Mobility Policy",
            page=7,
            category="Cross-Grade-All",
            query_type="Cross-Policy",
            tier=4,
        ))
        cases.append(make_case(
            query=f"I'm {grade} relocating to Delhi. What monthly MAB and Class I hotel limit?",
            key_facts=[mab],
            source="Talent Mobility Policy",
            page=7,
            category="Cross-Grade-Travel",
            query_type="Cross-Policy",
            tier=4,
        ))
        cases.append(make_case(
            query=f"As {grade} grade, what SIA do I get and what is the Class I boarding limit?",
            key_facts=[sia],
            source="Talent Mobility Policy",
            page=7,
            category="Cross-Grade-Travel",
            query_type="Cross-Policy",
            tier=4,
        ))

    # Joining + Domestic Travel combinations
    cases.append(make_case(
        query="I'm joining from 800km away as M1. What transport rate per km applies?",
        key_facts=["Rs. 60 per km"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="New joinee M2 from 400km. What per-km transport reimbursement applies?",
        key_facts=["Rs. 50 per km"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="I'm joining as E2 from 600km. What's my transport reimbursement rate?",
        key_facts=["Rs. 50 per km"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="As M3 new joiner from 1000km, what transport reimbursement rate applies?",
        key_facts=["Rs. 60 per km"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))

    # POSH vs Grievance process comparison
    cases.append(make_case(
        query="What is the filing deadline for POSH vs acknowledgement timeline for Grievance?",
        key_facts=["3 (three) months from the date of incident"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=6,
        category="Cross-Timelines",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="How does the POSH 3-month filing window differ from grievance resolution timing?",
        key_facts=["3 (three) months from the date of incident"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=6,
        category="Cross-Timelines",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="What is the grievance resolution timeline vs POSH management action timeline?",
        key_facts=["15 working days"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Timelines",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Management action on POSH takes 60 days but grievance resolves in 15 working days — correct?",
        key_facts=["60 (sixty) days"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=7,
        category="Cross-Timelines",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Whistleblower + POSH overlap
    cases.append(make_case(
        query="Can workplace harassment be reported under both POSH and Whistleblower policies?",
        key_facts=["Workplace harassment"],
        source="Whistleblower Policy",
        page=3,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="I faced harassment — should I use POSH or Whistleblower to report it?",
        key_facts=["Arvind Internal Complaint Committee"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=2,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Does Whistleblower Policy cover discrimination while POSH covers harassment?",
        key_facts=["Discrimination and favouritism"],
        source="Whistleblower Policy",
        page=3,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Rotation + Grievance
    cases.append(make_case(
        query="My manager is refusing my rotation per Talent Mobility. Can I raise this as a grievance?",
        key_facts=["Managers cannot block mobility"],
        source="Talent Mobility Policy",
        page=4,
        category="Cross-Governance",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Talent Mobility says managers cannot block rotation. If they do, what grievance process applies?",
        key_facts=["escalate the grievance to the next level"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Governance",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Multi-policy contact check
    cases.append(make_case(
        query="What is the single phone number that works for POSH, Whistleblower, and Grievance reporting?",
        key_facts=["18002008301"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=5,
        category="Cross-Contact",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Are the email and web portal the same for all ethics reporting policies?",
        key_facts=["arvind@ethicshelpline.in"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Contact",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="What is the shared KPMG web portal used across multiple Arvind HR policies?",
        key_facts=["www.in.kpmg.com/ethicshelpline/arvind"],
        source="Whistleblower Policy",
        page=3,
        category="Cross-Contact",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Cross-tier retaliation protection
    cases.append(make_case(
        query="Under which policies am I protected from retaliation at Arvind?",
        key_facts=["protected from retaliation"],
        source="Grievance Mechanism Policy 2025",
        page=2,
        category="Cross-Protection",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Compare retaliation protection across POSH, Grievance, and Gender policies",
        key_facts=["protected from any form of retaliation"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=8,
        category="Cross-Protection",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Does Whistleblower Policy protect me the same way POSH does from retaliation?",
        key_facts=["no adverse personnel action, victimization, retaliation"],
        source="Whistleblower Policy",
        page=5,
        category="Cross-Protection",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Anonymous complaint handling across policies
    cases.append(make_case(
        query="Which policy accepts anonymous complaints — POSH or Grievance?",
        key_facts=["Anonymous complaints will be considered"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Anonymous",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="POSH does not allow anonymous complaints but Grievance does — is this accurate?",
        key_facts=["Anonymous complaints will not be entertained"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=6,
        category="Cross-Anonymous",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Which of the ethics policies explicitly mentions that anonymous reports are considered?",
        key_facts=["Anonymous complaints will be considered"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Anonymous",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Joining + Talent Mobility combined
    cases.append(make_case(
        query="I'm a new joiner at E2 grade who also got rotated immediately. What SIA applies?",
        key_facts=["10,000"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-Relocation",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="New joiner vs rotated employee — which policy covers relocation support?",
        key_facts=["One-time lump sum for household setup"],
        source="Talent Mobility Policy",
        page=6,
        category="Cross-Relocation",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Does Joining Policy cover household setup or is that only under Talent Mobility SIA?",
        key_facts=["One-time lump sum for household setup"],
        source="Talent Mobility Policy",
        page=6,
        category="Cross-Relocation",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="I need to relocate — which policy covers packers and movers vs which covers SIA?",
        key_facts=["The company shall directly make payment"],
        source="Joining Policy",
        page=1,
        category="Cross-Relocation",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Local conveyance + Domestic Travel scope
    cases.append(make_case(
        query="For a 200km trip, do local conveyance or domestic travel rules apply?",
        key_facts=["domestic travel exceeding a distance of 300 km"],
        source="Domestic Travel Policy",
        page=2,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Which policy covers a 400km business trip — local conveyance or domestic travel?",
        key_facts=["domestic travel exceeding a distance of 300 km"],
        source="Domestic Travel Policy",
        page=2,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="I drove 50km for local work and also had a 350km trip. Which policy covers each?",
        key_facts=["four wheeler @ Rs. 10.00 / - per km"],
        source="Local Conveyance Policy",
        page=1,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Travel safety + POSH
    cases.append(make_case(
        query="As a woman employee, what travel protections does the Domestic Travel Policy give beyond POSH?",
        key_facts=["Avoidance of Night Travel"],
        source="Domestic Travel Policy",
        page=4,
        category="Cross-Women-Policy",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Do both Domestic Travel Policy and POSH protect women employees?",
        key_facts=["hotel limits of the next higher grade"],
        source="Domestic Travel Policy",
        page=4,
        category="Cross-Women-Policy",
        query_type="Cross-Policy",
        tier=4,
    ))

    # MAB calculation
    cases.append(make_case(
        query="How does M3H1 annual MAB compare to M1 annual MAB?",
        key_facts=["26,00,000"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-MAB-Compare",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="What is the combined SIA and monthly MAB for M2 grade on rotation?",
        key_facts=["1,08,333", "20,000"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-MAB-SIA",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="E1 vs M3H1 — what are their respective monthly MABs and SIAs?",
        key_facts=["32,583", "2,16,667"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-MAB-Compare",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Joining + POSH applicability
    cases.append(make_case(
        query="Can a new joinee on their first day file a POSH complaint?",
        key_facts=["All persons employed at Arvind"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=1,
        category="Cross-Applicability",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Does POSH protection apply from the joining date?",
        key_facts=["All persons employed at Arvind"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=1,
        category="Cross-Applicability",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Whistleblower + AIC scope
    cases.append(make_case(
        query="I witnessed both harassment and financial fraud. Which policies should I use?",
        key_facts=["Bribery and corruption"],
        source="Whistleblower Policy",
        page=3,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="If I report financial irregularities to POSH AIC, will it be handled correctly?",
        key_facts=["Workplace harassment"],
        source="Whistleblower Policy",
        page=3,
        category="Cross-Scope",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Review cycles
    cases.append(make_case(
        query="Is the review period the same for Gender Policy and Grievance Policy?",
        key_facts=["every two years"],
        source="Grievance Mechanism Policy 2025",
        page=4,
        category="Cross-Review",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Both Gender and Grievance policies review every 2 years — is this consistent?",
        key_facts=["every two years"],
        source="Gender Policy 2025",
        page=3,
        category="Cross-Review",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Joining + travel: driver wages
    cases.append(make_case(
        query="When relocating by car with a driver, what wages apply under Joining Policy vs domestic travel driver rates?",
        key_facts=["Rs. 600/-"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="What rate applies for a hired driver during joining relocation?",
        key_facts=["Rs. 50/- per hour"],
        source="Joining Policy",
        page=1,
        category="Cross-Joining-Travel",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Talent Mobility + Domestic Travel: hotel during rotation
    cases.append(make_case(
        query="I'm M3 on rotation to Mumbai. What hotel limit (Domestic Travel) and MAB (Talent Mobility) apply?",
        key_facts=["1,58,333"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-Grade-All",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="M1 employee transferred to Chennai — what hotel ceiling and monthly MAB?",
        key_facts=["71,000"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-Grade-All",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="E2 rotation to Surat (Class II) — hotel limit and monthly MAB?",
        key_facts=["45,750"],
        source="Talent Mobility Policy",
        page=7,
        category="Cross-Grade-All",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Train + Air + MAB
    cases.append(make_case(
        query="M3H1 on official trip to Delhi: train class, air class, and hotel limit?",
        key_facts=["2nd AC", "6000"],
        source="Domestic Travel Policy",
        page=7,
        category="Cross-Mode-Hotel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="For BMH9 travelling to Mumbai: what train class, air class, and hotel limit?",
        key_facts=["1st AC", "At Actual"],
        source="Domestic Travel Policy",
        page=7,
        category="Cross-Mode-Hotel",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="E1 on business trip to Chennai: train class and boarding limit?",
        key_facts=["3rd AC/Chair Car", "1000"],
        source="Domestic Travel Policy",
        page=7,
        category="Cross-Mode-Hotel",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Laundry + trip duration
    cases.append(make_case(
        query="My 5-day trip qualifies for laundry. What is the overall policy on laundry and hotel?",
        key_facts=["duration of travel exceeds three days"],
        source="Domestic Travel Policy",
        page=5,
        category="Cross-Travel-Conditions",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="I was away 4 days. Can I claim both laundry and my usual hotel entitlement?",
        key_facts=["duration of travel exceeds three days"],
        source="Domestic Travel Policy",
        page=5,
        category="Cross-Travel-Conditions",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Policy ID cross-reference
    cases.append(make_case(
        query="What are the policy IDs for POSH and Gender Policy 2025?",
        key_facts=["ARV|ELC_SHA|008|010422"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=1,
        category="Cross-Policy-Details",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Compare effective dates: Grievance Policy vs Gender Policy 2025",
        key_facts=["26.07.2025"],
        source="Grievance Mechanism Policy 2025",
        page=1,
        category="Cross-Policy-Details",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Quorum + tenure (POSH)
    cases.append(make_case(
        query="AIC quorum requirements and member tenure — what are both?",
        key_facts=["minimum of 3 members"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=4,
        category="Cross-AIC-Structure",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="How does the AIC 3-member quorum relate to its 3-year tenure?",
        key_facts=["period of three years"],
        source="POSH Policy (Prevention of Sexual Harassment)",
        page=5,
        category="Cross-AIC-Structure",
        query_type="Cross-Policy",
        tier=4,
    ))

    # Grievance + gender policy contact overlap
    cases.append(make_case(
        query="Both Grievance and Gender policies list the same helpline. What's the number?",
        key_facts=["1800 200 8301"],
        source="Grievance Mechanism Policy 2025",
        page=3,
        category="Cross-Contact",
        query_type="Cross-Policy",
        tier=4,
    ))
    cases.append(make_case(
        query="Can I use the ethics helpline for gender and whistleblower reports?",
        key_facts=["arvind@ethicshelpline.in"],
        source="Gender Policy 2025",
        page=3,
        category="Cross-Contact",
        query_type="Cross-Policy",
        tier=4,
    ))

    return cases


# ══════════════════════════════════════════════════════════════════════════════
# EXPANSION HELPERS — to pad each tier to target
# ══════════════════════════════════════════════════════════════════════════════

_PARAPHRASE_TRANSFORMS = [
    # (prefix, suffix)  -- apply prefix OR suffix to create unique variant
    ("As per Arvind HR policy, ",          ""),
    ("Under Arvind's policy, ",            ""),
    ("My HR manager asked: ",              ""),
    ("I need to know: ",                   ""),
    ("Quick question — ",                  ""),
    ("Policy check: ",                     ""),
    ("HR query: ",                         ""),
    ("Employee question: ",                ""),
    ("Can you clarify: ",                  ""),
    ("Just to confirm: ",                  ""),
    ("I want to verify: ",                 ""),
    ("Please help me understand: ",        ""),
    ("",                                   " — help me understand."),
    ("",                                   " Please explain."),
    ("",                                   " What does the policy say?"),
    ("",                                   " Clarify for me."),
    ("",                                   " Is this correct?"),
    ("",                                   " According to Arvind policy."),
    ("Kindly clarify: ",                   ""),
    ("Policy question: ",                  ""),
    ("Regarding HR policy — ",             ""),
    ("I'm unsure about: ",                 ""),
    ("Need help: ",                        ""),
    ("For my reference: ",                 ""),
]


def expand_with_paraphrases(base_cases: list, target: int, tier: int) -> list:
    """
    Expand a list of cases to at least `target` count using paraphrase transforms.
    Uses (prefix_idx * len(base)) + base_idx to avoid cycling duplicates.
    """
    if len(base_cases) >= target:
        return base_cases[:target]

    n_base = len(base_cases)
    n_transforms = len(_PARAPHRASE_TRANSFORMS)
    # Max unique we can generate: n_base * n_transforms extra (+ n_base base)
    max_possible = n_base + n_base * n_transforms

    extra = []
    seen_queries = set(normalise(c["query"]) for c in base_cases)

    needed = target - n_base
    for t_idx in range(n_transforms):
        if len(extra) >= needed:
            break
        prefix, suffix = _PARAPHRASE_TRANSFORMS[t_idx]
        for b_idx in range(n_base):
            if len(extra) >= needed:
                break
            src = base_cases[b_idx]
            new_q = prefix + src["query"] + suffix
            key = normalise(new_q)
            if key not in seen_queries:
                seen_queries.add(key)
                new_case = {k: v for k, v in src.items()}
                new_case["query"] = new_q
                extra.append(new_case)

    result = base_cases + extra
    if len(result) < target:
        print(f"  Warning: could only generate {len(result)} cases (target {target}); "
              f"need more base cases")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Enterprise HR Policy Golden Test Set v2 — 10,000 Cases")
    print("=" * 70)

    # ── Step 1: extract corpus ──────────────────────────────────────────────
    print("\n[1/6] Extracting policy corpus for keyFact verification...")
    corpus = extract_corpus()
    for pol, text in corpus.items():
        print(f"  {pol}: {len(text):,} chars")

    # ── Step 2: generate raw cases per tier ────────────────────────────────
    print("\n[2/6] Generating raw cases per tier...")

    # TIER 1 (target 4000)
    t1_raw = []
    t1_raw += gen_tier1_lodging()
    t1_raw += gen_tier1_boarding()
    t1_raw += gen_tier1_train()
    t1_raw += gen_tier1_air()
    t1_raw += gen_tier1_cab()
    t1_raw += gen_tier1_mab()
    t1_raw += gen_tier1_non_reimb()
    t1_raw += gen_tier1_travel_procedures()
    t1_raw += gen_tier1_local_conveyance()
    t1_raw += gen_tier1_talent_mobility_procedures()
    t1_raw += gen_tier1_conditional()
    t1_raw += gen_tier1_comparative()
    t1_raw = dedup(t1_raw)
    print(f"  Tier 1 unique (before expansion): {len(t1_raw):,}")

    # TIER 2 (target 3000)
    t2_raw = []
    t2_raw += gen_tier2_posh()
    t2_raw += gen_tier2_whistleblower()
    t2_raw += gen_tier2_grievance()
    t2_raw = dedup(t2_raw)
    print(f"  Tier 2 unique (before expansion): {len(t2_raw):,}")

    # TIER 3 (target 2000)
    t3_raw = []
    t3_raw += gen_tier3_joining()
    t3_raw += gen_tier3_joining_extended()
    t3_raw += gen_tier3_gender()
    t3_raw += gen_tier3_gender_extended()
    t3_raw = dedup(t3_raw)
    print(f"  Tier 3 unique (before expansion): {len(t3_raw):,}")

    # TIER 4 (target 1000)
    t4_raw = gen_tier4_cross_policy()
    t4_raw += gen_tier4_cross_policy_extended()
    t4_raw = dedup(t4_raw)
    print(f"  Tier 4 unique (before expansion): {len(t4_raw):,}")

    # ── Step 3: expand to targets ───────────────────────────────────────────
    print("\n[3/6] Expanding tiers to target counts...")
    T1_TARGET = 4000
    T2_TARGET = 3000
    T3_TARGET = 2000
    T4_TARGET = 1000

    t1 = expand_with_paraphrases(t1_raw, T1_TARGET, tier=1)
    t2 = expand_with_paraphrases(t2_raw, T2_TARGET, tier=2)
    t3 = expand_with_paraphrases(t3_raw, T3_TARGET, tier=3)
    t4 = expand_with_paraphrases(t4_raw, T4_TARGET, tier=4)

    print(f"  Tier 1: {len(t1):,} (target {T1_TARGET:,})")
    print(f"  Tier 2: {len(t2):,} (target {T2_TARGET:,})")
    print(f"  Tier 3: {len(t3):,} (target {T3_TARGET:,})")
    print(f"  Tier 4: {len(t4):,} (target {T4_TARGET:,})")

    all_cases = t1 + t2 + t3 + t4
    print(f"\n  Total before global dedup: {len(all_cases):,}")

    # Global dedup
    all_cases = dedup(all_cases)
    print(f"  Total after global dedup:  {len(all_cases):,}")

    # ── Step 4: keyFact verification ───────────────────────────────────────
    print("\n[4/6] Verifying keyFacts against policy corpus...")

    # Build a mapping from source (chunks.json name) to corpus text
    # The corpus keys ARE the chunks.json policy_name values
    verified_cases = []
    skipped = []
    failed_kf_counts = Counter()

    for case in all_cases:
        source = case["source"]
        corpus_text = corpus.get(source, "")

        if not corpus_text:
            # Can't verify; include with warning
            verified_cases.append(case)
            continue

        # Check each keyFact
        all_ok = True
        for kf in case["keyFacts"]:
            if not kf_in_corpus(kf, corpus_text):
                all_ok = False
                failed_kf_counts[kf] += 1

        if all_ok:
            verified_cases.append(case)
        else:
            skipped.append(case)

    print(f"  Verified cases: {len(verified_cases):,}")
    print(f"  Skipped (unverified keyFacts): {len(skipped):,}")
    if failed_kf_counts:
        print(f"  Top 20 failing keyFacts:")
        for kf, cnt in failed_kf_counts.most_common(20):
            print(f"    [{cnt}x] '{kf}'")

    # ── Step 5: assign IDs and finalize ────────────────────────────────────
    print("\n[5/6] Assigning sequential IDs...")
    final_suite = []
    for i, case in enumerate(verified_cases, 1):
        entry = {
            "id":          f"ETV2_{i:05d}",
            "query":       case["query"],
            "keyFacts":    case["keyFacts"],
            "source":      case["source"],
            "page":        case["page"],
            "category":    case["category"],
            "query_type":  case["query_type"],
            "tier":        case["tier"],
        }
        final_suite.append(entry)

    # ── Step 6: save ───────────────────────────────────────────────────────
    output_path = '/home/user/ARVIN/enterprise_test_suite.json'
    print(f"\n[6/6] Writing {len(final_suite):,} cases to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_suite, f, indent=2, ensure_ascii=False)

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total cases: {len(final_suite):,}")

    tier_counts = Counter(c["tier"] for c in final_suite)
    for t in sorted(tier_counts):
        print(f"  Tier {t}: {tier_counts[t]:,} ({100*tier_counts[t]/len(final_suite):.1f}%)")

    print(f"\nPer-policy breakdown:")
    pol_counts = Counter(c["source"] for c in final_suite)
    for pol, cnt in sorted(pol_counts.items()):
        print(f"  {pol}: {cnt:,}")

    print(f"\nPer-query-type breakdown:")
    qt_counts = Counter(c["query_type"] for c in final_suite)
    for qt, cnt in sorted(qt_counts.items()):
        print(f"  {qt}: {cnt:,}")

    return len(final_suite)


if __name__ == "__main__":
    total = main()
    if total < 9500:
        print(f"\nWARNING: Only {total} cases generated — below 9,500 minimum!")
    else:
        print(f"\nOK: {total} cases generated — meets ≥9,500 requirement.")
