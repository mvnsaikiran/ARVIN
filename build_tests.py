import pdfplumber, re, json
from docx import Document

# ─────────────────────────────────────────────
# Build full-text corpus per policy
# ─────────────────────────────────────────────
def pdf_text(path):
    pages = {}
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            t = page.extract_text() or ""
            pages[i] = t
    return pages

def docx_text(path):
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            parts.append(" ".join(c.text.strip() for c in row.cells))
    return {1: "\n".join(parts)}

BASE = "/home/user/ARVIN/policies/"
corpora = {
    "Local Conveyance Policy":              pdf_text(BASE+"cf8daeee-localconveyancepolicyarvindlimited.pdf"),
    "Domestic Travel Policy":               pdf_text(BASE+"f34aa66a-domestictravelpolicyarvindlimited.pdf"),
    "POSH Policy (Prevention of Sexual Harassment)": pdf_text(BASE+"4d8fe661-poshpolicyarvindlimited.pdf"),
    "Whistleblower Policy":                 pdf_text(BASE+"cbdae693-whistleblowerpolicyarvindlimited.pdf"),
    "Grievance Mechanism Policy 2025":      pdf_text(BASE+"e08407da-arvindgrievancemechanismpolicy2025.pdf"),
    "Gender Policy 2025":                   pdf_text(BASE+"99ecde3a-arvindgenderpolicy2025.pdf"),
    "Talent Mobility Policy":               pdf_text(BASE+"adea8313-talentmobility.pdf"),
    "Joining Policy":                       docx_text(BASE+"bad821d9-joiningpolicyarvindlimited.docx"),
}

corpus_full = {}
for pol, pages in corpora.items():
    corpus_full[pol] = "\n".join(pages.values()).lower()

def ok(fact, policy):
    return fact.lower() in corpus_full[policy]

# ─────────────────────────────────────────────
# Test cases - each tuple: (query, keyFacts, source, page, category)
# ALL keyFacts verified against corpus before inclusion
# ─────────────────────────────────────────────
raw_tests = []

# =============================================================
# DOMESTIC TRAVEL POLICY (~130 cases)
# =============================================================
DTP = "Domestic Travel Policy"

raw_tests += [
    # --- Lodging limits Class I ---
    ("What is the lodging limit for BMH3-H6 grade in Class I cities?",
     ["8000","class i","bmh3, h4, h5, h6"],
     DTP, 7, "Lodging Limits"),
    ("BMH3 grade employee ka hotel limit kya hai Class I city mein?",
     ["8000","class i","bmh3, h4, h5, h6"],
     DTP, 7, "Lodging Limits"),
    ("What lodging entitlement does M3-H1 get in a Class I city?",
     ["6000","class i","m3h1, m3, m2"],
     DTP, 7, "Lodging Limits"),
    ("M3 grade mein Class I mein kitna hotel limit milta hai?",
     ["6000","m3h1, m3, m2","class i"],
     DTP, 7, "Lodging Limits"),
    ("What is the hotel limit for M1/E2/E1 grade in Class I?",
     ["3400","m1, mt, e2, get, e1, ot","class i"],
     DTP, 7, "Lodging Limits"),
    ("E1 grade employee Class I mein kitna hotel le sakta hai?",
     ["3400","class i","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Lodging Limits"),
    ("What is the lodging entitlement for BMH7 and above?",
     ["at actual","bmh7 and above"],
     DTP, 7, "Lodging Limits"),
    ("Senior grade BMH7 ke liye lodging limit kya hai?",
     ["at actual","bmh7 and above"],
     DTP, 7, "Lodging Limits"),

    # --- Lodging limits Class II ---
    ("What is the hotel limit for BMH3-H6 in a Class II city?",
     ["6000","class ii","bmh3, h4, h5, h6"],
     DTP, 7, "Lodging Limits"),
    ("BMH5 grade ke liye Class II city mein lodging limit kya hai?",
     ["6000","class ii","bmh3, h4, h5, h6"],
     DTP, 7, "Lodging Limits"),
    ("What lodging limit does M3-M2 grade get in Class II?",
     ["5000","class ii","m3h1, m3, m2"],
     DTP, 7, "Lodging Limits"),
    ("M2 employee ko Class II mein kitna milta hai hotel ke liye?",
     ["5000","class ii","m3h1, m3, m2"],
     DTP, 7, "Lodging Limits"),
    ("What is the lodging limit for M1/E2/E1 in Class II city?",
     ["2300","class ii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Lodging Limits"),
    ("E2 grade employee Class II mein hotel ka limit kya hai?",
     ["2300","class ii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Lodging Limits"),

    # --- Lodging limits Class III ---
    ("What is the hotel limit for BMH3-H6 in Class III cities?",
     ["5000","class iii","bmh3, h4, h5, h6"],
     DTP, 7, "Lodging Limits"),
    ("What is the lodging entitlement for M3-M2 grade in Class III?",
     ["4000","class iii","m3h1, m3, m2"],
     DTP, 7, "Lodging Limits"),
    ("What is the hotel limit for E1/OT grade in Class III?",
     ["1700","class iii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Lodging Limits"),
    ("OT grade employee ko Class III mein hotel limit kya milta hai?",
     ["1700","class iii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Lodging Limits"),

    # --- Boarding limits ---
    ("What is the boarding (food) limit for BMH3-H6 in Class I city?",
     ["1500","class i","bmh3, h4, h5, h6"],
     DTP, 7, "Boarding Limits"),
    ("BMH4 grade ke liye Class I mein boarding limit kya hai?",
     ["1500","class i","bmh3, h4, h5, h6"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding entitlement for M3H1/M3/M2 in Class I?",
     ["1200","class i","m3h1, m3, m2"],
     DTP, 7, "Boarding Limits"),
    ("M2 employee ka food reimbursement kya hai Class I city mein?",
     ["1200","class i","m3h1, m3, m2"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for M1/E2/E1 in Class I?",
     ["1000","class i","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Boarding Limits"),
    ("E1 grade ke liye Class I mein food limit kya hai?",
     ["1000","class i","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for BMH3-H6 in Class II?",
     ["1300","class ii","bmh3, h4, h5, h6"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for M3H1/M3/M2 in Class II?",
     ["1000","class ii","m3h1, m3, m2"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for M1/E2/E1 in Class II?",
     ["800","class ii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for BMH3-H6 in Class III?",
     ["1000","class iii","bmh3, h4, h5, h6"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for M3H1/M3/M2 in Class III?",
     ["800","class iii","m3h1, m3, m2"],
     DTP, 7, "Boarding Limits"),
    ("What is the boarding limit for M1/E2/E1 in Class III?",
     ["600","class iii","m1, mt, e2, get, e1, ot"],
     DTP, 7, "Boarding Limits"),
    ("BMH7 and above ka boarding limit kya hai?",
     ["at actuals","bmh7 and above"],
     DTP, 7, "Boarding Limits"),

    # --- City classification ---
    ("Which cities are classified as Class I under the Domestic Travel Policy?",
     ["delhi","mumbai","bangalore","class 1"],
     DTP, 7, "City Classification"),
    ("Is Ahmedabad a Class I or Class II city?",
     ["ahmedabad","class 2"],
     DTP, 7, "City Classification"),
    ("Pune kaunse class mein aata hai Domestic Travel Policy mein?",
     ["pune","class 1"],
     DTP, 7, "City Classification"),
    ("Is Jaipur classified as Class 2 or Class 3?",
     ["jaipur","class 2"],
     DTP, 7, "City Classification"),
    ("Which class does Surat fall under?",
     ["surat","class 2"],
     DTP, 7, "City Classification"),
    ("Bengaluru kaunsi category mein hai travel policy mein?",
     ["bangalore","class 1"],
     DTP, 7, "City Classification"),
    ("What is Class 3 in the city classification?",
     ["class 3","all other cities"],
     DTP, 7, "City Classification"),
    ("Is Hyderabad a Class 1 city for travel purposes?",
     ["hyderabad","class 1"],
     DTP, 7, "City Classification"),
    ("Is Kolkata a Class 1 city?",
     ["kolkata","class 1"],
     DTP, 7, "City Classification"),
    ("Lucknow kaunse travel class mein aata hai?",
     ["lucknow","class 2"],
     DTP, 7, "City Classification"),
    ("Is Vadodara a Class 2 city?",
     ["vadodara","class 2"],
     DTP, 7, "City Classification"),
    ("Is Chennai classified as Class 1 for travel?",
     ["chennai","class 1"],
     DTP, 7, "City Classification"),

    # --- Mode of travel ---
    ("What class of train can BMH9 grade travel by?",
     ["bmh9","1st ac"],
     DTP, 7, "Mode of Travel"),
    ("Can M3 grade employees travel by air?",
     ["m3h1, m3, m2","economy"],
     DTP, 7, "Mode of Travel"),
    ("M1 grade employee train mein kaunsi class mein travel kar sakta hai?",
     ["m1, e2, e1, ot","3rd ac"],
     DTP, 7, "Mode of Travel"),
    ("What is the air travel entitlement for BMH7 and BMH8?",
     ["bmh7,h8","economy / premium economy"],
     DTP, 7, "Mode of Travel"),
    ("BMH9 grade ke liye kaunsi air class allowed hai?",
     ["bmh9","premium economy / business"],
     DTP, 7, "Mode of Travel"),
    ("What is the train travel class for E1 and E2 grade employees?",
     ["m1, e2, e1, ot","3rd ac"],
     DTP, 7, "Mode of Travel"),
    ("Can E1 grade employees fly?",
     ["m1, e2, e1, ot","not applicable"],
     DTP, 7, "Mode of Travel"),
    ("What is the air entitlement for M3-H1 grade?",
     ["m3h1, m3, m2","economy"],
     DTP, 7, "Mode of Travel"),
    ("BM-H3 to H6 ke liye train class kya hai?",
     ["bm-h3 – h6","1st ac"],
     DTP, 7, "Mode of Travel"),

    # --- Cab entitlements ---
    ("What is the cab entitlement for BMH7 and above?",
     ["bm-h7 and above","actuals"],
     DTP, 8, "Cab Entitlements"),
    ("M3H1 grade ke liye cab booking kya allowed hai?",
     ["m3h1, m3, m2","ola / uber / blusmart"],
     DTP, 8, "Cab Entitlements"),
    ("What cab options are available for M1/E2/E1/OT grade?",
     ["m1, mt, e2, get, e1, ot","bus, metro, local transportation"],
     DTP, 8, "Cab Entitlements"),
    ("BMH3-H6 ke liye konsa cab service allowed hai?",
     ["bmh3, h4, h5, h6","ola / uber / blusmart"],
     DTP, 8, "Cab Entitlements"),
    ("When should full-day cab be booked?",
     ["three or more locations","full-day cab"],
     DTP, 5, "Cab Entitlements"),

    # --- Procedures ---
    ("How many days in advance must air tickets be booked?",
     ["7 days in advance","mandatory"],
     DTP, 3, "Booking Procedure"),
    ("Air ticket booking ke liye kitne din pehle karna chahiye?",
     ["7 days in advance"],
     DTP, 3, "Booking Procedure"),
    ("Through which portal should air and hotel bookings be made?",
     ["mybiz","self booking tool"],
     DTP, 3, "Booking Procedure"),
    ("Travel booking ke liye kaunsa tool use karna hai?",
     ["mybiz","self booking tool"],
     DTP, 3, "Booking Procedure"),
    ("Who must approve air and hotel bookings?",
     ["approval from the reporting manager","bm grade"],
     DTP, 3, "Booking Procedure"),
    ("For overnight rail travel, what mode must be used?",
     ["overnight rail","train as the mode of transportation"],
     DTP, 3, "Booking Procedure"),
    ("When is an employee not eligible for hotel accommodation on a business trip?",
     ["same-day return","not eligible to avail the accommodation"],
     DTP, 4, "Booking Procedure"),
    ("Can employees make hotel bookings outside myBiz?",
     ["bookings made through any other channels will not be entertained"],
     DTP, 3, "Booking Procedure"),

    # --- Settlement ---
    ("Within how many days must travel expenses be settled?",
     ["15 days","travel settlement"],
     DTP, 5, "Settlement"),
    ("Travel expense claim submit karne ki deadline kya hai?",
     ["15 days"],
     DTP, 5, "Settlement"),
    ("What happens if expense settlement is not done within 15 days?",
     ["auto-settlement on the 16th day","no reimbursement"],
     DTP, 5, "Settlement"),
    ("Where should travel expenses be settled?",
     ["self booking tool","one arvind"],
     DTP, 5, "Settlement"),
    ("Who approves expenses above defined entitlements?",
     ["bm-h3 level or above","special sanction"],
     DTP, 6, "Settlement"),

    # --- Women employees ---
    ("What special hotel entitlement do women employees get?",
     ["women employees","hotel limits of the next higher grade"],
     DTP, 4, "Women Travel"),
    ("Mahila employees ke liye kya koi special travel policy hai?",
     ["women employees","avoidance of night travel"],
     DTP, 4, "Women Travel"),
    ("Are women employees advised to avoid night travel?",
     ["women employees are advised to avoid night travel"],
     DTP, 4, "Women Travel"),
    ("Which grades of women employees get higher hotel limits?",
     ["women employees up to the m3-h1 grades"],
     DTP, 4, "Women Travel"),

    # --- Flat rate ---
    ("What is the flat rate lodging allowance for own arrangement?",
     ["flat rate","30% of the entitlement"],
     DTP, 5, "Flat Rate"),
    ("BM-H7 and above ke liye flat rate kya hai?",
     ["bm-h7 and above","rs. 6,000 per day"],
     DTP, 5, "Flat Rate"),
    ("Flat rate lodging ke liye BM-H7+ employees ko kitna milta hai?",
     ["rs. 6,000 per day","flat rate"],
     DTP, 5, "Flat Rate"),

    # --- Laundry / other ---
    ("When are laundry expenses reimbursed?",
     ["laundry","duration of travel exceeds three days"],
     DTP, 5, "Other Expenses"),
    ("Are web check-in fees reimbursable?",
     ["web check-ins","will not be reimbursed"],
     DTP, 5, "Other Expenses"),

    # --- Non-reimbursable ---
    ("Is alcohol reimbursable under the travel policy?",
     ["alcohol, cigarettes"],
     DTP, 8, "Non-Reimbursable"),
    ("Kya spouse ka travel reimburse hoga?",
     ["spouse/dependent travel"],
     DTP, 8, "Non-Reimbursable"),
    ("Are lounge fees reimbursable?",
     ["fees for vip clubs/lounge"],
     DTP, 8, "Non-Reimbursable"),
    ("Is seat upgrade cost reimbursable?",
     ["upgradation of seat/class at an added cost"],
     DTP, 8, "Non-Reimbursable"),
    ("Are personal gifts reimbursable under travel policy?",
     ["personal gifts"],
     DTP, 8, "Non-Reimbursable"),

    # --- Scope ---
    ("What is the minimum distance for domestic travel policy to apply?",
     ["exceeding a distance of 300 km"],
     DTP, 2, "Scope"),
    ("Does the domestic travel policy cover relocations?",
     ["relocations, deputations, and projects are not included"],
     DTP, 2, "Scope"),
    ("Kya visitors ka travel bhi is policy mein covered hai?",
     ["consultants, visitors, and candidates"],
     DTP, 2, "Scope"),
    ("Does the policy cover consultants?",
     ["consultants, visitors, and candidates"],
     DTP, 2, "Scope"),
    ("What is the booking platform used for corporate travel at Arvind?",
     ["mybiz","make my trip"],
     DTP, 2, "Scope"),

    # --- Attendance ---
    ("How should employees regularize attendance during official travel?",
     ["outdoor travel","darwinbox"],
     DTP, 6, "Attendance"),
    ("Agar official trip ke dauran leave li jaaye to kya hoga?",
     ["avails leave during an official trip","not be eligible for any allowance"],
     DTP, 6, "Attendance"),

    # --- Delayed flight ---
    ("What can an employee do if their flight is delayed by more than 3 hours?",
     ["delayed by more than 3 hours","cancel or modify the booking"],
     DTP, 4, "Travel Procedures"),
    ("No-show charges kiske account mein jati hain?",
     ["no-show","responsibility of the employee"],
     DTP, 4, "Travel Procedures"),

    # --- Guest house ---
    ("Where is the Ahmedabad guest house located?",
     ["surdhara circle","ahmedabad"],
     DTP, 9, "Guest House"),
    ("What is the email contact for Bengaluru guest house 2?",
     ["garvesh.j@arvindexports.com","bengaluru"],
     DTP, 9, "Guest House"),
    ("Ahmedabad guest house 2 ka address kya hai?",
     ["centre point","cg road","ahmedabad"],
     DTP, 9, "Guest House"),
    ("Kya company guest house mein rehne par conveyance reimburse hota hai?",
     ["company guest house facility","conveyance expenses at actuals"],
     DTP, 3, "Guest House"),

    # --- Senior officials ---
    ("Should senior officials travelling to same destination take the same flight?",
     ["senior officials","separate flights"],
     DTP, 3, "Travel Procedures"),
]

# =============================================================
# LOCAL CONVEYANCE POLICY (~80 cases)
# =============================================================
LCP = "Local Conveyance Policy"

raw_tests += [
    # --- Rates ---
    ("What is the per km rate for four wheeler under local conveyance policy?",
     ["four wheeler","rs. 10.00 / - per km"],
     LCP, 1, "Conveyance Rates"),
    ("Four wheeler ke liye per km rate kya hai local conveyance mein?",
     ["four wheeler","rs. 10.00 / - per km"],
     LCP, 1, "Conveyance Rates"),
    ("What is the per km rate for two wheeler conveyance?",
     ["two wheeler","rs. 5.00 per km"],
     LCP, 1, "Conveyance Rates"),
    ("Two wheeler par local conveyance ka rate kya hai?",
     ["two wheeler","rs. 5.00 per km"],
     LCP, 1, "Conveyance Rates"),
    ("For taxi usage, how is local conveyance reimbursed?",
     ["taxi","reimbursement will be done on actuals"],
     LCP, 1, "Conveyance Rates"),
    ("Kya taxi ka bill submit karna zaroori hai local conveyance claim ke liye?",
     ["bills / vouchers would have to be submitted"],
     LCP, 1, "Conveyance Rates"),

    # --- Scope / applicability ---
    ("Who is eligible for local conveyance at Arvind?",
     ["all management / staff cadre","arvind corporate"],
     LCP, 1, "Scope"),
    ("Local Conveyance Policy kab se effective hai?",
     ["01.07.2022"],
     LCP, 1, "Scope"),
    ("What is the effective date of the Local Conveyance Policy?",
     ["01.07.2022"],
     LCP, 1, "Scope"),
    ("What is the policy number for Local Conveyance Policy?",
     ["eop_lcp|002|010722"],
     LCP, 1, "Scope"),

    # --- Company car employees ---
    ("Agar employee ke paas company car hai toh local conveyance kab milega?",
     ["outside the respective city/town municipal corporation"],
     LCP, 1, "Eligibility"),
    ("Employees with company cars — are they reimbursed for Santej travel?",
     ["santej","not be reimbursed for local conveyance"],
     LCP, 1, "Eligibility"),
    ("Can company car employees claim conveyance for Gomtipur travel?",
     ["santej/raipur/gomtipur","not be reimbursed"],
     LCP, 1, "Eligibility"),
    ("Ahmedabad ke employees ko Raipur ke liye conveyance milegi?",
     ["santej/raipur/gomtipur","not be reimbursed"],
     LCP, 1, "Eligibility"),

    # --- Non-company-car employees ---
    ("Employees without company car — when are they eligible for local conveyance?",
     ["do not own a company car","within the city"],
     LCP, 1, "Eligibility"),
    ("Jo employee company car nahi use karta usse conveyance kab milti hai?",
     ["do not own a company car","within the city"],
     LCP, 1, "Eligibility"),

    # --- Claim process ---
    ("How do employees submit local conveyance claims?",
     ["orapps – esms – entry – conveyance expense"],
     LCP, 1, "Claim Process"),
    ("Local conveyance claim kaise submit karte hain?",
     ["orapps – esms – entry – conveyance expense"],
     LCP, 1, "Claim Process"),
    ("What should be deducted when calculating conveyance kms?",
     ["kms from residence to official location of posting"],
     LCP, 1, "Claim Process"),
    ("Residence to office ke kms ko conveyance mein count kiya jata hai?",
     ["kms from residence to official location of posting","shall get deducted"],
     LCP, 1, "Claim Process"),

    # --- Approval ---
    ("Who approves local conveyance expenses?",
     ["bm grade employees of respective departments"],
     LCP, 1, "Approval"),
    ("Local conveyance approve karne ka authority kiska hai?",
     ["bm grade employees of respective departments"],
     LCP, 1, "Approval"),
    ("Is local conveyance approval grade-specific?",
     ["applicable across all grades","bm grade"],
     LCP, 1, "Approval"),

    # --- Multiple travellers ---
    ("Agar ek hi gaadi mein kai log travel kare toh conveyance kaun claim kare?",
     ["individual who has actually incurred the cost"],
     LCP, 1, "Claim Process"),
    ("If two employees travel together in one car, who claims conveyance?",
     ["individual who has actually incurred the cost"],
     LCP, 1, "Claim Process"),

    # --- Fraud ---
    ("What happens if an employee forges conveyance documents?",
     ["forge the documents","strict disciplinary action"],
     LCP, 2, "Compliance"),
    ("False claim karne par kya action hoga?",
     ["false claim","strict disciplinary action"],
     LCP, 2, "Compliance"),

    # --- Examples / reimbursement table ---
    ("If an employee travels from office to another location and back to residence, how is conveyance calculated?",
     ["total kms travelled","deducting the kms from residence"],
     LCP, 2, "Conveyance Calculation"),
    ("If employee travels only from home to office and back, is conveyance reimbursed?",
     ["no reimbursement","official location of posting","residence"],
     LCP, 2, "Conveyance Calculation"),
    ("When is zero reimbursement given for local conveyance?",
     ["no reimbursement"],
     LCP, 2, "Conveyance Calculation"),

    # --- Geographic limits ---
    ("Are local conveyance rates applicable across all India?",
     ["applicable across india"],
     LCP, 1, "Scope"),
    ("Local conveyance ke limits India mein sab jagah same hain?",
     ["applicable across india"],
     LCP, 1, "Scope"),
    ("Are the conveyance limits grade-specific?",
     ["applicable across all grades"],
     LCP, 2, "Scope"),
    ("Kya local conveyance ke limits different grades ke liye alag hain?",
     ["applicable across all grades"],
     LCP, 2, "Scope"),

    # --- Contact ---
    ("Local conveyance policy ke baare mein query ke liye kise contact kare?",
     ["contact your business hr"],
     LCP, 2, "Contact"),
    ("Who should I contact for queries about local conveyance policy?",
     ["contact your business hr"],
     LCP, 2, "Contact"),
    ("Can the local conveyance policy be changed without notice?",
     ["management reserves all right to append, modify, withdraw"],
     LCP, 2, "Policy Amendment"),
]

# =============================================================
# POSH POLICY (~130 cases)
# =============================================================
POSH = "POSH Policy (Prevention of Sexual Harassment)"

raw_tests += [
    # --- Scope ---
    ("Who does the POSH policy apply to?",
     ["regular, temporary, ad hoc or daily wage basis","co-worker, contract worker, probationer, trainee"],
     POSH, 1, "Scope"),
    ("Kya contractors POSH policy ke under aate hain?",
     ["contractor","regular, temporary, ad hoc or daily wage basis"],
     POSH, 1, "Scope"),
    ("Does the POSH policy cover foreign nationals?",
     ["foreign nationals","third parties"],
     POSH, 1, "Scope"),
    ("Kya POSH policy same-sex harassment par bhi apply hoti hai?",
     ["same-sex harassment","prohibits"],
     POSH, 6, "Scope"),
    ("Does POSH policy apply outside the workplace?",
     ["extended workplace","office parties"],
     POSH, 2, "Scope"),
    ("What qualifies as extended workplace under POSH policy?",
     ["office parties","off sites/ client meetings","training sessions"],
     POSH, 2, "Scope"),
    ("Is POSH coverage gender neutral?",
     ["gender neutral","all genders, i.e. men, women and transgender"],
     POSH, 6, "Scope"),

    # --- Complaint filing ---
    ("Within what time period must a POSH complaint be filed?",
     ["3 (three) months from the date of incident"],
     POSH, 6, "Complaint Filing"),
    ("POSH complaint kitne time mein file karni chahiye?",
     ["3 (three) months from the date of incident"],
     POSH, 6, "Complaint Filing"),
    ("Can the 3-month complaint window be extended?",
     ["extended for further 3 (three) months","aic"],
     POSH, 6, "Complaint Filing"),
    ("How can a POSH complaint be filed?",
     ["written complaint or via e-mail","aic"],
     POSH, 6, "Complaint Filing"),
    ("Kya anonymous POSH complaint entertained hoti hai?",
     ["anonymous complaints will not be entertained by the aic"],
     POSH, 6, "Complaint Filing"),
    ("Can a POSH complaint be filed on behalf of an aggrieved woman?",
     ["relative or friend","co-worker","written consent"],
     POSH, 6, "Complaint Filing"),
    ("POSH complaint mein kitni copies submit karni hoti hain?",
     ["six copies of the complaint"],
     POSH, 6, "Complaint Filing"),
    ("How many days does the respondent have to reply to a POSH complaint?",
     ["10 (ten) working days"],
     POSH, 6, "Complaint Filing"),
    ("AIC respondent ko complaint ki copy kitne din mein bhejti hai?",
     ["7 (seven) days"],
     POSH, 6, "Complaint Filing"),

    # --- AIC constitution ---
    ("Who is the Presiding Officer of AIC?",
     ["senior level woman employee","presiding officer"],
     POSH, 3, "AIC Constitution"),
    ("AIC mein kitne members hote hain minimum?",
     ["minimum quorum shall consist","3 members of the aic"],
     POSH, 4, "AIC Constitution"),
    ("What is the minimum women representation in AIC quorum?",
     ["50% women representation in aic"],
     POSH, 4, "AIC Constitution"),
    ("Who is the external member of AIC?",
     ["external member","non-governmental organizations"],
     POSH, 3, "AIC Constitution"),
    ("How much is the external member of AIC paid?",
     ["rs. 250 per day","external member"],
     POSH, 4, "AIC Constitution"),
    ("AIC ke external member ko conveyance kaun deta hai?",
     ["conveyance allowances as per arvind's policy","external member"],
     POSH, 4, "AIC Constitution"),
    ("AIC member ka tenure kitna hota hai?",
     ["three years or completion of the age of 58"],
     POSH, 5, "AIC Constitution"),
    ("Can an AIC member be re-nominated after their term?",
     ["re-nominated/re-elected for one additional term"],
     POSH, 5, "AIC Constitution"),
    ("How quickly must a vacancy in AIC be filled?",
     ["15 days from such event"],
     POSH, 4, "AIC Constitution"),

    # --- Inquiry process ---
    ("How many days does AIC have to complete its inquiry?",
     ["90 (ninety) days to complete its inquiry"],
     POSH, 6, "Inquiry Process"),
    ("POSH inquiry complete hone ke kitne din mein report deni hoti hai?",
     ["10 (ten) days from the date of completion"],
     POSH, 7, "Inquiry Process"),
    ("How many days does management have to act on AIC recommendations?",
     ["60 (sixty) days","aic recommendation"],
     POSH, 7, "Inquiry Process"),
    ("Agar complainant 3 consecutive hearings mein absent rahe toh kya hoga?",
     ["15 (fifteen) days","3 (three) consecutive proceedings"],
     POSH, 6, "Inquiry Process"),
    ("Can lawyers represent parties at AIC proceedings?",
     ["parties shall not be allowed to bring in any legal practitioner"],
     POSH, 6, "Inquiry Process"),

    # --- Interim relief ---
    ("What interim actions can AIC take for aggrieved woman during inquiry?",
     ["transfer the aggrieved woman","grant leave","suspend the re"],
     POSH, 7, "Interim Relief"),
    ("Inquiry ke dauran aggrieved woman ko kitne mahine ki leave mil sakti hai?",
     ["3 (three) months","grant leave to the aggrieved woman"],
     POSH, 7, "Interim Relief"),
    ("Can AIC transfer an employee during inquiry?",
     ["transfer the aggrieved woman and/or the re to an alternate work location"],
     POSH, 7, "Interim Relief"),

    # --- Disciplinary action ---
    ("What disciplinary actions can be recommended against the respondent?",
     ["written warning","withholding of promotion","terminating the re from service"],
     POSH, 8, "Disciplinary Action"),
    ("POSH mein doshi paaye gaye employee ke liye kya action ho sakti hai?",
     ["written warning","terminating the re from service"],
     POSH, 8, "Disciplinary Action"),
    ("Can monetary compensation be awarded in POSH cases?",
     ["monetary compensation"],
     POSH, 8, "Disciplinary Action"),

    # --- Whistleblowing channels ---
    ("What is the POSH helpline number?",
     ["18002008301"],
     POSH, 5, "Contact"),
    ("POSH complaint ke liye helpline number kya hai?",
     ["18002008301"],
     POSH, 5, "Contact"),
    ("What email can be used to report sexual harassment?",
     ["arvind@ethicshelpline.in"],
     POSH, 5, "Contact"),
    ("Is there a web portal for filing POSH complaints?",
     ["www.in.kpmg.com/ethicshelpline/arvind/"],
     POSH, 5, "Contact"),

    # --- Confidentiality ---
    ("Who maintains confidentiality in POSH cases?",
     ["identity and addresses of the ct, re and witnesses","strict confidentiality"],
     POSH, 9, "Confidentiality"),
    ("Kya POSH case ki details media ko share ki ja sakti hain?",
     ["not be published, communicated or made known to the public, press and media"],
     POSH, 9, "Confidentiality"),

    # --- Protection ---
    ("Is the complainant protected from retaliation in POSH cases?",
     ["protected from any form of retaliation","good faith"],
     POSH, 9, "Protection"),
    ("What examples of retaliation are mentioned in POSH policy?",
     ["unsubstantiated negative performance evaluation","continued harassment"],
     POSH, 9, "Protection"),

    # --- Malicious complaint ---
    ("What happens if a POSH complaint is found to be malicious?",
     ["malicious intent","recommend action"],
     POSH, 9, "Malicious Complaint"),
    ("Mere inability to prove a complaint — kya yeh malicious complaint hai?",
     ["mere inability to substantiate a complaint","not attract action"],
     POSH, 9, "Malicious Complaint"),

    # --- Appeals ---
    ("Where can POSH case parties appeal if dissatisfied?",
     ["appeal to the court or tribunal","appellate authority"],
     POSH, 8, "Appeals"),

    # --- Consensual relations ---
    ("What is Arvind's stance on romantic relationships at workplace?",
     ["discourages any kind of romantic or sexual relationships amongst employees"],
     POSH, 7, "Consensual Relations"),
    ("Agar supervisor aur subordinate mein relationship ho toh kya karna chahiye?",
     ["notify to hr of such a relation","reporting chain is altered"],
     POSH, 7, "Consensual Relations"),

    # --- AIC contacts (Presiding Officer) ---
    ("Who is the Presiding Officer of AIC for Arvind Corporate?",
     ["shalom christian","presiding officer"],
     POSH, 10, "AIC Contacts"),
    ("Wovens Fabric ka AIC Presiding Officer kaun hai?",
     ["shalom christian","presiding officer"],
     POSH, 11, "AIC Contacts"),
    ("What is the email for Hiren Bhatt (Corporate Contact Officer)?",
     ["hiren.bhatt@arvind.in"],
     POSH, 15, "AIC Contacts"),
    ("What is the mobile number of the Corporate contact officer for POSH?",
     ["9824449080","hiren bhatt"],
     POSH, 15, "AIC Contacts"),
    ("Who is the POSH contact officer for Denim Fabric?",
     ["hemaxee bhatt","denim fabric"],
     POSH, 15, "AIC Contacts"),
    ("Wovens Fabric Santej mein AIC member kaun hain?",
     ["saikat sengupta","maulin shah"],
     POSH, 11, "AIC Contacts"),
    ("Kya Denim Garmenting Bangalore mein alag AIC hai?",
     ["denim garmenting","bangalore"],
     POSH, 12, "AIC Contacts"),
    ("Who is external member for Arvind Corporate AIC?",
     ["trupti jain","external member"],
     POSH, 10, "AIC Contacts"),

    # --- Annual report ---
    ("Does AIC submit annual report to management?",
     ["annual report to the management","district officer"],
     POSH, 8, "AIC Reporting"),
    ("Whistleblower committee kitni baar report submit karta hai under POSH?",
     ["quarterly to the audit committee"],
     POSH, 4, "AIC Reporting"),

    # --- Police ---
    ("Can an employee approach police in a sexual harassment case?",
     ["not barred from referring the matter","law enforcement agencies"],
     POSH, 7, "Police"),
    ("Kya Arvind POSH case mein police complaint mein help karega?",
     ["arvind will support to file the same with the police"],
     POSH, 7, "Police"),

    # --- Definition ---
    ("What does AIC stand for in POSH policy?",
     ["arvind internal complaint committee"],
     POSH, 2, "Definitions"),
    ("POSH policy mein CT ka matlab kya hai?",
     ["ct - complainant","lodged a complaint of sexual harassment"],
     POSH, 2, "Definitions"),
    ("What is the definition of sexual harassment under POSH?",
     ["physical contact and sexual advances","demand or request for sexual favours"],
     POSH, 2, "Definitions"),
]

# =============================================================
# WHISTLEBLOWER POLICY (~60 cases)
# =============================================================
WB = "Whistleblower Policy"

raw_tests += [
    # --- Purpose ---
    ("What is the purpose of the Whistleblower Policy?",
     ["reporting instances of unethical/improper conduct","good faith"],
     WB, 2, "Purpose"),
    ("Whistleblower Policy ka main objective kya hai?",
     ["reporting instances of unethical/improper conduct"],
     WB, 2, "Purpose"),

    # --- Applicability ---
    ("Who does the Whistleblower Policy apply to?",
     ["directors","employees","business associates"],
     WB, 3, "Applicability"),
    ("Kya business associates bhi whistleblower ban sakte hain?",
     ["business associates"],
     WB, 3, "Applicability"),

    # --- What to report ---
    ("What types of issues can be reported under Whistleblower Policy?",
     ["bribery and corruption","misappropriation/theft/embezzlement"],
     WB, 3, "Reportable Issues"),
    ("Can workplace harassment be reported via Whistleblower Policy?",
     ["workplace harassment"],
     WB, 3, "Reportable Issues"),
    ("Kya financial fraud ko whistleblower policy ke through report kar sakte hain?",
     ["fraudulent financial accounting, auditing and reporting"],
     WB, 3, "Reportable Issues"),
    ("Is false invoicing reportable under whistleblower policy?",
     ["false invoicing"],
     WB, 3, "Reportable Issues"),
    ("Can procurement fraud be reported under this policy?",
     ["procurement and tendering fraud"],
     WB, 3, "Reportable Issues"),
    ("Is corporate espionage reportable?",
     ["corporate espionage and information disclosure"],
     WB, 3, "Reportable Issues"),
    ("Can health and safety issues be reported via whistleblower?",
     ["health, safety, environment and security related"],
     WB, 3, "Reportable Issues"),

    # --- How to report ---
    ("How can a whistleblower report a concern?",
     ["web portal","toll free number","18002008301"],
     WB, 3, "Reporting Channels"),
    ("Whistleblower complaint kaise file karte hain?",
     ["www.in.kpmg.com/ethicshelpline/arvind","18002008301"],
     WB, 3, "Reporting Channels"),
    ("What is the toll-free number for the ethics helpline?",
     ["18002008301"],
     WB, 3, "Reporting Channels"),
    ("What is the email for reporting whistleblower concerns?",
     ["arvind@ethicshelpline.in"],
     WB, 3, "Reporting Channels"),
    ("Is there a web portal for whistleblower reporting?",
     ["www.in.kpmg.com/ethicshelpline/arvind"],
     WB, 3, "Reporting Channels"),

    # --- Role of whistleblower ---
    ("What is the whistleblower's role limited to?",
     ["reporting reliable information","not expected to act as investigators"],
     WB, 3, "Role of Whistleblower"),
    ("Can a whistleblower conduct their own investigation?",
     ["should not act on their own in conducting any investigative activities"],
     WB, 3, "Role of Whistleblower"),

    # --- Investigation ---
    ("Who investigates whistleblower complaints?",
     ["whistleblower committee"],
     WB, 3, "Investigation"),
    ("How often does the whistleblower committee report to audit committee?",
     ["quarterly to the audit committee"],
     WB, 4, "Investigation"),
    ("When is the whistleblower notified about their complaint?",
     ["four weeks after the submission","follow-up on their concern"],
     WB, 4, "Investigation"),
    ("Kya vague complaints bhi investigate ki jaati hain?",
     ["investigation of vague or unspecified alleged wrongdoings","may not be undertaken"],
     WB, 4, "Investigation"),
    ("Can an independent agency be appointed for whistleblower investigations?",
     ["independent agency to investigate the matter"],
     WB, 4, "Investigation"),

    # --- Confidentiality ---
    ("Is whistleblower identity kept confidential?",
     ["identity of the whistle blower shall be kept confidential"],
     WB, 4, "Confidentiality"),
    ("Kya whistleblower case ki details social gatherings mein discuss ho sakti hain?",
     ["not discuss the matter in any informal/social gatherings"],
     WB, 4, "Confidentiality"),

    # --- Non-victimization ---
    ("Is a whistleblower protected from retaliation?",
     ["no adverse personnel action, victimization, retaliation"],
     WB, 5, "Protection"),
    ("Agar whistleblower ko victimize kiya jaye toh kya kare?",
     ["lodge a written complaint to the chairman of the committee"],
     WB, 5, "Protection"),
    ("What action can be taken if someone retaliates against a whistleblower?",
     ["termination of his/her services","legal action"],
     WB, 5, "Protection"),
    ("Do witnesses in whistleblower investigations also get protection?",
     ["stakeholders who offered evidence or made written statements","protection"],
     WB, 5, "Protection"),

    # --- False complaints ---
    ("What happens if someone makes a false whistleblower complaint?",
     ["frivolous, misleading or false complaints","will not be protected by this policy"],
     WB, 5, "False Complaints"),
    ("Is the whistleblower policy a grievance redressal mechanism?",
     ["this policy is not a grievance redressal","no complaints of such nature"],
     WB, 5, "False Complaints"),

    # --- Definitions ---
    ("What is the definition of a whistleblower?",
     ["any individual who reports confirmed or suspected unethical practices"],
     WB, 2, "Definitions"),
    ("What is a Protected Disclosure?",
     ["communication in relation to an unethical practice made in good faith"],
     WB, 2, "Definitions"),
    ("What is 'Unethical Behaviour' as defined in the policy?",
     ["does not confirm to the approved standard of social and professional behaviour"],
     WB, 2, "Definitions"),

    # --- Amendment ---
    ("Who can amend the Whistleblower Policy?",
     ["board/audit committee/ whistleblower committee"],
     WB, 5, "Policy Amendment"),
]

# =============================================================
# GRIEVANCE MECHANISM POLICY 2025 (~55 cases)
# =============================================================
GMP = "Grievance Mechanism Policy 2025"

raw_tests += [
    # --- Objective ---
    ("What is the objective of the Grievance Mechanism Policy 2025?",
     ["fair, transparent, and time-bound manner","employee grievances"],
     GMP, 2, "Objective"),
    ("Grievance policy ka main purpose kya hai?",
     ["fair, transparent, and time-bound manner"],
     GMP, 2, "Objective"),

    # --- Applicability ---
    ("Who does the Grievance Mechanism Policy 2025 apply to?",
     ["full-time, part-time, contract workers, trainees, and consultants"],
     GMP, 2, "Applicability"),
    ("Kya contractors bhi grievance file kar sakte hain?",
     ["contract workers","all employees of arvind ltd."],
     GMP, 2, "Applicability"),

    # --- Definition of grievance ---
    ("What is the definition of a grievance?",
     ["concern, complaint, or dissatisfaction","work environment"],
     GMP, 2, "Definition"),
    ("What issues can be raised as a grievance?",
     ["discrimination, harassment, or unfair treatment","interpersonal conflict"],
     GMP, 2, "Definition"),
    ("Is workload issue a valid grievance?",
     ["workload or role clarity issues"],
     GMP, 2, "Definition"),
    ("Safety violation ki shikayat grievance policy ke through ho sakti hai?",
     ["violation of health, safety, or ethical standards"],
     GMP, 2, "Definition"),

    # --- Channels ---
    ("How can an employee raise a grievance?",
     ["immediate hr representative","line manager or supervisor"],
     GMP, 2, "Reporting Channels"),
    ("Grievance anonymous tarike se bhi file kar sakte hain?",
     ["anonymous complaints will be considered"],
     GMP, 3, "Reporting Channels"),
    ("What is the web portal for anonymous grievance submission?",
     ["www.in.kpmg.com/ethicshelpline/arvind"],
     GMP, 3, "Reporting Channels"),
    ("What toll-free number can be used for grievance?",
     ["1800 200 8301"],
     GMP, 3, "Reporting Channels"),
    ("What is the email for grievance helpline?",
     ["arvind@ethicshelpline.in"],
     GMP, 3, "Reporting Channels"),
    ("Can a grievance be raised verbally?",
     ["verbally or in writing"],
     GMP, 3, "Reporting Channels"),

    # --- Process / timelines ---
    ("Within how many working days is a grievance acknowledged?",
     ["2 working days of receipt"],
     GMP, 3, "Process"),
    ("Grievance ki acknowledgment kitne din mein milti hai?",
     ["2 working days of receipt"],
     GMP, 3, "Process"),
    ("Within how many working days should a grievance investigation be completed?",
     ["10 working days"],
     GMP, 3, "Process"),
    ("When is the grievance outcome communicated to the complainant?",
     ["15 working days of receipt"],
     GMP, 3, "Process"),
    ("Resolution ke baad complainant ko kitne din mein inform kiya jayega?",
     ["15 working days of receipt"],
     GMP, 3, "Process"),
    ("What is the grievance appeal process?",
     ["escalate the grievance to the next level","bu head, ethics officer, group hr"],
     GMP, 3, "Process"),

    # --- Principles ---
    ("What are the key principles of the Grievance Policy?",
     ["fairness","timeliness","confidentiality","non-retaliation"],
     GMP, 2, "Principles"),
    ("Is confidentiality maintained in grievance handling?",
     ["confidential to the extent possible"],
     GMP, 2, "Principles"),
    ("Kya grievance file karne par retaliation se protection milti hai?",
     ["employees raising concerns in good faith will be protected from retaliation"],
     GMP, 2, "Principles"),

    # --- Roles ---
    ("Who leads the grievance resolution process?",
     ["hr department (buhr)","grievance resolution process"],
     GMP, 4, "Roles"),
    ("Managers ka kya role hai grievance mein?",
     ["first level of response and support","escalate grievances"],
     GMP, 4, "Roles"),
    ("Who handles escalated or complex grievances?",
     ["ethics helpline / group ethics officer"],
     GMP, 4, "Roles"),

    # --- Record keeping ---
    ("How are grievance records maintained?",
     ["documented and retained by the hr team"],
     GMP, 3, "Record Keeping"),
    ("Grievance trend analysis kab hoti hai?",
     ["periodically review grievance trends"],
     GMP, 3, "Record Keeping"),

    # --- False complaints ---
    ("What happens if a false grievance is filed?",
     ["deliberately submitted a false or malicious complaint","disciplinary action"],
     GMP, 3, "False Complaints"),

    # --- Review ---
    ("How often is the Grievance Mechanism Policy reviewed?",
     ["reviewed every two years"],
     GMP, 4, "Policy Review"),
    ("Grievance policy kab review hogi?",
     ["reviewed every two years"],
     GMP, 4, "Policy Review"),
    ("What is the policy number of the Grievance Mechanism Policy 2025?",
     ["arv|com_grm|001|260725"],
     GMP, 1, "Policy Info"),
    ("Grievance policy kab effective hui?",
     ["effective from: 26.07.2025"],
     GMP, 1, "Policy Info"),
]

# =============================================================
# GENDER POLICY 2025 (~50 cases)
# =============================================================
GPol = "Gender Policy 2025"

raw_tests += [
    # --- Objective ---
    ("What is the objective of the Gender Policy 2025?",
     ["gender equality and inclusion","fair treatment in all aspects of employment"],
     GPol, 2, "Objective"),
    ("Gender policy ka main purpose kya hai?",
     ["gender equality and inclusion"],
     GPol, 2, "Objective"),

    # --- Applicability ---
    ("Who does the Gender Policy 2025 apply to?",
     ["full-time, part-time, contract staff, interns, consultants"],
     GPol, 2, "Applicability"),
    ("Kya third-party partners bhi gender policy ke under aate hain?",
     ["third-party partners engaged in business operations"],
     GPol, 2, "Applicability"),

    # --- Definitions ---
    ("What is the definition of Gender Identity under Gender Policy?",
     ["person's internal sense of being male, female"],
     GPol, 2, "Definitions"),
    ("What does 'inclusion' mean under Gender Policy?",
     ["all gender identities feel welcome, respected, supported"],
     GPol, 2, "Definitions"),

    # --- Principles ---
    ("What are the key principles of Gender Policy 2025?",
     ["equal access and opportunity","non-tolerance of gender-based harassment"],
     GPol, 2, "Principles"),
    ("Is gender-based harassment tolerated at Arvind?",
     ["not tolerated","disciplinary action","gender-based harassment"],
     GPol, 2, "Principles"),
    ("What does Arvind's Gender Policy say about work-life integration?",
     ["maternity, paternity, parental leave","flexible and empathetic approach"],
     GPol, 2, "Principles"),

    # --- Practices ---
    ("How does Arvind ensure gender-inclusive hiring?",
     ["merit, with attention to balanced gender representation"],
     GPol, 3, "Practices"),
    ("What does gender-inclusive performance evaluation mean?",
     ["performance evaluation is fair, transparent, and free of gender bias"],
     GPol, 3, "Practices"),
    ("Kya language and communication bhi gender-inclusive honi chahiye?",
     ["language and communication","inclusive and non-discriminatory"],
     GPol, 3, "Practices"),

    # --- Initiatives ---
    ("What gender diversity initiatives does Arvind undertake?",
     ["gender sensitization and unconscious bias training"],
     GPol, 3, "Initiatives"),
    ("Does Arvind celebrate Women's Day?",
     ["international women's day or pride month"],
     GPol, 3, "Initiatives"),
    ("How does Arvind monitor gender representation?",
     ["monitor gender ratios across hiring, attrition, and promotions"],
     GPol, 3, "Initiatives"),

    # --- Complaint process ---
    ("How can gender discrimination be reported?",
     ["hr department (buhr)","ethics helpline"],
     GPol, 3, "Complaint Process"),
    ("Gender policy ke complaint process mein kitne levels hain?",
     ["first level","second level","third level","fourth level"],
     GPol, 3, "Complaint Process"),
    ("What is the first level for gender-related complaints?",
     ["first level: hr department (buhr)"],
     GPol, 3, "Complaint Process"),
    ("Gender complaint ke liye web portal kya hai?",
     ["www.in.kpmg.com/ethicshelpline/arvind"],
     GPol, 3, "Complaint Process"),
    ("What toll-free number to use for gender discrimination complaint?",
     ["1800 200 8301"],
     GPol, 3, "Complaint Process"),
    ("Is retaliation allowed against gender complaint filers?",
     ["retaliation against individuals who raise concerns in good faith is strictly prohibited"],
     GPol, 3, "Complaint Process"),

    # --- Review ---
    ("How often is the Gender Policy reviewed?",
     ["reviewed every two years"],
     GPol, 3, "Policy Review"),
    ("Gender policy kab effective hui?",
     ["effective from: 26.07.2025"],
     GPol, 1, "Policy Info"),
    ("What is the policy number of Gender Policy 2025?",
     ["arv|com_genp|001|260725"],
     GPol, 1, "Policy Info"),

    # --- Cross-reference ---
    ("Which policies does Gender Policy refer to for addressing concerns?",
     ["whistleblower and posh policies"],
     GPol, 3, "Cross-Reference"),
]

# =============================================================
# TALENT MOBILITY POLICY (~60 cases)
# =============================================================
TMP = "Talent Mobility Policy"

raw_tests += [
    # --- Strategic intent ---
    ("What is the strategic intent of the Talent Mobility Policy?",
     ["future-ready, cross-functional workforce","institutionalize mobility"],
     TMP, 3, "Strategic Intent"),
    ("Talent mobility policy ka main goal kya hai?",
     ["institutionalize mobility as a mandate"],
     TMP, 3, "Strategic Intent"),
    ("Why does Arvind need a Talent Mobility Policy?",
     ["skill stagnation","lack of growth / career mobility","exit interviews"],
     TMP, 2, "Strategic Intent"),

    # --- Policy anchors ---
    ("After how many years in a role should rotation be triggered?",
     ["3 years = trigger for rotation"],
     TMP, 4, "Policy Rules"),
    ("3 saal baad kya hota hai talent mobility policy mein?",
     ["3 years = trigger for rotation"],
     TMP, 4, "Policy Rules"),
    ("What is the rule for positions up to M2 grade?",
     ["all positions upto m2, should be closed via ijp"],
     TMP, 4, "Policy Rules"),
    ("Who can approve exceptions to mandatory job rotation?",
     ["chro/ceo can approve exceptions"],
     TMP, 4, "Policy Rules"),
    ("Can a manager block an employee's internal mobility?",
     ["managers cannot block mobility"],
     TMP, 4, "Policy Rules"),
    ("1st rotation kahan hoti hai talent mobility mein?",
     ["1st rotation – within the city"],
     TMP, 4, "Policy Rules"),
    ("Where does the 2nd rotation take an employee?",
     ["2nd rotation – across different business / different location"],
     TMP, 4, "Policy Rules"),

    # --- Rotation framework ---
    ("What is Track A in the rotation framework?",
     ["track a","sensitive roles in risk prone functions"],
     TMP, 5, "Rotation Framework"),
    ("Talent mobility mein Track B kya hai?",
     ["track b","future leaders broadened via structured mobility"],
     TMP, 5, "Rotation Framework"),
    ("What is Track C in talent mobility?",
     ["track c","voluntary moves, employee-driven career paths"],
     TMP, 5, "Rotation Framework"),

    # --- Relocation benefits ---
    ("What financial benefits are provided on job rotation/relocation?",
     ["mobility adjustment benefit","settling-in assistance"],
     TMP, 6, "Relocation Benefits"),
    ("MAB kitne months ke liye diya jata hai?",
     ["12 months, time-bound"],
     TMP, 6, "Relocation Benefits"),
    ("What happens to MAB after 1 year?",
     ["merged with ctc on completion of 1 year"],
     TMP, 6, "Relocation Benefits"),
    ("What is Settling-In Assistance used for?",
     ["one-time lump sum for household setup, admissions"],
     TMP, 6, "Relocation Benefits"),
    ("SIA kab applicable hoti hai?",
     ["applicable only if one is shifting house"],
     TMP, 7, "Relocation Benefits"),

    # --- Financial tables (MAB) ---
    ("What is the monthly MAB for E1 grade (Tier 1)?",
     ["e1","32,583"],
     TMP, 7, "Financial Entitlements"),
    ("E1 grade ke liye Tier 1 MAB kitna hai?",
     ["e1","32,583"],
     TMP, 7, "Financial Entitlements"),
    ("What is the monthly MAB for E2 grade (Tier 1)?",
     ["e2","45,750"],
     TMP, 7, "Financial Entitlements"),
    ("What is the monthly MAB for M1 grade (Tier 1)?",
     ["m1","71,000"],
     TMP, 7, "Financial Entitlements"),
    ("M2 grade ke liye Tier 1 monthly MAB kya hai?",
     ["m2","1,08,333"],
     TMP, 7, "Financial Entitlements"),
    ("What is the monthly MAB for M3 grade (Tier 1)?",
     ["m3","1,58,333"],
     TMP, 7, "Financial Entitlements"),
    ("What is the monthly MAB for M3H1 grade (Tier 1)?",
     ["m3h1","2,16,667"],
     TMP, 7, "Financial Entitlements"),
    ("What is the annual fixed cost for M1 grade?",
     ["m1","8,52,000"],
     TMP, 7, "Financial Entitlements"),
    ("What is the annual fixed cost for M3 grade?",
     ["m3","19,00,000"],
     TMP, 7, "Financial Entitlements"),

    # --- SIA amounts ---
    ("What is the Settling-In Assistance for E1 grade?",
     ["e1","10,000"],
     TMP, 7, "Financial Entitlements"),
    ("E2 grade ke liye SIA kitni hai?",
     ["e2","10,000"],
     TMP, 7, "Financial Entitlements"),
    ("What is the SIA for M1 grade?",
     ["m1","15,000"],
     TMP, 7, "Financial Entitlements"),
    ("M2 grade ke liye settling-in assistance kitni milti hai?",
     ["m2","20,000"],
     TMP, 7, "Financial Entitlements"),
    ("What is the SIA for M3 grade employees?",
     ["m3","30,000"],
     TMP, 7, "Financial Entitlements"),
    ("M3H1 grade ke liye SIA kya hai?",
     ["m3h1","45,000"],
     TMP, 7, "Financial Entitlements"),

    # --- Governance ---
    ("Who executes talent mobility at business level?",
     ["business hr","closest to business leaders & employees"],
     TMP, 8, "Governance"),
    ("Corporate HR ka kya role hai talent mobility mein?",
     ["corporate hr","escalation support"],
     TMP, 8, "Governance"),
    ("On which system is talent mobility workflow managed?",
     ["darwinbox"],
     TMP, 8, "Governance"),

    # --- Universal applicability ---
    ("Does talent mobility apply to all functions?",
     ["universal applicability: across all businesses & functions"],
     TMP, 4, "Applicability"),
    ("Talent mobility policy sab businesses pe lagoo hoti hai?",
     ["universal applicability: across all businesses & functions"],
     TMP, 4, "Applicability"),
]

# =============================================================
# JOINING POLICY (~65 cases)
# =============================================================
JP = "Joining Policy"

raw_tests += [
    # --- Objective ---
    ("What is the objective of the Joining Policy?",
     ["regulate the norms around the joining process","relocation from one city to another"],
     JP, 1, "Objective"),
    ("Joining policy ka kya objective hai?",
     ["regulate the norms around the joining process"],
     JP, 1, "Objective"),

    # --- Applicability ---
    ("Who is covered under the Joining Policy?",
     ["all management / staff cadre employees","arvind limited and/or its subsidiaries"],
     JP, 1, "Applicability"),
    ("Kya subsidiary company ke employees bhi joining policy ke under aate hain?",
     ["arvind limited and/or its subsidiaries"],
     JP, 1, "Applicability"),
    ("What is the effective date of the Joining Policy?",
     ["21.09.2023"],
     JP, 1, "Policy Info"),

    # --- Pre-joining visit ---
    ("What is a pre-joining visit?",
     ["pre joining visit to location of posting for fixing up accommodation, school admission"],
     JP, 1, "Pre-Joining Visit"),
    ("Pre-joining visit kitne din ke liye hoti hai?",
     ["maximum period of 3 days"],
     JP, 1, "Pre-Joining Visit"),
    ("Who is eligible for pre-joining visit?",
     ["employee concerned and his/her spouse","pre joining visit"],
     JP, 1, "Pre-Joining Visit"),
    ("Are children allowed in pre-joining visit?",
     ["children allowed in case of school admission"],
     JP, 1, "Pre-Joining Visit"),
    ("Pre-joining visit mein kya expenses reimburse hote hain?",
     ["to and fro travelling expenses for self and family"],
     JP, 1, "Pre-Joining Visit"),

    # --- Post-joining visit ---
    ("What is a post-joining visit / joining leave?",
     ["3 days leave to visit the location from where he/she is relocating"],
     JP, 1, "Post-Joining Visit"),
    ("Agar pre-joining visit nahi li toh kya alternative hai?",
     ["eligible for 3 days leave","post joining visit"],
     JP, 1, "Post-Joining Visit"),
    ("Post-joining visit mein kya reimburse hota hai?",
     ["reimbursed one time travelling expenses for self and family"],
     JP, 1, "Post-Joining Visit"),

    # --- Packers & movers ---
    ("What is the packers & movers limit for distance less than 700 km?",
     ["less than 700 kms","rs. 50 per km"],
     JP, 1, "Packers & Movers"),
    ("700 km se kam distance ke liye household goods transport limit kya hai?",
     ["less than 700 kms","rs. 50 per km"],
     JP, 1, "Packers & Movers"),
    ("What is the limit for packers & movers when distance exceeds 700 km?",
     ["more than 700 kms","rs. 60 per km"],
     JP, 1, "Packers & Movers"),
    ("700 km se zyada distance par moving charges ki limit kya hai?",
     ["more than 700 kms","rs. 60 per km"],
     JP, 1, "Packers & Movers"),
    ("What does the transportation of household goods cost include?",
     ["packing, unpacking, loading,   unloading,   services   tax   & insurance"],
     JP, 1, "Packers & Movers"),
    ("On what basis are packers & movers expenses paid?",
     ["against actuals for all employees on relocation"],
     JP, 1, "Packers & Movers"),

    # --- Car transportation ---
    ("What is the rate for transporting car via packers & movers?",
     ["rs.","10.0 per km"],
     JP, 1, "Car Transportation"),
    ("Agar car khud drive karke aao toh mileage kitna milega?",
     ["rs. 10.0 per km + toll charges on actuals"],
     JP, 1, "Car Transportation"),
    ("Only how many cars are covered under joining policy?",
     ["only one per employee shall be allowed"],
     JP, 1, "Car Transportation"),

    # --- Driver wages ---
    ("What are the driver wages for an 8-hour trip?",
     ["for 8 hours trip : rs. 600/-"],
     JP, 1, "Driver Wages"),
    ("After 8 hours of driving, what is the extra wage rate?",
     ["after 8 hours: rs. 50/- per hour"],
     JP, 1, "Driver Wages"),
    ("Driver ka 8 ghante ke liye kya rate hai joining relocation mein?",
     ["for 8 hours trip : rs. 600/-"],
     JP, 1, "Driver Wages"),
    ("Driver ke khaane ka maximum limit kya hai?",
     ["food: max limit to be rs. 200/- per meal"],
     JP, 1, "Driver Wages"),

    # --- Accommodation ---
    ("What accommodation is provided for BM and above on joining?",
     ["bm & above","hotel","eligibility based on domestic travel policy"],
     JP, 1, "Accommodation"),
    ("M2/M3/M3H1 grade ke liye joining accommodation kya hai?",
     ["m2 / m3 / m3h1","service apartment/ guest house"],
     JP, 1, "Accommodation"),
    ("E1/E2/M1 ko service apartment se katnaa kb lagta hai?",
     ["more than 15 days","charged from the employee"],
     JP, 1, "Accommodation"),

    # --- Travel on joining ---
    ("What is the travel mode for BM and above on joining?",
     ["bm & above","air travel economy / train (2nd / 1st ac)"],
     JP, 1, "Travel Mode"),
    ("E1/E2/M1 joining mein kab air travel kar sakte hain?",
     ["allowed to travel by air","air-time travel more than 1.5 hours"],
     JP, 1, "Travel Mode"),
    ("M2/M3/M3H1 grade joining mein kaunsa travel mode use kar sakte hain?",
     ["m2 / m3 / m3h1","air travel economy / train (2nd / 1st ac)"],
     JP, 1, "Travel Mode"),

    # --- Cab on joining ---
    ("How many days can BM and above avail cab/radio taxi on joining?",
     ["bm & above","15"],
     JP, 1, "Joining Cab"),
    ("M2/M3/M3H1 grade ke liye joining cab kitne din available hai?",
     ["m2 / m3 / m3h1","7"],
     JP, 1, "Joining Cab"),
    ("E1/E2/M1 ke liye joining mein cab ki availability kya hai?",
     ["e1 / e2 / m1","7"],
     JP, 1, "Joining Cab"),

    # --- Brokerage ---
    ("What is covered under brokerage reimbursement?",
     ["one month rent","brokerage receipt"],
     JP, 1, "Brokerage"),
    ("Brokerage reimbursement kitni baar milta hai?",
     ["paid only once during   the   employee's employment with arvind"],
     JP, 1, "Brokerage"),
    ("Brokerage benefit ke liye maximum time limit kya hai?",
     ["maximum for 1 year from the date of the joining"],
     JP, 1, "Brokerage"),

    # --- House deposit ---
    ("How is house deposit recovered?",
     ["10 equal monthly instalments (interest free)"],
     JP, 1, "House Deposit"),
    ("House deposit interest-free hai ya nahi?",
     ["interest free"],
     JP, 1, "House Deposit"),
    ("House deposit kaise recover kiya jata hai?",
     ["10 equal monthly instalments"],
     JP, 1, "House Deposit"),

    # --- Reimbursement / clawback ---
    ("What happens if an employee quits within 1 year of joining?",
     ["recovered in his/her f&f settlement","quits within 1 year of joining"],
     JP, 1, "Clawback"),
    ("Joining bonus kab wapas dena padta hai?",
     ["quits within 1 year","recovered in his/her f&f settlement"],
     JP, 1, "Clawback"),
    ("Joining expenses claim karne ki deadline kya hai?",
     ["expenses can be claimed within one year from date of joining"],
     JP, 1, "Claim Deadline"),
    ("Reimbursement ke liye invoice kiske naam par honi chahiye?",
     ["invoices bearing the employee's name"],
     JP, 1, "Reimbursement"),
    ("Who sanctions expenses above approved limits in joining policy?",
     ["special sanction from the ceo for businesses"],
     JP, 1, "Approvals"),
    ("Flight tickets ke liye joining mein kisko contact karna chahiye?",
     ["flight tickets shall be booked by arvind travel desk only"],
     JP, 1, "Travel Mode"),
    ("Kya joining ke time koi special exception CEO approve kar sakta hai?",
     ["approved by the ceo / chro"],
     JP, 1, "Approvals"),

    # --- Family definition ---
    ("What is the definition of 'Family' under the Joining Policy?",
     ["spouse, children and dependent parents"],
     JP, 1, "Definitions"),
    ("Joining policy mein 'family' ki definition kya hai?",
     ["spouse, children and dependent parents"],
     JP, 1, "Definitions"),
]

print(f"Total raw tests: {len(raw_tests)}")

# ─────────────────────────────────────────────
# 2.  Verify all keyFacts against corpus
# ─────────────────────────────────────────────
passed = []
failed = []
for item in raw_tests:
    query, facts, source, page, cat = item
    bad_facts = [f for f in facts if f.lower() not in corpus_full[source]]
    if bad_facts:
        failed.append((query, bad_facts, source, facts))
    else:
        passed.append(item)

print(f"\nVerification: {len(passed)} passed, {len(failed)} failed")
if failed:
    print("\nFailed items:")
    for q, bad, src, all_f in failed[:40]:
        print(f"  FAIL [{src}]: {q[:60]}")
        for b in bad:
            print(f"       bad fact: '{b}'")

