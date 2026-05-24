#!/usr/bin/env python3
"""
Expand enterprise_test_suite.json from 8,855 → 10,000 cases.
Generates new cases for under-represented categories, deduplicates
against existing suite, verifies keyFacts against policy corpus,
then writes the combined 10,000-case suite back to the same file.
"""

import json, re, os
import pdfplumber
from docx import Document
from collections import Counter

SUITE_FILE = '/home/user/ARVIN/enterprise_test_suite.json'
POLICY_DIR = '/home/user/ARVIN/policies'
TARGET      = 10_000


# ─── Normalise (same as generator) ───────────────────────────────────────────

def normalise(text: str) -> str:
    t = text
    t = re.sub(r'Rs\.?\s*', '', t)
    t = re.sub(r'₹\s*', '', t)
    t = re.sub(r'/-', '', t)
    t = re.sub(r',', '', t)
    t = re.sub(r'\([^)]*\)', '', t)
    t = re.sub(r'-', ' ', t)
    t = re.sub(r'/', ' or ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()


# ─── Corpus extraction (same as generator) ───────────────────────────────────

FILES = {
    'Local Conveyance Policy': 'cf8daeee-localconveyancepolicyarvindlimited.pdf',
    'Domestic Travel Policy':  'f34aa66a-domestictravelpolicyarvindlimited.pdf',
    'Grievance Mechanism Policy': 'e08407da-arvindgrievancemechanismpolicy2025.pdf',
    'POSH Policy':             '4d8fe661-poshpolicyarvindlimited.pdf',
    'Whistleblower Policy':    'cbdae693-whistleblowerpolicyarvindlimited.pdf',
    'Gender Policy':           '99ecde3a-arvindgenderpolicy2025.pdf',
    'Talent Mobility Policy':  'adea8313-talentmobility.pdf',
    'Joining Policy':          'bad821d9-joiningpolicyarvindlimited.docx',
}

def extract_corpus():
    corpus = {}
    for policy_name, filename in FILES.items():
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
                print(f"  Warning: {filename}: {e}")
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
                print(f"  Warning: {filename}: {e}")
        corpus[policy_name] = normalise(raw_text)
    return corpus


def verify_keyfact(kf: str, source: str, corpus: dict) -> bool:
    """Return True if kf (normalised) is found in the corpus for source."""
    norm_kf = normalise(kf)
    if len(norm_kf) < 2:
        return True
    for key, text in corpus.items():
        if key.lower() in source.lower() or source.lower() in key.lower():
            return norm_kf in text
    # partial match
    src_words = source.lower().split()
    for key, text in corpus.items():
        if any(w in key.lower() for w in src_words if len(w) > 4):
            return norm_kf in text
    return False


# ─── New case generators ──────────────────────────────────────────────────────

GRADE_TRAIN = {
    "BMH9":        "1st AC",
    "BMH7/H8":     "1st AC",
    "BM-H3–H6":    "1st AC",
    "M3H1/M3/M2":  "2nd AC",
    "M1/E2/E1/OT": "3rd AC/Chair Car",
}

GRADE_AIR = {
    "BMH9":        "Premium Economy / Business",
    "BMH7/H8":     "Economy / Premium Economy",
    "M3H1/M3/M2":  "Economy",
}

GRADE_CAB = {
    "BM-H7 and above":     "Actuals",
    "BMH3-H6":             "Ola / Uber / BluSmart",
    "M3H1/M3/M2":          "Ola / Uber / BluSmart",
    "M1/MT/E2/GET/E1/OT":  "Ola / Uber / BluSmart",
}

GRADE_LODGING = {
    "BMH7 and above":        {"Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual"},
    "BMH3-H6":               {"Class I": "8000", "Class II": "6000", "Class III": "5000"},
    "M3H1/M3/M2":            {"Class I": "6000", "Class II": "5000", "Class III": "4000"},
    "M1/MT/E2/GET/E1/OT":    {"Class I": "3400", "Class II": "2300", "Class III": "1700"},
}

MAB_DATA = {
    "E1":   {"monthly": "32,583",   "annual": "3,91,000",  "sia": "10,000"},
    "E2":   {"monthly": "45,750",   "annual": "5,49,000",  "sia": "10,000"},
    "M1":   {"monthly": "71,000",   "annual": "8,52,000",  "sia": "15,000"},
    "M2":   {"monthly": "1,08,333", "annual": "13,00,000", "sia": "20,000"},
    "M3":   {"monthly": "1,58,333", "annual": "19,00,000", "sia": "30,000"},
    "M3H1": {"monthly": "2,16,667", "annual": "26,00,000", "sia": "45,000"},
}


def _case(query, key_facts, source, page, category):
    return {"query": query, "keyFacts": key_facts, "source": source,
            "page": page, "category": category}


def gen_extended_transport():
    """More query variants for train, air, cab entitlements."""
    cases = []

    # Train — 10 more variants per grade
    extra_train = [
        "What train class does {g} grade get on official travel?",
        "I'm a {g} employee going on a business trip. What train class can I book?",
        "Train entitlement for grade {g} under the Domestic Travel Policy?",
        "Can a {g} grade employee travel 1st AC by train?",
        "Which train class is {g} entitled to for domestic travel?",
        "What is the rail class for {g} employees?",
        "I am {g}. Tell me my train class entitlement.",
        "Is 1st AC allowed for {g} grade employees?",
        "My grade is {g}. What train class should I book for official travel?",
        "Train class policy for {g} staff?",
    ]
    for grade, tc in GRADE_TRAIN.items():
        for tmpl in extra_train:
            cases.append(_case(
                tmpl.format(g=grade), [tc],
                "Domestic Travel Policy", 7, f"Train - {grade}"
            ))

    # Air — 10 more variants per grade
    extra_air = [
        "What flight class is {g} grade entitled to?",
        "Can a {g} employee book business class?",
        "I am {g}. What air travel class do I get?",
        "Air travel entitlement for {g} employees?",
        "Flight class for {g} grade on domestic travel?",
        "Which airline class can {g} staff book?",
        "Is economy class the only option for {g}?",
        "What does the policy say about air travel for {g}?",
        "My grade is {g}. What is my flight class?",
        "Air ticket class for {g} as per Domestic Travel Policy?",
    ]
    for grade, ac in GRADE_AIR.items():
        for tmpl in extra_air:
            cases.append(_case(
                tmpl.format(g=grade), [ac],
                "Domestic Travel Policy", 7, f"Air Travel - {grade}"
            ))

    # Cab — 10 more variants per grade
    extra_cab = [
        "What cab service can {g} employees use?",
        "I am {g}. Which cab apps are allowed?",
        "Cab booking options for {g} grade?",
        "Can {g} employees use Ola or Uber?",
        "What transport can I book as a {g} employee?",
        "Local transport policy for {g} grade employees?",
        "Which cab services are approved for {g}?",
        "How can a {g} employee travel locally on business trips?",
        "Cab entitlement for {g} under Domestic Travel Policy?",
        "What is the cab policy for {g} grade?",
    ]
    for grade, cab in GRADE_CAB.items():
        for tmpl in extra_cab:
            cases.append(_case(
                tmpl.format(g=grade), [cab[:40]],
                "Domestic Travel Policy", 8, f"Cab - {grade}"
            ))

    return cases


def gen_extended_mab_sia():
    """More query variants for MAB and SIA per grade."""
    cases = []

    extra_monthly = [
        "What monthly MAB amount does {g} grade receive?",
        "How much is the mobility adjustment benefit per month for {g}?",
        "MAB monthly for {g} employees on rotation?",
        "I got rotated as {g}. How much monthly MAB do I get?",
        "Monthly rotation allowance for {g} grade?",
        "What is the monthly MAB as per Talent Mobility Policy for {g}?",
        "Tell me the MAB per month for grade {g}.",
        "Mobility benefit monthly amount for {g}?",
        "My grade is {g}. What monthly benefit comes with rotation?",
        "As a {g} employee on rotation, what is my monthly MAB?",
    ]
    extra_annual = [
        "What is the annual MAB for {g}?",
        "Total yearly mobility allowance for {g}?",
        "How much annual MAB does a {g} employee get?",
        "Yearly rotation benefit for {g} grade?",
        "Annual mobility adjustment for {g}?",
        "What is the per-annum MAB for {g} grade employees?",
        "Tell me the annual MAB entitlement for {g}.",
        "MAB annualised amount for {g}?",
        "My grade is {g}. What is the full year MAB?",
        "Talent Mobility annual allowance for {g}?",
    ]
    extra_sia = [
        "What is the SIA amount for {g}?",
        "How much settling-in assistance does {g} get?",
        "SIA entitlement for {g} grade employees?",
        "I am {g} and just relocated. What SIA do I get?",
        "What is the one-time settling-in amount for {g}?",
        "Settling-in assistance for {g} grade on relocation?",
        "Tell me the SIA for grade {g}.",
        "One-time lump sum for {g} employees on relocation?",
        "My grade is {g}. How much SIA am I entitled to?",
        "SIA amount under Talent Mobility Policy for {g}?",
    ]

    for grade, data in MAB_DATA.items():
        for tmpl in extra_monthly:
            cases.append(_case(
                tmpl.format(g=grade), [data["monthly"]],
                "Talent Mobility Policy", 7, f"MAB Monthly - {grade}"
            ))
        for tmpl in extra_annual:
            cases.append(_case(
                tmpl.format(g=grade), [data["annual"]],
                "Talent Mobility Policy", 7, f"MAB Annual - {grade}"
            ))
        for tmpl in extra_sia:
            cases.append(_case(
                tmpl.format(g=grade), [data["sia"]],
                "Talent Mobility Policy", 7, f"SIA - {grade}"
            ))

    return cases


def gen_extended_lodging():
    """More city variants for lodging and boarding."""
    CLASS1_EXTRA = ["Hyderabad", "Chennai", "Kolkata"]
    CLASS2_EXTRA = ["Surat", "Jaipur", "Lucknow", "Nagpur", "Indore", "Kochi"]
    CLASS3_EXTRA = ["Dehradun", "Raipur", "Cuttack"]

    cases = []
    for grade, city_limits in GRADE_LODGING.items():
        for city_class, amount in city_limits.items():
            city_list = (CLASS1_EXTRA if city_class == "Class I"
                         else CLASS2_EXTRA if city_class == "Class II"
                         else CLASS3_EXTRA)
            for city in city_list:
                cases += [
                    _case(f"I am a {grade} employee visiting {city}. What is my hotel limit?",
                          [amount], "Domestic Travel Policy", 7, f"Lodging - {grade} - {city_class}"),
                    _case(f"Lodging allowance for {grade} in {city} ({city_class})?",
                          [amount], "Domestic Travel Policy", 7, f"Lodging - {grade} - {city_class}"),
                    _case(f"What is the hotel reimbursement cap for {grade} in {city}?",
                          [amount], "Domestic Travel Policy", 7, f"Lodging - {grade} - {city_class}"),
                ]
    return cases


def gen_extended_posh():
    """More POSH structural and procedural query variants."""
    cases = []

    posh_extras = [
        # Quorum
        ("What is the minimum quorum required for AIC to conduct inquiry?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("How many AIC members must be present for the inquiry to be valid?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("AIC cannot proceed without how many members?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("Quorum requirement for Arvind Internal Complaint Committee?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("What is the women member requirement in AIC for quorum?",
         ["50% women representation"], "POSH Policy", 4, "Quorum"),
        ("AIC must have what percentage of women members?",
         ["50% women representation"], "POSH Policy", 4, "Quorum"),
        ("Is 50% women representation mandatory in AIC?",
         ["50% women representation"], "POSH Policy", 4, "Quorum"),

        # External member fee
        ("How is the external AIC member compensated?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),
        ("What fee is paid to the external member of AIC per day?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),
        ("External member of AIC gets how much per day?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),
        ("AIC external member daily remuneration?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),

        # Vacancy in AIC
        ("If an AIC member leaves, within how many days must the vacancy be filled?",
         ["within 15 days"], "POSH Policy", 4, "Vacancy"),
        ("AIC vacancy must be filled within how many days?",
         ["within 15 days"], "POSH Policy", 4, "Vacancy"),
        ("Timeframe to fill AIC vacancy?",
         ["within 15 days"], "POSH Policy", 4, "Vacancy"),
        ("What is the deadline to fill AIC vacancy after a member exits?",
         ["within 15 days"], "POSH Policy", 4, "Vacancy"),

        # AIC powers
        ("What powers does the AIC have under POSH?",
         ["powers as that of a civil court"], "POSH Policy", 4, "AIC Powers"),
        ("Can AIC summon witnesses like a court?",
         ["powers as that of a civil court"], "POSH Policy", 4, "AIC Powers"),
        ("Does AIC function like a civil court?",
         ["powers as that of a civil court"], "POSH Policy", 4, "AIC Powers"),

        # Filing deadline
        ("What is the time limit to file a POSH complaint?",
         ["3 (three) months from the date of incident"], "POSH Policy", 6, "Filing Deadline"),
        ("When should I file my POSH complaint by?",
         ["3 (three) months from the date of incident"], "POSH Policy", 6, "Filing Deadline"),
        ("Can the POSH complaint deadline be extended?",
         ["extended for further 3 (three) months"], "POSH Policy", 6, "Filing Deadline"),
        ("By how long can the POSH complaint deadline be extended?",
         ["extended for further 3 (three) months"], "POSH Policy", 6, "Filing Deadline"),

        # AIC tenure
        ("How long does an AIC member serve?",
         ["period of three years"], "POSH Policy", 5, "AIC Tenure"),
        ("What is the tenure of the AIC presiding officer?",
         ["period of three years"], "POSH Policy", 5, "AIC Tenure"),
        ("Can an AIC member be re-nominated after their tenure?",
         ["re-nominated/re-elected for one additional term"], "POSH Policy", 5, "AIC Tenure"),
        ("AIC member tenure for employees who are 58 years old?",
         ["period of three years or completion of the age of 58 years"], "POSH Policy", 5, "AIC Tenure"),

        # Management action timeline
        ("In how many days must management act on AIC findings?",
         ["60 (sixty) days"], "POSH Policy", 7, "Management Action"),
        ("What is the deadline for management to implement AIC recommendations?",
         ["60 (sixty) days"], "POSH Policy", 7, "Management Action"),
        ("Management has how many days to act on POSH AIC report?",
         ["60 (sixty) days"], "POSH Policy", 7, "Management Action"),

        # AIC report
        ("When must AIC submit its report after inquiry?",
         ["within a period of 10 (ten) days"], "POSH Policy", 7, "AIC Report"),
        ("AIC report submission timeline?",
         ["within a period of 10 (ten) days"], "POSH Policy", 7, "AIC Report"),
        ("How many days does AIC have to submit findings?",
         ["within a period of 10 (ten) days"], "POSH Policy", 7, "AIC Report"),

        # Interim relief
        ("Can an aggrieved woman get leave during POSH inquiry?",
         ["leave to the Aggrieved Woman up to a period of 3 (three) months"], "POSH Policy", 7, "Interim Relief"),
        ("How much additional leave can be given during POSH proceedings?",
         ["leave to the Aggrieved Woman up to a period of 3 (three) months"], "POSH Policy", 7, "Interim Relief"),
        ("Is the interim leave under POSH in addition to normal leaves?",
         ["in addition to the entitled leaves"], "POSH Policy", 7, "Interim Relief"),

        # Interim action on respondent
        ("What interim action can be taken against the respondent during inquiry?",
         ["suspend the RE for defined period"], "POSH Policy", 7, "Interim Action"),
        ("Can the respondent be suspended pending POSH inquiry?",
         ["suspend the RE for defined period"], "POSH Policy", 7, "Interim Action"),

        # Who can file
        ("Can a co-worker file POSH on behalf of the aggrieved woman?",
         ["Her co-worker"], "POSH Policy", 5, "Who Can File"),
        ("Can I file a POSH complaint on behalf of my colleague?",
         ["Her co-worker"], "POSH Policy", 5, "Who Can File"),
        ("Who can file POSH if the woman is unable to?",
         ["Her relative or friend"], "POSH Policy", 5, "Who Can File"),
        ("If a woman is incapacitated, who can file the POSH complaint?",
         ["written consent of her legal heir"], "POSH Policy", 5, "Who Can File"),

        # Notice period
        ("How much notice must AIC give before the inquiry?",
         ["notice of 15 (fifteen) days"], "POSH Policy", 6, "AIC Procedures"),
        ("What is the advance notice period before AIC inquiry?",
         ["notice of 15 (fifteen) days"], "POSH Policy", 6, "AIC Procedures"),

        # Timelines
        ("How many working days does AIC have to complete inquiry?",
         ["10 (ten) working days"], "POSH Policy", 7, "Timelines"),
        ("AIC inquiry completion timeline?",
         ["10 (ten) working days"], "POSH Policy", 7, "Timelines"),
        ("How long can the respondent take to reply to the complaint?",
         ["7 (seven) days"], "POSH Policy", 6, "Timelines"),
        ("Respondent reply deadline to POSH complaint?",
         ["7 (seven) days"], "POSH Policy", 6, "Timelines"),
    ]

    for q, kf, src, pg, cat in posh_extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_grievance():
    """More grievance mechanism query variants."""
    cases = []

    extras = [
        ("How quickly is a grievance acknowledged?",
         ["2 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("Grievance acknowledgement timeline?",
         ["2 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("In how many days will my grievance be investigated?",
         ["10 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("Grievance investigation deadline?",
         ["10 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("What is the final grievance resolution timeline?",
         ["15 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("In how many working days will I get grievance resolution?",
         ["15 working days"], "Grievance Mechanism Policy", 3, "Timelines"),
        ("Where do I escalate grievance after line manager?",
         ["Head of Department"], "Grievance Mechanism Policy", 2, "Escalation Channels"),
        ("Who is the third escalation for grievance?",
         ["Head of Department"], "Grievance Mechanism Policy", 2, "Escalation Channels"),
        ("Can I raise a grievance to HR directly?",
         ["Immediate HR Representative"], "Grievance Mechanism Policy", 2, "Escalation Channels"),
        ("What is the first point of contact for grievance?",
         ["Line Manager or Supervisor"], "Grievance Mechanism Policy", 2, "Escalation Channels"),
        ("Can I raise a grievance verbally?",
         ["raised verbally or in writing"], "Grievance Mechanism Policy", 3, "Filing"),
        ("Does the grievance policy accept verbal complaints?",
         ["raised verbally or in writing"], "Grievance Mechanism Policy", 3, "Filing"),
        ("Are anonymous grievance complaints accepted?",
         ["Anonymous complaints will be considered"], "Grievance Mechanism Policy", 3, "Anonymous"),
        ("Will anonymous complaints be looked into under grievance policy?",
         ["Anonymous complaints will be considered"], "Grievance Mechanism Policy", 3, "Anonymous"),
        ("How often is the grievance policy reviewed by Arvind?",
         ["every two years"], "Grievance Mechanism Policy", 4, "Review"),
        ("Grievance policy review cycle?",
         ["every two years"], "Grievance Mechanism Policy", 4, "Review"),
        ("Are part-time employees covered under the Grievance Policy?",
         ["part-time"], "Grievance Mechanism Policy", 2, "Applicability"),
        ("Can trainees file a grievance?",
         ["trainees"], "Grievance Mechanism Policy", 2, "Applicability"),
        ("Does the Grievance Policy protect me from retaliation?",
         ["protected from retaliation"], "Grievance Mechanism Policy", 2, "Protection"),
        ("Can I be penalised for filing a genuine grievance?",
         ["protected from retaliation"], "Grievance Mechanism Policy", 2, "Protection"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_joining():
    """More joining policy query variants."""
    cases = []

    extras = [
        ("What is the pre-joining visit duration?",
         ["maximum period of 3 days"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Duration of pre-joining visit under Joining Policy?",
         ["maximum period of 3 days"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Can my spouse accompany me on pre-joining trip?",
         ["spouse"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Is spouse allowed on pre-joining visit?",
         ["spouse"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("Relocation transport rate for distance under 700 km?",
         ["Rs. 50 per km"], "Joining Policy", 1, "Transportation"),
        ("What is the per km rate for joining relocation under 700 km?",
         ["Rs. 50 per km"], "Joining Policy", 1, "Transportation"),
        ("Relocation transport rate for distance above 700 km?",
         ["Rs. 60 per km"], "Joining Policy", 1, "Transportation"),
        ("Per km rate for joining relocation over 700 km?",
         ["Rs. 60 per km"], "Joining Policy", 1, "Transportation"),
        ("Car reimbursement rate per km for Joining Policy?",
         ["Rs. 10.0 per km"], "Joining Policy", 1, "Car Transport"),
        ("What do I get per km for driving my own car during relocation?",
         ["Rs. 10.0 per km"], "Joining Policy", 1, "Car Transport"),
        ("Driver wage for 8 hours during joining?",
         ["Rs. 600/-"], "Joining Policy", 1, "Driver Wages"),
        ("What is the full-day driver wage under Joining Policy?",
         ["Rs. 600/-"], "Joining Policy", 1, "Driver Wages"),
        ("Overtime driver wage per hour?",
         ["Rs. 50/- per hour"], "Joining Policy", 1, "Driver Wages"),
        ("Driver rate per hour after 8-hour window?",
         ["Rs. 50/- per hour"], "Joining Policy", 1, "Driver Wages"),
        ("What is the food limit per meal for joining relocation?",
         ["Rs. 200/- per meal"], "Joining Policy", 1, "Food Limit"),
        ("Meal reimbursement cap during joining travel?",
         ["Rs. 200/- per meal"], "Joining Policy", 1, "Food Limit"),
        ("Is brokerage paid for house during relocation?",
         ["One month rent"], "Joining Policy", 1, "Brokerage"),
        ("How much brokerage can I claim on joining?",
         ["One month rent"], "Joining Policy", 1, "Brokerage"),
        ("For how long is brokerage reimbursable after joining?",
         ["maximum for 1 year from the date of the joining"], "Joining Policy", 1, "Brokerage Validity"),
        ("House deposit recovery method under Joining Policy?",
         ["10 equal monthly instalments"], "Joining Policy", 1, "House Deposit"),
        ("How is house deposit recovered from salary?",
         ["10 equal monthly instalments"], "Joining Policy", 1, "House Deposit"),
        ("Deadline to claim joining expenses?",
         ["One Year from Date of Joining"], "Joining Policy", 1, "Expense Claim Deadline"),
        ("How long do I have to submit joining expense claims?",
         ["One Year from Date of Joining"], "Joining Policy", 1, "Expense Claim Deadline"),
        ("If I leave before one year, what happens to my relocation expenses?",
         ["recovered in his/her F&F settlement"], "Joining Policy", 1, "Quit < 1 Year"),
        ("Relocation recovery if employee quits within a year?",
         ["recovered in his/her F&F settlement"], "Joining Policy", 1, "Quit < 1 Year"),
        ("Who books flights for new joiners?",
         ["Arvind Travel Desk"], "Joining Policy", 1, "Flight Booking"),
        ("How do I book my joining travel ticket?",
         ["Arvind Travel Desk"], "Joining Policy", 1, "Flight Booking"),
        ("Are joining expenses taxed?",
         ["Income tax shall be grossed up"], "Joining Policy", 1, "Tax"),
        ("Tax treatment of joining relocation allowance?",
         ["Income tax shall be grossed up"], "Joining Policy", 1, "Tax"),
        ("Who pays packers and movers directly?",
         ["The company shall directly make payment"], "Joining Policy", 1, "Packers & Movers"),
        ("Does the company pay movers directly or reimburse?",
         ["The company shall directly make payment"], "Joining Policy", 1, "Packers & Movers"),
        ("Can I take both pre-joining and post-joining visit?",
         ["either a Pre-Joining Visit OR Post Joining Visit"], "Joining Policy", 1, "Visit Options"),
        ("Are pre-joining and post-joining visits both allowed?",
         ["either a Pre-Joining Visit OR Post Joining Visit"], "Joining Policy", 1, "Visit Options"),
        ("Who approves exceptions to Joining Policy?",
         ["CEO"], "Joining Policy", 1, "Approvals"),
        ("Approval authority for Joining Policy exceptions?",
         ["CEO"], "Joining Policy", 1, "Approvals"),
        ("Are joining benefits applicable to Arvind subsidiaries?",
         ["subsidiaries"], "Joining Policy", 1, "Applicability"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_whistleblower():
    """More whistleblower policy query variants."""
    cases = []

    wb_issues_short = [
        ("Breach of internal compliance requirements", "Breach of internal compliance"),
        ("Non-compliance/breach of legal and regulatory requirements", "Non-compliance or breach of legal"),
        ("Bribery and corruption", "Bribery and corruption"),
        ("Procurement and tendering fraud", "Procurement and tendering fraud"),
        ("Misappropriation/theft/embezzlement of company assets", "Misappropriation or theft"),
        ("Corporate espionage and information disclosure", "Corporate espionage"),
        ("Undue awarding of contracts", "Undue awarding of contracts"),
        ("False invoicing", "False invoicing"),
        ("Fraudulent financial accounting, auditing and reporting", "Fraudulent financial accounting"),
        ("Employee negligence", "Employee negligence"),
        ("Health, safety, environment and security related", "Health safety environment"),
        ("Workplace harassment", "Workplace harassment"),
        ("Discrimination and favouritism", "Discrimination and favouritism"),
    ]

    extra_tmpls = [
        "Is {issue} reportable under the Whistleblower Policy?",
        "Can I use the ethics helpline to report {short}?",
        "My colleague is engaged in {short}. Should I report it under Whistleblower Policy?",
        "Does Arvind's Whistleblower Policy cover {short}?",
        "I witnessed {short}. Which policy should I use to report it?",
    ]

    for full, short in wb_issues_short:
        for tmpl in extra_tmpls:
            q = tmpl.format(issue=full, short=short)
            cases.append(_case(q, [full[:40]], "Whistleblower Policy", 3, "Reportable Issues"))

    extras_general = [
        ("How often does the Whistleblower Committee report to the Audit Committee?",
         ["quarterly"], "Whistleblower Policy", 4, "Reporting Frequency"),
        ("Whistleblower reporting frequency to Audit Committee?",
         ["quarterly"], "Whistleblower Policy", 4, "Reporting Frequency"),
        ("Is the whistleblower's identity kept confidential?",
         ["identity of the whistle blower shall be kept confidential"], "Whistleblower Policy", 4, "Confidentiality"),
        ("After how long can I follow up on my whistleblower complaint?",
         ["four weeks after the submission"], "Whistleblower Policy", 4, "Follow-up"),
        ("Whistleblower follow-up period?",
         ["four weeks after the submission"], "Whistleblower Policy", 4, "Follow-up"),
        ("Can an external agency investigate whistleblower complaints?",
         ["appoint an independent agency"], "Whistleblower Policy", 4, "Investigation"),
        ("Am I protected from retaliation as a whistleblower?",
         ["no adverse personnel action, victimization, retaliation"], "Whistleblower Policy", 5, "Protection"),
        ("What if I make a false whistleblower report?",
         ["will not be protected by this Policy"], "Whistleblower Policy", 5, "False Complaints"),
        ("I faced retaliation after reporting. What is my recourse?",
         ["lodge a written complaint to the Chairman"], "Whistleblower Policy", 5, "Retaliation Recourse"),
        ("Must I cooperate with a whistleblower investigation?",
         ["duty to cooperate with investigations"], "Whistleblower Policy", 4, "Responsibilities"),
        ("Are Directors covered by the Whistleblower Policy?",
         ["Directors"], "Whistleblower Policy", 3, "Applicability"),
        ("Are Business Associates included in Whistleblower Policy scope?",
         ["Business Associates"], "Whistleblower Policy", 3, "Applicability"),
    ]

    for q, kf, src, pg, cat in extras_general:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_gender():
    """More gender policy query variants."""
    cases = []

    extras = [
        ("When did the Gender Policy come into effect?",
         ["25.07.2025"], "Gender Policy", 1, "Policy Details"),
        ("Gender Policy effective date?",
         ["25.07.2025"], "Gender Policy", 1, "Policy Details"),
        ("What is the Gender Policy issue date?",
         ["26.07.2025"], "Gender Policy", 1, "Policy Details"),
        ("Gender Policy policy number?",
         ["ARV|COM_GENP|001|260725"], "Gender Policy", 1, "Policy Details"),
        ("What is the code for the Gender Policy?",
         ["ARV|COM_GENP|001|260725"], "Gender Policy", 1, "Policy Details"),
        ("Do interns come under the Gender Policy?",
         ["interns"], "Gender Policy", 2, "Applicability"),
        ("Are contract staff included in the Gender Policy scope?",
         ["contract staff"], "Gender Policy", 2, "Applicability"),
        ("Does Gender Policy apply to third-party partners?",
         ["third-party partners"], "Gender Policy", 2, "Applicability"),
        ("Where do I file a gender discrimination complaint?",
         ["HR Department"], "Gender Policy", 3, "Complaint Process"),
        ("Who do I approach for gender complaint?",
         ["Line Manager"], "Gender Policy", 3, "Complaint Process"),
        ("How often is the Gender Policy reviewed?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Gender policy review frequency?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Is retaliation for gender complaint prohibited?",
         ["retaliation against individuals who raise concerns in good faith is strictly prohibited"],
         "Gender Policy", 3, "Protection"),
        ("Can I be penalised for raising gender concerns in good faith?",
         ["retaliation against individuals who raise concerns in good faith is strictly prohibited"],
         "Gender Policy", 3, "Protection"),
        ("Are promotions based on merit under Gender Policy?",
         ["Hiring and Promotions are conducted based on merit"], "Gender Policy", 3, "Principles"),
        ("What does Gender Policy say about merit-based promotions?",
         ["Hiring and Promotions are conducted based on merit"], "Gender Policy", 3, "Principles"),
        ("Ethics helpline number for gender complaints?",
         ["1800 200 8301"], "Gender Policy", 3, "Contact"),
        ("Email for gender policy complaints?",
         ["arvind@ethicshelpline.in"], "Gender Policy", 3, "Contact"),
        ("Web portal for gender policy complaint?",
         ["www.in.kpmg.com/ethicshelpline/arvind"], "Gender Policy", 3, "Contact"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_talent_mobility():
    """More talent mobility query variants."""
    cases = []

    extras = [
        ("What triggers mandatory rotation under Talent Mobility Policy?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("After how many years does mandatory rotation kick in?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("How long before an employee must rotate?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("What is the rotation trigger period?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("Which positions must be filled via IJP?",
         ["All positions upto M2"], "Talent Mobility Policy", 4, "IJP"),
        ("Internal Job Posting applies to which grades?",
         ["All positions upto M2"], "Talent Mobility Policy", 4, "IJP"),
        ("Can a manager block an employee's rotation?",
         ["Managers cannot block mobility"], "Talent Mobility Policy", 4, "Governance"),
        ("Who can approve exceptions to Talent Mobility?",
         ["CHRO/CEO can approve exceptions"], "Talent Mobility Policy", 4, "Exceptions"),
        ("What is the 1st rotation model?",
         ["1st Rotation – within the city"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("First rotation is within which area?",
         ["1st Rotation – within the city"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("What does the 2nd rotation involve?",
         ["2nd Rotation – across different business / different location"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("Second rotation is across which geography?",
         ["2nd Rotation – across different business / different location"], "Talent Mobility Policy", 4, "Rotation Framework"),
        ("How long does MAB last before merging with CTC?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
        ("What happens to MAB after one year?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
        ("MAB is given for how long before absorption into CTC?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
        ("When am I eligible for SIA?",
         ["shifting house"], "Talent Mobility Policy", 6, "SIA Condition"),
        ("SIA is given when employee does what?",
         ["shifting house"], "Talent Mobility Policy", 6, "SIA Condition"),
        ("Minimum relocation distance to be eligible for SIA?",
         ["relocation >20 kms"], "Talent Mobility Policy", 7, "SIA Condition"),
        ("SIA distance eligibility?",
         ["relocation >20 kms"], "Talent Mobility Policy", 7, "SIA Condition"),
        ("SIA is one-time or recurring?",
         ["One time"], "Talent Mobility Policy", 6, "SIA Type"),
        ("What type of benefit is SIA?",
         ["One time"], "Talent Mobility Policy", 6, "SIA Type"),
        ("What does SIA stand for?",
         ["One-time lump sum for household setup"], "Talent Mobility Policy", 6, "SIA Description"),
        ("SIA purpose in Talent Mobility Policy?",
         ["One-time lump sum for household setup"], "Talent Mobility Policy", 6, "SIA Description"),
        ("What is MAB?",
         ["Monthly allowance"], "Talent Mobility Policy", 6, "MAB Description"),
        ("MAB is what type of payment?",
         ["Monthly allowance"], "Talent Mobility Policy", 6, "MAB Description"),
        ("Risk of keeping employees in sensitive roles too long?",
         ["sensitive roles exceed tenure"], "Talent Mobility Policy", 2, "Risk"),
        ("Why does Talent Mobility Policy enforce rotation?",
         ["sensitive roles exceed tenure"], "Talent Mobility Policy", 2, "Risk"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_extended_local_conveyance():
    """More local conveyance query variants."""
    cases = []

    extras = [
        ("Four-wheeler reimbursement rate for local travel?",
         ["four wheeler @ Rs. 10.00 / - per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Car reimbursement per km under Local Conveyance Policy?",
         ["four wheeler @ Rs. 10.00 / - per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Two-wheeler rate for official travel?",
         ["two wheeler @ Rs. 5.00 per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Bike reimbursement per km under Local Conveyance Policy?",
         ["two wheeler @ Rs. 5.00 per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Is cab reimbursed on actuals?",
         ["reimbursement will be done on actuals"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("How is cab reimbursed under Local Conveyance Policy?",
         ["reimbursement will be done on actuals"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("Where do I submit conveyance claims?",
         ["Orapps – ESMS – Entry – Conveyance Expense"], "Local Conveyance Policy", 1, "Claim Process"),
        ("Conveyance claim submission path in Orapps?",
         ["Orapps – ESMS – Entry – Conveyance Expense"], "Local Conveyance Policy", 1, "Claim Process"),
        ("Who approves local conveyance claims?",
         ["approved only by BM grade employees"], "Local Conveyance Policy", 1, "Approval"),
        ("BM grade approves which claims?",
         ["approved only by BM grade employees"], "Local Conveyance Policy", 1, "Approval"),
        ("Does Local Conveyance Policy apply outside city limits?",
         ["outside the respective City/Town Municipal Corporation"], "Local Conveyance Policy", 1, "Eligibility"),
        ("Is travel outside municipal limits reimbursable under LC Policy?",
         ["outside the respective City/Town Municipal Corporation"], "Local Conveyance Policy", 1, "Eligibility"),
        ("Penalty for fake conveyance claims?",
         ["strict disciplinary action shall be taken"], "Local Conveyance Policy", 2, "Compliance"),
        ("What action is taken for fraudulent conveyance claims?",
         ["strict disciplinary action shall be taken"], "Local Conveyance Policy", 2, "Compliance"),
        ("Can two employees both claim for the same shared cab?",
         ["individual who has actually incurred the cost"], "Local Conveyance Policy", 1, "Reimbursement Rules"),
        ("Who can claim if a cab is shared between colleagues?",
         ["individual who has actually incurred the cost"], "Local Conveyance Policy", 1, "Reimbursement Rules"),
        ("Does Local Conveyance apply to BM grade too?",
         ["applicable across all grades"], "Local Conveyance Policy", 1, "Applicability"),
        ("Local Conveyance Policy — which grades?",
         ["applicable across all grades"], "Local Conveyance Policy", 1, "Applicability"),
        ("Is Local Conveyance applicable in all states?",
         ["applicable across India"], "Local Conveyance Policy", 1, "Applicability"),
        ("Is this conveyance policy pan-India?",
         ["applicable across India"], "Local Conveyance Policy", 1, "Applicability"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_more_dt_scenarios():
    """More Domestic Travel Policy scenario questions."""
    cases = []

    extras = [
        ("How many days in advance must travel be booked?",
         ["at least 7 days in advance"], "Domestic Travel Policy", 3, "Procedures"),
        ("Advance booking requirement for domestic travel?",
         ["at least 7 days in advance"], "Domestic Travel Policy", 3, "Procedures"),
        ("What travel booking tool must I use?",
         ["myBiz"], "Domestic Travel Policy", 2, "Booking Tool"),
        ("Which platform to book official travel?",
         ["myBiz"], "Domestic Travel Policy", 2, "Booking Tool"),
        ("Settlement deadline for travel expenses?",
         ["within 15 days of the trip"], "Domestic Travel Policy", 5, "Settlement"),
        ("In how many days must I settle travel bills?",
         ["within 15 days of the trip"], "Domestic Travel Policy", 5, "Settlement"),
        ("What happens on day 16 if I don't settle travel expenses?",
         ["auto-settlement on the 16th day"], "Domestic Travel Policy", 5, "Settlement"),
        ("Auto-settlement trigger for travel expenses?",
         ["auto-settlement on the 16th day"], "Domestic Travel Policy", 5, "Settlement"),
        ("When can I claim laundry during travel?",
         ["duration of travel exceeds three days"], "Domestic Travel Policy", 5, "Laundry"),
        ("Is laundry reimbursable for 2-day trips?",
         ["duration of travel exceeds three days"], "Domestic Travel Policy", 5, "Laundry"),
        ("Can I stay in a hotel for a same-day trip?",
         ["not eligible to avail the accommodation"], "Domestic Travel Policy", 3, "Same-Day Return"),
        ("Same-day return and hotel entitlement?",
         ["not eligible to avail the accommodation"], "Domestic Travel Policy", 3, "Same-Day Return"),
        ("What distance makes domestic travel eligible for policy?",
         ["domestic travel exceeding a distance of 300 km"], "Domestic Travel Policy", 2, "Scope"),
        ("Minimum distance for Domestic Travel Policy to apply?",
         ["domestic travel exceeding a distance of 300 km"], "Domestic Travel Policy", 2, "Scope"),
        ("My flight was delayed 4 hours. What am I entitled to?",
         ["delayed by more than 3 hours"], "Domestic Travel Policy", 4, "Flight Delay"),
        ("Flight delay policy — what is the threshold?",
         ["delayed by more than 3 hours"], "Domestic Travel Policy", 4, "Flight Delay"),
        ("Can senior leaders travel on the same flight?",
         ["senior officials travelling to the same destination on the same day take separate flights"],
         "Domestic Travel Policy", 3, "Travel Guidelines"),
        ("What is the travel guideline for senior officials?",
         ["senior officials travelling to the same destination on the same day take separate flights"],
         "Domestic Travel Policy", 3, "Travel Guidelines"),
        ("Can a female employee use a higher grade hotel?",
         ["hotel limits of the next higher grade"], "Domestic Travel Policy", 4, "Women Policy"),
        ("Women travel safety: night travel policy?",
         ["Avoidance of Night Travel"], "Domestic Travel Policy", 4, "Women Policy"),
        ("Should women employees avoid service apartments?",
         ["avoid staying in service apartments"], "Domestic Travel Policy", 4, "Women Policy"),
        ("What flat rate applies if I arrange my own stay?",
         ["30% of the entitlement"], "Domestic Travel Policy", 5, "Flat Rate"),
        ("Flat rate for BMH7+ if self-arranging accommodation?",
         ["Rs. 6,000 per day"], "Domestic Travel Policy", 5, "Flat Rate"),
        ("Full day cab booking trigger?",
         ["travel to three or more locations on a given day"], "Domestic Travel Policy", 5, "Cab Policy"),
        ("When can I book a full-day cab?",
         ["travel to three or more locations on a given day"], "Domestic Travel Policy", 5, "Cab Policy"),
        ("Hotel limit inclusive of taxes?",
         ["inclusive of applicable taxes"], "Domestic Travel Policy", 7, "Lodging"),
        ("Are taxes included in lodging limits?",
         ["inclusive of applicable taxes"], "Domestic Travel Policy", 7, "Lodging"),
    ]

    for q, kf, src, pg, cat in extras:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_more_informal():
    """Additional informal/mixed language query variants."""
    cases = []

    informals = [
        ("Meri relocation ho rahi hai. Packers and movers kaun pay karega?",
         ["The company shall directly make payment"], "Joining Policy", 1, "Packers & Movers"),
        ("M3H1 ko kitna monthly MAB milta hai?",
         ["2,16,667"], "Talent Mobility Policy", 7, "MAB - M3H1"),
        ("M3H1 ka SIA kitna hai?",
         ["45,000"], "Talent Mobility Policy", 7, "SIA - M3H1"),
        ("M3 employee ka monthly MAB kya hai?",
         ["1,58,333"], "Talent Mobility Policy", 7, "MAB - M3"),
        ("M3 ka annual MAB?",
         ["19,00,000"], "Talent Mobility Policy", 7, "MAB - M3"),
        ("M2 ka monthly MAB amount kya hai?",
         ["1,08,333"], "Talent Mobility Policy", 7, "MAB - M2"),
        ("M1 ka annual MAB batao?",
         ["8,52,000"], "Talent Mobility Policy", 7, "MAB - M1"),
        ("E2 employee SIA kya hoga?",
         ["10,000"], "Talent Mobility Policy", 7, "SIA - E1/E2"),
        ("Mumbai mein BMH3-H6 ka hotel limit kya hai?",
         ["8000"], "Domestic Travel Policy", 7, "Lodging"),
        ("Delhi mein M3 ka hotel limit?",
         ["6000"], "Domestic Travel Policy", 7, "Lodging"),
        ("Class II city mein M1 ka lodging limit?",
         ["2300"], "Domestic Travel Policy", 7, "Lodging"),
        ("Kya BMH9 ko flight mein business class milti hai?",
         ["Premium Economy / Business"], "Domestic Travel Policy", 7, "Mode of Travel"),
        ("BMH7/H8 ko kaunsa flight class milega?",
         ["Economy / Premium Economy"], "Domestic Travel Policy", 7, "Mode of Travel"),
        ("M3H1 ko train mein kaunsa class milega?",
         ["2nd AC"], "Domestic Travel Policy", 7, "Mode of Travel"),
        ("E1 ko train mein kaunsa class milega?",
         ["3rd AC/Chair Car"], "Domestic Travel Policy", 7, "Mode of Travel"),
        ("4-wheeler se office travel karne par kya milega?",
         ["four wheeler @ Rs. 10.00 / - per km"], "Local Conveyance Policy", 1, "Conveyance Rates"),
        ("AIC mein kitne member hone chahiye?",
         ["minimum of 3 members"], "POSH Policy", 4, "Quorum"),
        ("POSH mein external member ko kitna milta hai per day?",
         ["Rs. 250 per day"], "POSH Policy", 4, "External Member"),
        ("POSH complaint kitni copies daalni padti hai?",
         ["six copies of the complaint"], "POSH Policy", 6, "Filing"),
        ("Gender policy kitne saal mein review hoti hai?",
         ["every two years"], "Gender Policy", 3, "Review"),
        ("Whistleblower complaint karne ke baad follow up kab kar sakte hain?",
         ["four weeks after the submission"], "Whistleblower Policy", 4, "Follow-up"),
        ("Grievance policy mein anonymous complaint chalti hai?",
         ["Anonymous complaints will be considered"], "Grievance Mechanism Policy", 3, "Anonymous"),
        ("Joining policy mein pre-joining visit kitne din ka hota hai?",
         ["maximum period of 3 days"], "Joining Policy", 1, "Pre-Joining Visit"),
        ("700 km se kam relocation par per km kya milega?",
         ["Rs. 50 per km"], "Joining Policy", 1, "Transportation"),
        ("700 km se zyada relocation par per km kya milega?",
         ["Rs. 60 per km"], "Joining Policy", 1, "Transportation"),
        ("AIC mein mahilao ka ratio kya hona chahiye?",
         ["50% women representation"], "POSH Policy", 4, "Quorum"),
        ("3 saal baad rotation mandatory hai kya?",
         ["3 years = trigger for rotation"], "Talent Mobility Policy", 4, "Rotation Trigger"),
        ("SIA ke liye kitna distance chahiye?",
         ["relocation >20 kms"], "Talent Mobility Policy", 7, "SIA Condition"),
        ("Ghar shift karne par SIA milega?",
         ["shifting house"], "Talent Mobility Policy", 6, "SIA Condition"),
        ("MAB kitne saal ke baad CTC mein merge hota hai?",
         ["merged with CTC on completion of 1 year"], "Talent Mobility Policy", 6, "MAB Duration"),
    ]

    for q, kf, src, pg, cat in informals:
        cases.append(_case(q, kf, src, pg, cat))

    return cases


def gen_bulk_extra(existing_facts):
    """Use remaining EXTRA_TEMPLATES not already used in original generator."""
    # Original generator used templates[:12]; we use [12:20]
    EXTRA_TEMPLATES_REMAINING = [
        "I work in a subsidiary. Does {fact} apply to me?",
        "Is {fact} mentioned in the latest version of the policy?",
        "What supporting documents do I need for {fact}?",
        "What happens if {fact} is not followed?",
        "Can {fact} be appealed?",
        "Is there an exception to {fact}?",
        "Who is responsible for implementing {fact}?",
        "How frequently does {fact} get updated?",
    ]
    cases = []
    for fact, source, page, category in existing_facts:
        short_fact = fact[:50]
        for tmpl in EXTRA_TEMPLATES_REMAINING:
            q = tmpl.format(fact=short_fact, source=source)
            cases.append(_case(q, [fact[:40]], source, page, category))
    return cases


# ─── Main expansion logic ─────────────────────────────────────────────────────

ORIGINAL_FACTS = [
    # Local Conveyance
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
    # Domestic Travel
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
    # Grievance
    ("2 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("10 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("15 working days", "Grievance Mechanism Policy", 3, "Timelines"),
    ("every two years", "Grievance Mechanism Policy", 4, "Review"),
    ("raised verbally or in writing", "Grievance Mechanism Policy", 3, "Filing"),
    ("Anonymous complaints will be considered", "Grievance Mechanism Policy", 3, "Anonymous"),
    ("protected from retaliation", "Grievance Mechanism Policy", 2, "Protection"),
    ("part-time", "Grievance Mechanism Policy", 2, "Applicability"),
    ("contract workers", "Grievance Mechanism Policy", 2, "Applicability"),
    ("trainees", "Grievance Mechanism Policy", 2, "Applicability"),
    ("Immediate HR Representative", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("Line Manager or Supervisor", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("Head of Department", "Grievance Mechanism Policy", 2, "Escalation Channels"),
    ("escalate the grievance to the next level", "Grievance Mechanism Policy", 3, "Escalation"),
    # POSH
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
    ("leave to the Aggrieved Woman up to a period of 3 (three) months", "POSH Policy", 7, "Interim Relief"),
    ("in addition to the entitled leaves", "POSH Policy", 7, "Interim Relief"),
    ("suspend the RE for defined period", "POSH Policy", 7, "Interim Action"),
    ("not be published, communicated or made known", "POSH Policy", 8, "Confidentiality"),
    ("disciplinary action will be taken", "POSH Policy", 8, "Confidentiality"),
    ("protected from any form of retaliation", "POSH Policy", 8, "Protection"),
    ("allegation was malicious", "POSH Policy", 8, "False Complaints"),
    ("All persons employed at Arvind", "POSH Policy", 1, "Applicability"),
    ("Third parties and/or visitors", "POSH Policy", 1, "Applicability"),
    ("outside the workplace", "POSH Policy", 2, "Scope"),
    ("Office parties", "POSH Policy", 2, "Scope"),
    ("prohibits same-sex harassment", "POSH Policy", 5, "Scope"),
    ("gender neutral", "POSH Policy", 5, "Scope"),
    ("Her relative or friend", "POSH Policy", 5, "Who Can File"),
    ("Her co-worker", "POSH Policy", 5, "Who Can File"),
    ("notice of 15 (fifteen) days", "POSH Policy", 6, "AIC Procedures"),
    # Whistleblower
    ("Breach of internal compliance requirements", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Bribery and corruption", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Procurement and tendering fraud", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Undue awarding of contracts", "Whistleblower Policy", 3, "Reportable Issues"),
    ("False invoicing", "Whistleblower Policy", 3, "Reportable Issues"),
    ("Employee negligence", "Whistleblower Policy", 3, "Reportable Issues"),
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
    # Gender
    ("all employees of Arvind Ltd", "Gender Policy", 2, "Applicability"),
    ("interns", "Gender Policy", 2, "Applicability"),
    ("contract staff", "Gender Policy", 2, "Applicability"),
    ("third-party partners", "Gender Policy", 2, "Applicability"),
    ("every two years", "Gender Policy", 3, "Review"),
    ("retaliation against individuals who raise concerns in good faith is strictly prohibited", "Gender Policy", 3, "Protection"),
    ("Hiring and Promotions are conducted based on merit", "Gender Policy", 3, "Principles"),
    # Talent Mobility
    ("3 years = trigger for rotation", "Talent Mobility Policy", 4, "Rotation Trigger"),
    ("All positions upto M2", "Talent Mobility Policy", 4, "IJP"),
    ("Managers cannot block mobility", "Talent Mobility Policy", 4, "Governance"),
    ("CHRO/CEO can approve exceptions", "Talent Mobility Policy", 4, "Exceptions"),
    ("1st Rotation – within the city", "Talent Mobility Policy", 4, "Rotation Framework"),
    ("2nd Rotation – across different business / different location", "Talent Mobility Policy", 4, "Rotation Framework"),
    ("merged with CTC on completion of 1 year", "Talent Mobility Policy", 6, "MAB Duration"),
    ("shifting house", "Talent Mobility Policy", 6, "SIA Condition"),
    ("relocation >20 kms", "Talent Mobility Policy", 7, "SIA Condition"),
    ("One time", "Talent Mobility Policy", 6, "SIA Type"),
    ("sensitive roles exceed tenure", "Talent Mobility Policy", 2, "Risk"),
    ("Monthly allowance", "Talent Mobility Policy", 6, "MAB Description"),
    ("One-time lump sum for household setup", "Talent Mobility Policy", 6, "SIA Description"),
    # Joining
    ("maximum period of 3 days", "Joining Policy", 1, "Pre-Joining Visit"),
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
    ("Income tax shall be grossed up", "Joining Policy", 1, "Tax"),
    ("The company shall directly make payment", "Joining Policy", 1, "Packers & Movers"),
    ("either a Pre-Joining Visit OR Post Joining Visit", "Joining Policy", 1, "Visit Options"),
    ("subsidiaries", "Joining Policy", 1, "Applicability"),
]


def main():
    print("=" * 60)
    print("Suite Expansion: 8,855 → 10,000")
    print("=" * 60)

    # Load existing suite
    print("\n[1] Loading existing suite...")
    with open(SUITE_FILE) as f:
        existing = json.load(f)
    existing_queries = {c["query"].strip().lower() for c in existing}
    print(f"  Loaded {len(existing)} existing cases")
    print(f"  Unique query strings: {len(existing_queries)}")

    # Extract corpus for verification
    print("\n[2] Extracting policy corpus...")
    corpus = extract_corpus()
    for p, t in corpus.items():
        print(f"  {p}: {len(t):,} chars")

    # Generate all new candidates
    print("\n[3] Generating new case candidates...")
    new_raw = []
    new_raw += gen_extended_transport()
    print(f"  Transport: {len(new_raw)}")
    n = len(new_raw)
    new_raw += gen_extended_mab_sia()
    print(f"  MAB/SIA: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_lodging()
    print(f"  Lodging: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_posh()
    print(f"  POSH: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_grievance()
    print(f"  Grievance: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_joining()
    print(f"  Joining: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_whistleblower()
    print(f"  Whistleblower: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_gender()
    print(f"  Gender: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_talent_mobility()
    print(f"  Talent Mobility: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_extended_local_conveyance()
    print(f"  Local Conveyance: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_more_dt_scenarios()
    print(f"  DT Scenarios: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_more_informal()
    print(f"  Informal: +{len(new_raw)-n}")
    n = len(new_raw)
    new_raw += gen_bulk_extra(ORIGINAL_FACTS)
    print(f"  Bulk extra: +{len(new_raw)-n}")
    print(f"  Total raw candidates: {len(new_raw)}")

    # Deduplicate against existing + within new
    print("\n[4] Deduplicating...")
    seen = set(existing_queries)
    unique_new = []
    for c in new_raw:
        q_lower = c["query"].strip().lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_new.append(c)
    print(f"  Unique new cases: {len(unique_new)}")

    # Verify keyFacts against corpus
    print("\n[5] Verifying keyFacts...")
    verified = []
    failed_kf = 0
    for c in unique_new:
        ok = all(verify_keyfact(kf, c["source"], corpus) for kf in c["keyFacts"])
        if ok:
            verified.append(c)
        else:
            failed_kf += 1
    print(f"  Passed verification: {len(verified)}")
    print(f"  Failed verification (excluded): {failed_kf}")

    # How many do we need?
    need = TARGET - len(existing)
    print(f"\n[6] Need {need} more cases. Have {len(verified)} verified candidates.")

    if len(verified) < need:
        print(f"  WARNING: Only {len(verified)} verified candidates — will produce {len(existing)+len(verified)} total")
        to_add = verified
    else:
        to_add = verified[:need]
        print(f"  Selecting first {len(to_add)} cases (surplus discarded)")

    # Assign new IDs
    start_id = len(existing) + 1
    new_cases = []
    for i, c in enumerate(to_add, start_id):
        new_cases.append({
            "id":       f"ETC{i:05d}",
            "query":    c["query"],
            "keyFacts": c["keyFacts"],
            "source":   c["source"],
            "page":     c["page"],
            "category": c["category"],
        })

    # Merge and save
    combined = existing + new_cases
    print(f"\n[7] Saving combined suite: {len(combined)} cases...")
    with open(SUITE_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"  Saved → {SUITE_FILE}")

    # Stats
    policy_counts = Counter(c["source"] for c in combined)
    print(f"\nFinal distribution:")
    for pol, cnt in sorted(policy_counts.items()):
        print(f"  {pol}: {cnt}")

    cat_counts = Counter(c["category"] for c in combined)
    print(f"\nTop 20 categories:")
    for cat, cnt in cat_counts.most_common(20):
        print(f"  {cat}: {cnt}")

    print(f"\n{'='*60}")
    print(f"DONE: {len(combined):,} total cases in {SUITE_FILE}")
    print(f"  Added {len(new_cases)} new cases to existing {len(existing)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
