import type { FullTest } from "./fullTestSuite";

const CAPABILITY_TARGETS = {
  "HRIS Transactions": 40,
  "Payroll Discrepancy": 24,
  "Case Continuations": 24,
  "Cross Policy Synthesis": 24,
  "Manager Support": 24,
  "Recruiting Workflows": 24,
  "Multilingual HR": 16,
  "Document Proofs": 16,
  "Ambiguous Queries": 24,
  "Workflow Completion": 24,
} as const;

const ENTERPRISE_PREFIXES = [
  "",
  "Please help with ",
  "Can you handle ",
  "Need support for ",
];

const ENTERPRISE_SUFFIXES = [
  "",
  " right now",
  " for me",
  " with next steps",
];

function normalizeSpaces(value: string) {
  return value.replace(/\s+/g, " ").trim();
}

function makeVariantQuery(baseQuery: string, variantIndex: number) {
  const clean = normalizeSpaces(baseQuery).replace(/[?!.]+$/g, "");
  const prefix = ENTERPRISE_PREFIXES[variantIndex % ENTERPRISE_PREFIXES.length];
  const suffix = ENTERPRISE_SUFFIXES[Math.floor(variantIndex / ENTERPRISE_PREFIXES.length) % ENTERPRISE_SUFFIXES.length];
  return `${normalizeSpaces(`${prefix}${clean}${suffix}`)}?`;
}

const DOCUMENT_PROOF_ASSET = {
  id: "doc_joining_001",
  name: "Joining Policy- Arvind Limited.pdf",
  content:
    "Reimbursements: Joining Expense (Notice Pay Buyout / Variable Pay / Joining Bonus). The expenses can be claimed within One Year from the date of joining of the employee. Brokerage: One month rent reimbursed against receipt.",
};

const ENTERPRISE_BASE_TESTS: FullTest[] = [
  {
    id: "ENT0001",
    query: "Apply leave for next Friday",
    exactAnswer: `I can help you prepare a leave request for next Friday with **Riya Shah** as approver and the **Leave & Attendance** route. Current available leave is **28.5 days**.`,
    keyFacts: ["Riya Shah", "Leave & Attendance", "28.5"],
    source: "Leave Workflow Assistant",
    page: 0,
    category: "HRIS Transactions",
    subcategory: "Leave Application",
    userUid: "local-user-001",
  },
  {
    id: "ENT0002",
    query: "Correct my missing punch for yesterday",
    exactAnswer: `Attendance regularization should be raised with **Riya Shah** as approver. Include the date, in/out time, and a short note.`,
    keyFacts: ["attendance regularization", "Riya Shah", "in/out time"],
    source: "Attendance Workflow Assistant",
    page: 0,
    category: "HRIS Transactions",
    subcategory: "Attendance Correction",
    userUid: "local-user-001",
  },
  {
    id: "ENT0003",
    query: "Download my payslip PDF",
    exactAnswer: `The latest payslip snapshot is for **April 2026** with **₹142,350** net pay. The chatbot should route the user to the payroll or ESS document path for the full PDF.`,
    keyFacts: ["April 2026", "142,350", "PDF"],
    source: "Payslip Document Assistant",
    page: 0,
    category: "HRIS Transactions",
    subcategory: "Payslip Download",
    userUid: "local-user-001",
  },
  {
    id: "ENT0004",
    query: "Update my dependent details",
    exactAnswer: `A dependent-details update case should be created with **Benefits Desk** routing, an SLA, and a checklist for dependent proof and enrollment documents.`,
    keyFacts: ["Benefits Desk", "dependent", "SLA"],
    source: "Employee Data Change Workflow",
    page: 0,
    category: "HRIS Transactions",
    subcategory: "Dependent Update",
    userUid: "local-user-001",
  },
  {
    id: "ENT0005",
    query: "Why is my April net pay lower than March?",
    exactAnswer: `The current HRIS snapshot shows **April 2026** and **March 2026** net pay are both **₹142,350**, so no lower April amount is visible in the available data.`,
    keyFacts: ["April 2026", "March 2026", "142,350"],
    source: "Payroll Comparison Assistant",
    page: 0,
    category: "Payroll Discrepancy",
    subcategory: "Month Comparison",
    userUid: "local-user-001",
  },
  {
    id: "ENT0006",
    query: "Why was PF deducted twice?",
    exactAnswer: `PF-deduction questions should be treated as **high-risk payroll** topics, routed to **Payroll Operations**, and answered with a checklist of payslip month and screenshot details.`,
    keyFacts: ["high-risk payroll", "Payroll Operations", "screenshot"],
    source: "Payroll Safe-Handling Workflow",
    page: 0,
    category: "Payroll Discrepancy",
    subcategory: "PF Investigation",
    userUid: "local-user-001",
  },
  {
    id: "ENT0007",
    query: "I raised a grievance and my manager retaliated, what now?",
    exactAnswer: `This should trigger a **confidential grievance retaliation** follow-up routed to **BUHR** with immediate documentation of the retaliation details.`,
    keyFacts: ["confidential", "grievance retaliation", "BUHR"],
    source: "Employee Relations Workflow",
    page: 0,
    category: "Case Continuations",
    subcategory: "Retaliation Follow-up",
    userUid: "local-user-001",
  },
  {
    id: "ENT0008",
    query: "I moved cities, my grade changed, and my reimbursement was rejected, explain all impacts",
    exactAnswer: `The assistant should compare the mobility and joining policy support, explain that profile changes affect grade/location-based guidance, and route reimbursement rejection to the correct HR workflow instead of guessing.`,
    keyFacts: ["mobility", "joining policy", "reimbursement"],
    source: "Cross-Policy Comparison Assistant",
    page: 0,
    category: "Case Continuations",
    subcategory: "Multi-factor Explanation",
    userUid: "local-user-001",
  },
  {
    id: "ENT0009",
    query: "Compare joining relocation benefits vs talent mobility relocation benefits",
    exactAnswer: `The chatbot should explain that **Joining Policy** supports onboarding relocation, while **Talent Mobility Policy** supports internal transfer or rotation through **MAB** and **SIA**.`,
    keyFacts: ["Joining Policy", "Talent Mobility Policy", "MAB", "SIA"],
    source: "Cross-Policy Comparison Assistant",
    page: 0,
    category: "Cross Policy Synthesis",
    subcategory: "Benefit Comparison",
    userUid: "local-user-001",
  },
  {
    id: "ENT0010",
    query: "If I transfer and resign within a year, what gets recovered?",
    exactAnswer: `The clearest recovery rule is under the **Joining Policy** for quitting within **1 year**, including **Joining Bonus**, **Relocation Expenses**, **Notice Pay Buyout**, and **Variable Pay Reimbursement including brokerage**.`,
    keyFacts: ["1 year", "Joining Bonus", "Relocation Expenses", "brokerage"],
    source: "Cross-Policy Recovery Assistant",
    page: 0,
    category: "Cross Policy Synthesis",
    subcategory: "Recovery Logic",
    userUid: "local-user-001",
  },
  {
    id: "ENT0011",
    query: "Show leave risk and pending actions for my team",
    exactAnswer: `Manager view should show **3** team members reviewed, **1** leave risk flagged, and about **92%** average attendance with the flagged employee named.`,
    keyFacts: ["3", "1", "92", "Jane Smith"],
    source: "Manager Service Insights",
    page: 0,
    category: "Manager Support",
    subcategory: "Leave Risk",
    userUid: "local-manager-001",
  },
  {
    id: "ENT0012",
    query: "Which team members need approval attention this week?",
    exactAnswer: `The manager watchlist should call out **Jane Smith** being on leave and **John Doe** having a pending travel follow-up.`,
    keyFacts: ["Jane Smith", "John Doe", "pending"],
    source: "Manager Approval Watchlist",
    page: 0,
    category: "Manager Support",
    subcategory: "Approval Watchlist",
    userUid: "local-manager-001",
  },
  {
    id: "ENT0013",
    query: "Screen this candidate for an HR operations analyst role",
    exactAnswer: `Candidate screening should assess **HR operations**, **HRIS coordination**, **SLA-driven support**, and risk checks around process discipline and data accuracy.`,
    keyFacts: ["HR operations", "HRIS", "SLA", "data accuracy"],
    source: "Recruiting Workflow Assistant",
    page: 0,
    category: "Recruiting Workflows",
    subcategory: "Candidate Screening",
    userUid: "local-hrbp-001",
  },
  {
    id: "ENT0014",
    query: "Schedule 4 candidate interviews next week",
    exactAnswer: `Interview scheduling should use **30-45 minute** slots, panel confirmation, consolidated invites, and reminders for the **4 candidate interviews**.`,
    keyFacts: ["30-45 minute", "4 candidate interviews", "panel", "reminders"],
    source: "Recruiting Scheduling Assistant",
    page: 0,
    category: "Recruiting Workflows",
    subcategory: "Interview Scheduling",
    userUid: "local-hrbp-001",
  },
  {
    id: "ENT0015",
    query: "Suggest interview questions for an HR analyst role",
    exactAnswer: `The assistant should suggest questions covering **payroll discrepancy investigation**, **HR data accuracy**, **employee support queues**, and **policy compliance**.`,
    keyFacts: ["payroll discrepancy", "HR data accuracy", "employee support", "policy compliance"],
    source: "Recruiting Interview Assistant",
    page: 0,
    category: "Recruiting Workflows",
    subcategory: "Interview Questions",
    userUid: "local-hrbp-001",
  },
  {
    id: "ENT0016",
    query: "meri leave balance batao",
    exactAnswer: `The chatbot should still return the employee leave snapshot with **8.5 casual**, **15 earned**, **4 sick**, and **1 comp off** even for a Hindi-style query.`,
    keyFacts: ["8.5", "15", "4", "1"],
    source: "Personalized HRIS Snapshot",
    page: 0,
    category: "Multilingual HR",
    subcategory: "Hindi Query",
    userUid: "local-user-001",
    language: "hindi",
  },
  {
    id: "ENT0017",
    query: "maru payslip bataavo",
    exactAnswer: `The chatbot should still return the latest payslip snapshot with **April 2026** and **₹142,350** net pay for a Gujarati-style query.`,
    keyFacts: ["April 2026", "142,350"],
    source: "Personalized HRIS Snapshot",
    page: 0,
    category: "Multilingual HR",
    subcategory: "Gujarati Query",
    userUid: "local-user-001",
    language: "gujarati",
  },
  {
    id: "ENT0018",
    query: "Which uploaded file proves the joining expense claim deadline?",
    exactAnswer: `The chatbot should point to **Joining Policy- Arvind Limited.pdf** and quote the excerpt saying the expenses can be claimed within **One Year** from the date of joining.`,
    keyFacts: ["Joining Policy- Arvind Limited.pdf", "One Year", "date of joining"],
    source: "Uploaded Knowledge Proof Assistant",
    page: 0,
    category: "Document Proofs",
    subcategory: "Uploaded Asset Proof",
    userUid: "local-user-001",
    knowledgeAssets: [DOCUMENT_PROOF_ASSET],
  },
  {
    id: "ENT0019",
    query: "salary issue",
    exactAnswer: `The chatbot should clarify whether the salary issue is about **payslip**, **tax deduction**, **PF**, or **net pay change** instead of guessing.`,
    keyFacts: ["payslip", "tax deduction", "PF", "net pay"],
    source: "Ambiguity Clarifier",
    page: 0,
    category: "Ambiguous Queries",
    subcategory: "Salary Triage",
    userUid: "local-user-001",
  },
  {
    id: "ENT0020",
    query: "my reimbursement problem",
    exactAnswer: `The chatbot should ask whether the reimbursement problem is **travel**, **local conveyance**, **joining relocation**, or **payroll** related.`,
    keyFacts: ["travel", "local conveyance", "joining relocation", "payroll"],
    source: "Ambiguity Clarifier",
    page: 0,
    category: "Ambiguous Queries",
    subcategory: "Reimbursement Triage",
    userUid: "local-user-001",
  },
  {
    id: "ENT0021",
    query: "Create a grievance case, assign it, and tell me the SLA",
    exactAnswer: `Workflow completion should create a case, show the **route**, **assignment group**, and **SLA**, and confirm that the item can now be tracked to closure.`,
    keyFacts: ["route", "assignment group", "SLA", "tracked"],
    source: "Workflow Automation Assistant",
    page: 0,
    category: "Workflow Completion",
    subcategory: "Case Routing",
    userUid: "local-user-001",
  },
  {
    id: "ENT0022",
    query: "Create HR ticket for my payroll issue and notify approver",
    exactAnswer: `The chatbot should start the workflow, provide a **Case ID**, route it for review, and mention the approver/assignment path and **SLA** instead of stopping at generic guidance.`,
    keyFacts: ["Case ID", "route", "SLA", "approver"],
    source: "Workflow Automation Assistant",
    page: 0,
    category: "Workflow Completion",
    subcategory: "Payroll Routing",
    userUid: "local-user-001",
  },
];

function buildCategorySuite(category: keyof typeof CAPABILITY_TARGETS) {
  const baseTests = ENTERPRISE_BASE_TESTS.filter((test) => test.category === category);
  const targetCount = CAPABILITY_TARGETS[category];

  if (baseTests.length >= targetCount) {
    return baseTests.slice(0, targetCount);
  }

  const tests: FullTest[] = [...baseTests];
  let extraIndex = 0;

  while (tests.length < targetCount) {
    const seed = baseTests[extraIndex % baseTests.length];
    const variantRound = Math.floor(extraIndex / baseTests.length) + 1;

    tests.push({
      ...seed,
      id: `${seed.id}-E${variantRound}-${(extraIndex % baseTests.length) + 1}`,
      query: makeVariantQuery(seed.query, variantRound),
    });

    extraIndex += 1;
  }

  return tests;
}

export const ENTERPRISE_CAPABILITY_BENCHMARK_SUITE: FullTest[] = (
  Object.keys(CAPABILITY_TARGETS) as Array<keyof typeof CAPABILITY_TARGETS>
).flatMap((category) => buildCategorySuite(category)).map((test, index) => ({
  ...test,
  id: `EC${String(index + 1).padStart(4, "0")}`,
}));

export const ENTERPRISE_CAPABILITY_BENCHMARK_COUNT = ENTERPRISE_CAPABILITY_BENCHMARK_SUITE.length;
