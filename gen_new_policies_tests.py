"""
Generate test cases for the 5 new policies:
 1. Employee Assistance Program (EAP)
 2. Employee Expense Reimbursement Policy
 3. Exit & Full & Final Settlement Policy
 4. Group Health Insurance Policy
 5. Group Personal Accident Insurance Scheme
"""
import json, random

QUERIES_EAP = [
    ("What is EAP?", ["free and confidential", "one-to-one support"], "Basics"),
    ("What is the Employee Assistance Program?", ["free and confidential", "counsellor"], "Basics"),
    ("What does EAP stand for?", ["Employee Assistance Program"], "Basics"),
    ("Who provides EAP at Arvind?", ["1to1help", "1to1Help"], "Provider"),
    ("Which company provides the EAP app?", ["1to1help"], "Provider"),
    ("What can I use EAP for?", ["stress", "anxiety", "family"], "Use-Cases"),
    ("When should I contact EAP?", ["stress", "work pressure", "burnout"], "Use-Cases"),
    ("Is EAP confidential?", ["confidential", "no need to inform"], "Confidentiality"),
    ("Does my manager know if I use EAP?", ["confidential", "no need to inform"], "Confidentiality"),
    ("Is EAP free?", ["free and confidential"], "Cost"),
    ("How much does EAP cost?", ["free and confidential"], "Cost"),
    ("How does EAP work?", ["phone", "video", "in person"], "How-It-Works"),
    ("What modes of counselling are available in EAP?", ["phone", "video", "in person"], "How-It-Works"),
    ("What is the EAP toll-free number?", ["1800-258-8121", "1800-258-8999"], "Contact"),
    ("EAP emergency contact number", ["1800-258-8121", "1800-258-8999"], "Contact"),
    ("How do I download the 1to1help app?", ["Play Store", "App Store"], "App"),
    ("How to register on 1to1help?", ["work email", "OTP"], "App"),
    ("Is my username on 1to1help private?", ["private", "not be shared"], "App"),
    ("Can a manager refer an employee for EAP counselling?", ["managersupport@1to1help.net", "voluntary"], "Manager-Referral"),
    ("What is the manager referral process for EAP?", ["managersupport@1to1help.net"], "Manager-Referral"),
    ("Can my manager force me to use EAP?", ["voluntary", "cannot force"], "Manager-Referral"),
    ("Is EAP voluntary?", ["voluntary"], "Manager-Referral"),
    ("What is the turnaround time for EAP referrals?", ["9 am", "9 pm", "same day"], "Turnaround"),
    ("How quickly does EAP respond to referrals?", ["9 am", "9 pm", "next day"], "Turnaround"),
    ("What self-help content is available on 1to1help?", ["articles", "podcasts", "videos"], "Self-Help"),
    ("How many assessments are on the EAP app?", ["180"], "Assessments"),
    ("What topics are covered in EAP articles?", ["stress management", "self-development"], "Self-Help"),
]

QUERIES_EER = [
    ("What is the Employee Expense Reimbursement Policy?", ["ARV|ELC_EER", "01.04.2026"], "Policy-Details"),
    ("When is the Expense Reimbursement Policy effective?", ["01.04.2026"], "Policy-Details"),
    ("Is there reimbursement for birthday celebrations?", ["no reimbursement", "HR"], "Birthday"),
    ("Who handles birthday celebrations at Arvind?", ["HR"], "Birthday"),
    ("What is the farewell gift limit for CXO-level employees?", ["10,000", "CEO", "CHRO"], "Farewell"),
    ("Who approves CXO farewell gift expense?", ["CEO", "CHRO"], "Farewell"),
    ("Is giving gifts to vendors allowed?", ["prohibited", "CEO", "CHRO", "Group Ethics Officer"], "Gifts"),
    ("What is the gift policy at Arvind?", ["prohibited"], "Gifts"),
    ("Can I get reimbursed for working late food?", ["8:00 pm", "Admin", "5:00 pm"], "Late-Food"),
    ("What is the process for late night dinner at office?", ["8:00 pm", "5:00 pm", "Admin"], "Late-Food"),
    ("How do I claim fuel expenses for company car?", ["fuel vouchers", "petrol pumps"], "Car-Expenses"),
    ("How is company car maintenance handled?", ["dealerships", "company name"], "Car-Expenses"),
    ("Can I buy stationery and claim reimbursement?", ["admin team", "no reimbursement"], "Admin-Purchases"),
    ("Where should I claim telephone charges for international trips?", ["travel settlement"], "Travel-Expenses"),
    ("Where do I submit conveyance expenses?", ["conveyance tab"], "Conveyance"),
    ("Within how many days must I submit expenses?", ["7 working days"], "Submission"),
    ("What happens if I delay expense submission?", ["forfeiture of reimbursement"], "Non-Compliance"),
    ("Who approves expense reimbursement requests?", ["Department Head", "Accounts Officer"], "Approval"),
    ("Who approves exceptions to the expense policy?", ["CFO", "CHRO"], "Exceptions"),
    ("Is puja expense reimbursed?", ["Admin team", "Pandit"], "Puja"),
]

QUERIES_FNF = [
    ("What is the notice period at Arvind?", ["60", "sixty days"], "Notice-Period"),
    ("How many days notice is required for resignation?", ["60", "sixty"], "Notice-Period"),
    ("What is included in Notice Pay?", ["Basic Salary", "House Rent Allowance", "Flexible Benefits Plan"], "Notice-Pay"),
    ("How is Notice Pay calculated?", ["basic salary", "Personal Allowance", "HRA", "Flexible Benefits Plan"], "Notice-Pay"),
    ("How to resign from Arvind?", ["Darwinbox", "Employee Life Cycle", "Separation"], "Resignation-Process"),
    ("Can I resign by email?", ["email", "not be considered valid"], "Resignation-Process"),
    ("When does my notice period start?", ["date", "resigned in the system"], "Resignation-Process"),
    ("What is the final settlement timeline?", ["30 days", "last working day"], "FnF-Timeline"),
    ("Within how many days is the final payout done?", ["30 days", "last working day"], "FnF-Timeline"),
    ("What is the Eklavya policy recovery rule?", ["50%", "100%", "tuition"], "Eklavya"),
    ("What happens if I leave within 1 year of completing Eklavya?", ["100%", "tuition fee"], "Eklavya"),
    ("Eklavya recovery within 2 years?", ["50%", "tuition fee"], "Eklavya"),
    ("When do I get the experience letter?", ["last working day"], "Letters"),
    ("When is the relieving letter issued?", ["No Dues Clearance"], "Letters"),
    ("What is No Dues Clearance?", ["Business HR", "CMG", "IT", "Admin", "Finance"], "No-Dues"),
    ("Who is involved in No Dues Clearance?", ["Business HR", "CMG", "IT", "Admin", "Finance"], "No-Dues"),
    ("What is IT clearance during exit?", ["laptops", "last working day", "damaged"], "IT-Clearance"),
    ("How is PL balance paid during FnF?", ["Consolidated Salary", "Basic Salary"], "PL-Payout"),
    ("Can I transfer my PF on exit?", ["transfer", "UAN", "EPFO"], "PF"),
    ("What is the HR contact for FnF exceptions?", ["corporate.hr@arvind.in"], "Contact"),
    ("What happens with LWP during notice period?", ["gross salary", "not adjusted"], "LWP"),
    ("What is the policy number for FnF settlement?", ["ARV|COR|ELC_FnF|001|010922"], "Policy-Details"),
    ("Effective date of FnF policy?", ["24.02.2024"], "Policy-Details"),
]

QUERIES_GHI = [
    ("What is the health insurance cover for M1 grade?", ["4,00,000", "8,000", "12,000"], "Entitlement-M1"),
    ("What is the family floater for M2?", ["4,00,000"], "Entitlement-M1"),
    ("What is the health insurance for BM grade?", ["6,00,000", "12,000", "18,000"], "Entitlement-BM"),
    ("What is the room rent limit for BM?", ["12,000"], "Entitlement-BM"),
    ("What is the ICU charge limit for BM?", ["18,000"], "Entitlement-BM"),
    ("What is the health cover for E1 grade?", ["3,00,000", "6,000", "9,000"], "Entitlement-E1"),
    ("What is the room charge for E2?", ["6,000"], "Entitlement-E1"),
    ("What is the ICU limit for M3?", ["12,000"], "Entitlement-M1"),
    ("Who is covered under GHI?", ["spouse", "two children", "25 years"], "Applicability"),
    ("Is my spouse covered under health insurance?", ["spouse", "two children"], "Applicability"),
    ("Are children covered under GHI?", ["two children", "25 years"], "Applicability"),
    ("What is the maternity benefit under GHI?", ["50,000", "normal delivery"], "Maternity"),
    ("What is the limit for C-section delivery?", ["85,000", "abnormal delivery"], "Maternity"),
    ("Is maternity covered under GHI?", ["50,000", "85,000"], "Maternity"),
    ("What is the critical illness benefit?", ["5,00,000", "once-in-a-lifetime"], "Critical-Illness"),
    ("What diseases are covered under critical illness?", ["cardiac", "cancer", "renal"], "Critical-Illness"),
    ("How do I use cashless hospitalisation?", ["FHPL", "network hospital", "pre-authorisation"], "Cashless"),
    ("What is the GHI helpline number?", ["1800-425-4033"], "Contact"),
    ("Where do I intimate a claim?", ["1800-425-4033", "intimation@fhpl.net"], "Contact"),
    ("Within how many hours must I intimate hospitalisation?", ["24 hours"], "Intimation"),
    ("How do I file a reimbursement claim?", ["30 days", "discharge"], "Claim-Process"),
    ("What is the claim submission deadline?", ["30 days", "discharge"], "Claim-Process"),
    ("How many days pre-hospitalisation is covered?", ["30 days"], "Coverage-Period"),
    ("How many days post-hospitalisation is covered?", ["60 days"], "Coverage-Period"),
    ("Is ambulance covered under GHI?", ["5,000", "ambulance"], "Coverage"),
    ("Is Ayush treatment covered?", ["Ayush", "family sum insured"], "Coverage"),
    ("Is oral chemotherapy covered?", ["Oral Chemotherapy", "sum insured"], "Coverage"),
    ("What is the minimum hospitalisation period for GHI?", ["24 hrs", "24 hours"], "Eligibility"),
    ("Policy number for Group Health Insurance?", ["ARV|EBF_MLB|005|010126"], "Policy-Details"),
    ("Effective date of GHI policy?", ["01.01.2026"], "Policy-Details"),
]

QUERIES_GPA = [
    ("What is the Capital Sum Insured formula?", ["60 times", "monthly basic"], "CSI"),
    ("How is CSI calculated under GPA?", ["60 times", "monthly basic"], "CSI"),
    ("What is the accidental death benefit?", ["24 times", "monthly consolidated", "5 lakhs"], "Death-Benefit"),
    ("What is the TTD benefit amount?", ["1%", "5,000", "100 weeks"], "TTD"),
    ("How long is TTD benefit paid?", ["100 weeks"], "TTD"),
    ("What is covered under accidental hospitalisation?", ["25%", "40%"], "Medical-Extension"),
    ("What is the education grant for children under GPA?", ["10%", "10,000", "two children"], "Education-Grant"),
    ("Education grant after accidental death?", ["10,000 per child", "25 years"], "Education-Grant"),
    ("What is covered for broken bones?", ["20,000", "IPD", "OPD"], "Fracture"),
    ("Is fracture covered under personal accident insurance?", ["20,000"], "Fracture"),
    ("What is the ambulance charge under GPA?", ["3,000", "actuals"], "Ambulance"),
    ("What is covered for funeral expenses?", ["2,500", "2%", "CSI"], "Funeral"),
    ("What is PTD?", ["Partial Total Disablement"], "Definitions"),
    ("What is TTD?", ["Temporary Total Disablement"], "Definitions"),
    ("What is PPD?", ["Permanent Partial Disablement"], "Definitions"),
    ("Who is covered under GPA?", ["management", "staff cadre", "subsidiaries"], "Applicability"),
    ("Can sum insured change during the year?", ["promotion", "grade change"], "Mid-Term"),
    ("What is the maximum accumulation under GPA?", ["50 crores"], "Maximum"),
    ("Policy number for Group Personal Accident?", ["ARV|COR|EBF_GPA|001|01012026"], "Policy-Details"),
    ("Effective date of GPA scheme?", ["01.01.2026"], "Policy-Details"),
]

def make_cases(queries, source, prefix):
    cases = []
    for q_text, key_facts, category in queries:
        variants = [
            q_text,
            f"As per Arvind HR policy, {q_text}",
            f"Please tell me: {q_text}",
            f"HR query: {q_text}",
        ]
        for i, variant in enumerate(variants):
            cases.append({
                "id":        f"{prefix}_{len(cases)+1:04d}",
                "query":     variant,
                "source":    source,
                "keyFacts":  key_facts,
                "category":  category,
            })
    return cases

all_new = []
all_new += make_cases(QUERIES_EAP, "Employee Assistance Program (EAP)", "EAP")
all_new += make_cases(QUERIES_EER, "Employee Expense Reimbursement Policy", "EER")
all_new += make_cases(QUERIES_FNF, "Exit & Full & Final Settlement Policy", "FNF")
all_new += make_cases(QUERIES_GHI, "Group Health Insurance Policy", "GHI")
all_new += make_cases(QUERIES_GPA, "Group Personal Accident Insurance Scheme", "GPA")

random.shuffle(all_new)

with open("new_policies_test_suite.json", "w") as f:
    json.dump(all_new, f, indent=2)

print(f"Generated {len(all_new)} test cases")
from collections import Counter
cats = Counter(c["source"] for c in all_new)
for src, cnt in sorted(cats.items()):
    print(f"  {src}: {cnt}")
