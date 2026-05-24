// AUTO-GENERATED benchmark test cases — 200 sample from 6419 total
export interface BenchmarkTest {
  id: string;
  query: string;
  exactAnswer: string;
  keyFacts: string[];
  source: string;
  page: number;
  category: string;
  subcategory: string;
}

export const BENCHMARK_TESTS: BenchmarkTest[] = [
  {
    id: "TC03087",
    query: "hi, what is the ethics helpline web portal?",
    exactAnswer: `The Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["kpmg.com/ethicshelpline/arvind"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC03878",
    query: "pls tell mobility allowance for M1?",
    exactAnswer: `For **M1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹8,52,000 |
| Monthly | ₹71,000 |
| MAB: Tier 2 → Tier 1 (15%) | ₹10,650/month |
| MAB: Discretionary (5%) | ₹3,550/month |
| Settling-In Assistance (SIA) | ₹15,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["10,650", "15,000", "M1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC05223",
    query: "Can you help me understand: What is the ethics helpline toll free number?",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC03791",
    query: "What to do if I face sexual harassment? as per policy",
    exactAnswer: `You can file a complaint through:

1. **Supervisor / Reporting Manager** (any trusted person in hierarchy)
2. **Business Unit HR Head**
3. **Whistleblowing channels:**
   - 📞 Hotline: 18002008301
   - 📧 Email: arvind@ethicshelpline.in
   - 🌐 Portal: www.in.kpmg.com/ethicshelpline/arvind/

Complaints must be in **writing or email** with your signature. **Anonymous complaints are NOT accepted by AIC.**

*Source: POSH Policy, Page 5*`,
    keyFacts: ["AIC", "writing", "18002008301", "ethicshelpline"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Complaint Filing",
  },
  {
    id: "TC02273",
    query: "List all Arvind HR policies in detail",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC03421",
    query: "Ahmedabad local conveyance restrictions please tell me",
    exactAnswer: `Employees in Ahmedabad with a company car are **not reimbursed** for travelling to **Santej, Raipur, Gomtipur, or other units in the vicinity of Ahmedabad city**.

*Source: Local Conveyance Policy, Page 1, Section 4(a)(ii)*`,
    keyFacts: ["Santej", "Raipur", "Gomtipur", "Ahmedabad"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Restrictions",
  },
  {
    id: "TC02569",
    query: "Can manager block my rotation?",
    exactAnswer: `**Managers cannot block mobility.** Only the **CHRO or CEO** can approve exceptions to the talent mobility policy.

*Source: Talent Mobility Policy, Page 4*`,
    keyFacts: ["CHRO", "CEO", "cannot block"],
    source: "Talent Mobility Policy",
    page: 4,
    category: "Talent Mobility",
    subcategory: "Governance",
  },
  {
    id: "TC00923",
    query: "According to company policy, mobility adjustment benefit for m3h1",
    exactAnswer: `For **M3H1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹26,00,000 |
| Monthly | ₹2,16,667 |
| MAB: Tier 2 → Tier 1 (15%) | ₹32,500/month |
| MAB: Discretionary (5%) | ₹10,833/month |
| Settling-In Assistance (SIA) | ₹45,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["32,500", "45,000", "M3H1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC03267",
    query: "Can I report a grievance anonymously? please tell me",
    exactAnswer: `**Yes.** Anonymous complaints will be considered **provided sufficient information is provided for investigation**. Use the Ethics Helpline (web, phone, or email) for anonymous submissions.

*Source: Grievance Mechanism Policy, Page 2*`,
    keyFacts: ["anonymous", "sufficient information", "Ethics Helpline"],
    source: "Grievance Mechanism Policy",
    page: 2,
    category: "Grievance",
    subcategory: "Anonymous",
  },
  {
    id: "TC00016",
    query: "Lodging limit for m3 in Class I?",
    exactAnswer: `For **M3H1, M3, and M2**, the lodging limit in Class I cities is **₹6000 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["6000", "M3", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Lodging Limits",
  },
  {
    id: "TC03253",
    query: "According to company policy, joining expense claim deadline",
    exactAnswer: `Joining expenses must be **claimed within 1 year from the Date of Joining**.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["1 year", "Date of Joining"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Claim Deadline",
  },
  {
    id: "TC04384",
    query: "Gender complaint channels in detail",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC02129",
    query: "What happens if I leave within 1 year of joining?",
    exactAnswer: `If you **quit within 1 year of joining**, the following will be **recovered in your Full & Final settlement**:

• Joining Bonus
• Relocation Expenses
• Notice Pay Buyout
• Variable Pay Reimbursement (including brokerage)

*Source: Joining Policy, Page 2*`,
    keyFacts: ["1 year", "Full & Final", "recovered", "Joining Bonus"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Recovery",
  },
  {
    id: "TC06000",
    query: "hi, what actions can aic recommend?",
    exactAnswer: `If the allegation is proved, the AIC may recommend:

• Written warning or apology
• Reprimand/Censure
• Withholding promotion or pay increment
• **Termination** from service
• Counselling session
• Community service
• **Monetary compensation**

*Source: POSH Policy, Page 8*`,
    keyFacts: ["termination", "monetary compensation", "written warning"],
    source: "POSH Policy",
    page: 8,
    category: "POSH",
    subcategory: "Disciplinary Actions",
  },
  {
    id: "TC01157",
    query: "What is the household goods transportation limit for joining? as per policy",
    exactAnswer: `Transportation of household goods on joining:

• **Less than 700 km**: Maximum ₹50 per km or Actuals (whichever is **lesser**) + Income tax gross-up
• **More than 700 km**: Maximum ₹60 per km or Actuals (whichever is **lesser**) + Income tax gross-up

*Source: Joining Policy, Page 1*`,
    keyFacts: ["50 per km", "60 per km", "700 km", "lesser"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Relocation",
  },
  {
    id: "TC00101",
    query: "Mobility Adjustment Benefit for E2 in detail",
    exactAnswer: `For **E2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹5,49,000 |
| Monthly | ₹45,750 |
| MAB: Tier 2 → Tier 1 (15%) | ₹6,863/month |
| MAB: Discretionary (5%) | ₹2,288/month |
| Settling-In Assistance (SIA) | ₹10,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["6,863", "10,000", "E2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC00559",
    query: "What class is Bhopal for travel? please tell me",
    exactAnswer: `**Bhopal** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Bhopal", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC01420",
    query: "pls tell appeal process for grievances?",
    exactAnswer: `If you are unsatisfied with the resolution, you may **escalate to the next level in the hierarchy** — such as BU Head, Ethics Officer, or Group HR.

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["escalate", "BU Head", "Ethics Officer", "Group HR"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Appeals",
  },
  {
    id: "TC01041",
    query: "whats the ethics helpline web portal",
    exactAnswer: `The Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["kpmg.com/ethicshelpline/arvind"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC00452",
    query: "How do I report unethical behaviour? as per policy",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC05321",
    query: "Can you help me understand: Arvind ethics complaint email",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC01250",
    query: "What policies does Arvind have? in detail",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC05202",
    query: "Personal car local conveyance rate",
    exactAnswer: `For personal **four-wheeler (car)**, the reimbursement is **₹10.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["10.00", "four-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC02626",
    query: "House deposit advance on joining relocation please tell me",
    exactAnswer: `The company provides a **house deposit as an advance** to the employee, recovered in **10 equal monthly instalments (interest-free)**.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["advance", "10 equal monthly instalments", "interest-free"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "House Deposit",
  },
  {
    id: "TC06252",
    query: "Whistleblower reporting channels in detail",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC01699",
    query: "Can you help me understand: Ethics helpline contact email",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC00424",
    query: "what punishment can be given for sexual harassment",
    exactAnswer: `If the allegation is proved, the AIC may recommend:

• Written warning or apology
• Reprimand/Censure
• Withholding promotion or pay increment
• **Termination** from service
• Counselling session
• Community service
• **Monetary compensation**

*Source: POSH Policy, Page 8*`,
    keyFacts: ["termination", "monetary compensation", "written warning"],
    source: "POSH Policy",
    page: 8,
    category: "POSH",
    subcategory: "Disciplinary Actions",
  },
  {
    id: "TC02516",
    query: "What policies does Arvind have?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC06115",
    query: "Pre-joining visit eligibility as per policy",
    exactAnswer: `New recruits are eligible for a **Pre-Joining Visit** for a **maximum of 3 days** to the posting location (for accommodation, school admission, etc.). Travel expenses for **self and spouse** (and children for school admission) are reimbursed.

*Source: Joining Policy, Page 1*`,
    keyFacts: ["3 days", "pre-joining", "spouse"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Pre-Joining",
  },
  {
    id: "TC04728",
    query: "M1 lodging and boarding Class I please tell me",
    exactAnswer: `For **M1** in **Class I** cities:

| Type | Limit |
|---|---|
| Lodging (hotel) | ₹3400/day |
| Boarding (food) | ₹1000/day |

All limits include GST. Per 24-hour period.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["3400", "1000", "M1", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Combined Limits",
  },
  {
    id: "TC04090",
    query: "Can you help me understand: How to call for POSH complaint?",
    exactAnswer: `The POSH/Ethics Helpline toll-free number is **18002008301**.

*Source: POSH Policy, Page 5*`,
    keyFacts: ["18002008301"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Contact",
  },
  {
    id: "TC03595",
    query: "whats the mobility allowance for m3",
    exactAnswer: `For **M3**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹19,00,000 |
| Monthly | ₹1,58,333 |
| MAB: Tier 2 → Tier 1 (15%) | ₹23,750/month |
| MAB: Discretionary (5%) | ₹7,917/month |
| Settling-In Assistance (SIA) | ₹30,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["23,750", "30,000", "M3"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC04871",
    query: "Mobility Adjustment Benefit for M3H1 as per policy",
    exactAnswer: `For **M3H1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹26,00,000 |
| Monthly | ₹2,16,667 |
| MAB: Tier 2 → Tier 1 (15%) | ₹32,500/month |
| MAB: Discretionary (5%) | ₹10,833/month |
| Settling-In Assistance (SIA) | ₹45,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["32,500", "45,000", "M3H1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC02511",
    query: "hi, what is the posh toll free number?",
    exactAnswer: `The POSH/Ethics Helpline toll-free number is **18002008301**.

*Source: POSH Policy, Page 5*`,
    keyFacts: ["18002008301"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Contact",
  },
  {
    id: "TC01841",
    query: "whats the posh inquiry timeline",
    exactAnswer: `The AIC has **90 days** to complete its inquiry. The inquiry report must be submitted to management within **10 days** of completion. Management then has **60 days** to act on the recommendations.

*Source: POSH Policy, Page 6-7*`,
    keyFacts: ["90 days", "10 days", "60 days"],
    source: "POSH Policy",
    page: 6,
    category: "POSH",
    subcategory: "Timeline",
  },
  {
    id: "TC04385",
    query: "Can you help me understand: How much is reimbursed for bike travel?",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC05454",
    query: "According to company policy, arvind toll free helpline",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC05974",
    query: "I have a work complaint, what do I do? as per policy",
    exactAnswer: `You can raise a grievance through any of these channels:

1. **Immediate HR Representative (BUHR)**
2. **Line Manager or Supervisor**
3. **Head of Department (HOD)**
4. **Ethics Helpline:**
   - 🌐 Web: www.in.kpmg.com/ethicshelpline/arvind
   - 📞 Toll-Free: 1800 200 8301
   - 📧 Email: arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Grievance Mechanism Policy, Page 2*`,
    keyFacts: ["BUHR", "1800 200 8301", "ethicshelpline"],
    source: "Grievance Mechanism Policy",
    page: 2,
    category: "Grievance",
    subcategory: "Channels",
  },
  {
    id: "TC05083",
    query: "Four-wheeler conveyance rate per km please tell me",
    exactAnswer: `For personal **four-wheeler (car)**, the reimbursement is **₹10.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["10.00", "four-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC00037",
    query: "Ethics helpline how to report please tell me",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC05611",
    query: "What hotel can new joinee stay in? in detail",
    exactAnswer: `Temporary accommodation for new joiners:

| Grade | Accommodation Type |
|---|---|
| BM & Above | Hotel (as per domestic travel policy) |
| M2 / M3 / M3H1 | Service Apartment / Guest House |
| E1 / E2 / M1 | Service Apartment / Guest House |

For E1/E2/M1: If staying in service apartment **beyond 15 days** with special CHRO permission, charges are levied.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["Hotel", "Service Apartment", "CHRO", "15 days"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Accommodation",
  },
  {
    id: "TC03405",
    query: "Can you help me understand: Types of whistleblower complaints",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC02716",
    query: "When will my grievance be acknowledged? as per policy",
    exactAnswer: `Your grievance will be **acknowledged within 2 working days** of receipt (where your identity is known).

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["2 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC04281",
    query: "According to company policy, what is the mab for m3h1?",
    exactAnswer: `For **M3H1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹26,00,000 |
| Monthly | ₹2,16,667 |
| MAB: Tier 2 → Tier 1 (15%) | ₹32,500/month |
| MAB: Discretionary (5%) | ₹10,833/month |
| Settling-In Assistance (SIA) | ₹45,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["32,500", "45,000", "M3H1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC00319",
    query: "How do I report gender discrimination? please tell me",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC00945",
    query: "What class is Rajkot for travel? as per policy",
    exactAnswer: `**Rajkot** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Rajkot", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC00764",
    query: "Can you help me understand: Mobility Adjustment Benefit for M3",
    exactAnswer: `For **M3**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹19,00,000 |
| Monthly | ₹1,58,333 |
| MAB: Tier 2 → Tier 1 (15%) | ₹23,750/month |
| MAB: Discretionary (5%) | ₹7,917/month |
| Settling-In Assistance (SIA) | ₹30,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["23,750", "30,000", "M3"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC04021",
    query: "What is the gender policy at Arvind? please tell me",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC06184",
    query: "List all Arvind HR policies please tell me",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00412",
    query: "Is NCR Class I or Class II for travel policy? as per policy",
    exactAnswer: `**NCR** is classified as a **Class I city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["NCR", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC00218",
    query: "Main kaise report gender discrimination?",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC00024",
    query: "whistleblower reporting channels",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC02425",
    query: "hi, what is the ethics helpline toll free number?",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC02666",
    query: "list all arvind hr policies",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC02675",
    query: "What are the total travel limits for E2 in Class I city?",
    exactAnswer: `For **E2** in **Class I** cities:

| Type | Limit |
|---|---|
| Lodging (hotel) | ₹3400/day |
| Boarding (food) | ₹1000/day |

All limits include GST. Per 24-hour period.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["3400", "1000", "E2", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Combined Limits",
  },
  {
    id: "TC00942",
    query: "Which city class does Lucknow fall in?",
    exactAnswer: `**Lucknow** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Lucknow", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC01872",
    query: "Kya hai ethics helpline toll free number?",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC04732",
    query: "What is the ethics helpline email? please tell me",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC03632",
    query: "hi, ethics helpline how to report",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC03947",
    query: "I want to know what happens if I file a false grievance?",
    exactAnswer: `Any employee found to have **deliberately submitted a false or malicious complaint** may be subject to **disciplinary action** in line with the company's Code of Conduct.

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["false", "malicious", "disciplinary action"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "False Complaints",
  },
  {
    id: "TC00603",
    query: "I want to know what accommodation do I get when joining from outstation?",
    exactAnswer: `Temporary accommodation for new joiners:

| Grade | Accommodation Type |
|---|---|
| BM & Above | Hotel (as per domestic travel policy) |
| M2 / M3 / M3H1 | Service Apartment / Guest House |
| E1 / E2 / M1 | Service Apartment / Guest House |

For E1/E2/M1: If staying in service apartment **beyond 15 days** with special CHRO permission, charges are levied.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["Hotel", "Service Apartment", "CHRO", "15 days"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Accommodation",
  },
  {
    id: "TC05056",
    query: "Gender policy applicability please tell me",
    exactAnswer: `The Gender Policy applies to **all employees of Arvind Ltd.**, including:
• Full-time employees
• Part-time employees
• Contract staff
• Interns
• Consultants
• Third-party partners engaged in business operations

*Source: Gender Policy, Page 2*`,
    keyFacts: ["full-time", "interns", "consultants", "third-party"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Applicability",
  },
  {
    id: "TC03308",
    query: "List all Arvind HR policies as per policy",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC03571",
    query: "How do I report unethical behaviour?",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC04314",
    query: "when was the gender policy effective",
    exactAnswer: `The Gender Policy was issued on **25.07.2025** and is effective from **26.07.2025**.

Policy Number: ARV|COM_GENP|001|260725

*Source: Gender Policy, Page 1*`,
    keyFacts: ["25.07.2025", "26.07.2025"],
    source: "Gender Policy",
    page: 1,
    category: "Gender Policy",
    subcategory: "Details",
  },
  {
    id: "TC03260",
    query: "What is the house deposit policy on joining? in detail",
    exactAnswer: `The company provides a **house deposit as an advance** to the employee, recovered in **10 equal monthly instalments (interest-free)**.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["advance", "10 equal monthly instalments", "interest-free"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "House Deposit",
  },
  {
    id: "TC04232",
    query: "According to company policy, relocation household goods reimbursement",
    exactAnswer: `Transportation of household goods on joining:

• **Less than 700 km**: Maximum ₹50 per km or Actuals (whichever is **lesser**) + Income tax gross-up
• **More than 700 km**: Maximum ₹60 per km or Actuals (whichever is **lesser**) + Income tax gross-up

*Source: Joining Policy, Page 1*`,
    keyFacts: ["50 per km", "60 per km", "700 km", "lesser"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Relocation",
  },
  {
    id: "TC06272",
    query: "Shared vehicle conveyance claim",
    exactAnswer: `If more than one person travels in the same vehicle, **only the individual who actually incurred the cost** can claim reimbursement — not both travellers.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(v)*`,
    keyFacts: ["only the individual", "actually incurred"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Rules",
  },
  {
    id: "TC03206",
    query: "Job rotation allowance M2",
    exactAnswer: `For **M2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹13,00,000 |
| Monthly | ₹1,08,333 |
| MAB: Tier 2 → Tier 1 (15%) | ₹16,250/month |
| MAB: Discretionary (5%) | ₹5,417/month |
| Settling-In Assistance (SIA) | ₹20,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["16,250", "20,000", "M2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC05034",
    query: "How do I claim local conveyance? in detail",
    exactAnswer: `Local conveyance claims must be submitted in **Orapps → ESMS → Entry → Conveyance Expense**. Enter total km travelled; to-and-fro km from residence to official location will be automatically deducted.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(ii)*`,
    keyFacts: ["Orapps", "ESMS", "Conveyance Expense"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Claims",
  },
  {
    id: "TC04375",
    query: "According to company policy, who does the gender policy apply to?",
    exactAnswer: `The Gender Policy applies to **all employees of Arvind Ltd.**, including:
• Full-time employees
• Part-time employees
• Contract staff
• Interns
• Consultants
• Third-party partners engaged in business operations

*Source: Gender Policy, Page 2*`,
    keyFacts: ["full-time", "interns", "consultants", "third-party"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Applicability",
  },
  {
    id: "TC02654",
    query: "What HR policies are available? please tell me",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00073",
    query: "hi, what types of grievances are covered?",
    exactAnswer: `A grievance includes any concern about your work environment or employment. Examples:

• **Discrimination, harassment, or unfair treatment**
• **Interpersonal conflict or misconduct**
• **Workload or role clarity issues**
• **Breach of company policy or code of conduct**
• **Violation of health, safety, or ethical standards**

*Source: Grievance Mechanism Policy, Page 2*`,
    keyFacts: ["discrimination", "harassment", "misconduct"],
    source: "Grievance Mechanism Policy",
    page: 2,
    category: "Grievance",
    subcategory: "Definition",
  },
  {
    id: "TC04300",
    query: "According to company policy, what is the per km rate for two-wheeler?",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC05624",
    query: "Gender policy effective date as per policy",
    exactAnswer: `The Gender Policy was issued on **25.07.2025** and is effective from **26.07.2025**.

Policy Number: ARV|COM_GENP|001|260725

*Source: Gender Policy, Page 1*`,
    keyFacts: ["25.07.2025", "26.07.2025"],
    source: "Gender Policy",
    page: 1,
    category: "Gender Policy",
    subcategory: "Details",
  },
  {
    id: "TC03647",
    query: "Does Arvind have a gender equality policy? in detail",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC00541",
    query: "hi, what accommodation do i get when joining from outstation?",
    exactAnswer: `Temporary accommodation for new joiners:

| Grade | Accommodation Type |
|---|---|
| BM & Above | Hotel (as per domestic travel policy) |
| M2 / M3 / M3H1 | Service Apartment / Guest House |
| E1 / E2 / M1 | Service Apartment / Guest House |

For E1/E2/M1: If staying in service apartment **beyond 15 days** with special CHRO permission, charges are levied.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["Hotel", "Service Apartment", "CHRO", "15 days"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Accommodation",
  },
  {
    id: "TC03095",
    query: "whats covered under whistleblower",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC03134",
    query: "What triggers job rotation? in detail",
    exactAnswer: `**3 years in the same role** is the trigger for mandatory rotation. All positions up to **M2 grade** should be closed via **Internal Job Posting (IJP)**; exceptions must be justified.

*Source: Talent Mobility Policy, Page 4*`,
    keyFacts: ["3 years", "IJP", "M2"],
    source: "Talent Mobility Policy",
    page: 4,
    category: "Talent Mobility",
    subcategory: "Rotation Rules",
  },
  {
    id: "TC04044",
    query: "hi, does arvind have a gender equality policy?",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC02230",
    query: "Talent mobility tracks",
    exactAnswer: `There are **3 rotation tracks**:

• **Track A — Risk Mitigation**: Mandatory rotation for sensitive roles in risk-prone functions
• **Track B — Leadership/HiPo**: Future leaders broadened via structured mobility
• **Track C — On Demand**: Voluntary, employee-driven career paths

*Source: Talent Mobility Policy, Page 5*`,
    keyFacts: ["Track A", "Track B", "Track C"],
    source: "Talent Mobility Policy",
    page: 5,
    category: "Talent Mobility",
    subcategory: "Rotation Framework",
  },
  {
    id: "TC04474",
    query: "Can you help me understand: Whistleblower confidentiality",
    exactAnswer: `**Yes.** Arvind guarantees:

• **Complete confidentiality** — your identity will not be disclosed
• **No retaliation** — victimization will be treated as a serious disciplinary matter
• **Protection** — if victimized, file a written complaint to the Committee Chairman

*Source: Whistleblower Policy, Pages 4-5, Sections 9-10*`,
    keyFacts: ["confidentiality", "no retaliation", "protection"],
    source: "Whistleblower Policy",
    page: 4,
    category: "Whistleblower",
    subcategory: "Protection",
  },
  {
    id: "TC00710",
    query: "hi, pre-joining visit eligibility",
    exactAnswer: `New recruits are eligible for a **Pre-Joining Visit** for a **maximum of 3 days** to the posting location (for accommodation, school admission, etc.). Travel expenses for **self and spouse** (and children for school admission) are reimbursed.

*Source: Joining Policy, Page 1*`,
    keyFacts: ["3 days", "pre-joining", "spouse"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Pre-Joining",
  },
  {
    id: "TC00949",
    query: "Arvind gender inclusion policy in detail",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC00058",
    query: "How long does grievance investigation take?",
    exactAnswer: `The investigation should be **completed within 10 working days** wherever possible.

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["10 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC01825",
    query: "does arvind have a gender equality policy",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC01963",
    query: "Kya hai first rotation under talent mobility?",
    exactAnswer: `The **1st Rotation** is **within the same city**. The **2nd Rotation** is across a **different business or different location**.

*Source: Talent Mobility Policy, Page 4*`,
    keyFacts: ["1st Rotation", "within the city", "2nd Rotation"],
    source: "Talent Mobility Policy",
    page: 4,
    category: "Talent Mobility",
    subcategory: "Rotation Sequence",
  },
  {
    id: "TC03739",
    query: "Can you help me understand: Ethics helpline how to report",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC03323",
    query: "what policies does arvind have",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC02915",
    query: "hi, which cab service can m1 book?",
    exactAnswer: `For **M1, MT, E2, GET, E1, OT**, the cab/conveyance entitlement is: **Ola, Uber, BluSmart, Bus, Metro, or Local Transportation**.

*Source: Domestic Travel Policy, Annexure B, Page 8*`,
    keyFacts: ["Ola"],
    source: "Domestic Travel Policy",
    page: 8,
    category: "Domestic Travel",
    subcategory: "Cab Entitlements",
  },
  {
    id: "TC00914",
    query: "ethics helpline contact email",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC02203",
    query: "whats the per km rate for two-wheeler",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC06066",
    query: "What class is Ranchi for travel? please tell me",
    exactAnswer: `**Ranchi** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Ranchi", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC03019",
    query: "What is the POSH inquiry timeline? in detail",
    exactAnswer: `The AIC has **90 days** to complete its inquiry. The inquiry report must be submitted to management within **10 days** of completion. Management then has **60 days** to act on the recommendations.

*Source: POSH Policy, Page 6-7*`,
    keyFacts: ["90 days", "10 days", "60 days"],
    source: "POSH Policy",
    page: 6,
    category: "POSH",
    subcategory: "Timeline",
  },
  {
    id: "TC05117",
    query: "hi, what is the gender policy at arvind?",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC02906",
    query: "I want to know what class is Jammu for travel?",
    exactAnswer: `**Jammu** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Jammu", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC00316",
    query: "Mobility Adjustment Benefit for M3H1 please tell me",
    exactAnswer: `For **M3H1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹26,00,000 |
| Monthly | ₹2,16,667 |
| MAB: Tier 2 → Tier 1 (15%) | ₹32,500/month |
| MAB: Discretionary (5%) | ₹10,833/month |
| Settling-In Assistance (SIA) | ₹45,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["32,500", "45,000", "M3H1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC01013",
    query: "Ethics helpline phone number as per policy",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC03064",
    query: "According to company policy, rent brokerage limit on relocation",
    exactAnswer: `Brokerage: **One month's rent** is reimbursed against a brokerage receipt. This benefit is available **only once** during the employee's employment with Arvind, and is available for a **maximum of 1 year** from the date of joining.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["one month rent", "only once", "1 year"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Brokerage",
  },
  {
    id: "TC03485",
    query: "What is the ethics helpline web portal? as per policy",
    exactAnswer: `The Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["kpmg.com/ethicshelpline/arvind"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC01592",
    query: "According to company policy, gender complaint channels",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC01787",
    query: "According to company policy, city classification of hyderabad",
    exactAnswer: `**Hyderabad** is classified as a **Class I city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Hyderabad", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC05637",
    query: "According to company policy, job rotation allowance e2",
    exactAnswer: `For **E2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹5,49,000 |
| Monthly | ₹45,750 |
| MAB: Tier 2 → Tier 1 (15%) | ₹6,863/month |
| MAB: Discretionary (5%) | ₹2,288/month |
| Settling-In Assistance (SIA) | ₹10,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["6,863", "10,000", "E2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC00476",
    query: "How to report sexual harassment at Arvind?",
    exactAnswer: `You can file a complaint through:

1. **Supervisor / Reporting Manager** (any trusted person in hierarchy)
2. **Business Unit HR Head**
3. **Whistleblowing channels:**
   - 📞 Hotline: 18002008301
   - 📧 Email: arvind@ethicshelpline.in
   - 🌐 Portal: www.in.kpmg.com/ethicshelpline/arvind/

Complaints must be in **writing or email** with your signature. **Anonymous complaints are NOT accepted by AIC.**

*Source: POSH Policy, Page 5*`,
    keyFacts: ["AIC", "writing", "18002008301", "ethicshelpline"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Complaint Filing",
  },
  {
    id: "TC01392",
    query: "According to company policy, what hr policies are available?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC04186",
    query: "Gender complaint channels as per policy",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC02923",
    query: "Arvind ethics complaint email in detail",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC02740",
    query: "What HR policies are available? as per policy",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC05803",
    query: "What hotel can new joinee stay in? please tell me",
    exactAnswer: `Temporary accommodation for new joiners:

| Grade | Accommodation Type |
|---|---|
| BM & Above | Hotel (as per domestic travel policy) |
| M2 / M3 / M3H1 | Service Apartment / Guest House |
| E1 / E2 / M1 | Service Apartment / Guest House |

For E1/E2/M1: If staying in service apartment **beyond 15 days** with special CHRO permission, charges are levied.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["Hotel", "Service Apartment", "CHRO", "15 days"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Accommodation",
  },
  {
    id: "TC04107",
    query: "According to company policy, lodging limit for m3 in class i?",
    exactAnswer: `For **M3H1, M3, and M2**, the lodging limit in Class I cities is **₹6000 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["6000", "M3", "Class I"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Lodging Limits",
  },
  {
    id: "TC00954",
    query: "Can you help me understand: What HR policies are available?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00567",
    query: "What is the POSH toll free number? in detail",
    exactAnswer: `The POSH/Ethics Helpline toll-free number is **18002008301**.

*Source: POSH Policy, Page 5*`,
    keyFacts: ["18002008301"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Contact",
  },
  {
    id: "TC05049",
    query: "Tell me covered under whistleblower?",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC05895",
    query: "How do I report unethical behaviour? please tell me",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC05809",
    query: "Can you help me understand: Car reimbursement per km",
    exactAnswer: `For personal **four-wheeler (car)**, the reimbursement is **₹10.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["10.00", "four-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC04625",
    query: "What punishment can be given for sexual harassment?",
    exactAnswer: `If the allegation is proved, the AIC may recommend:

• Written warning or apology
• Reprimand/Censure
• Withholding promotion or pay increment
• **Termination** from service
• Counselling session
• Community service
• **Monetary compensation**

*Source: POSH Policy, Page 8*`,
    keyFacts: ["termination", "monetary compensation", "written warning"],
    source: "POSH Policy",
    page: 8,
    category: "POSH",
    subcategory: "Disciplinary Actions",
  },
  {
    id: "TC02993",
    query: "According to company policy, how long does it take to acknowledge a grievance?",
    exactAnswer: `Your grievance will be **acknowledged within 2 working days** of receipt (where your identity is known).

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["2 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC02938",
    query: "recovery on early exit from joining",
    exactAnswer: `If you **quit within 1 year of joining**, the following will be **recovered in your Full & Final settlement**:

• Joining Bonus
• Relocation Expenses
• Notice Pay Buyout
• Variable Pay Reimbursement (including brokerage)

*Source: Joining Policy, Page 2*`,
    keyFacts: ["1 year", "Full & Final", "recovered", "Joining Bonus"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Recovery",
  },
  {
    id: "TC01091",
    query: "According to company policy, what happens if i leave within 1 year of joining?",
    exactAnswer: `If you **quit within 1 year of joining**, the following will be **recovered in your Full & Final settlement**:

• Joining Bonus
• Relocation Expenses
• Notice Pay Buyout
• Variable Pay Reimbursement (including brokerage)

*Source: Joining Policy, Page 2*`,
    keyFacts: ["1 year", "Full & Final", "recovered", "Joining Bonus"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Recovery",
  },
  {
    id: "TC03893",
    query: "Local conveyance approval authority in detail",
    exactAnswer: `Local conveyance expenses must be approved **only by BM grade employees** of the respective department. The manager is responsible for ensuring the authenticity of claims.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(vi)*`,
    keyFacts: ["BM grade", "manager"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Approval",
  },
  {
    id: "TC00744",
    query: "What is the lodging limit for OT in Class II?",
    exactAnswer: `For **OT** (and M1, MT, E2, GET, E1, OT group), the lodging limit in Class II cities is **₹2300 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["2300", "OT", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Lodging Limits",
  },
  {
    id: "TC01613",
    query: "I want to know what can I report under the whistleblower policy?",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC05919",
    query: "hi, mobility adjustment benefit for e1",
    exactAnswer: `For **E1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹3,91,000 |
| Monthly | ₹32,583 |
| MAB: Tier 2 → Tier 1 (15%) | ₹4,888/month |
| MAB: Discretionary (5%) | ₹1,629/month |
| Settling-In Assistance (SIA) | ₹10,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["4,888", "10,000", "E1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC05792",
    query: "Can you help me understand: What are employees in Ahmedabad NOT reimbursed for?",
    exactAnswer: `Employees in Ahmedabad with a company car are **not reimbursed** for travelling to **Santej, Raipur, Gomtipur, or other units in the vicinity of Ahmedabad city**.

*Source: Local Conveyance Policy, Page 1, Section 4(a)(ii)*`,
    keyFacts: ["Santej", "Raipur", "Gomtipur", "Ahmedabad"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Restrictions",
  },
  {
    id: "TC01847",
    query: "hi, are per km rates same everywhere?",
    exactAnswer: `**Yes.** The local conveyance per-km rates (₹10/km for four-wheeler, ₹5/km for two-wheeler) are **applicable across India** for all grades.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(iv)*`,
    keyFacts: ["across India", "all grades"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Applicability",
  },
  {
    id: "TC00518",
    query: "Grievance investigation timeline please tell me",
    exactAnswer: `The investigation should be **completed within 10 working days** wherever possible.

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["10 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC01575",
    query: "Tell me the pre-joining visit policy?",
    exactAnswer: `New recruits are eligible for a **Pre-Joining Visit** for a **maximum of 3 days** to the posting location (for accommodation, school admission, etc.). Travel expenses for **self and spouse** (and children for school admission) are reimbursed.

*Source: Joining Policy, Page 1*`,
    keyFacts: ["3 days", "pre-joining", "spouse"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Pre-Joining",
  },
  {
    id: "TC02403",
    query: "What is the mobility allowance for E2? please tell me",
    exactAnswer: `For **E2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹5,49,000 |
| Monthly | ₹45,750 |
| MAB: Tier 2 → Tier 1 (15%) | ₹6,863/month |
| MAB: Discretionary (5%) | ₹2,288/month |
| Settling-In Assistance (SIA) | ₹10,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["6,863", "10,000", "E2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC04092",
    query: "How much can m3 claim for hotel in Class III?",
    exactAnswer: `For **M3H1, M3, and M2**, the lodging limit in Class III cities is **₹4000 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["4000", "M3", "Class III"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Lodging Limits",
  },
  {
    id: "TC05364",
    query: "What policies does Arvind have? as per policy",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00215",
    query: "what are employees in ahmedabad not reimbursed for",
    exactAnswer: `Employees in Ahmedabad with a company car are **not reimbursed** for travelling to **Santej, Raipur, Gomtipur, or other units in the vicinity of Ahmedabad city**.

*Source: Local Conveyance Policy, Page 1, Section 4(a)(ii)*`,
    keyFacts: ["Santej", "Raipur", "Gomtipur", "Ahmedabad"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Restrictions",
  },
  {
    id: "TC02586",
    query: "According to company policy, what is the gender policy at arvind?",
    exactAnswer: `Arvind's Gender Policy ensures **equal access to opportunities, representation, and fair treatment** for all gender identities across all levels of employment — from hiring and advancement to workplace safety.

*Source: Gender Policy, Page 2*`,
    keyFacts: ["gender equality", "equal access", "all gender identities"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Overview",
  },
  {
    id: "TC02704",
    query: "how do i file a sexual harassment complaint",
    exactAnswer: `You can file a complaint through:

1. **Supervisor / Reporting Manager** (any trusted person in hierarchy)
2. **Business Unit HR Head**
3. **Whistleblowing channels:**
   - 📞 Hotline: 18002008301
   - 📧 Email: arvind@ethicshelpline.in
   - 🌐 Portal: www.in.kpmg.com/ethicshelpline/arvind/

Complaints must be in **writing or email** with your signature. **Anonymous complaints are NOT accepted by AIC.**

*Source: POSH Policy, Page 5*`,
    keyFacts: ["AIC", "writing", "18002008301", "ethicshelpline"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Complaint Filing",
  },
  {
    id: "TC03094",
    query: "Grievance acknowledgement timeline in detail",
    exactAnswer: `Your grievance will be **acknowledged within 2 working days** of receipt (where your identity is known).

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["2 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC05958",
    query: "hi, what policies does arvind have?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC05455",
    query: "I want to know what is extended workplace in POSH?",
    exactAnswer: `**Yes.** POSH covers the **Extended Workplace** which includes:

• Office parties
• Off-sites / Client meetings
• Training sessions / Outbound trainings
• Travel for office purposes
• Any place visited in the course of employment
• A dwelling place or house

*Source: POSH Policy, Page 2*`,
    keyFacts: ["office parties", "off-sites", "travel", "extended workplace"],
    source: "POSH Policy",
    page: 2,
    category: "POSH",
    subcategory: "Scope",
  },
  {
    id: "TC04208",
    query: "According to company policy, what actions can aic recommend?",
    exactAnswer: `If the allegation is proved, the AIC may recommend:

• Written warning or apology
• Reprimand/Censure
• Withholding promotion or pay increment
• **Termination** from service
• Counselling session
• Community service
• **Monetary compensation**

*Source: POSH Policy, Page 8*`,
    keyFacts: ["termination", "monetary compensation", "written warning"],
    source: "POSH Policy",
    page: 8,
    category: "POSH",
    subcategory: "Disciplinary Actions",
  },
  {
    id: "TC00076",
    query: "Is POSH applicable at office parties?",
    exactAnswer: `**Yes.** POSH covers the **Extended Workplace** which includes:

• Office parties
• Off-sites / Client meetings
• Training sessions / Outbound trainings
• Travel for office purposes
• Any place visited in the course of employment
• A dwelling place or house

*Source: POSH Policy, Page 2*`,
    keyFacts: ["office parties", "off-sites", "travel", "extended workplace"],
    source: "POSH Policy",
    page: 2,
    category: "POSH",
    subcategory: "Scope",
  },
  {
    id: "TC05203",
    query: "who do i contact for gender bias issues",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC03831",
    query: "Who do I contact for gender bias issues? in detail",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC04761",
    query: "Are local conveyance rates applicable across India? please tell me",
    exactAnswer: `**Yes.** The local conveyance per-km rates (₹10/km for four-wheeler, ₹5/km for two-wheeler) are **applicable across India** for all grades.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(iv)*`,
    keyFacts: ["across India", "all grades"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Applicability",
  },
  {
    id: "TC03537",
    query: "What is the MAB for grade m3?",
    exactAnswer: `For **M3**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹19,00,000 |
| Monthly | ₹1,58,333 |
| MAB: Tier 2 → Tier 1 (15%) | ₹23,750/month |
| MAB: Discretionary (5%) | ₹7,917/month |
| Settling-In Assistance (SIA) | ₹30,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["23,750", "30,000", "M3"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC01939",
    query: "According to company policy, packers and movers limit for joining",
    exactAnswer: `Transportation of household goods on joining:

• **Less than 700 km**: Maximum ₹50 per km or Actuals (whichever is **lesser**) + Income tax gross-up
• **More than 700 km**: Maximum ₹60 per km or Actuals (whichever is **lesser**) + Income tax gross-up

*Source: Joining Policy, Page 1*`,
    keyFacts: ["50 per km", "60 per km", "700 km", "lesser"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Relocation",
  },
  {
    id: "TC05498",
    query: "Can I visit before joining to find accommodation? in detail",
    exactAnswer: `New recruits are eligible for a **Pre-Joining Visit** for a **maximum of 3 days** to the posting location (for accommodation, school admission, etc.). Travel expenses for **self and spouse** (and children for school admission) are reimbursed.

*Source: Joining Policy, Page 1*`,
    keyFacts: ["3 days", "pre-joining", "spouse"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Pre-Joining",
  },
  {
    id: "TC03687",
    query: "According to company policy, mt hotel allowance class ii city",
    exactAnswer: `For **MT** (and M1, MT, E2, GET, E1, OT group), the lodging limit in Class II cities is **₹2300 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["2300", "MT", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Lodging Limits",
  },
  {
    id: "TC04364",
    query: "Ethics helpline how to report as per policy",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC01816",
    query: "Can you help me understand: List all Arvind HR policies",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC01323",
    query: "Ethics helpline website URL",
    exactAnswer: `The Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["kpmg.com/ethicshelpline/arvind"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC06239",
    query: "Mobility Adjustment Benefit for grade m2",
    exactAnswer: `For **M2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹13,00,000 |
| Monthly | ₹1,08,333 |
| MAB: Tier 2 → Tier 1 (15%) | ₹16,250/month |
| MAB: Discretionary (5%) | ₹5,417/month |
| Settling-In Assistance (SIA) | ₹20,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["16,250", "20,000", "M2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC02735",
    query: "scooter bike per km rate local conveyance",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC05072",
    query: "Two-wheeler conveyance reimbursement per km",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC06053",
    query: "What cab can grade m3H1 use?",
    exactAnswer: `For **M3H1, M3, M2**, the cab/conveyance entitlement is: **Ola, Uber, or BluSmart**.

*Source: Domestic Travel Policy, Annexure B, Page 8*`,
    keyFacts: ["Ola"],
    source: "Domestic Travel Policy",
    page: 8,
    category: "Domestic Travel",
    subcategory: "Cab Entitlements",
  },
  {
    id: "TC04252",
    query: "Scooter bike per km rate local conveyance as per policy",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC02195",
    query: "I want to know what channels can I use to raise a complaint?",
    exactAnswer: `You can raise a grievance through any of these channels:

1. **Immediate HR Representative (BUHR)**
2. **Line Manager or Supervisor**
3. **Head of Department (HOD)**
4. **Ethics Helpline:**
   - 🌐 Web: www.in.kpmg.com/ethicshelpline/arvind
   - 📞 Toll-Free: 1800 200 8301
   - 📧 Email: arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Grievance Mechanism Policy, Page 2*`,
    keyFacts: ["BUHR", "1800 200 8301", "ethicshelpline"],
    source: "Grievance Mechanism Policy",
    page: 2,
    category: "Grievance",
    subcategory: "Channels",
  },
  {
    id: "TC03752",
    query: "what hr policies are available",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC04425",
    query: "Is Rajkot Class I or Class Two for travel policy?",
    exactAnswer: `**Rajkot** is classified as a **Class II city** under the Domestic Travel Policy.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["Rajkot", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "City Classification",
  },
  {
    id: "TC05032",
    query: "Is POSH applicable at office parties? in detail",
    exactAnswer: `**Yes.** POSH covers the **Extended Workplace** which includes:

• Office parties
• Off-sites / Client meetings
• Training sessions / Outbound trainings
• Travel for office purposes
• Any place visited in the course of employment
• A dwelling place or house

*Source: POSH Policy, Page 2*`,
    keyFacts: ["office parties", "off-sites", "travel", "extended workplace"],
    source: "POSH Policy",
    page: 2,
    category: "POSH",
    subcategory: "Scope",
  },
  {
    id: "TC01593",
    query: "hi, what is the per km rate for two-wheeler?",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC05720",
    query: "What is the driver wage reimbursement during relocation?",
    exactAnswer: `Driver wages during relocation:

• For **8 hours trip**: ₹600/-
• **After 8 hours**: ₹50/- per hour
• **Food**: Max ₹200/- per meal

*Source: Joining Policy, Page 1*`,
    keyFacts: ["600", "50 per hour", "200 per meal"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Driver Wages",
  },
  {
    id: "TC04780",
    query: "What actions can AIC recommend? please tell me",
    exactAnswer: `If the allegation is proved, the AIC may recommend:

• Written warning or apology
• Reprimand/Censure
• Withholding promotion or pay increment
• **Termination** from service
• Counselling session
• Community service
• **Monetary compensation**

*Source: POSH Policy, Page 8*`,
    keyFacts: ["termination", "monetary compensation", "written warning"],
    source: "POSH Policy",
    page: 8,
    category: "POSH",
    subcategory: "Disciplinary Actions",
  },
  {
    id: "TC01688",
    query: "Will I face retaliation for reporting? in detail",
    exactAnswer: `**Yes.** Arvind guarantees:

• **Complete confidentiality** — your identity will not be disclosed
• **No retaliation** — victimization will be treated as a serious disciplinary matter
• **Protection** — if victimized, file a written complaint to the Committee Chairman

*Source: Whistleblower Policy, Pages 4-5, Sections 9-10*`,
    keyFacts: ["confidentiality", "no retaliation", "protection"],
    source: "Whistleblower Policy",
    page: 4,
    category: "Whistleblower",
    subcategory: "Protection",
  },
  {
    id: "TC05786",
    query: "M3 lodging and boarding Class Three",
    exactAnswer: `For **M3** in **Class III** cities:

| Type | Limit |
|---|---|
| Lodging (hotel) | ₹4000/day |
| Boarding (food) | ₹800/day |

All limits include GST. Per 24-hour period.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["4000", "800", "M3", "Class III"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Combined Limits",
  },
  {
    id: "TC00305",
    query: "What is the brokerage reimbursement on joining? as per policy",
    exactAnswer: `Brokerage: **One month's rent** is reimbursed against a brokerage receipt. This benefit is available **only once** during the employee's employment with Arvind, and is available for a **maximum of 1 year** from the date of joining.

*Source: Joining Policy, Page 2*`,
    keyFacts: ["one month rent", "only once", "1 year"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Brokerage",
  },
  {
    id: "TC03238",
    query: "hi, what is the per km rate for four-wheeler?",
    exactAnswer: `For personal **four-wheeler (car)**, the reimbursement is **₹10.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["10.00", "four-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC00401",
    query: "hi, what is the ethics helpline email?",
    exactAnswer: `The Ethics Helpline email is: **arvind@ethicshelpline.in**

This is managed by KPMG on behalf of Arvind.

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["arvind@ethicshelpline.in"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC03406",
    query: "What HR policies are available? in detail",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00177",
    query: "Job rotation allowance kitna milega E2",
    exactAnswer: `For **E2**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹5,49,000 |
| Monthly | ₹45,750 |
| MAB: Tier 2 → Tier 1 (15%) | ₹6,863/month |
| MAB: Discretionary (5%) | ₹2,288/month |
| Settling-In Assistance (SIA) | ₹10,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["6,863", "10,000", "E2"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC00440",
    query: "How do I file a sexual harassment complaint? in detail",
    exactAnswer: `You can file a complaint through:

1. **Supervisor / Reporting Manager** (any trusted person in hierarchy)
2. **Business Unit HR Head**
3. **Whistleblowing channels:**
   - 📞 Hotline: 18002008301
   - 📧 Email: arvind@ethicshelpline.in
   - 🌐 Portal: www.in.kpmg.com/ethicshelpline/arvind/

Complaints must be in **writing or email** with your signature. **Anonymous complaints are NOT accepted by AIC.**

*Source: POSH Policy, Page 5*`,
    keyFacts: ["AIC", "writing", "18002008301", "ethicshelpline"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Complaint Filing",
  },
  {
    id: "TC01752",
    query: "hi, how to raise a whistleblower complaint?",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC03594",
    query: "Kya hai boarding limit for BMH3 in Class III?",
    exactAnswer: `For **BMH3, H4, H5, H6**, the boarding (food) limit in Class III cities is **₹1000 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["1000", "boarding", "Class III"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Boarding Limits",
  },
  {
    id: "TC03760",
    query: "POSH helpline number in detail",
    exactAnswer: `The POSH/Ethics Helpline toll-free number is **18002008301**.

*Source: POSH Policy, Page 5*`,
    keyFacts: ["18002008301"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Contact",
  },
  {
    id: "TC03331",
    query: "hi, whistleblower reporting channels",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC01025",
    query: "What is the mobility allowance for M1?",
    exactAnswer: `For **M1**, the Mobility Adjustment Benefit (MAB) details are:

| Metric | Amount |
|---|---|
| Annual Median Salary | ₹8,52,000 |
| Monthly | ₹71,000 |
| MAB: Tier 2 → Tier 1 (15%) | ₹10,650/month |
| MAB: Discretionary (5%) | ₹3,550/month |
| Settling-In Assistance (SIA) | ₹15,000 one-time |

MAB is paid for **12 months** and merged into CTC after completion of 1 year.

*Source: Talent Mobility Policy, Page 7*`,
    keyFacts: ["10,650", "15,000", "M1"],
    source: "Talent Mobility Policy",
    page: 7,
    category: "Talent Mobility",
    subcategory: "MAB",
  },
  {
    id: "TC03418",
    query: "Can men file POSH complaints? in detail",
    exactAnswer: `**Yes.** The POSH policy is **gender neutral** and covers **all genders** — men, women, and transgender individuals. It also prohibits **same-sex harassment**.

*Source: POSH Policy, Page 5*`,
    keyFacts: ["gender neutral", "all genders", "transgender", "same-sex"],
    source: "POSH Policy",
    page: 5,
    category: "POSH",
    subcategory: "Scope",
  },
  {
    id: "TC04372",
    query: "Can you help me understand: Relocation household goods reimbursement",
    exactAnswer: `Transportation of household goods on joining:

• **Less than 700 km**: Maximum ₹50 per km or Actuals (whichever is **lesser**) + Income tax gross-up
• **More than 700 km**: Maximum ₹60 per km or Actuals (whichever is **lesser**) + Income tax gross-up

*Source: Joining Policy, Page 1*`,
    keyFacts: ["50 per km", "60 per km", "700 km", "lesser"],
    source: "Joining Policy",
    page: 1,
    category: "Joining Policy",
    subcategory: "Relocation",
  },
  {
    id: "TC03478",
    query: "Can you help me understand: How do I report unethical behaviour?",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
  {
    id: "TC01176",
    query: "M3 lodging and boarding Class II as per policy",
    exactAnswer: `For **M3** in **Class II** cities:

| Type | Limit |
|---|---|
| Lodging (hotel) | ₹5000/day |
| Boarding (food) | ₹1000/day |

All limits include GST. Per 24-hour period.

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["5000", "1000", "M3", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Combined Limits",
  },
  {
    id: "TC02670",
    query: "ethics helpline website url",
    exactAnswer: `The Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["kpmg.com/ethicshelpline/arvind"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC02331",
    query: "hi, what hr policies are available?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC00556",
    query: "Can you help me understand: What is the boarding limit for E1 in Class II?",
    exactAnswer: `For **E1** (M1, MT, E2, GET, E1, OT group), the boarding (food) limit in Class II cities is **₹800 per day** (inclusive of GST).

*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    keyFacts: ["800", "boarding", "E1", "Class II"],
    source: "Domestic Travel Policy",
    page: 7,
    category: "Domestic Travel",
    subcategory: "Boarding Limits",
  },
  {
    id: "TC04522",
    query: "What channels can I use to raise a complaint? please tell me",
    exactAnswer: `You can raise a grievance through any of these channels:

1. **Immediate HR Representative (BUHR)**
2. **Line Manager or Supervisor**
3. **Head of Department (HOD)**
4. **Ethics Helpline:**
   - 🌐 Web: www.in.kpmg.com/ethicshelpline/arvind
   - 📞 Toll-Free: 1800 200 8301
   - 📧 Email: arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Grievance Mechanism Policy, Page 2*`,
    keyFacts: ["BUHR", "1800 200 8301", "ethicshelpline"],
    source: "Grievance Mechanism Policy",
    page: 2,
    category: "Grievance",
    subcategory: "Channels",
  },
  {
    id: "TC00902",
    query: "How much is reimbursed for bike travel? as per policy",
    exactAnswer: `For personal **two-wheeler (bike/scooter)**, the reimbursement is **₹5.00 per km**.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
    keyFacts: ["5.00", "two-wheeler", "per km"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Per Km Rate",
  },
  {
    id: "TC00220",
    query: "What is the time limit kitna hai to file a POSH complaint?",
    exactAnswer: `A complaint must be filed **within 3 months from the date of the incident** (or last incident in case of a series). This can be extended by a further **3 months** if the AIC is satisfied with the reason for delay.

*Source: POSH Policy, Page 6*`,
    keyFacts: ["3 months", "extended"],
    source: "POSH Policy",
    page: 6,
    category: "POSH",
    subcategory: "Timeline",
  },
  {
    id: "TC02153",
    query: "Can you help me understand: Arvind toll free helpline",
    exactAnswer: `The Ethics Helpline toll-free number is: **1800 200 8301** (also listed as 18002008301 in some policies).

*Source: Multiple policies — Whistleblower, POSH, Grievance, Gender*`,
    keyFacts: ["1800 200 8301"],
    source: "Multiple Policies",
    page: 0,
    category: "Contact Info",
    subcategory: "Ethics Helpline",
  },
  {
    id: "TC01314",
    query: "what can i report under the whistleblower policy",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC05221",
    query: "hi, list all arvind hr policies",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC04788",
    query: "hi, shared vehicle conveyance claim",
    exactAnswer: `If more than one person travels in the same vehicle, **only the individual who actually incurred the cost** can claim reimbursement — not both travellers.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(v)*`,
    keyFacts: ["only the individual", "actually incurred"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Rules",
  },
  {
    id: "TC04890",
    query: "How long does it take to acknowledge a grievance? please tell me",
    exactAnswer: `Your grievance will be **acknowledged within 2 working days** of receipt (where your identity is known).

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["2 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC05776",
    query: "According to company policy, who do i contact for gender bias issues?",
    exactAnswer: `Report gender discrimination through:

1. **First Level**: HR Department (BUHR)
2. **Second Level**: Line Manager
3. **Third Level**: Head of Department (HOD)
4. **Fourth Level**: Ethics Helpline
   - 🌐 www.in.kpmg.com/ethicshelpline/arvind
   - 📞 1800 200 8301
   - 📧 arvind@ethicshelpline.in
5. **Group Ethics Officer**

*Source: Gender Policy, Page 3*`,
    keyFacts: ["BUHR", "1800 200 8301", "Ethics Helpline"],
    source: "Gender Policy",
    page: 3,
    category: "Gender Policy",
    subcategory: "Complaint",
  },
  {
    id: "TC02253",
    query: "How long after incident can I file POSH complaint? as per policy",
    exactAnswer: `A complaint must be filed **within 3 months from the date of the incident** (or last incident in case of a series). This can be extended by a further **3 months** if the AIC is satisfied with the reason for delay.

*Source: POSH Policy, Page 6*`,
    keyFacts: ["3 months", "extended"],
    source: "POSH Policy",
    page: 6,
    category: "POSH",
    subcategory: "Timeline",
  },
  {
    id: "TC00126",
    query: "Types of whistleblower complaints in detail",
    exactAnswer: `You can report:

• Bribery and corruption
• Procurement/tendering fraud
• Misappropriation/theft of company assets
• False invoicing
• Fraudulent financial reporting
• Workplace harassment
• Discrimination
• Health, safety, environment violations
• Breach of compliance requirements
• Employee negligence

*Source: Whistleblower Policy, Pages 3-4, Section 5*`,
    keyFacts: ["bribery", "fraud", "harassment", "corruption"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Coverage",
  },
  {
    id: "TC00491",
    query: "Are per km rates same everywhere?",
    exactAnswer: `**Yes.** The local conveyance per-km rates (₹10/km for four-wheeler, ₹5/km for two-wheeler) are **applicable across India** for all grades.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(iv)*`,
    keyFacts: ["across India", "all grades"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Applicability",
  },
  {
    id: "TC06117",
    query: "I want to know what HR policies are available?",
    exactAnswer: `Arvind Limited has the following HR policies:

1. **Domestic Travel Policy** (ARV|EOP_DTP|003|270723)
2. **Local Conveyance Policy** (ARV|COR|EOP_LCP|002|010722)
3. **POSH Policy** (ARV|ELC_SHA|008|010422)
4. **Whistleblower Policy**
5. **Grievance Mechanism Policy** (ARV|COM_GRM|001|260725)
6. **Gender Policy** (ARV|COM_GENP|001|260725)
7. **Talent Mobility Policy**
8. **Joining Policy**`,
    keyFacts: ["Domestic Travel", "POSH", "Whistleblower", "Grievance"],
    source: "Multiple Policies",
    page: 0,
    category: "Policy Overview",
    subcategory: "List",
  },
  {
    id: "TC05399",
    query: "What happens if I leave within 1 year of joining? please tell me",
    exactAnswer: `If you **quit within 1 year of joining**, the following will be **recovered in your Full & Final settlement**:

• Joining Bonus
• Relocation Expenses
• Notice Pay Buyout
• Variable Pay Reimbursement (including brokerage)

*Source: Joining Policy, Page 2*`,
    keyFacts: ["1 year", "Full & Final", "recovered", "Joining Bonus"],
    source: "Joining Policy",
    page: 2,
    category: "Joining Policy",
    subcategory: "Recovery",
  },
  {
    id: "TC05746",
    query: "Are per km rates same everywhere? as per policy",
    exactAnswer: `**Yes.** The local conveyance per-km rates (₹10/km for four-wheeler, ₹5/km for two-wheeler) are **applicable across India** for all grades.

*Source: Local Conveyance Policy, Page 1, Section 4(b)(iv)*`,
    keyFacts: ["across India", "all grades"],
    source: "Local Conveyance Policy",
    page: 1,
    category: "Local Conveyance",
    subcategory: "Applicability",
  },
  {
    id: "TC06419",
    query: "hi, how many days to investigate a grievance?",
    exactAnswer: `The investigation should be **completed within 10 working days** wherever possible.

*Source: Grievance Mechanism Policy, Page 3*`,
    keyFacts: ["10 working days"],
    source: "Grievance Mechanism Policy",
    page: 3,
    category: "Grievance",
    subcategory: "Timelines",
  },
  {
    id: "TC01549",
    query: "Can you help me understand: Gender policy applicability",
    exactAnswer: `The Gender Policy applies to **all employees of Arvind Ltd.**, including:
• Full-time employees
• Part-time employees
• Contract staff
• Interns
• Consultants
• Third-party partners engaged in business operations

*Source: Gender Policy, Page 2*`,
    keyFacts: ["full-time", "interns", "consultants", "third-party"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Applicability",
  },
  {
    id: "TC01766",
    query: "Who does the gender policy apply to? in detail",
    exactAnswer: `The Gender Policy applies to **all employees of Arvind Ltd.**, including:
• Full-time employees
• Part-time employees
• Contract staff
• Interns
• Consultants
• Third-party partners engaged in business operations

*Source: Gender Policy, Page 2*`,
    keyFacts: ["full-time", "interns", "consultants", "third-party"],
    source: "Gender Policy",
    page: 2,
    category: "Gender Policy",
    subcategory: "Applicability",
  },
  {
    id: "TC03300",
    query: "Can a trainee raise a POSH complaint?",
    exactAnswer: `**Yes.** The POSH Policy covers all persons employed at Arvind on any basis — including **trainees, apprentices, probationers, contract workers**, and others. Trainees can file complaints.

*Source: POSH Policy, Page 1*`,
    keyFacts: ["trainees", "probationers", "contract workers"],
    source: "POSH Policy",
    page: 1,
    category: "POSH",
    subcategory: "Scope",
  },
  {
    id: "TC02727",
    query: "Whistleblower reporting channels as per policy",
    exactAnswer: `Report through any of these channels:

• 🌐 **Web Portal**: www.in.kpmg.com/ethicshelpline/arvind
• 📞 **Toll-Free**: 18002008301
• 📧 **Email**: arvind@ethicshelpline.in

*Source: Whistleblower Policy, Page 3, Section 6*`,
    keyFacts: ["18002008301", "ethicshelpline", "kpmg"],
    source: "Whistleblower Policy",
    page: 3,
    category: "Whistleblower",
    subcategory: "Channels",
  },
];

export const TOTAL_TEST_CASES = 6419;