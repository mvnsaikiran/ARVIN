"""
Generate test cases for 4 batch-2 policies:
 1. Group Term Life Insurance (GTI)
 2. Pankh Employee Referral
 3. Domestic Travel Expense Settlement Procedure
 4. Voluntary Death Contribution Scheme
"""
import json, random

QUERIES_GTI = [
    ("What is Group Term Life Insurance?", ["financial security", "natural death"], "Basics"),
    ("What does GTI cover at Arvind?", ["natural death", "suicide"], "Basics"),
    ("Is suicide covered under term life insurance?", ["suicide", "not be applicable"], "Exclusions"),
    ("What is the life insurance cover for M1 grade?", ["8,00,000"], "Grade-M1"),
    ("What is the GTI cover for M2?", ["12,50,000"], "Grade-M2"),
    ("What is the life insurance for M3?", ["18,00,000"], "Grade-M3"),
    ("What is the term life cover for E1?", ["3,00,000"], "Grade-E1"),
    ("What is the life insurance for E2?", ["5,50,000"], "Grade-E2"),
    ("What is the GTI cover for OT grade?", ["2,50,000"], "Grade-OT"),
    ("What is the life insurance for BMH9?", ["1,00,00,000"], "Grade-BMH9"),
    ("What is the term life cover for AVP?", ["50,00,000"], "Grade-AVP"),
    ("What is the GTI cover for VP grade?", ["85,00,000"], "Grade-VP"),
    ("What is the life insurance for BMH3?", ["30,00,000"], "Grade-BMH"),
    ("How is the death claim processed?", ["CMG", "death certificate", "Insurance Section"], "Settlement"),
    ("Who processes the life insurance claim?", ["CMG", "Insurance Section"], "Settlement"),
    ("What happens to the claim amount in GTI?", ["dues", "balance", "nominee", "Gratuity"], "Settlement"),
    ("Policy number for Group Term Life Insurance?", ["ARV|COR|EBF_GTI"], "Policy-Details"),
    ("Effective date of GTI policy?", ["01.01.2026"], "Policy-Details"),
    ("Who is covered under group term life insurance?", ["management", "staff cadre", "subsidiary"], "Applicability"),
    ("What is the life cover for DET grade?", ["3,00,000"], "Grade-E1"),
]

QUERIES_PANKH = [
    ("What is the Pankh employee referral program?", ["diverse", "inclusive", "M3"], "Basics"),
    ("Who can participate in the Pankh referral program?", ["all employees", "HR team", "selection process"], "Eligibility"),
    ("Can HR team members refer candidates under Pankh?", ["HR team", "selection process"], "Exclusions"),
    ("What grades are open for employee referrals?", ["M3", "upto M3"], "Eligibility"),
    ("What is the referral reward for E1-E2 grade?", ["5,000", "5000"], "Reward-E1"),
    ("What is the referral reward for M1?", ["7,500", "7500"], "Reward-M1"),
    ("What is the referral reward for M2 or M3?", ["10,000", "10000"], "Reward-M2M3"),
    ("What is the bonus for 5 successful referrals?", ["20,000", "20000"], "Bonus"),
    ("Is there a reward for referring male candidates?", ["no monetary reward", "no reward"], "Male-Referral"),
    ("When is the referral payout made?", ["3 months", "6 months", "tranches"], "Payout"),
    ("What conditions must be met for referral payout?", ["employed at Arvind", "not on notice"], "Payout-Conditions"),
    ("Is referral payout taxable?", ["taxable"], "Tax"),
    ("How do I refer a candidate in Darwinbox?", ["Darwinbox", "Recruitment", "Refer Tab"], "Process"),
    ("What is the policy number for Pankh?", ["ARV|ELC_PER"], "Policy-Details"),
    ("When was the Pankh program effective?", ["01.01.2023"], "Policy-Details"),
    ("What kind of candidates get monetary reward in Pankh?", ["female", "transgender", "specially-abled"], "Reward-Criteria"),
    ("What is the referral bonus for 5 diverse hires?", ["20,000"], "Bonus"),
    ("Can referred employees be on notice at time of payout?", ["not on notice", "employed"], "Payout-Conditions"),
]

QUERIES_TRAVEL = [
    ("How do I submit travel expenses in OneArvind?", ["OneArvind", "Services", "Travel Menu", "MMT"], "Process"),
    ("What is the path for travel settlement in OneArvind?", ["Services", "Travel Menu", "Travel Booking", "MMT"], "Process"),
    ("How do I initiate travel settlement?", ["My Tour Dashboard", "Tour No", "Initiate Settlement"], "Process"),
    ("What is the My Tour Dashboard?", ["unsettled expenses", "Tour No", "settlement"], "Process"),
    ("What expense types can I claim for travel?", ["Boarding", "Flat Rate", "Conveyance", "Telephone"], "Expense-Types"),
    ("What does Boarding expense cover?", ["Food", "Dining"], "Expense-Types"),
    ("What does Flat Rate mean in travel expenses?", ["relatives", "friends"], "Expense-Types"),
    ("What conveyance modes are covered in travel settlement?", ["Uber", "Ola", "Taxi", "Auto", "Metro"], "Conveyance"),
    ("Are hotel phone calls reimbursed?", ["hotel phones", "NOT be reimbursed", "not reimbursed"], "Exclusions"),
    ("Is web check-in reimbursed?", ["Web check-in", "not be reimbursed"], "Exclusions"),
    ("Is express boarding reimbursed?", ["Express boarding", "not be reimbursed"], "Exclusions"),
    ("Are extra baggage charges reimbursed?", ["Extra baggage", "receipts", "approval"], "Baggage"),
    ("How does the manager approve travel expenses?", ["Manager Approval", "My Team Tour", "Tour Pending"], "Manager-Approval"),
    ("What system is used for travel booking?", ["MMT", "Travel Booking", "OneArvind"], "System"),
    ("What is Create Your Tour Expenses?", ["Create Your Tour", "expense", "MMT"], "Process"),
    ("Is invoice required for travel expenses?", ["invoice", "mandatory"], "Requirements"),
]

QUERIES_VDCS = [
    ("What is the Voluntary Death Contribution Scheme?", ["monetary contributions", "deceased", "dependants"], "Basics"),
    ("Who is covered under VDCS?", ["management", "staff cadre", "Arvind Ltd", "subsidiaries"], "Applicability"),
    ("What is the death contribution for OT grade?", ["100"], "Grade-OT"),
    ("What is the death contribution for E1?", ["100"], "Grade-E1"),
    ("What is the death contribution for M1?", ["175"], "Grade-M1"),
    ("What is the death contribution for M2?", ["200"], "Grade-M2"),
    ("What is the death contribution for M3?", ["300"], "Grade-M3"),
    ("What is the death contribution for BMH3?", ["550"], "Grade-BMH"),
    ("What is the death contribution for BMH6?", ["800"], "Grade-BMH6"),
    ("What is the contribution for BMH5?", ["550"], "Grade-BMH"),
    ("How much does an M1 employee contribute when a colleague dies?", ["175"], "Grade-M1"),
    ("What is the policy number for Voluntary Death Contribution?", ["ARV|EFB_IPP"], "Policy-Details"),
    ("When is the VDCS effective from?", ["01.05.2021"], "Policy-Details"),
    ("Who benefits from the Voluntary Death Contribution Scheme?", ["dependants", "beneficiaries"], "Basics"),
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
        for variant in variants:
            cases.append({
                "id":       f"{prefix}_{len(cases)+1:04d}",
                "query":    variant,
                "source":   source,
                "keyFacts": key_facts,
                "category": category,
            })
    return cases


all_b2 = []
all_b2 += make_cases(QUERIES_GTI,   "Group Term Life Insurance",                       "GTI")
all_b2 += make_cases(QUERIES_PANKH, "Pankh Employee Referral",                         "PER")
all_b2 += make_cases(QUERIES_TRAVEL,"Domestic Travel Expense Settlement Procedure",    "TSP")
all_b2 += make_cases(QUERIES_VDCS,  "Voluntary Death Contribution Scheme",             "VDC")

random.shuffle(all_b2)

with open("batch2_test_suite.json", "w") as f:
    json.dump(all_b2, f, indent=2)

print(f"Generated {len(all_b2)} test cases")
from collections import Counter
cats = Counter(c["source"] for c in all_b2)
for src, cnt in sorted(cats.items()):
    print(f"  {src}: {cnt}")
