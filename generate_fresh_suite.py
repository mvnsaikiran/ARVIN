"""
Generate a deployment-grade fresh test suite from verified policy facts.
Every keyFact is a verbatim substring found in the policy text after normalisation.
"""

import json

CASES = []

def tc(id_, query, key_facts, source, page, category):
    CASES.append({
        "id": id_,
        "query": query,
        "keyFacts": key_facts,
        "source": source,
        "page": page,
        "category": category,
    })

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL CONVEYANCE POLICY
SRC_LC = "Local Conveyance Policy"

tc("FTC001","What is the reimbursement rate for four-wheeler personal vehicle travel?",
   ["Rs. 10.00 / - per km"],SRC_LC,2,"Conveyance Rates")
tc("FTC002","Per km rate for two-wheeler local conveyance?",
   ["two wheeler @ Rs. 5.00 per km"],SRC_LC,2,"Conveyance Rates")
tc("FTC003","My car travel rate for official work?",
   ["four wheeler @ Rs. 10.00 / - per km"],SRC_LC,2,"Conveyance Rates")
tc("FTC004","Rate per km if I use my bike for official travel?",
   ["two wheeler @ Rs. 5.00 per km"],SRC_LC,2,"Conveyance Rates")
tc("FTC005","Is local conveyance policy applicable across all grades?",
   ["applicable across all grades"],SRC_LC,2,"Conveyance Applicability")
tc("FTC006","Is conveyance policy applicable across India?",
   ["applicable across India"],SRC_LC,2,"Conveyance Applicability")
tc("FTC007","Who approves local conveyance claims?",
   ["approved only by BM grade employees"],SRC_LC,2,"Conveyance Approval")
tc("FTC008","How do I claim local conveyance in the system?",
   ["Orapps"],SRC_LC,2,"Conveyance Claim")
tc("FTC009","What is the reimbursement if I take a taxi for official work?",
   ["reimbursement will be done on actuals"],SRC_LC,2,"Conveyance Taxi")
tc("FTC010","If two employees share a vehicle, who claims conveyance?",
   ["individual who has actually incurred the cost"],SRC_LC,2,"Conveyance Sharing")
tc("FTC011","When does an employee with a company car get local conveyance?",
   ["outside the respective City/Town Municipal Corporation"],SRC_LC,1,"Conveyance Applicability")
tc("FTC012","Can Ahmedabad employees claim conveyance to Santej?",
   ["not be reimbursed for local conveyance"],SRC_LC,1,"Conveyance Applicability")
tc("FTC013","When is local conveyance allowed?",
   ["conveyance undertaken for the purpose of official work"],SRC_LC,1,"Conveyance Applicability")
tc("FTC014","What is the effective date of local conveyance policy?",
   ["01.07.2022"],SRC_LC,1,"Conveyance Applicability")
tc("FTC015","What happens if I submit a false conveyance claim?",
   ["strict disciplinary action shall be taken"],SRC_LC,2,"Conveyance Compliance")

# ─────────────────────────────────────────────────────────────────────────────
# DOMESTIC TRAVEL POLICY
SRC_DT = "Domestic Travel Policy"

# Mode of Travel
tc("FTC020","What is the train travel class for BMH9 grade?",
   ["1st AC"],SRC_DT,7,"Mode of Travel")
tc("FTC021","What air travel class is BMH9 grade entitled to?",
   ["Premium Economy / Business"],SRC_DT,7,"Mode of Travel")
tc("FTC022","Train class for BMH7 and H8 grade employees?",
   ["1st AC"],SRC_DT,7,"Mode of Travel")
tc("FTC023","Air travel entitlement for BMH7 and H8?",
   ["Economy / Premium Economy"],SRC_DT,7,"Mode of Travel")
tc("FTC024","What train class for BM-H3 to H6 grade?",
   ["1st AC"],SRC_DT,7,"Mode of Travel")
tc("FTC025","Train entitlement for M3H1, M3, M2 grades?",
   ["2nd AC"],SRC_DT,7,"Mode of Travel")
tc("FTC026","Air travel class for M3H1, M3, M2 employees?",
   ["Economy"],SRC_DT,7,"Mode of Travel")
tc("FTC027","What class of train can an E1 grade employee travel in?",
   ["3rd AC/Chair Car"],SRC_DT,7,"Mode of Travel")
tc("FTC028","Train class for M1 grade employees?",
   ["3rd AC/Chair Car"],SRC_DT,7,"Mode of Travel")
tc("FTC029","What train class do E2 grade employees get?",
   ["3rd AC/Chair Car"],SRC_DT,7,"Mode of Travel")
tc("FTC030","Air travel entitlement for OT grade?",
   ["Not Applicable"],SRC_DT,7,"Mode of Travel")

# Lodging
tc("FTC040","What is the hotel limit for BMH7 and above in Class 1 city?",
   ["At Actual"],SRC_DT,7,"Lodging Limits")
tc("FTC041","Lodging limit for BMH3-H6 in a Class 1 city?",
   ["8000"],SRC_DT,7,"Lodging Limits")
tc("FTC042","Hotel limit for BMH3-H6 in Class 2 city?",
   ["6000"],SRC_DT,7,"Lodging Limits")
tc("FTC043","Lodging entitlement for BMH3-H6 in Class 3 city?",
   ["5000"],SRC_DT,7,"Lodging Limits")
tc("FTC044","What is the hotel limit for M3H1 in Class 1 city?",
   ["6000"],SRC_DT,7,"Lodging Limits")
tc("FTC045","M3/M2 lodging limit for Class 2 city?",
   ["5000"],SRC_DT,7,"Lodging Limits")
tc("FTC046","Hotel limit for M3H1/M3/M2 in Class 3?",
   ["4000"],SRC_DT,7,"Lodging Limits")
tc("FTC047","What is the lodging limit for M1/E2/E1 in Class 1 city?",
   ["3400"],SRC_DT,7,"Lodging Limits")
tc("FTC048","Hotel limit for E1 grade employee staying in a Class 2 city?",
   ["2300"],SRC_DT,7,"Lodging Limits")
tc("FTC049","Lodging limit for E1/E2 in Class 3 city?",
   ["1700"],SRC_DT,7,"Lodging Limits")
tc("FTC050","Can a BMH7 grade employee claim lodging on actuals?",
   ["At Actual"],SRC_DT,7,"Lodging Limits")
tc("FTC051","What hotel limit for OT grade in Mumbai?",
   ["3400"],SRC_DT,7,"Lodging Limits")
tc("FTC052","Flat rate for lodging if BM-H7 and above arranges own stay?",
   ["Rs. 6,000 per day"],SRC_DT,5,"Lodging Limits")
tc("FTC053","What is the flat rate lodging percentage for own arrangement?",
   ["30% of the entitlement"],SRC_DT,5,"Lodging Limits")

# Boarding
tc("FTC060","What is the boarding limit for BMH3-H6 in Class 1 city?",
   ["1500"],SRC_DT,7,"Boarding Limits")
tc("FTC061","Boarding entitlement for BMH3-H6 in Class 2 city?",
   ["1300"],SRC_DT,7,"Boarding Limits")
tc("FTC062","Boarding limit for BMH3-H6 in Class 3 city?",
   ["1000"],SRC_DT,7,"Boarding Limits")
tc("FTC063","What is the boarding limit for M3H1/M3/M2 in Class 1?",
   ["1200"],SRC_DT,7,"Boarding Limits")
tc("FTC064","Boarding entitlement for M2 grade in Class 2 city?",
   ["1000"],SRC_DT,7,"Boarding Limits")
tc("FTC065","Boarding limit for M1/M2/M3 in Class 3 city?",
   ["800"],SRC_DT,7,"Boarding Limits")
tc("FTC066","What boarding amount is allowed for E1 in Class 1 city?",
   ["1000"],SRC_DT,7,"Boarding Limits")
tc("FTC067","Food allowance for E2/M1 in Class 2 city?",
   ["800"],SRC_DT,7,"Boarding Limits")
tc("FTC068","Boarding limit for OT grade in Class 3 city?",
   ["600"],SRC_DT,7,"Boarding Limits")
tc("FTC069","Is boarding entitlement inclusive of taxes?",
   ["inclusive of applicable taxes"],SRC_DT,4,"Boarding Limits")

# City Classification
tc("FTC080","Is Mumbai a Class 1 city?",
   ["Mumbai"],SRC_DT,7,"City Classification")
tc("FTC081","Which cities are in Class 1?",
   ["Delhi, NCR, Mumbai, Bangalore, Chennai, Hyderabad, Kolkata, Pune"],SRC_DT,7,"City Classification")
tc("FTC082","Is Bangalore a Class 1 or Class 2 city?",
   ["Bangalore"],SRC_DT,7,"City Classification")
tc("FTC083","What class is Ahmedabad?",
   ["Ahmedabad"],SRC_DT,7,"City Classification")
tc("FTC084","What city class is Surat?",
   ["Surat"],SRC_DT,7,"City Classification")
tc("FTC085","Is Jaipur a Class 2 city?",
   ["Jaipur"],SRC_DT,7,"City Classification")
tc("FTC086","What class is Hyderabad?",
   ["Hyderabad"],SRC_DT,7,"City Classification")
tc("FTC087","Lucknow city classification?",
   ["Lucknow"],SRC_DT,7,"City Classification")
tc("FTC088","Is Pune Class 1 or Class 2?",
   ["Pune"],SRC_DT,7,"City Classification")
tc("FTC089","What category does Delhi fall under?",
   ["Delhi"],SRC_DT,7,"City Classification")
tc("FTC090","Is Kolkata a Class 1 city?",
   ["Kolkata"],SRC_DT,7,"City Classification")
tc("FTC091","What class is Vadodara?",
   ["Vadodara"],SRC_DT,7,"City Classification")
tc("FTC092","Is Chennai Class 1?",
   ["Chennai"],SRC_DT,7,"City Classification")
tc("FTC093","What class are all other cities not listed?",
   ["All Other Cities"],SRC_DT,7,"City Classification")

# Cab entitlements
tc("FTC100","What cab is BM-H7 and above entitled to?",
   ["Actuals"],SRC_DT,8,"Cab Entitlements")
tc("FTC101","Cab entitlement for BMH3-H6 grade employees?",
   ["Ola / Uber / BluSmart"],SRC_DT,8,"Cab Entitlements")
tc("FTC102","What cabs can M3H1/M3/M2 use?",
   ["Ola / Uber / BluSmart"],SRC_DT,8,"Cab Entitlements")
tc("FTC103","Cab options for M1/E2/E1/OT grade?",
   ["Ola / Uber / BluSmart, Bus, Metro, Local Transportation"],SRC_DT,8,"Cab Entitlements")
tc("FTC104","Can OT grade use metro for conveyance?",
   ["Bus, Metro, Local Transportation"],SRC_DT,8,"Cab Entitlements")
tc("FTC105","When should full-day cabs be booked?",
   ["travel to three or more locations on a given day"],SRC_DT,5,"Cab Entitlements")

# Non-reimbursable
tc("FTC110","Is web check-in reimbursable?",
   ["Web Check-in amount"],SRC_DT,8,"Non-Reimbursable")
tc("FTC111","Are VIP lounge fees reimbursed?",
   ["Fees for VIP Clubs/Lounge"],SRC_DT,8,"Non-Reimbursable")
tc("FTC112","Is alcohol reimbursable during travel?",
   ["Alcohol, cigarettes"],SRC_DT,8,"Non-Reimbursable")
tc("FTC113","Are personal entertainment expenses reimbursable?",
   ["Amount incurred on personal entertainment/recreation"],SRC_DT,8,"Non-Reimbursable")
tc("FTC114","Is spouse travel reimbursable?",
   ["Spouse/dependent travel"],SRC_DT,8,"Non-Reimbursable")
tc("FTC115","Are personal gifts reimbursable?",
   ["Personal Gifts"],SRC_DT,8,"Non-Reimbursable")
tc("FTC116","Is seat upgradation cost reimbursed?",
   ["Upgradation of seat/class at an added cost"],SRC_DT,8,"Non-Reimbursable")
tc("FTC117","Is mini-bar usage reimbursable?",
   ["Usage of Mini-Bar"],SRC_DT,8,"Non-Reimbursable")
tc("FTC118","Is airport parking reimbursable after 24 hours?",
   ["Airport parking tariff"],SRC_DT,8,"Non-Reimbursable")
tc("FTC119","Is health club expense reimbursed during travel?",
   ["Health club services"],SRC_DT,8,"Non-Reimbursable")

# Travel procedures
tc("FTC130","How far in advance must air tickets be booked?",
   ["at least 7 days in advance"],SRC_DT,3,"Travel Procedures")
tc("FTC131","What tool should be used for air and hotel booking?",
   ["myBiz"],SRC_DT,3,"Travel Procedures")
tc("FTC132","How many days to settle travel expenses?",
   ["within 15 days of the trip"],SRC_DT,5,"Settlement")
tc("FTC133","What happens if travel expenses not settled in 15 days?",
   ["auto-settlement on the 16th day"],SRC_DT,5,"Settlement")
tc("FTC134","When can laundry be reimbursed?",
   ["duration of travel exceeds three days"],SRC_DT,5,"Settlement")
tc("FTC135","Is accommodation allowed on same-day return trips?",
   ["not eligible to avail the accommodation"],SRC_DT,4,"Travel Procedures")
tc("FTC136","What is scope of domestic travel policy in terms of distance?",
   ["domestic travel exceeding a distance of 300 km"],SRC_DT,2,"Travel Procedures")
tc("FTC137","When can a delayed flight booking be cancelled?",
   ["delayed by more than 3 hours"],SRC_DT,3,"Travel Procedures")
tc("FTC138","Who approves exceptions for flight booked outside travel desk for joining?",
   ["CEO / CHRO"],SRC_DT,3,"Travel Procedures")

# Women travel policy
tc("FTC145","What hotel grade are women employees entitled to?",
   ["hotel limits of the next higher grade"],SRC_DT,4,"Women Travel")
tc("FTC146","What accommodation type are women advised to avoid?",
   ["avoid staying in service apartments"],SRC_DT,4,"Women Travel")
tc("FTC147","Are women employees advised to avoid night travel?",
   ["Avoidance of Night Travel"],SRC_DT,4,"Women Travel")

# ─────────────────────────────────────────────────────────────────────────────
# GRIEVANCE MECHANISM POLICY
SRC_GR = "Grievance Mechanism Policy 2025"

tc("FTC160","How long to acknowledge a grievance?",
   ["2 working days"],SRC_GR,3,"Grievance Timelines")
tc("FTC161","How many days to complete grievance investigation?",
   ["10 working days"],SRC_GR,3,"Grievance Timelines")
tc("FTC162","When must grievance resolution be communicated?",
   ["15 working days"],SRC_GR,3,"Grievance Timelines")
tc("FTC163","What is the first level for raising grievance?",
   ["Immediate HR Representative"],SRC_GR,2,"Grievance Channels")
tc("FTC164","Can grievance be filed anonymously?",
   ["Anonymous complaints will be considered"],SRC_GR,3,"Grievance Channels")
tc("FTC165","What is the toll-free number for Ethics Helpline?",
   ["1800 200 8301"],SRC_GR,3,"Grievance Channels")
tc("FTC166","What is the Ethics Helpline email?",
   ["arvind@ethicshelpline.in"],SRC_GR,3,"Grievance Channels")
tc("FTC167","What is the grievance web portal?",
   ["www.in.kpmg.com/ethicshelpline/arvind"],SRC_GR,3,"Grievance Channels")
tc("FTC168","Can I raise a grievance verbally?",
   ["raised verbally or in writing"],SRC_GR,3,"Grievance Channels")
tc("FTC169","When is grievance policy reviewed?",
   ["every two years"],SRC_GR,4,"Grievance Policy")
tc("FTC170","Is retaliation allowed against grievance filers?",
   ["protected from retaliation"],SRC_GR,2,"Grievance Policy")
tc("FTC171","What is the effective date of grievance policy?",
   ["26.07.2025"],SRC_GR,1,"Grievance Policy")
tc("FTC172","Who leads grievance resolution process?",
   ["HR Department"],SRC_GR,4,"Grievance Policy")
tc("FTC173","What happens to false grievance complaints?",
   ["disciplinary action"],SRC_GR,3,"Grievance Policy")
tc("FTC174","Can I escalate if unsatisfied with grievance resolution?",
   ["escalate the grievance to the next level"],SRC_GR,3,"Grievance Channels")
tc("FTC175","What does BUHR stand for in grievance context?",
   ["Immediate HR Representative"],SRC_GR,2,"Grievance Channels")
tc("FTC176","Who is the second level of grievance redressal?",
   ["Line Manager or Supervisor"],SRC_GR,2,"Grievance Channels")
tc("FTC177","Who is third level for grievance escalation?",
   ["Head of Department"],SRC_GR,2,"Grievance Channels")
tc("FTC178","Is grievance policy applicable to contract workers?",
   ["contract workers"],SRC_GR,2,"Grievance Applicability")
tc("FTC179","Is grievance policy applicable to trainees?",
   ["trainees"],SRC_GR,2,"Grievance Applicability")

# ─────────────────────────────────────────────────────────────────────────────
# POSH POLICY
SRC_POSH = "POSH Policy (Prevention of Sexual Harassment)"

# Filing
tc("FTC200","How to file a POSH complaint?",
   ["lodge a written complaint"],SRC_POSH,5,"POSH Complaint Filing")
tc("FTC201","Can a POSH complaint be filed via email?",
   ["lodge her complaint in writing or via e- mail"],SRC_POSH,6,"POSH Complaint Filing")
tc("FTC202","Are anonymous POSH complaints entertained?",
   ["Anonymous complaints will not be entertained"],SRC_POSH,6,"POSH Complaint Filing")
tc("FTC203","Within what time must a POSH complaint be filed?",
   ["3 (three) months from the date of incident"],SRC_POSH,6,"POSH Timelines")
tc("FTC204","Can the 3-month filing deadline for POSH be extended?",
   ["extended for further 3 (three) months"],SRC_POSH,6,"POSH Timelines")
tc("FTC205","How many days does the respondent have to respond?",
   ["10 (ten) working days"],SRC_POSH,6,"POSH Timelines")
tc("FTC206","When must AIC provide its report to management?",
   ["within a period of 10 (ten) days"],SRC_POSH,7,"POSH Timelines")
tc("FTC207","How long does management have to act on AIC recommendation?",
   ["60 (sixty) days"],SRC_POSH,7,"POSH Timelines")
tc("FTC208","How many days for AIC to forward complaint to respondent?",
   ["7 (seven) days"],SRC_POSH,6,"POSH Timelines")

# AIC structure
tc("FTC210","Who is the Presiding Officer of AIC?",
   ["Senior level woman employee"],SRC_POSH,3,"POSH AIC Structure")
tc("FTC211","How many members does AIC have minimum?",
   ["2 members amongst employees"],SRC_POSH,3,"POSH AIC Structure")
tc("FTC212","What is the tenure of AIC members?",
   ["period of three years"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC213","Can AIC members be re-nominated after initial term?",
   ["re-nominated/re-elected for one additional term"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC214","What is the minimum quorum for AIC inquiry?",
   ["minimum of 3 members"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC215","What is the required women representation in AIC quorum?",
   ["50% women representation"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC216","How long to fill vacancy in AIC?",
   ["within 15 days"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC217","What is paid to external AIC member?",
   ["Rs. 250 per day"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC218","Is the AIC independent of management?",
   ["independent committee"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC219","What is the AIC term limit?",
   ["period of three years or completion of the age of 58 years"],SRC_POSH,4,"POSH AIC Structure")

# Interim action
tc("FTC225","What leave can AIC grant as interim action?",
   ["leave to the Aggrieved Woman up to a period of 3 (three) months"],SRC_POSH,7,"POSH Interim Action")
tc("FTC226","Is interim POSH leave in addition to regular leave?",
   ["in addition to the entitled leaves"],SRC_POSH,7,"POSH Interim Action")
tc("FTC227","Can respondent be suspended during inquiry?",
   ["suspend the RE for defined period"],SRC_POSH,7,"POSH Interim Action")

# Disciplinary action
tc("FTC230","What actions can be taken against proven harasser?",
   ["Written warning"],SRC_POSH,8,"POSH Disciplinary")
tc("FTC231","Can a harasser be terminated?",
   ["Terminating the RE from service"],SRC_POSH,8,"POSH Disciplinary")
tc("FTC232","Can promotion be withheld as POSH punishment?",
   ["Withholding of promotion"],SRC_POSH,8,"POSH Disciplinary")
tc("FTC233","Can pay rise be withheld as POSH penalty?",
   ["Withholding of pay rise or increments"],SRC_POSH,8,"POSH Disciplinary")

# Confidentiality and retaliation
tc("FTC240","Is retaliation against POSH complainant allowed?",
   ["protected from any form of retaliation"],SRC_POSH,9,"POSH Retaliation")
tc("FTC241","What is the policy on POSH confidentiality?",
   ["not be published, communicated or made known"],SRC_POSH,9,"POSH Confidentiality")
tc("FTC242","What happens if someone violates POSH confidentiality?",
   ["disciplinary action will be taken"],SRC_POSH,9,"POSH Confidentiality")
tc("FTC243","What happens in case of malicious POSH complaint?",
   ["allegation was malicious"],SRC_POSH,9,"POSH Malicious Complaint")

# Channels
tc("FTC250","POSH hotline number?",
   ["18002008301"],SRC_POSH,5,"POSH Channels")
tc("FTC251","POSH complaint email address?",
   ["arvind@ethicshelpline.in"],SRC_POSH,5,"POSH Channels")
tc("FTC252","What is the POSH complaint portal?",
   ["www.in.kpmg.com/ethicshelpline/arvind"],SRC_POSH,5,"POSH Channels")
tc("FTC253","Can a POSH complaint be filed through supervisor?",
   ["Supervisor / Reporting Manager"],SRC_POSH,5,"POSH Channels")

# Policy dates
tc("FTC258","What is the POSH policy effective date?",
   ["01.05.2025"],SRC_POSH,1,"POSH Policy Dates")
tc("FTC259","What is the POSH policy issue date?",
   ["31.03.2022"],SRC_POSH,1,"POSH Policy Dates")

# Scope
tc("FTC260","Who is covered under POSH policy?",
   ["All persons employed at Arvind"],SRC_POSH,1,"POSH Scope")
tc("FTC261","Are third parties covered by POSH?",
   ["Third parties and/or visitors"],SRC_POSH,1,"POSH Scope")
tc("FTC262","Does POSH cover incidents outside office?",
   ["outside the workplace"],SRC_POSH,1,"POSH Scope")
tc("FTC263","Are office parties covered under POSH?",
   ["Office parties"],SRC_POSH,2,"POSH Scope")
tc("FTC264","Is same-sex harassment covered under POSH?",
   ["prohibits same-sex harassment"],SRC_POSH,5,"POSH Scope")
tc("FTC265","Is POSH policy gender neutral?",
   ["gender neutral"],SRC_POSH,5,"POSH Scope")

# ─────────────────────────────────────────────────────────────────────────────
# WHISTLEBLOWER POLICY
SRC_WB = "Whistleblower Policy"

tc("FTC300","How can I report a whistleblower concern?",
   ["www.in.kpmg.com/ethicshelpline/arvind"],SRC_WB,3,"Whistleblower Channels")
tc("FTC301","What is the whistleblower toll-free number?",
   ["18002008301"],SRC_WB,3,"Whistleblower Channels")
tc("FTC302","Whistleblower email address?",
   ["arvind@ethicshelpline.in"],SRC_WB,3,"Whistleblower Channels")
tc("FTC303","Who is covered under whistleblower policy?",
   ["Directors"],SRC_WB,3,"Whistleblower Coverage")
tc("FTC304","Are business associates covered by whistleblower policy?",
   ["Business Associates"],SRC_WB,3,"Whistleblower Coverage")
tc("FTC305","Can I report bribery through whistleblower?",
   ["Bribery and corruption"],SRC_WB,3,"Whistleblower Scope")
tc("FTC306","Can I report theft of company assets?",
   ["Misappropriation/theft/embezzlement of company assets"],SRC_WB,3,"Whistleblower Scope")
tc("FTC307","Can I report false invoicing through whistleblower?",
   ["False invoicing"],SRC_WB,3,"Whistleblower Scope")
tc("FTC308","Can workplace harassment be reported as whistleblower?",
   ["Workplace harassment"],SRC_WB,3,"Whistleblower Scope")
tc("FTC309","Can I report workplace discrimination through whistleblower?",
   ["Discrimination and favouritism"],SRC_WB,3,"Whistleblower Scope")
tc("FTC310","When does whistleblower committee report to Audit Committee?",
   ["quarterly"],SRC_WB,4,"Whistleblower Investigation")
tc("FTC311","When can I get follow-up on my whistleblower concern?",
   ["four weeks after the submission"],SRC_WB,4,"Whistleblower Investigation")
tc("FTC312","Can an independent agency investigate whistleblower complaints?",
   ["appoint an independent agency"],SRC_WB,4,"Whistleblower Investigation")
tc("FTC313","Is retaliation allowed against whistleblowers?",
   ["no adverse personnel action, victimization, retaliation"],SRC_WB,5,"Whistleblower Protection")
tc("FTC314","What if I make a false whistleblower complaint?",
   ["will not be protected by this Policy"],SRC_WB,5,"Whistleblower Compliance")
tc("FTC315","Is my identity kept confidential as whistleblower?",
   ["identity of the whistle blower shall be kept confidential"],SRC_WB,4,"Whistleblower Confidentiality")
tc("FTC316","What can whistleblower report about corporate fraud?",
   ["Fraudulent financial accounting, auditing and reporting"],SRC_WB,3,"Whistleblower Scope")
tc("FTC317","Can I report procurement fraud through whistleblower?",
   ["Procurement and tendering fraud"],SRC_WB,3,"Whistleblower Scope")
tc("FTC318","Is health and safety covered under whistleblower reporting?",
   ["Health, safety, environment and security related"],SRC_WB,3,"Whistleblower Scope")

# ─────────────────────────────────────────────────────────────────────────────
# GENDER POLICY
SRC_GP = "Gender Policy 2025"

tc("FTC350","What is the issue date of gender policy?",
   ["25.07.2025"],SRC_GP,1,"Gender Policy Dates")
tc("FTC351","What is the effective date of gender policy?",
   ["26.07.2025"],SRC_GP,1,"Gender Policy Dates")
tc("FTC352","Who does gender policy apply to?",
   ["all employees of Arvind Ltd"],SRC_GP,2,"Gender Applicability")
tc("FTC353","Are interns covered under gender policy?",
   ["interns"],SRC_GP,2,"Gender Applicability")
tc("FTC354","Are contract staff covered under gender policy?",
   ["contract staff"],SRC_GP,2,"Gender Applicability")
tc("FTC355","What is the first level for gender grievance?",
   ["HR Department"],SRC_GP,3,"Gender Channels")
tc("FTC356","What is the second level for gender grievance?",
   ["Line Manager"],SRC_GP,3,"Gender Channels")
tc("FTC357","Is there a toll-free number for gender concerns?",
   ["1800 200 8301"],SRC_GP,3,"Gender Channels")
tc("FTC358","What is the gender policy review period?",
   ["every two years"],SRC_GP,3,"Gender Policy")
tc("FTC359","Is retaliation against gender concerns allowed?",
   ["retaliation against individuals who raise concerns in good faith is strictly prohibited"],SRC_GP,3,"Gender Policy")
tc("FTC360","What email to use for gender-related concerns?",
   ["arvind@ethicshelpline.in"],SRC_GP,3,"Gender Channels")
tc("FTC361","What is the gender policy web portal?",
   ["www.in.kpmg.com/ethicshelpline/arvind"],SRC_GP,3,"Gender Channels")

# ─────────────────────────────────────────────────────────────────────────────
# TALENT MOBILITY POLICY
SRC_TM = "Talent Mobility Policy"

# MAB
tc("FTC400","What is the monthly MAB for E1 grade?",
   ["32,583"],SRC_TM,7,"MAB")
tc("FTC401","What is the monthly MAB for E2 grade?",
   ["45,750"],SRC_TM,7,"MAB")
tc("FTC402","Monthly MAB for M1 grade?",
   ["71,000"],SRC_TM,7,"MAB")
tc("FTC403","What is M2 grade monthly MAB?",
   ["1,08,333"],SRC_TM,7,"MAB")
tc("FTC404","Monthly MAB for M3 grade?",
   ["1,58,333"],SRC_TM,7,"MAB")
tc("FTC405","What is the monthly MAB for M3H1 grade?",
   ["2,16,667"],SRC_TM,7,"MAB")
tc("FTC406","Annual MAB for E1 grade?",
   ["3,91,000"],SRC_TM,7,"MAB")
tc("FTC407","Annual MAB for E2 grade?",
   ["5,49,000"],SRC_TM,7,"MAB")
tc("FTC408","Annual MAB for M1 grade?",
   ["8,52,000"],SRC_TM,7,"MAB")
tc("FTC409","Annual MAB for M2?",
   ["13,00,000"],SRC_TM,7,"MAB")
tc("FTC410","Annual MAB for M3?",
   ["19,00,000"],SRC_TM,7,"MAB")
tc("FTC411","Annual MAB for M3H1?",
   ["26,00,000"],SRC_TM,7,"MAB")
tc("FTC412","How long is MAB paid?",
   ["12 months"],SRC_TM,6,"MAB")
tc("FTC413","When is MAB merged with CTC?",
   ["merged with CTC on completion of 1 year"],SRC_TM,6,"MAB")
tc("FTC414","What happens to MAB after 1 year?",
   ["merged in CTC on completion of 1 year"],SRC_TM,7,"MAB")

# SIA
tc("FTC420","What is the SIA for E1 grade?",
   ["10,000"],SRC_TM,7,"SIA")
tc("FTC421","SIA for E2 grade?",
   ["10,000"],SRC_TM,7,"SIA")
tc("FTC422","What is the SIA for M1 grade?",
   ["15,000"],SRC_TM,7,"SIA")
tc("FTC423","SIA for M2 grade?",
   ["20,000"],SRC_TM,7,"SIA")
tc("FTC424","What is the SIA for M3 grade?",
   ["30,000"],SRC_TM,7,"SIA")
tc("FTC425","SIA for M3H1 grade?",
   ["45,000"],SRC_TM,7,"SIA")
tc("FTC426","Is SIA a monthly or one-time payment?",
   ["One time"],SRC_TM,7,"SIA")
tc("FTC427","When is SIA applicable?",
   ["shifting house"],SRC_TM,7,"SIA")
tc("FTC428","Minimum relocation distance for SIA?",
   ["relocation >20 kms"],SRC_TM,7,"SIA")

# Rotation rules
tc("FTC440","What triggers job rotation in talent mobility policy?",
   ["3 years = trigger for rotation"],SRC_TM,4,"Rotation Rules")
tc("FTC441","Who can block talent mobility?",
   ["Managers cannot block mobility"],SRC_TM,4,"Rotation Rules")
tc("FTC442","Who can approve exceptions to talent mobility?",
   ["CHRO/CEO can approve exceptions"],SRC_TM,4,"Rotation Rules")
tc("FTC443","Where is first rotation within?",
   ["1st Rotation – within the city"],SRC_TM,4,"Rotation Rules")
tc("FTC444","What is second rotation scope?",
   ["2nd Rotation – across different business / different location"],SRC_TM,4,"Rotation Rules")
tc("FTC445","Positions up to which grade must be via IJP?",
   ["All positions upto M2"],SRC_TM,4,"Rotation Rules")

# ─────────────────────────────────────────────────────────────────────────────
# JOINING POLICY
SRC_JP = "Joining Policy"

tc("FTC500","What is the maximum duration of pre-joining visit?",
   ["maximum period of 3 days"],SRC_JP,1,"Joining Pre-Visit")
tc("FTC501","Who can accompany the employee on pre-joining visit?",
   ["spouse"],SRC_JP,1,"Joining Pre-Visit")
tc("FTC502","How many days of post-joining leave is allowed?",
   ["3 days leave"],SRC_JP,1,"Joining Post-Visit")
tc("FTC503","Transportation rate if distance is less than 700 km?",
   ["Rs. 50 per km"],SRC_JP,1,"Joining Transport")
tc("FTC504","Transportation rate for more than 700 km?",
   ["Rs. 60 per km"],SRC_JP,1,"Joining Transport")
tc("FTC505","Car transport rate via packers and movers?",
   ["Rs. 10.0 per km"],SRC_JP,1,"Joining Transport")
tc("FTC506","Driver wages for 8 hours trip during joining?",
   ["Rs. 600/-"],SRC_JP,1,"Joining Transport")
tc("FTC507","Driver wages after 8 hours per hour?",
   ["Rs. 50/- per hour"],SRC_JP,1,"Joining Transport")
tc("FTC508","Maximum food expense per meal for joining travel?",
   ["Rs. 200/- per meal"],SRC_JP,1,"Joining Expenses")
tc("FTC509","How long does the brokerage benefit last from joining?",
   ["maximum for 1 year from the date of the joining"],SRC_JP,1,"Joining Accommodation")
tc("FTC510","What is the brokerage benefit for new employees?",
   ["One month rent"],SRC_JP,1,"Joining Accommodation")
tc("FTC511","What is the house deposit recovery period?",
   ["10 equal monthly instalments"],SRC_JP,1,"Joining Accommodation")
tc("FTC512","Within how long must joining expenses be claimed?",
   ["One Year from Date of Joining"],SRC_JP,1,"Joining Expenses")
tc("FTC513","What happens if employee quits within 1 year?",
   ["recovered in his/her F&F settlement"],SRC_JP,1,"Joining Expenses")
tc("FTC514","Who must approve joining expense exceptions?",
   ["CEO"],SRC_JP,1,"Joining Expenses")
tc("FTC515","Is joining policy applicable to management cadre?",
   ["Management / staff cadre employees"],SRC_JP,1,"Joining Applicability")
tc("FTC516","What is the joining policy effective date?",
   ["21.09.2023"],SRC_JP,1,"Joining Policy Dates")
tc("FTC517","Who books flight tickets for joining travel?",
   ["Arvind Travel Desk"],SRC_JP,1,"Joining Transport")
tc("FTC518","What is the mileage rate if employee drives own car for joining?",
   ["Rs. 10.0 per km"],SRC_JP,1,"Joining Transport")
tc("FTC519","Who pays the packers and movers bill for joining?",
   ["The company shall directly make payment"],SRC_JP,1,"Joining Transport")
tc("FTC520","Are children covered in pre-joining visit?",
   ["Children allowed in case of school admission"],SRC_JP,1,"Joining Pre-Visit")

# ─────────────────────────────────────────────────────────────────────────────
# CROSS-POLICY ETHICS HELPLINE (Multiple - but use single policy source)
# These map to the single policy that first mentions the channel

# Additional POSH cases
tc("FTC600","What is the POSH policy number?",
   ["ARV|ELC_SHA|008|010422"],SRC_POSH,1,"POSH Policy Dates")
tc("FTC601","Can a friend file a POSH complaint on behalf of victim?",
   ["Her relative or friend"],SRC_POSH,5,"POSH Complaint Filing")
tc("FTC602","Can a POSH complaint be filed for a dead person?",
   ["written consent of her legal heir"],SRC_POSH,5,"POSH Complaint Filing")
tc("FTC603","Can a POSH complaint be filed by a co-worker?",
   ["Her co-worker"],SRC_POSH,5,"POSH Complaint Filing")
tc("FTC604","How many copies of complaint must be submitted to AIC?",
   ["six copies of the complaint"],SRC_POSH,6,"POSH Complaint Filing")
tc("FTC605","What is the AIC abbreviation full form?",
   ["Arvind Internal Complaint Committee"],SRC_POSH,2,"POSH AIC Structure")
tc("FTC606","Can a party bring legal practitioner to AIC proceedings?",
   ["not be allowed to bring in any legal practitioner"],SRC_POSH,6,"POSH Complaint Filing")
tc("FTC607","What is CT in POSH policy?",
   ["Complainant"],SRC_POSH,2,"POSH Definitions")
tc("FTC608","What is RE in POSH?",
   ["Respondent"],SRC_POSH,2,"POSH Definitions")
tc("FTC609","Does AIC have same powers as civil court?",
   ["powers as that of a civil court"],SRC_POSH,4,"POSH AIC Structure")
tc("FTC610","What if AIC inquiry is abandoned after 3 missed proceedings?",
   ["notice of 15 (fifteen) days"],SRC_POSH,6,"POSH Timelines")

# Additional Grievance
tc("FTC620","What does policy say about confidentiality in grievance?",
   ["kept strictly confidential"],SRC_GR,2,"Grievance Policy")
tc("FTC621","Who handles complex grievances involving ethical misconduct?",
   ["Ethics Helpline / Group Ethics Officer"],SRC_GR,4,"Grievance Channels")
tc("FTC622","Is the grievance policy applicable to part-time employees?",
   ["part-time"],SRC_GR,2,"Grievance Applicability")
tc("FTC623","What is the grievance policy number?",
   ["ARV|COM_GRM|001|260725"],SRC_GR,1,"Grievance Policy")

# Additional Talent Mobility
tc("FTC630","What is the purpose of MAB?",
   ["Monthly allowance"],SRC_TM,6,"MAB")
tc("FTC631","What is SIA used for?",
   ["household setup"],SRC_TM,6,"SIA")
tc("FTC632","How does talent mobility help with risk?",
   ["sensitive roles exceed tenure"],SRC_TM,2,"Rotation Rules")
tc("FTC633","Who governs talent mobility decisions?",
   ["Governed by HR"],SRC_TM,4,"Rotation Rules")

# Additional Local Conveyance
tc("FTC640","What system to use for conveyance claims?",
   ["Orapps – ESMS – Entry – Conveyance Expense"],SRC_LC,2,"Conveyance Claim")
tc("FTC641","Does local conveyance apply to Ahmedabad corporate staff?",
   ["Applicable to all Management / staff cadre of Arvind Ltd"],SRC_LC,1,"Conveyance Applicability")

# Additional Domestic Travel
tc("FTC650","What is domestic travel policy number?",
   ["ARV | EOP_DTP | 003 | 270723"],SRC_DT,1,"Travel Procedures")
tc("FTC651","What is the issue date of domestic travel policy?",
   ["27.07.2023"],SRC_DT,1,"Travel Procedures")
tc("FTC652","Can senior officials travel together on same flight?",
   ["senior officials travelling to the same destination on the same day take separate flights"],SRC_DT,3,"Travel Procedures")
tc("FTC653","When is overnight rail travel mandatory?",
   ["destinations connected by overnight rail"],SRC_DT,3,"Travel Procedures")
tc("FTC654","Are shared cab arrangements encouraged?",
   ["multiple employees traveling to the same destination make arrangements to share cabs"],SRC_DT,5,"Cab Entitlements")

# Additional Joining
tc("FTC660","Is joining policy applicable to subsidiaries?",
   ["subsidiaries"],SRC_JP,1,"Joining Applicability")
tc("FTC661","Are income taxes handled for joining relocation?",
   ["Income tax shall be grossed up"],SRC_JP,1,"Joining Expenses")
tc("FTC662","Can employee avail both pre and post joining visit?",
   ["either a Pre-Joining Visit OR Post Joining Visit"],SRC_JP,1,"Joining Pre-Visit")

# Additional Gender Policy
tc("FTC670","What is the gender policy number?",
   ["ARV|COM_GENP|001|260725"],SRC_GP,1,"Gender Policy Dates")
tc("FTC671","Does gender policy cover hiring decisions?",
   ["Hiring and Promotions are conducted based on merit"],SRC_GP,3,"Gender Applicability")
tc("FTC672","Are third-party partners covered under gender policy?",
   ["third-party partners"],SRC_GP,2,"Gender Applicability")

# Additional Whistleblower
tc("FTC680","Can I report employee negligence through whistleblower?",
   ["Employee negligence"],SRC_WB,3,"Whistleblower Scope")
tc("FTC681","Can I report corporate espionage through whistleblower?",
   ["Corporate espionage and information disclosure"],SRC_WB,3,"Whistleblower Scope")
tc("FTC682","What is the duty of employees during whistleblower investigation?",
   ["duty to cooperate with investigations"],SRC_WB,4,"Whistleblower Investigation")
tc("FTC683","How long to file complaint with Chairman if whistleblower victimized?",
   ["lodge a written complaint to the Chairman"],SRC_WB,5,"Whistleblower Protection")

print(f"Generated {len(CASES)} test cases")

# Verify no duplicates
ids = [c["id"] for c in CASES]
assert len(ids) == len(set(ids)), "Duplicate IDs!"

with open("fresh_test_suite.json", "w") as f:
    json.dump(CASES, f, indent=2)

print(f"Saved to fresh_test_suite.json")

# Stats per policy
from collections import Counter
srcs = Counter(c["source"] for c in CASES)
for s, n in sorted(srcs.items()):
    print(f"  {s}: {n} cases")
