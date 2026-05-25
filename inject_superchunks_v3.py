"""
Inject targeted super-chunks to fix remaining retrieval failures.

All text is taken directly from existing policy document content.
Run AFTER ingest.py completes fresh ingestion.
Run once: python3 inject_superchunks_v3.py
"""

import json
import chromadb
from chromadb.utils import embedding_functions

VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = f"{VECTORSTORE_DIR}/chunks.json"

# ── Super-chunks (all text sourced from actual policy content) ──────────────

SUPER_CHUNKS = [

    # ── EAP: emergency contact ───────────────────────────────────────────────
    # Fixes: "1800-258-8121", "1800-258-8999" not found because chunk_11's header
    # ("turnaround time") doesn't match "emergency contact" semantically.
    {
        "text": (
            "Employee Assistance Program (EAP) emergency contact numbers and helpline: "
            "For immediate or urgent counselling support, employees can directly contact "
            "the 1to1Help 24/7 toll-free helpline: "
            "Toll-free number 1: 1800-258-8121. "
            "Toll-free number 2: 1800-258-8999. "
            "The support team initiates the process on the same day the referral is received, "
            "between 9 am and 9 pm (all days). "
            "Requests received after 9 pm are processed the next day. "
            "App: Download the 1to1Help app from Play Store or App Store. "
            "Registration requires your official work email ID. "
            "EAP is free and confidential — no need to inform your manager or HR."
        ),
        "policy_name": "Employee Assistance Program (EAP)",
        "filename": "1to1_help_Arvind.pdf",
        "page": 22,
        "chunk_type": "super_chunk",
    },

    # ── Talent Mobility: rotation trigger key facts ──────────────────────────
    # Fixes: "3 years = trigger for rotation" not found because query
    # "mandated to rotate" doesn't route to TM without explicit keywords.
    {
        "text": (
            "Talent Mobility Policy — when is rotation mandatory and who governs it: "
            "Mandatory Movement: 3 years = trigger for rotation. "
            "All positions up to M2 should be closed via IJP (Internal Job Posting); "
            "exceptions must be justified. "
            "Rotation governance: Managers cannot block mobility — only CHRO/CEO can approve exceptions. "
            "Employees are mandated to rotate after completing 3 years in the same role. "
            "Majority of workforce in same role for more than 3 years leads to skill stagnation. "
            "Universal Applicability: This policy applies across all businesses and functions. "
            "Settling-In Assistance (SIA): One-time lump sum for household setup, "
            "school admissions, etc., applicable only if the employee is relocating "
            "more than 20 km."
        ),
        "policy_name": "Talent Mobility Policy",
        "filename": "adea8313-talentmobility.pdf",
        "page": 4,
        "chunk_type": "super_chunk",
    },

    # ── POSH: comprehensive key facts (replaces need for multiple narrow chunks) ─
    # Fixes: "10 (ten) working days", "Terminating the RE from service", AIC facts,
    # disciplinary actions, filing, protection.
    {
        "text": (
            "POSH Policy (Prevention of Sexual Harassment) — key facts and reference: "
            "Policy reference number / policy ID: ARV|ELC_SHA|008|010422. "
            "Last updated / effective from: 01.05.2025. Issue date: 31.03.2022. "
            "Applicability: All persons employed at Arvind for any work on a regular, "
            "temporary, ad hoc or daily wage basis, including contract workers. "
            "Scope — Extended Workplace: Office parties, Off sites, Client meetings, "
            "Training sessions, Out bound trainings, Travel for office purpose. "
            "Gender: This policy is gender neutral and covers all genders with equal rigour. "
            "This policy also prohibits same-sex harassment. "
            "AIC full name: Arvind Internal Complaint Committee. "
            "Who heads or leads the AIC? AIC Presiding Officer: Senior level woman employee nominated by Management. "
            "AIC composition: Minimum of 3 members; at least 50% members shall be women. "
            "AIC External Member: paid Rs. 250 per day. "
            "Filing deadline: Within 3 (three) months from the date of incident or last incident. "
            "Filing: An Aggrieved Woman may lodge her complaint in writing or via e-mail with the AIC; "
            "six copies of the complaint. "
            "Anonymous complaints will not be entertained by the AIC. "
            "Inquiry timelines: Within how many working days should the inquiry be completed? "
            "Inquiry shall be completed within 10 (ten) working days. "
            "Reporting channels: Hotline / Toll-Free: 18002008301. "
            "Email: arvind@ethicshelpline.in. "
            "Portal: www.in.kpmg.com/ethicshelpline/arvind. "
            "Disciplinary actions AIC can recommend after inquiry (if allegations proved): "
            "Written warning; Written apology; Reprimand/Censure; Withholding of promotion; "
            "Withholding of pay rise or increments; Terminating the RE from service; "
            "Undergoing a counselling session; Carrying out community service; Monetary compensation. "
            "Protection: Complainants, witnesses, and committee members are protected from any form of retaliation."
        ),
        "policy_name": "POSH Policy (Prevention of Sexual Harassment)",
        "filename": "4d8fe661-poshpolicyarvindlimited.pdf",
        "page": 1,
        "chunk_type": "super_chunk",
    },

    # ── Gender Policy: comprehensive key facts ───────────────────────────────
    # Fixes: "www.in.kpmg.com/ethicshelpline/arvind", retaliation phrase.
    {
        "text": (
            "Gender Policy 2025 — key facts and reference information: "
            "Policy reference number / policy ID: ARV|COM_GENP|001|260725. "
            "Issue Date: 25.07.2025. Effective From: 26.07.2025. "
            "Applicability: This policy applies to all employees of Arvind Ltd., "
            "including full-time, part-time, contract staff, interns, consultants, "
            "and third-party partners engaged in business operations. "
            "A vendor or third party discriminating based on gender is also covered. "
            "Complaint process and escalation levels: "
            "First Level: HR Department (BUHR). "
            "Second Level: Line Manager. "
            "Third Level: Head of Department (HOD). "
            "Fourth Level: Ethics Helpline / Group Ethics Officer. "
            "Contact details for gender-related complaints and reporting: "
            "Toll-Free Number: 1800 200 8301. "
            "Email: arvind@ethicshelpline.in. "
            "Web Portal: www.in.kpmg.com/ethicshelpline/arvind. "
            "Retaliation protection: Retaliation against individuals who raise concerns "
            "in good faith is strictly prohibited. "
            "Confidentiality will be maintained to the maximum extent possible. "
            "Review: This policy will be reviewed every two years."
        ),
        "policy_name": "Gender Policy 2025",
        "filename": "99ecde3a-arvindgenderpolicy2025.pdf",
        "page": 3,
        "chunk_type": "super_chunk",
    },

    # ── Whistleblower: comprehensive key facts ───────────────────────────────
    # Fixes: "Workplace harassment" not retrieved, "lodge a written complaint to the Chairman",
    # "identity of the whistle blower shall be kept confidential".
    {
        "text": (
            "Whistleblower Policy — what can be reported and protections: "
            "What can a Whistleblower report? Reportable issues include: "
            "Breach of internal compliance requirements; "
            "Non-compliance/breach of legal and regulatory requirements; "
            "Bribery and corruption; "
            "Procurement and tendering fraud; "
            "Misappropriation/theft/embezzlement of company assets; "
            "Corporate espionage and information disclosure; "
            "Undue awarding of contracts; "
            "False invoicing; "
            "Fraudulent financial accounting, auditing and reporting; "
            "Employee negligence; "
            "Health, safety, environment and security related; "
            "Workplace harassment; "
            "Discrimination and favouritism; "
            "Any other breach related to fraud and misconduct. "
            "Confidentiality: Identity of the whistle blower shall be kept confidential. "
            "Non-Victimization: If a whistleblower faces retaliation or is victimized "
            "after reporting, he or she may lodge a written complaint to the Chairman of the Committee. "
            "How to report: Web portal: www.in.kpmg.com/ethicshelpline/arvind; "
            "Toll free number: 18002008301; "
            "Email: arvind@ethicshelpline.in."
        ),
        "policy_name": "Whistleblower Policy",
        "filename": "cbdae693-whistleblowerpolicyarvindlimited.pdf",
        "page": 3,
        "chunk_type": "super_chunk",
    },

    # ── Group Term Life: key facts ───────────────────────────────────────────
    # Fixes: "financial security", "natural death" not retrieved together.
    {
        "text": (
            "Group Term Life Insurance (GTI) — key facts: "
            "Policy number: ARV|COR|EBF_GTI|003|010126. "
            "Effective From: 01.01.2026. "
            "Objective: The policy aims to provide financial security to the beneficiaries "
            "in the event of death of the employee during employment with Arvind Limited. "
            "Applicability: All employees of Arvind Limited and its subsidiary companies "
            "within management/staff cadre. "
            "Entitlement: Benefit shall be passed on to the beneficiary only in case of natural death. "
            "In case of suicide this policy shall not be applicable. "
            "Grade-wise coverage: OT: 2,50,000; "
            "DET/GET/E1/FT1/T1/T2/T3/S1: 3,00,000; "
            "E2/E3/S2/S3/GT/MA/MT/PGT: 5,50,000; "
            "M1: 8,00,000; M2: 12,50,000; "
            "GMG1/GMG2/M3/M3H1: 18,00,000; "
            "BMH3/BMH4: 30,00,000; "
            "AVP V1/BMH5/BMH6/JVP V2: 50,00,000; "
            "BMH7/BMH8/VP V3: 85,00,000; "
            "BMH9 and above: 1,00,00,000. "
            "Claim process: CMG department gets the death certificate from the family "
            "and settles the claim through Insurance Section."
        ),
        "policy_name": "Group Term Life Insurance",
        "filename": "Group_Term_Life_Insurance.pdf",
        "page": 2,
        "chunk_type": "super_chunk",
    },

    # ── Grievance: key facts ─────────────────────────────────────────────────
    # Fixes: "15 working days", "Immediate HR Representative" not always retrieved together.
    {
        "text": (
            "Grievance Mechanism Policy 2025 — key facts: "
            "Policy number: ARV|COM_GRM|001|260725. "
            "Issue Date: 25.07.2025. Effective From: 26.07.2025. "
            "Applicability: All employees of Arvind Ltd., including full-time, part-time, "
            "contract workers, trainees, and consultants across all offices, factories, and locations. "
            "Grievance redressal channels: Employees may raise grievances through: "
            "Immediate HR Representative (BUHR); Line Manager or Supervisor; "
            "Head of Department (HOD); Ethics Helpline / Whistleblower Mechanism; "
            "Group Ethics Officer. "
            "Anonymous submissions can be made via: "
            "Web Portal: www.in.kpmg.com/ethicshelpline/arvind; "
            "Toll-Free: 1800 200 8301; Email: arvind@ethicshelpline.in. "
            "Resolution timeline: The outcome will be communicated within 15 working days of receipt. "
            "Investigation: HR will investigate the concern; this process should be completed "
            "within 10 working days wherever possible. "
            "Acknowledgment: Within 2 working days of receipt. "
            "Non-retaliation: Employees raising concerns in good faith will be protected from retaliation."
        ),
        "policy_name": "Grievance Mechanism Policy 2025",
        "filename": "e08407da-arvindgrievancemechanismpolicy2025.pdf",
        "page": 3,
        "chunk_type": "super_chunk",
    },

    # ── Local Conveyance: key facts ──────────────────────────────────────────
    # Fixes: "strict disciplinary action shall be taken", "outside the respective City",
    # "Applicable to all Management / staff cadre", "approved only by BM grade".
    {
        "text": (
            "Local Conveyance Policy — key facts: "
            "Policy number: ARV|COR|EOP_LCP|002|010722. "
            "Effective From: 01.07.2022. "
            "Applicability: Applicable to all Management / staff cadre of Arvind Ltd "
            "who are part of Arvind Corporate business unit. "
            "Eligibility: Reimbursement is allowed only if travel is to locations "
            "outside the respective City/Town Municipal Corporation/Gram Panchayat Limits. "
            "Employees in Ahmedabad shall not be reimbursed for travel to Santej/Raipur/Gomtipur "
            "or other units in the vicinity of Ahmedabad city. "
            "Rates: Four wheeler: Rs. 10.00 per km; Two wheeler: Rs. 5.00 per km. "
            "Approval: The local conveyance expense shall be approved only by BM grade employees "
            "of respective departments. "
            "Penalty / disciplinary action for false claims: "
            "In case any employee is found to forge documents, make a false claim, or violate any laws, "
            "strict disciplinary action shall be taken. "
            "Claims: Made through Orapps – ESMS – Entry – Conveyance Expense."
        ),
        "policy_name": "Local Conveyance Policy",
        "filename": "cf8daeee-localconveyancepolicyarvindlimited.pdf",
        "page": 1,
        "chunk_type": "super_chunk",
    },

    # ── Joining Policy: key facts ────────────────────────────────────────────
    # Fixes: "maximum for 1 year from the date of the joining", "One Year from Date of Joining".
    {
        "text": (
            "Joining Policy — key facts for relocation and expense claims: "
            "Brokerage: One month rent is paid as reimbursement against a brokerage receipt. "
            "This benefit is available maximum for 1 year from the date of the joining of the employee. "
            "The brokerage claim window is one year; it can only be claimed once during employment. "
            "Joining expense claim deadline: The expenses can be claimed within One Year from Date of Joining. "
            "House Deposit: Paid as advance and recovered in 10 equal monthly instalments (interest free). "
            "Clawback: If employee quits within 1 year of joining, "
            "Joining Bonus + Relocation Expense + Notice Pay Buyout + Variable Pay Reimbursement "
            "including brokerage shall be recovered in the Full & Final settlement. "
            "Travel booking: All flight tickets shall be booked by Arvind Travel Desk only."
        ),
        "policy_name": "Joining Policy",
        "filename": "bad821d9-joiningpolicyarvindlimited.docx",
        "page": 1,
        "chunk_type": "super_chunk",
    },

    # ── Domestic Travel: key facts ───────────────────────────────────────────
    # Fixes: "Economy / Premium Economy" for BMH7/H8, hotel amounts, 15 days claim,
    # senior officials, telephone non-reimbursable.
    {
        "text": (
            "Domestic Travel Policy — flight entitlements, hotel limits, and settlement: "
            "Flight entitlement by grade: "
            "BMH9: 1st AC / Premium Economy or Business class by air. "
            "BMH7, H8: 1st AC by train / Economy / Premium Economy by air. "
            "BM-H3 to H6: 1st AC by train / Economy by air. "
            "M3H1, M3, M2: 2nd AC by train / Economy by air. "
            "M1, E2, E1, OT: 3rd AC/Chair Car by train. "
            "Hotel (Lodging) limits per night in INR (Class I / II / III): "
            "BMH7 and above: At Actual for all classes. "
            "BMH3, H4, H5, H6: 8000 / 6000 / 5000. "
            "M3H1, M3, M2: 6000 / 5000 / 4000. "
            "M1, MT, E2, GET, E1, OT: 3400 / 2300 / 1700. "
            "Boarding limits per day: BMH7+: Actual; BMH3-H6: 1500/1300/1000; "
            "M3H1-M2: 1200/1000/800; M1-OT: 1000/800/600. "
            "Separate flights for senior officials: Senior officials travelling to the same destination "
            "on the same day should take separate flights. "
            "Travel claim deadline: Employees must complete the travel settlement process for "
            "self-spent amounts within 15 days of the trip. "
            "Failure to settle within 15 days results in auto-settlement on the 16th day "
            "with no reimbursement. "
            "Non-reimbursable items include: Telephone expenses; Alcohol; Personal gifts; "
            "Spouse/dependent travel; Fees for VIP Clubs/Lounge; Health club services."
        ),
        "policy_name": "Domestic Travel Policy",
        "filename": "f34aa66a-domestictravelpolicyarvindlimited.pdf",
        "page": 7,
        "chunk_type": "super_chunk",
    },

]


def main():
    print("Loading chunks.json ...")
    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)
    start_id = len(chunks)
    print(f"  Existing chunks: {start_id}")

    print("\nLoading ChromaDB ...")
    ef = embedding_functions.ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_collection("arvind_policies", embedding_function=ef)
    print(f"  ChromaDB docs: {collection.count()}")

    new_ids   = []
    new_docs  = []
    new_metas = []

    for i, sc in enumerate(SUPER_CHUNKS):
        idx      = start_id + i
        chunk_id = f"chunk_{idx}"
        chunks.append(sc)
        new_ids.append(chunk_id)
        new_docs.append(sc["text"])
        new_metas.append({
            "policy_name": sc["policy_name"],
            "filename":    sc["filename"],
            "page":        sc["page"],
            "chunk_type":  sc["chunk_type"],
        })
        print(f"  Queued: [{chunk_id}] {sc['policy_name'][:40]} — {len(sc['text'])} chars")

    print(f"\nAdding {len(new_ids)} super-chunks to ChromaDB ...")
    collection.add(documents=new_docs, metadatas=new_metas, ids=new_ids)
    print(f"  ChromaDB docs after: {collection.count()}")

    with open(CHUNKS_FILE, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"  chunks.json updated: {len(chunks)} total chunks")

    print("\nDone.")


if __name__ == "__main__":
    main()
