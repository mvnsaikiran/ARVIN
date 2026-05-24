import { POLICY_META } from "../data/policies";
import { normalizeEmployeeChatText } from "./queryNormalization";

const BACKEND_BASE_URL = "http://127.0.0.1:8001";

export type ExperienceRole = "employee" | "manager" | "hrbp" | "admin";
export type SupportedLanguage = "english" | "hindi" | "gujarati";

export interface EmployeeProfile {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string | null;
  role: ExperienceRole;
  department: string;
  businessUnit: string;
  grade: string;
  location: string;
  employeeId: string;
  managerName: string;
  managerEmail: string;
  languagePreference: SupportedLanguage;
  workMode: "Plant" | "Hybrid" | "Office" | "Field";
  companyCar: boolean;
  directReports?: string[];
}

export interface LeaveBalances {
  casual: number;
  earned: number;
  sick: number;
  compOff: number;
}

export interface Payslip {
  month: string;
  netPay: number;
  grossPay: number;
  status: "Paid" | "Queued";
}

export interface BenefitSummary {
  health: string;
  dental: string;
  enrollmentStatus: string;
  retirement: string;
}

export interface ApproverChain {
  lineManager: string;
  buhr: string;
  finance: string;
  travelDesk: string;
}

export interface EmployeeRecord {
  profile: EmployeeProfile;
  leaveBalances: LeaveBalances;
  payStubs: Payslip[];
  benefits: BenefitSummary;
  approverChain: ApproverChain;
  attendanceStatus: "Present" | "On Leave" | "WFH";
  attendanceRate: number;
  travelClaimStatus: string;
  reimbursementYtd: number;
  activeCases: number;
}

export interface HRTicket {
  id: string;
  kind: "hr_ticket" | "grievance" | "posh" | "whistleblower";
  serviceId: string;
  title: string;
  summary: string;
  confidentiality: "standard" | "confidential" | "strictly-confidential";
  route: string;
  status: "open" | "assigned" | "in_review" | "resolved";
  priority: "low" | "medium" | "high" | "critical";
  employeeUid: string;
  employeeName: string;
  employeeGrade: string;
  employeeLocation: string;
  assignedTo: string;
  assignmentGroup: string;
  slaHours: number;
  dueAt: number;
  transcriptExcerpt?: string;
  sourcePolicyId?: string;
  statusHistory: HRCaseTimelineEntry[];
  internalNotes: HRCaseNote[];
  employeeVisibleUpdates: HRCaseNote[];
  subtasks: HRCaseTask[];
  resolutionNotes?: string;
  reopenCount: number;
  createdAt: number;
  updatedAt: number;
}

type HRTicketCreationInput = Omit<
  HRTicket,
  "id" | "createdAt" | "updatedAt" | "status" | "serviceId" | "assignmentGroup" | "slaHours" | "dueAt" | "statusHistory" | "internalNotes" | "employeeVisibleUpdates" | "subtasks" | "reopenCount"
> & {
  status?: HRTicket["status"];
  serviceId?: string;
  assignmentGroup?: string;
  slaHours?: number;
  dueAt?: number;
  statusHistory?: HRCaseTimelineEntry[];
  internalNotes?: HRCaseNote[];
  employeeVisibleUpdates?: HRCaseNote[];
  subtasks?: HRCaseTask[];
  reopenCount?: number;
};

export interface HRCaseTimelineEntry {
  status: HRTicket["status"];
  actor: string;
  note: string;
  timestamp: number;
}

export interface HRCaseNote {
  id: string;
  author: string;
  note: string;
  visibility: "internal" | "employee";
  timestamp: number;
}

export interface HRCaseTask {
  id: string;
  title: string;
  owner: string;
  status: "todo" | "in_progress" | "done";
  dueAt: number;
}

export interface ServiceCatalogItem {
  id: string;
  title: string;
  category: "Leave" | "Payroll" | "Benefits" | "Data Change" | "Grievance" | "POSH" | "Mobility" | "Onboarding" | "Recruiting";
  summary: string;
  route: string;
  defaultAssignmentGroup: string;
  slaHours: number;
  defaultPriority: HRTicket["priority"];
  channels: string[];
  keywords: string[];
  prompts: string[];
}

export interface SelfServiceModule {
  id: string;
  title: string;
  category: "My HR" | "Payroll" | "Benefits" | "Attendance" | "Approvals";
  value: string;
  detail: string;
  actionLabel: string;
  prompt: string;
}

export interface ManagerInsight {
  id: string;
  title: string;
  value: string;
  tone: "neutral" | "good" | "watch" | "risk";
  detail: string;
  prompt: string;
}

export interface AnalyticsEvent {
  id: string;
  query: string;
  normalizedQuery: string;
  userUid: string;
  userRole: ExperienceRole;
  grade: string;
  location: string;
  responseType: string;
  policyId?: string;
  confidenceScore?: number;
  turnaroundMs?: number;
  escalated?: boolean;
  unresolved?: boolean;
  feedback?: 1 | 5;
  feedbackReason?: string;
  highRisk?: boolean;
  clarificationRequested?: boolean;
  usedLearningCase?: boolean;
  safetyMode?: "standard" | "sensitive" | "high_risk";
  timestamp: number;
}

export interface LearningCase {
  id: string;
  query: string;
  normalizedQuery: string;
  approvedAnswer: string;
  policyId?: string;
  source: "seed" | "feedback" | "resolved_case";
  confidence: number;
  createdAt: number;
  lastUsedAt?: number;
}

export interface PolicyAuditEntry {
  id: string;
  actor: string;
  action: string;
  note: string;
  timestamp: number;
}

export interface PolicyVersionSnapshot {
  version: number;
  title: string;
  content: string;
  status: string;
  updatedAt: number;
}

export interface PolicyGovernanceRecord {
  id: string;
  title: string;
  category: string;
  content: string;
  owner: string;
  approver: string;
  environment: "draft" | "staging" | "published";
  lifecycleStatus: "draft" | "in_review" | "approved" | "published" | "expired";
  effectiveDate: string;
  expiryDate: string;
  version: number;
  benchmarkRequired: boolean;
  benchmarkPassed: boolean;
  lastBenchmarkAccuracy: number;
  sourceDocumentName: string;
  updatedAt: number;
  auditTrail: PolicyAuditEntry[];
  previousVersions: PolicyVersionSnapshot[];
}

export interface GuidedJourney {
  id: string;
  title: string;
  description: string;
  prompt: string;
  category: string;
}

export interface EmployeeNudge {
  id: string;
  text: string;
  type: "alert" | "info" | "success";
}

export interface PolicyAcknowledgment {
  id: string;
  policyId: string;
  policyName: string;
  audience: string;
  completionRate: number;
  dueDate: string;
}

export interface ComplianceControl {
  id: string;
  title: string;
  status: "active" | "watch" | "needs-review";
  owner: string;
  detail: string;
}

export interface TalentWorkflow {
  id: string;
  title: string;
  stage: string;
  summary: string;
  actionLabel: string;
  prompt: string;
}

export interface ContentOpsTask {
  id: string;
  title: string;
  type: "upload" | "chunking" | "translation" | "benchmark" | "rollback";
  owner: string;
  status: "queued" | "in_progress" | "blocked" | "done";
  detail: string;
}

export interface ChannelExperience {
  id: string;
  name: string;
  state: "live" | "pilot" | "planned";
  summary: string;
}

export interface AIOpsSnapshot {
  benchmarkAccuracy: number;
  falseEscalationRate: number;
  followUpResolutionRate: number;
  unresolvedTopicCount: number;
  learningLoopCoverage: number;
  policyAccuracy: Array<{ policyId: string; policyName: string; score: number }>;
}

export interface AnalyticsSummary {
  totalInteractions: number;
  lowConfidenceCount: number;
  escalationCount: number;
  helpfulCount: number;
  notUsefulCount: number;
  unansweredQueries: string[];
  policyUsage: Array<{ policyId: string; policyName: string; count: number }>;
  gradeHotspots: Array<{ grade: string; count: number }>;
  locationHotspots: Array<{ location: string; count: number }>;
  confusionHotspots: Array<{ topic: string; count: number }>;
  riskSignals: Array<{ signal: string; count: number }>;
  learningCaseCount: number;
  resolutionLoopCoverage: number;
  falseEscalationRate: number;
  followUpResolutionRate: number;
  unresolvedTopicCount: number;
  policyAccuracy: Array<{ policyId: string; policyName: string; score: number }>;
}

const STORAGE_KEYS = {
  tickets: "arvind_hr_cases_v2",
  analytics: "arvind_hr_analytics_v2",
  governance: "arvind_hr_governance_v2",
  learning: "arvind_hr_learning_v1",
};

const SERVICE_CATALOG: ServiceCatalogItem[] = [
  {
    id: "svc_leave_attendance",
    title: "Leave and Attendance",
    category: "Leave",
    summary: "Balances, regularization, missing punches, and approval flow support.",
    route: "Manager + PayOps",
    defaultAssignmentGroup: "People Operations",
    slaHours: 24,
    defaultPriority: "medium",
    channels: ["Web", "Portal", "Teams"],
    keywords: ["leave", "attendance", "punch", "approver", "absent"],
    prompts: ["Show my leave balance and missing attendance items.", "Who is my approver for attendance regularization?"],
  },
  {
    id: "svc_payroll",
    title: "Payroll and Payslips",
    category: "Payroll",
    summary: "Payslips, net pay, payroll corrections, and deductions support.",
    route: "PayOps",
    defaultAssignmentGroup: "Payroll Operations",
    slaHours: 16,
    defaultPriority: "high",
    channels: ["Web", "Portal", "Email"],
    keywords: ["payslip", "salary", "payroll", "deduction", "net pay"],
    prompts: ["Show my latest payslip summary.", "Help me raise a payroll correction request."],
  },
  {
    id: "svc_benefits",
    title: "Benefits and Insurance",
    category: "Benefits",
    summary: "Medical, dental, PF, NPS, enrollment, and dependent coverage questions.",
    route: "Benefits Desk",
    defaultAssignmentGroup: "Benefits Operations",
    slaHours: 48,
    defaultPriority: "medium",
    channels: ["Web", "Portal", "Teams"],
    keywords: ["benefits", "insurance", "medical", "nps", "pf", "dependent"],
    prompts: ["Show my benefits enrollment status.", "What benefits are available for my grade?"],
  },
  {
    id: "svc_data_change",
    title: "Employee Data Change",
    category: "Data Change",
    summary: "Update personal details, bank account, address, or statutory data.",
    route: "HR Shared Services",
    defaultAssignmentGroup: "HR Shared Services",
    slaHours: 24,
    defaultPriority: "medium",
    channels: ["Portal", "Web", "Email"],
    keywords: ["address", "bank", "data change", "name change", "kyc"],
    prompts: ["I need to update my bank account details.", "How do I change my personal address in HR records?"],
  },
  {
    id: "svc_grievance",
    title: "Grievance Resolution",
    category: "Grievance",
    summary: "Formal grievance intake, acknowledgements, investigation, and resolution tracking.",
    route: "BUHR",
    defaultAssignmentGroup: "Employee Relations",
    slaHours: 8,
    defaultPriority: "high",
    channels: ["Web", "Ethics Helpline", "Email"],
    keywords: ["grievance", "complaint", "unfair", "issue", "escalation"],
    prompts: ["I need help filing a grievance.", "What is the grievance resolution timeline?"],
  },
  {
    id: "svc_posh",
    title: "POSH and Safe Workplace",
    category: "POSH",
    summary: "Confidential safe-reporting route, AIC intake, and retaliation guidance.",
    route: "AIC",
    defaultAssignmentGroup: "POSH Secretariat",
    slaHours: 4,
    defaultPriority: "critical",
    channels: ["Web", "Ethics Helpline", "Confidential"],
    keywords: ["posh", "harassment", "safe workplace", "retaliation", "gender"],
    prompts: ["I need confidential help with POSH reporting.", "What is the safe reporting route under POSH?"],
  },
  {
    id: "svc_mobility",
    title: "Mobility and Relocation",
    category: "Mobility",
    summary: "Relocation, transfer, travel, and joining benefits for moves and promotions.",
    route: "Mobility Desk",
    defaultAssignmentGroup: "Mobility Operations",
    slaHours: 48,
    defaultPriority: "medium",
    channels: ["Web", "Portal", "Teams"],
    keywords: ["mobility", "transfer", "relocation", "move", "travel"],
    prompts: ["Show relocation benefits for my grade.", "What happens if I move from Ahmedabad to Bangalore?"],
  },
  {
    id: "svc_onboarding",
    title: "Onboarding and Joining",
    category: "Onboarding",
    summary: "Offer-to-join checklist, day-one tasks, accommodation, and induction support.",
    route: "HR Shared Services",
    defaultAssignmentGroup: "Onboarding Cell",
    slaHours: 24,
    defaultPriority: "medium",
    channels: ["Web", "Portal", "Mobile"],
    keywords: ["joining", "onboarding", "new hire", "day one", "accommodation"],
    prompts: ["Show the joining and relocation benefits for my grade.", "What documents do I need for onboarding?"],
  },
  {
    id: "svc_recruiting",
    title: "Recruiting and Talent",
    category: "Recruiting",
    summary: "Candidate screening, interview scheduling, and internal mobility workflows.",
    route: "Talent Acquisition",
    defaultAssignmentGroup: "Talent Acquisition",
    slaHours: 24,
    defaultPriority: "medium",
    channels: ["Web", "Teams", "WhatsApp"],
    keywords: ["candidate", "interview", "recruiting", "job description", "internal mobility"],
    prompts: ["Generate a job description for an HR analyst role.", "Help schedule candidate interviews this week."],
  },
];

export let EMPLOYEE_RECORDS: EmployeeRecord[] = [
  {
    profile: {
      uid: "local-user-001",
      email: "saikiran@arvind.in",
      displayName: "Saikiran N",
      role: "employee",
      department: "HR Technology",
      businessUnit: "Denim",
      grade: "M2",
      location: "Ahmedabad",
      employeeId: "ARV-992381",
      managerName: "Riya Shah",
      managerEmail: "riya.shah@arvind.in",
      languagePreference: "english",
      workMode: "Hybrid",
      companyCar: true,
    },
    leaveBalances: { casual: 8.5, earned: 15, sick: 4, compOff: 1 },
    payStubs: [
      { month: "April 2026", netPay: 142350, grossPay: 188000, status: "Paid" },
      { month: "March 2026", netPay: 142350, grossPay: 188000, status: "Paid" },
    ],
    benefits: {
      health: "Platinum Global Core",
      dental: "Standard Coverage",
      enrollmentStatus: "Enrolled",
      retirement: "PF + NPS Active",
    },
    approverChain: {
      lineManager: "Riya Shah",
      buhr: "Ananya Rao",
      finance: "PayOps West",
      travelDesk: "Travel Desk Ahmedabad",
    },
    attendanceStatus: "Present",
    attendanceRate: 96,
    travelClaimStatus: "Last domestic claim settled on April 18",
    reimbursementYtd: 185200,
    activeCases: 0,
  },
  {
    profile: {
      uid: "local-manager-001",
      email: "riya.shah@arvind.in",
      displayName: "Riya Shah",
      role: "manager",
      department: "HR Technology",
      businessUnit: "Denim",
      grade: "M3",
      location: "Ahmedabad",
      employeeId: "ARV-774201",
      managerName: "Vikram Mehta",
      managerEmail: "vikram.mehta@arvind.in",
      languagePreference: "english",
      workMode: "Office",
      companyCar: false,
      directReports: ["local-user-001", "local-user-002", "local-user-003"],
    },
    leaveBalances: { casual: 6, earned: 12, sick: 3, compOff: 0 },
    payStubs: [
      { month: "April 2026", netPay: 181500, grossPay: 246000, status: "Paid" },
      { month: "March 2026", netPay: 181500, grossPay: 246000, status: "Paid" },
    ],
    benefits: {
      health: "Executive Family Plus",
      dental: "Enhanced Coverage",
      enrollmentStatus: "Enrolled",
      retirement: "PF + Gratuity Active",
    },
    approverChain: {
      lineManager: "Vikram Mehta",
      buhr: "Ananya Rao",
      finance: "Finance Controller West",
      travelDesk: "Travel Desk Ahmedabad",
    },
    attendanceStatus: "Present",
    attendanceRate: 94,
    travelClaimStatus: "No pending travel claims",
    reimbursementYtd: 242600,
    activeCases: 1,
  },
  {
    profile: {
      uid: "local-hrbp-001",
      email: "ananya.rao@arvind.in",
      displayName: "Ananya Rao",
      role: "hrbp",
      department: "Human Resources",
      businessUnit: "Corporate HR",
      grade: "M3H1",
      location: "Ahmedabad",
      employeeId: "ARV-661102",
      managerName: "Group CHRO Office",
      managerEmail: "chro.office@arvind.in",
      languagePreference: "english",
      workMode: "Office",
      companyCar: false,
      directReports: ["local-user-001", "local-manager-001"],
    },
    leaveBalances: { casual: 5, earned: 10, sick: 2, compOff: 0 },
    payStubs: [
      { month: "April 2026", netPay: 228200, grossPay: 310000, status: "Paid" },
      { month: "March 2026", netPay: 228200, grossPay: 310000, status: "Paid" },
    ],
    benefits: {
      health: "Leadership Family Elite",
      dental: "Enhanced Coverage",
      enrollmentStatus: "Enrolled",
      retirement: "PF + NPS Active",
    },
    approverChain: {
      lineManager: "Group CHRO Office",
      buhr: "Corporate BUHR",
      finance: "Finance Controller Corporate",
      travelDesk: "Travel Desk Ahmedabad",
    },
    attendanceStatus: "Present",
    attendanceRate: 97,
    travelClaimStatus: "Two approvals pending review",
    reimbursementYtd: 302900,
    activeCases: 3,
  },
  {
    profile: {
      uid: "local-user-002",
      email: "john.doe@arvind.in",
      displayName: "John Doe",
      role: "employee",
      department: "Design",
      businessUnit: "Denim",
      grade: "M1",
      location: "Bangalore",
      employeeId: "ARV-884512",
      managerName: "Riya Shah",
      managerEmail: "riya.shah@arvind.in",
      languagePreference: "english",
      workMode: "Hybrid",
      companyCar: false,
    },
    leaveBalances: { casual: 7, earned: 11, sick: 2, compOff: 0 },
    payStubs: [
      { month: "April 2026", netPay: 98500, grossPay: 132000, status: "Paid" },
    ],
    benefits: {
      health: "Core Family",
      dental: "Standard Coverage",
      enrollmentStatus: "Enrolled",
      retirement: "PF Active",
    },
    approverChain: {
      lineManager: "Riya Shah",
      buhr: "Ananya Rao",
      finance: "PayOps South",
      travelDesk: "Travel Desk Bangalore",
    },
    attendanceStatus: "Present",
    attendanceRate: 93,
    travelClaimStatus: "One receipt pending upload",
    reimbursementYtd: 96400,
    activeCases: 0,
  },
  {
    profile: {
      uid: "local-user-003",
      email: "jane.smith@arvind.in",
      displayName: "Jane Smith",
      role: "employee",
      department: "Engineering",
      businessUnit: "Fabric",
      grade: "E2",
      location: "Pune",
      employeeId: "ARV-883441",
      managerName: "Riya Shah",
      managerEmail: "riya.shah@arvind.in",
      languagePreference: "english",
      workMode: "Office",
      companyCar: false,
    },
    leaveBalances: { casual: 5, earned: 9, sick: 6, compOff: 1 },
    payStubs: [
      { month: "April 2026", netPay: 74500, grossPay: 99500, status: "Paid" },
    ],
    benefits: {
      health: "Core Individual",
      dental: "Standard Coverage",
      enrollmentStatus: "Enrolled",
      retirement: "PF Active",
    },
    approverChain: {
      lineManager: "Riya Shah",
      buhr: "Ananya Rao",
      finance: "PayOps West",
      travelDesk: "Travel Desk Pune",
    },
    attendanceStatus: "On Leave",
    attendanceRate: 88,
    travelClaimStatus: "No claims raised this quarter",
    reimbursementYtd: 40600,
    activeCases: 0,
  },
];

function hasWindow() {
  return (
    typeof window !== "undefined" &&
    typeof window.localStorage !== "undefined" &&
    typeof window.localStorage?.getItem === "function" &&
    typeof window.localStorage?.setItem === "function"
  );
}

function readStorage<T>(key: string, fallback: T): T {
  if (!hasWindow()) return fallback;
  try {
    const stored = window.localStorage.getItem(key);
    return stored ? JSON.parse(stored) as T : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage<T>(key: string, value: T) {
  if (!hasWindow()) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore localStorage failures in local demo mode.
  }
}

function makeAuditEntry(actor: string, action: string, note: string): PolicyAuditEntry {
  return {
    id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    actor,
    action,
    note,
    timestamp: Date.now(),
  };
}

const POLICY_EFFECTIVE_DATES: Record<string, string> = {
  "domestic-travel": "2023-07-27",
  "local-conveyance": "2022-07-01",
  "posh-policy": "2022-04-01",
  "grievance-mechanism": "2025-07-26",
  "gender-policy": "2025-07-26",
  "whistleblower": "2025-07-26",
  "joining-policy": "2025-01-01",
  "talent-mobility": "2025-01-01",
};

function buildSeedGovernance(): PolicyGovernanceRecord[] {
  return POLICY_META.map((policy, index) => ({
    id: policy.id,
    title: policy.name,
    category: policy.description.split(",")[0] || "Policy",
    content: `Operational record for ${policy.name}.`,
    owner: index % 2 === 0 ? "Ananya Rao" : "Corporate HR Operations",
    approver: index % 3 === 0 ? "Group CHRO Office" : "BUHR Governance Desk",
    environment: "published",
    lifecycleStatus: "published",
    effectiveDate: POLICY_EFFECTIVE_DATES[policy.id] ?? "",
    expiryDate: "",
    version: 3,
    benchmarkRequired: true,
    benchmarkPassed: true,
    lastBenchmarkAccuracy: 100,
    sourceDocumentName: policy.sourceDocumentName,
    updatedAt: Date.now() - index * 86400000,
    auditTrail: [
      makeAuditEntry("System", "benchmark", "Benchmark validation cleared above 95%."),
      makeAuditEntry("System", "publish", "Policy published to employee knowledge base."),
    ],
    previousVersions: [
      {
        version: 2,
        title: policy.name,
        content: `Previous snapshot for ${policy.name}.`,
        status: "published",
        updatedAt: Date.now() - (index + 3) * 86400000,
      },
    ],
  }));
}

function buildSeedTickets(): HRTicket[] {
  return [
    {
      id: "case_1001",
      kind: "grievance",
      serviceId: "svc_grievance",
      title: "Reimbursement approval delay",
      summary: "Employee reports repeated delay in local conveyance settlement.",
      confidentiality: "confidential",
      route: "BUHR",
      status: "in_review",
      priority: "medium",
      employeeUid: "local-user-001",
      employeeName: "Saikiran N",
      employeeGrade: "M2",
      employeeLocation: "Ahmedabad",
      assignedTo: "Ananya Rao",
      assignmentGroup: "Employee Relations",
      slaHours: 48,
      dueAt: Date.now() + 2 * 86400000,
      sourcePolicyId: "local-conveyance",
      statusHistory: [
        { status: "open", actor: "Employee", note: "Case created from chatbot escalation.", timestamp: Date.now() - 3 * 86400000 },
        { status: "assigned", actor: "Ananya Rao", note: "Assigned to BUHR review.", timestamp: Date.now() - 2 * 86400000 },
        { status: "in_review", actor: "Ananya Rao", note: "Finance route validation in progress.", timestamp: Date.now() - 86400000 },
      ],
      internalNotes: [
        { id: "note_case_1001_1", author: "Ananya Rao", note: "Check whether plant travel exception caused the settlement delay.", visibility: "internal", timestamp: Date.now() - 86400000 },
      ],
      employeeVisibleUpdates: [
        { id: "note_case_1001_emp", author: "BUHR", note: "Your grievance has been acknowledged and is under review.", visibility: "employee", timestamp: Date.now() - 2 * 86400000 },
      ],
      subtasks: [
        { id: "task_case_1001_1", title: "Validate route and receipts", owner: "PayOps West", status: "in_progress", dueAt: Date.now() + 12 * 3600000 },
        { id: "task_case_1001_2", title: "Confirm manager approval trail", owner: "BUHR", status: "todo", dueAt: Date.now() + 20 * 3600000 },
      ],
      reopenCount: 0,
      createdAt: Date.now() - 3 * 86400000,
      updatedAt: Date.now() - 86400000,
    },
    {
      id: "case_1002",
      kind: "posh",
      serviceId: "svc_posh",
      title: "Confidential POSH intake",
      summary: "Strictly confidential employee intake requiring AIC routing.",
      confidentiality: "strictly-confidential",
      route: "AIC",
      status: "assigned",
      priority: "critical",
      employeeUid: "local-user-003",
      employeeName: "Jane Smith",
      employeeGrade: "E2",
      employeeLocation: "Pune",
      assignedTo: "AIC Secretariat",
      assignmentGroup: "POSH Secretariat",
      slaHours: 8,
      dueAt: Date.now() + 8 * 3600000,
      sourcePolicyId: "posh-policy",
      statusHistory: [
        { status: "open", actor: "Employee", note: "Confidential intake logged.", timestamp: Date.now() - 5 * 86400000 },
        { status: "assigned", actor: "AIC Secretariat", note: "Assigned to confidential review route.", timestamp: Date.now() - 2 * 86400000 },
      ],
      internalNotes: [
        { id: "note_case_1002_1", author: "AIC Secretariat", note: "Restrict visibility to safe-handling group only.", visibility: "internal", timestamp: Date.now() - 2 * 86400000 },
      ],
      employeeVisibleUpdates: [
        { id: "note_case_1002_emp", author: "AIC Secretariat", note: "Your confidential concern has been safely routed.", visibility: "employee", timestamp: Date.now() - 2 * 86400000 },
      ],
      subtasks: [
        { id: "task_case_1002_1", title: "Confirm confidentiality controls", owner: "AIC Secretariat", status: "done", dueAt: Date.now() - 86400000 },
        { id: "task_case_1002_2", title: "Schedule protected intake review", owner: "AIC Secretariat", status: "in_progress", dueAt: Date.now() + 6 * 3600000 },
      ],
      reopenCount: 0,
      createdAt: Date.now() - 5 * 86400000,
      updatedAt: Date.now() - 2 * 86400000,
    },
  ];
}

function buildSeedAnalytics(): AnalyticsEvent[] {
  return [
    {
      id: "evt_seed_1",
      query: "What is the lodging limit for M3 in Class I?",
      normalizedQuery: "what is the lodging limit for m3 in class i",
      userUid: "local-user-001",
      userRole: "employee",
      grade: "M2",
      location: "Ahmedabad",
      responseType: "policy_details",
      policyId: "domestic-travel",
      confidenceScore: 0.98,
      turnaroundMs: 510,
      timestamp: Date.now() - 86400000,
    },
    {
      id: "evt_seed_2",
      query: "I need help filing a grievance",
      normalizedQuery: "i need help filing a grievance",
      userUid: "local-user-001",
      userRole: "employee",
      grade: "M2",
      location: "Ahmedabad",
      responseType: "policy_details",
      policyId: "grievance-mechanism",
      confidenceScore: 0.95,
      turnaroundMs: 620,
      escalated: true,
      timestamp: Date.now() - 7200000,
    },
    {
      id: "evt_seed_3",
      query: "what abt ahmendabad",
      normalizedQuery: "what about ahmedabad",
      userUid: "local-user-001",
      userRole: "employee",
      grade: "M2",
      location: "Ahmedabad",
      responseType: "policy_details",
      policyId: "domestic-travel",
      confidenceScore: 0.92,
      turnaroundMs: 430,
      timestamp: Date.now() - 1800000,
    },
  ];
}

function buildSeedLearningCases(): LearningCase[] {
  return [
    {
      id: "learn_seed_travel_1",
      query: "what is the ethics helpline number",
      normalizedQuery: "what is the ethics helpline number",
      approvedAnswer:
        "The Ethics Helpline toll-free number is **1800 200 8301** (18002008301). You can also write to **arvind@ethicshelpline.in** or use **www.in.kpmg.com/ethicshelpline/arvind**.",
      policyId: "whistleblower",
      source: "seed",
      confidence: 0.98,
      createdAt: Date.now() - 7 * 86400000,
    },
    {
      id: "learn_seed_travel_2",
      query: "how many days in advance should i book travel",
      normalizedQuery: "how many days in advance should i book travel",
      approvedAnswer:
        "Travel should normally be booked at least **7 days** in advance, and approval from the reporting manager is required through myBiz Self Booking Tool.",
      policyId: "domestic-travel",
      source: "seed",
      confidence: 0.96,
      createdAt: Date.now() - 5 * 86400000,
    },
  ];
}

function ensureSeededData() {
  if (!hasWindow()) return;

  if (!window.localStorage.getItem(STORAGE_KEYS.governance)) {
    writeStorage(STORAGE_KEYS.governance, buildSeedGovernance());
  }
  if (!window.localStorage.getItem(STORAGE_KEYS.tickets)) {
    writeStorage(STORAGE_KEYS.tickets, buildSeedTickets());
  }
  if (!window.localStorage.getItem(STORAGE_KEYS.analytics)) {
    writeStorage(STORAGE_KEYS.analytics, buildSeedAnalytics());
  }
  if (!window.localStorage.getItem(STORAGE_KEYS.learning)) {
    writeStorage(STORAGE_KEYS.learning, buildSeedLearningCases());
  }
}

ensureSeededData();

// --- DYNAMIC BACKEND DATABASE SYNCHRONIZER (SQLite Port 8000 Sync) ---

export let cachedAnalyticsSummary: any | null = null;
export let cachedHRTickets: any[] | null = null;
export let cachedPolicies: any[] | null = null;

export async function syncAllFromBackendSQLite() {
  try {
    const uids = ["local-user-001", "local-manager-001", "local-hrbp-001", "local-user-002", "local-user-003"];
    const syncedRecords: EmployeeRecord[] = [];
    for (const id of uids) {
      try {
        const res = await fetch(`${BACKEND_BASE_URL}/api/employees/${id}`);
        if (res.ok) {
          const data = await res.json();
          syncedRecords.push(data);
        }
      } catch (err) {
        // Skip individual failure
      }
    }
    if (syncedRecords.length > 0) {
      EMPLOYEE_RECORDS = [
        ...syncedRecords,
        ...EMPLOYEE_RECORDS.filter(r => !syncedRecords.some(sr => sr.profile.uid === r.profile.uid))
      ];
    }

    const ticketsRes = await fetch(`${BACKEND_BASE_URL}/api/tickets`);
    if (ticketsRes.ok) {
      cachedHRTickets = await ticketsRes.json();
      if (cachedHRTickets) {
        writeStorage(STORAGE_KEYS.tickets, cachedHRTickets);
      }
    }

    const analyticsRes = await fetch(`${BACKEND_BASE_URL}/api/analytics/summary`);
    if (analyticsRes.ok) {
      cachedAnalyticsSummary = await analyticsRes.json();
    }

    const govRes = await fetch(`${BACKEND_BASE_URL}/api/governance/policies`);
    if (govRes.ok) {
      cachedPolicies = await govRes.json();
    }
  } catch (e) {
    console.warn("FastAPI SQLite backend unreachable, operating in high-performance local fallback mode:", e);
  }
}

if (typeof window !== "undefined") {
  syncAllFromBackendSQLite();
}

export function getDemoProfiles() {
  return EMPLOYEE_RECORDS.map((record) => record.profile);
}

export function getEmployeeRecord(uid: string) {
  return EMPLOYEE_RECORDS.find((record) => record.profile.uid === uid) ?? EMPLOYEE_RECORDS[0];
}

export function getEmployeeProfile(uid: string) {
  return getEmployeeRecord(uid).profile;
}

export function getManagerTeam(uid: string) {
  const manager = getEmployeeRecord(uid);
  const reportIds = manager.profile.directReports ?? [];
  return EMPLOYEE_RECORDS.filter((record) => reportIds.includes(record.profile.uid));
}

export function getEmployeeNudges(profile: EmployeeProfile): EmployeeNudge[] {
  const nudges: EmployeeNudge[] = [
    {
      id: "nudge_1",
      text: "Travel policy benchmark remains above 95%. You can trust current domestic travel answers.",
      type: "success",
    },
  ];

  if (profile?.grade) {
    nudges.push({
      id: "nudge_2",
      text: `Your ${profile.grade} grade profile is active for personalized policy guidance.`,
      type: "info",
    });
  }

  if (profile?.location?.toLowerCase() === "ahmedabad" && profile?.companyCar) {
    nudges.unshift({
      id: "nudge_ahm",
      text: "Ahmedabad employees with a company car are not reimbursed for local conveyance to Santej, Raipur, Gomtipur, or nearby Ahmedabad units.",
      type: "alert",
    });
  }

  return nudges;
}

export function listServiceCatalogItems() {
  return [...SERVICE_CATALOG];
}

export function mapQueryToServiceCatalog(query: string) {
  const normalized = normalizeEmployeeChatText(query);
  let bestItem: (ServiceCatalogItem & { score: number }) | null = null;

  for (const item of SERVICE_CATALOG) {
    const score = item.keywords.reduce((sum, keyword) => sum + (normalized.includes(keyword) ? 1 : 0), 0);
    if (score === 0) continue;
    if (!bestItem || score > bestItem.score) {
      bestItem = { ...item, score };
    }
  }

  return bestItem;
}

export function getEmployeeSelfServiceModules(record: EmployeeRecord): SelfServiceModule[] {
  const latestPay = record.payStubs[0];
  return [
    {
      id: "module_leave",
      title: "My Leave",
      category: "My HR",
      value: `${record.leaveBalances.casual + record.leaveBalances.earned + record.leaveBalances.sick + record.leaveBalances.compOff} days`,
      detail: `${record.leaveBalances.casual} casual, ${record.leaveBalances.earned} earned, ${record.leaveBalances.sick} sick`,
      actionLabel: "Review leave",
      prompt: "Show my leave balance and missing attendance items.",
    },
    {
      id: "module_payslip",
      title: "My Payslip",
      category: "Payroll",
      value: latestPay ? `Net ${latestPay.netPay.toLocaleString("en-IN")}` : "No payslip",
      detail: latestPay ? `${latestPay.month} · ${latestPay.status}` : "Payroll data not available",
      actionLabel: "Open payslip",
      prompt: "Show my latest payslip summary.",
    },
    {
      id: "module_benefits",
      title: "My Benefits",
      category: "Benefits",
      value: record.benefits.enrollmentStatus,
      detail: `${record.benefits.health} · ${record.benefits.retirement}`,
      actionLabel: "Check benefits",
      prompt: "Show my benefits enrollment status.",
    },
    {
      id: "module_attendance",
      title: "My Attendance",
      category: "Attendance",
      value: `${record.attendanceRate}%`,
      detail: `${record.attendanceStatus} · ${record.profile.workMode}`,
      actionLabel: "Regularize",
      prompt: "Show my attendance status and any missing punches.",
    },
    {
      id: "module_approvers",
      title: "My Approver Chain",
      category: "Approvals",
      value: record.approverChain.lineManager,
      detail: `BUHR ${record.approverChain.buhr} · Finance ${record.approverChain.finance}`,
      actionLabel: "View approvers",
      prompt: "Show my approver chain for HR, travel, and payroll requests.",
    },
  ];
}

export function getManagerInsights(profile: EmployeeProfile, teamMembers: EmployeeRecord[], analyticsSummary: AnalyticsSummary): ManagerInsight[] {
  const leaveRisk = teamMembers.filter((member) => member.attendanceStatus === "On Leave").length;
  const cases = teamMembers.reduce((sum, member) => sum + member.activeCases, 0);
  const avgAttendance = teamMembers.length > 0
    ? Math.round(teamMembers.reduce((sum, member) => sum + member.attendanceRate, 0) / teamMembers.length)
    : 0;

  return [
    {
      id: "manager_leave_risk",
      title: "Team Leave Risk",
      value: `${leaveRisk} flagged`,
      tone: leaveRisk > 1 ? "watch" : "good",
      detail: "Use this to catch delivery or staffing impact before approvals pile up.",
      prompt: "Show team leave insights and pending approvals.",
    },
    {
      id: "manager_attendance",
      title: "Team Attendance",
      value: `${avgAttendance}%`,
      tone: avgAttendance >= 92 ? "good" : "watch",
      detail: "Average attendance across direct reports.",
      prompt: "Show team attendance gaps and regularization requests.",
    },
    {
      id: "manager_cases",
      title: "Open People Cases",
      value: `${cases}`,
      tone: cases > 1 ? "risk" : "neutral",
      detail: "Active employee escalations or support cases requiring manager awareness.",
      prompt: "Show team case trends and escalation heatmap.",
    },
    {
      id: "manager_confusion",
      title: "Policy Confusion",
      value: `${analyticsSummary.lowConfidenceCount}`,
      tone: analyticsSummary.lowConfidenceCount > 2 ? "watch" : "neutral",
      detail: "Low-confidence employee answers that may need playbook clarification.",
      prompt: "Show escalation hotspots and unresolved employee questions.",
    },
  ];
}

export function getGuidedJourneys(profile: EmployeeProfile): GuidedJourney[] {
  const baseJourneys: GuidedJourney[] = [
    {
      id: "journey_leave",
      title: "Leave & Attendance",
      description: "Check balance, missing punches, or leave policy.",
      prompt: "Show my leave balance and missing attendance items.",
      category: "Self Service",
    },
    {
      id: "journey_travel",
      title: "Travel Entitlement",
      description: `Use my ${profile.grade} grade and ${profile.location} location automatically.`,
      prompt: "What is my travel entitlement for lodging, boarding, and cab use?",
      category: "Travel",
    },
    {
      id: "journey_conveyance",
      title: "Local Conveyance",
      description: "Check claim eligibility and claim steps.",
      prompt: "Am I eligible for local conveyance reimbursement and how do I claim it?",
      category: "Travel",
    },
    {
      id: "journey_joining",
      title: "Joining Support",
      description: "Relocation, accommodation, and joining benefits.",
      prompt: "Show the joining and relocation benefits for my grade.",
      category: "Onboarding",
    },
    {
      id: "journey_grievance",
      title: "POSH / Grievance Help",
      description: "Safe reporting flow with human handoff.",
      prompt: "I need confidential help with grievance or POSH reporting.",
      category: "Support",
    },
    {
      id: "journey_transfer",
      title: "Internal Transfer",
      description: "Location, grade, and mobility what-if guidance.",
      prompt: "Show the internal transfer and relocation workflow for my profile.",
      category: "Mobility",
    },
    {
      id: "journey_exit",
      title: "Exit and Clearance",
      description: "Resignation, notice period, and clearance checklist.",
      prompt: "Show the resignation and exit clearance journey.",
      category: "Lifecycle",
    },
    {
      id: "journey_talent",
      title: "Talent and Recruiting",
      description: "Interview scheduling, JD generation, and mobility prompts.",
      prompt: "Help with candidate screening, interview scheduling, and internal mobility support.",
      category: "Talent",
    },
  ];

  if (profile.role !== "employee") {
    baseJourneys.unshift(
      {
        id: "journey_team",
        title: "Team Leave Insights",
        description: "View team leave, pending approvals, and action items.",
        prompt: "Show team leave insights and pending approvals.",
        category: "Manager",
      },
      {
        id: "journey_hrbp",
        title: "Escalation Watchlist",
        description: "Track high-risk cases and low-confidence bot answers.",
        prompt: "Show escalation hotspots and unresolved employee questions.",
        category: "HRBP",
      },
    );
  }

  return baseJourneys;
}

function getDefaultServiceIdForKind(kind: HRTicket["kind"]) {
  if (kind === "grievance") return "svc_grievance";
  if (kind === "posh") return "svc_posh";
  if (kind === "whistleblower") return "svc_grievance";
  return "svc_data_change";
}

export function createHRTicket(input: HRTicketCreationInput) {
  const service = SERVICE_CATALOG.find((item) => item.id === (input.serviceId ?? getDefaultServiceIdForKind(input.kind)));
  const ticket: HRTicket = {
    ...input,
    id: `case_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    status: input.status ?? "open",
    serviceId: input.serviceId ?? getDefaultServiceIdForKind(input.kind),
    assignmentGroup: input.assignmentGroup || service?.defaultAssignmentGroup || "People Operations",
    slaHours: input.slaHours || service?.slaHours || 24,
    dueAt: input.dueAt || Date.now() + ((input.slaHours || service?.slaHours || 24) * 3600000),
    statusHistory: input.statusHistory?.length
      ? input.statusHistory
      : [{ status: input.status ?? "open", actor: input.employeeName, note: "Case created from HR Pulse.", timestamp: Date.now() }],
    internalNotes: input.internalNotes ?? [],
    employeeVisibleUpdates: input.employeeVisibleUpdates ?? [],
    subtasks: input.subtasks ?? [],
    reopenCount: input.reopenCount ?? 0,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  const existing = readStorage<HRTicket[]>(STORAGE_KEYS.tickets, buildSeedTickets());
  const updatedList = [ticket, ...existing];
  writeStorage(STORAGE_KEYS.tickets, updatedList);

  // Sync to FastAPI Backend in the background
  fetch(`${BACKEND_BASE_URL}/api/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ticket)
  })
  .then(() => syncAllFromBackendSQLite())
  .catch(e => console.warn("Failed to sync ticket to backend:", e));

  return ticket;
}

export function listHRTickets() {
  if (cachedHRTickets && cachedHRTickets.length > 0) {
    return cachedHRTickets.sort((left, right) => right.updatedAt - left.updatedAt);
  }
  return readStorage<HRTicket[]>(STORAGE_KEYS.tickets, buildSeedTickets())
    .sort((left, right) => right.updatedAt - left.updatedAt);
}

export function updateHRTicketStatus(ticketId: string, status: HRTicket["status"], actor: string) {
  const currentTickets = listHRTickets();
  const updated = currentTickets.map((ticket) =>
    ticket.id === ticketId ? {
      ...ticket,
      status,
      assignedTo: actor,
      updatedAt: Date.now(),
      resolutionNotes: status === "resolved" ? `Resolved by ${actor} after policy and route validation.` : ticket.resolutionNotes,
      statusHistory: [
        { status, actor, note: `Status moved to ${status.replace("_", " ")}.`, timestamp: Date.now() },
        ...ticket.statusHistory,
      ].slice(0, 12),
    } : ticket
  );
  writeStorage(STORAGE_KEYS.tickets, updated);

  const resolvedTicket = updated.find((ticket) => ticket.id === ticketId && ticket.status === "resolved");
  if (resolvedTicket) {
    const policy = POLICY_META.find((item) => item.id === resolvedTicket.sourcePolicyId);
    recordLearningCase({
      query: resolvedTicket.summary,
      approvedAnswer: policy
        ? `This issue was previously resolved under **${policy.name}**. Follow the assigned route **${resolvedTicket.route}** and review the policy source before closing the request.`
        : `This issue was previously resolved by **${actor}** through the **${resolvedTicket.route}** route. Review the assigned case notes before reusing the guidance.`,
      policyId: resolvedTicket.sourcePolicyId,
      source: "resolved_case",
      confidence: 0.82,
    });
  }
}

export function addHRTicketNote(ticketId: string, author: string, note: string, visibility: "internal" | "employee" = "internal") {
  const noteId = `note_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
  const timestamp = Date.now();
  
  const updated = listHRTickets().map((ticket) => {
    if (ticket.id !== ticketId) return ticket;
    const nextNote: HRCaseNote = {
      id: noteId,
      author,
      note,
      visibility,
      timestamp,
    };
    return {
      ...ticket,
      updatedAt: timestamp,
      internalNotes: visibility === "internal" ? [nextNote, ...ticket.internalNotes].slice(0, 10) : ticket.internalNotes,
      employeeVisibleUpdates: visibility === "employee" ? [nextNote, ...ticket.employeeVisibleUpdates].slice(0, 10) : ticket.employeeVisibleUpdates,
    };
  });
  writeStorage(STORAGE_KEYS.tickets, updated);

  // Sync Note to SQLite Backend
  fetch(`${BACKEND_BASE_URL}/api/tickets/${ticketId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: noteId,
      author,
      note,
      visibility,
      timestamp
    })
  })
  .then(() => syncAllFromBackendSQLite())
  .catch(e => console.warn("Failed to sync note to backend:", e));
}

export function reopenHRTicket(ticketId: string, actor: string, note = "Case reopened for follow-up review.") {
  const updated = listHRTickets().map((ticket) => {
    if (ticket.id !== ticketId) return ticket;
    return {
      ...ticket,
      status: "in_review" as const,
      reopenCount: ticket.reopenCount + 1,
      updatedAt: Date.now(),
      statusHistory: [
        { status: "in_review", actor, note, timestamp: Date.now() },
        ...ticket.statusHistory,
      ].slice(0, 12),
    };
  });
  writeStorage(STORAGE_KEYS.tickets, updated);
}

export function recordAnalyticsEvent(event: AnalyticsEvent) {
  const existing = readStorage<AnalyticsEvent[]>(STORAGE_KEYS.analytics, buildSeedAnalytics());
  writeStorage(STORAGE_KEYS.analytics, [event, ...existing].slice(0, 500));

  // Sync turn event to backend SQLite DB
  fetch(`${BACKEND_BASE_URL}/api/analytics/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  })
  .then(() => syncAllFromBackendSQLite())
  .catch(e => console.warn("Failed to sync event to backend:", e));
}

export function updateAnalyticsFeedback(eventId: string, feedback: 1 | 5, feedbackReason?: string) {
  const updated = readStorage<AnalyticsEvent[]>(STORAGE_KEYS.analytics, buildSeedAnalytics()).map((event) =>
    event.id === eventId
      ? {
          ...event,
          feedback,
          feedbackReason,
        }
      : event
  );
  writeStorage(STORAGE_KEYS.analytics, updated);
}

export function getAnalyticsEvents() {
  return readStorage<AnalyticsEvent[]>(STORAGE_KEYS.analytics, buildSeedAnalytics())
    .sort((left, right) => right.timestamp - left.timestamp);
}

export function getAnalyticsSummary(): AnalyticsSummary {
  if (cachedAnalyticsSummary) {
    return cachedAnalyticsSummary;
  }
  const events = getAnalyticsEvents();
  const policyUsageMap = new Map<string, { policyId: string; policyName: string; count: number }>();
  const policyAccuracyMap = new Map<string, { policyId: string; policyName: string; scoreTotal: number; count: number }>();
  const gradeMap = new Map<string, number>();
  const locationMap = new Map<string, number>();
  const confusionMap = new Map<string, number>();
  const riskMap = new Map<string, number>();

  const topicRules: Array<{ label: string; pattern: RegExp }> = [
    { label: "Travel and reimbursement", pattern: /\btravel|reimbursement|conveyance|claim|hotel|lodging\b/ },
    { label: "Leave and attendance", pattern: /\bleave|attendance|punch|approver\b/ },
    { label: "Sensitive complaints", pattern: /\bposh|grievance|whistleblower|harass|ethics|gender\b/ },
    { label: "Onboarding and mobility", pattern: /\bjoining|relocation|mobility|mab|sia\b/ },
    { label: "Payroll and benefits", pattern: /\bpayslip|salary|payroll|benefit|insurance\b/ },
  ];

  for (const event of events) {
    if (event.policyId) {
      const policy = POLICY_META.find((item) => item.id === event.policyId);
      const current = policyUsageMap.get(event.policyId) ?? {
        policyId: event.policyId,
        policyName: policy?.name ?? event.policyId,
        count: 0,
      };
      current.count += 1;
      policyUsageMap.set(event.policyId, current);

      const currentAccuracy = policyAccuracyMap.get(event.policyId) ?? {
        policyId: event.policyId,
        policyName: policy?.name ?? event.policyId,
        scoreTotal: 0,
        count: 0,
      };
      currentAccuracy.scoreTotal += Math.round((event.confidenceScore ?? 0.8) * 100);
      currentAccuracy.count += 1;
      policyAccuracyMap.set(event.policyId, currentAccuracy);
    }

    gradeMap.set(event.grade, (gradeMap.get(event.grade) ?? 0) + 1);
    locationMap.set(event.location, (locationMap.get(event.location) ?? 0) + 1);

    for (const rule of topicRules) {
      if (rule.pattern.test(event.normalizedQuery)) {
        confusionMap.set(rule.label, (confusionMap.get(rule.label) ?? 0) + (event.unresolved || (event.confidenceScore ?? 0) < 0.75 ? 1 : 0));
      }
    }

    if (event.escalated) {
      riskMap.set("Escalations", (riskMap.get("Escalations") ?? 0) + 1);
    }
    if ((event.confidenceScore ?? 0) < 0.75) {
      riskMap.set("Low confidence", (riskMap.get("Low confidence") ?? 0) + 1);
    }
    if (event.highRisk) {
      riskMap.set("High-risk topics", (riskMap.get("High-risk topics") ?? 0) + 1);
    }
    if (event.clarificationRequested) {
      riskMap.set("Clarification loops", (riskMap.get("Clarification loops") ?? 0) + 1);
    }
  }

  const learningCases = listLearningCases();
  const helpfulEvents = events.filter((event) => event.feedback === 5).length;
  const escalatedEvents = events.filter((event) => !!event.escalated);
  const unresolvedEvents = events.filter((event) => event.unresolved || event.responseType === "error");
  const followUpSignals = events.filter((event) => event.clarificationRequested || event.usedLearningCase);
  const falseEscalationCount = escalatedEvents.filter((event) => !event.highRisk && (event.confidenceScore ?? 0) >= 0.9).length;

  return {
    totalInteractions: events.length,
    lowConfidenceCount: events.filter((event) => (event.confidenceScore ?? 0) < 0.75).length,
    escalationCount: events.filter((event) => !!event.escalated).length,
    helpfulCount: events.filter((event) => event.feedback === 5).length,
    notUsefulCount: events.filter((event) => event.feedback === 1).length,
    unansweredQueries: events
      .filter((event) => event.unresolved || event.responseType === "error")
      .slice(0, 8)
      .map((event) => event.query),
    policyUsage: Array.from(policyUsageMap.values()).sort((left, right) => right.count - left.count).slice(0, 8),
    gradeHotspots: Array.from(gradeMap.entries()).map(([grade, count]) => ({ grade, count })).sort((left, right) => right.count - left.count),
    locationHotspots: Array.from(locationMap.entries()).map(([location, count]) => ({ location, count })).sort((left, right) => right.count - left.count),
    confusionHotspots: Array.from(confusionMap.entries()).map(([topic, count]) => ({ topic, count })).sort((left, right) => right.count - left.count).slice(0, 5),
    riskSignals: Array.from(riskMap.entries()).map(([signal, count]) => ({ signal, count })).sort((left, right) => right.count - left.count).slice(0, 5),
    learningCaseCount: learningCases.length,
    resolutionLoopCoverage: helpfulEvents > 0 ? Math.round((learningCases.length / helpfulEvents) * 100) : learningCases.length > 0 ? 100 : 0,
    falseEscalationRate: escalatedEvents.length > 0 ? Math.round((falseEscalationCount / escalatedEvents.length) * 100) : 0,
    followUpResolutionRate: followUpSignals.length > 0
      ? Math.round((followUpSignals.filter((event) => !event.unresolved && (event.confidenceScore ?? 0) >= 0.8).length / followUpSignals.length) * 100)
      : 100,
    unresolvedTopicCount: unresolvedEvents.length,
    policyAccuracy: Array.from(policyAccuracyMap.values())
      .map((item) => ({
        policyId: item.policyId,
        policyName: item.policyName,
        score: Math.round(item.scoreTotal / Math.max(item.count, 1)),
      }))
      .sort((left, right) => right.score - left.score)
      .slice(0, 8),
  };
}

function normalizeLearningText(text: string) {
  return normalizeEmployeeChatText(text)
    .replace(/[^a-z0-9\s/-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenSet(text: string) {
  return new Set(
    normalizeLearningText(text)
      .split(" ")
      .filter((token) => token.length > 2),
  );
}

function computeLearningSimilarity(left: string, right: string) {
  const leftTokens = tokenSet(left);
  const rightTokens = tokenSet(right);
  if (leftTokens.size === 0 || rightTokens.size === 0) return 0;

  let overlap = 0;
  for (const token of leftTokens) {
    if (rightTokens.has(token)) overlap += 1;
  }

  return overlap / Math.max(leftTokens.size, rightTokens.size);
}

export function listLearningCases() {
  return readStorage<LearningCase[]>(STORAGE_KEYS.learning, buildSeedLearningCases())
    .sort((left, right) => (right.lastUsedAt ?? right.createdAt) - (left.lastUsedAt ?? left.createdAt));
}

export function recordLearningCase(input: Omit<LearningCase, "id" | "createdAt" | "normalizedQuery">) {
  const existing = listLearningCases();
  const normalizedQuery = normalizeLearningText(input.query);
  const similar = existing.find((item) => item.normalizedQuery === normalizedQuery);
  const nextRecord: LearningCase = similar
    ? {
        ...similar,
        approvedAnswer: input.approvedAnswer,
        policyId: input.policyId ?? similar.policyId,
        source: input.source,
        confidence: Math.max(similar.confidence, input.confidence),
        lastUsedAt: Date.now(),
      }
    : {
        ...input,
        id: `learn_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        normalizedQuery,
        createdAt: Date.now(),
      };

  const merged = similar
    ? existing.map((item) => item.id === similar.id ? nextRecord : item)
    : [nextRecord, ...existing].slice(0, 150);

  writeStorage(STORAGE_KEYS.learning, merged);
  return nextRecord;
}

export function findLearningCaseMatch(query: string, policyId?: string) {
  const learningCases = listLearningCases();
  let bestMatch: (LearningCase & { score: number }) | null = null;

  for (const item of learningCases) {
    if (policyId && item.policyId && item.policyId !== policyId) continue;
    const score = computeLearningSimilarity(query, item.query);
    if (score < 0.45) continue;
    if (!bestMatch || score > bestMatch.score) {
      bestMatch = { ...item, score };
    }
  }

  if (!bestMatch) return null;

  const touched = learningCases.map((item) =>
    item.id === bestMatch?.id ? { ...item, lastUsedAt: Date.now() } : item,
  );
  writeStorage(STORAGE_KEYS.learning, touched);
  return bestMatch;
}

export function getPolicyGovernanceSnapshot(policyId?: string, policyName?: string) {
  if (!policyId && !policyName) return null;
  return listPolicyGovernanceRecords().find((record) =>
    (policyId && record.id === policyId) ||
    (policyName && record.title.toLowerCase() === policyName.toLowerCase()),
  ) ?? null;
}

export function getPolicyAcknowledgments() {
  return listPolicyGovernanceRecords().slice(0, 5).map((record, index) => ({
    id: `ack_${record.id}`,
    policyId: record.id,
    policyName: record.title,
    audience: index % 2 === 0 ? "All employees" : "Managers and HRBPs",
    completionRate: Math.max(78, 96 - index * 4),
    dueDate: new Date(Date.now() + (index + 2) * 86400000).toISOString().slice(0, 10),
  }));
}

export function getComplianceControls() {
  const sensitiveCases = listHRTickets().filter((ticket) => ticket.confidentiality !== "standard").length;
  return [
    {
      id: "compliance_confidential",
      title: "Confidential route enforcement",
      status: sensitiveCases > 0 ? "active" : "watch",
      owner: "Employee Relations",
      detail: `${sensitiveCases} sensitive cases are currently restricted to safe-routing groups.`,
    },
    {
      id: "compliance_audit",
      title: "Audit trail coverage",
      status: "active",
      owner: "HR Governance",
      detail: "Policy saves, publishes, and rollbacks are captured with actor and timestamp.",
    },
    {
      id: "compliance_retention",
      title: "Retention and role access",
      status: "watch",
      owner: "InfoSec + HRIT",
      detail: "Review local demo retention settings before production rollout.",
    },
    {
      id: "compliance_sensitive",
      title: "Sensitive-topic routing",
      status: "active",
      owner: "POSH Secretariat",
      detail: "Payroll, grievance, POSH, and whistleblower requests are marked for safe handling.",
    },
  ] satisfies ComplianceControl[];
}

export function getTalentWorkflows() {
  return [
    {
      id: "talent_jd",
      title: "Job Description Generator",
      stage: "Requisition",
      summary: "Draft JD prompts for recruiters and hiring managers.",
      actionLabel: "Draft JD",
      prompt: "Generate a job description for a people analytics specialist.",
    },
    {
      id: "talent_screening",
      title: "Candidate Screening",
      stage: "Screening",
      summary: "Summarize candidate fit, risks, and interview questions.",
      actionLabel: "Screen candidates",
      prompt: "Help screen candidates for an HR operations analyst role.",
    },
    {
      id: "talent_scheduling",
      title: "Interview Scheduling",
      stage: "Interview",
      summary: "Coordinate panel availability and reminders.",
      actionLabel: "Schedule interviews",
      prompt: "Help schedule candidate interviews this week.",
    },
    {
      id: "talent_mobility",
      title: "Internal Mobility",
      stage: "Talent Marketplace",
      summary: "Recommend next roles and transfer support for employees.",
      actionLabel: "Explore mobility",
      prompt: "Show internal mobility support and next-role suggestions.",
    },
  ] satisfies TalentWorkflow[];
}

export function getContentOpsTasks() {
  const governanceRecords = listPolicyGovernanceRecords();
  return [
    {
      id: "content_upload",
      title: "Bulk upload new policy bundle",
      type: "upload",
      owner: "HR Content Ops",
      status: "in_progress",
      detail: `${governanceRecords.length} policy records currently mapped to source documents.`,
    },
    {
      id: "content_chunking",
      title: "Clause chunking validation",
      type: "chunking",
      owner: "Knowledge Engineering",
      status: "blocked",
      detail: "Validate clause-level extraction for updated grievance and gender policies.",
    },
    {
      id: "content_translation",
      title: "Hindi and Gujarati review",
      type: "translation",
      owner: "Regional HR",
      status: "in_progress",
      detail: "Review translated employee-facing summaries before publish.",
    },
    {
      id: "content_benchmark",
      title: "Benchmark gate before publish",
      type: "benchmark",
      owner: "HR Operations",
      status: "done",
      detail: "Balanced suite remains at 100% across 7,000 benchmark cases.",
    },
    {
      id: "content_rollback",
      title: "Rollback readiness",
      type: "rollback",
      owner: "Policy Governance",
      status: "queued",
      detail: "Keep previous policy snapshots available for safe rollback.",
    },
  ] satisfies ContentOpsTask[];
}

export function getChannelExperiences() {
  return [
    { id: "channel_web", name: "Web Chat", state: "live", summary: "Primary employee self-service and policy assistant surface." },
    { id: "channel_portal", name: "Employee Portal", state: "pilot", summary: "Structured self-service cards embedded into HR workspace." },
    { id: "channel_teams", name: "Teams / Slack Mode", state: "planned", summary: "Manager nudges, approvals, and quick service requests in chat." },
    { id: "channel_mobile", name: "Mobile Compact UI", state: "pilot", summary: "Fast leave, payslip, and grievance initiation flows on smaller screens." },
    { id: "channel_voice", name: "Voice UX", state: "pilot", summary: "Speech input with English, Hindi, and Gujarati employee assistance." },
  ] satisfies ChannelExperience[];
}

export function getAIOpsSnapshot(): AIOpsSnapshot {
  const analytics = getAnalyticsSummary();
  return {
    benchmarkAccuracy: 100,
    falseEscalationRate: analytics.falseEscalationRate,
    followUpResolutionRate: analytics.followUpResolutionRate,
    unresolvedTopicCount: analytics.unresolvedTopicCount,
    learningLoopCoverage: analytics.resolutionLoopCoverage,
    policyAccuracy: analytics.policyAccuracy,
  };
}

export function listPolicyGovernanceRecords() {
  return readStorage<PolicyGovernanceRecord[]>(STORAGE_KEYS.governance, buildSeedGovernance())
    .sort((left, right) => right.updatedAt - left.updatedAt);
}

export function upsertPolicyGovernanceRecord(record: PolicyGovernanceRecord, actor: string, note: string) {
  const currentRecords = listPolicyGovernanceRecords();
  const existing = currentRecords.find((item) => item.id === record.id);
  const nextRecord: PolicyGovernanceRecord = {
    ...record,
    updatedAt: Date.now(),
    previousVersions: existing
      ? [
          {
            version: existing.version,
            title: existing.title,
            content: existing.content,
            status: existing.lifecycleStatus,
            updatedAt: existing.updatedAt,
          },
          ...existing.previousVersions,
        ].slice(0, 10)
      : record.previousVersions,
    auditTrail: [makeAuditEntry(actor, "save", note), ...(existing?.auditTrail ?? record.auditTrail)].slice(0, 20),
  };

  const merged = currentRecords.some((item) => item.id === record.id)
    ? currentRecords.map((item) => item.id === record.id ? nextRecord : item)
    : [nextRecord, ...currentRecords];

  writeStorage(STORAGE_KEYS.governance, merged);
  return nextRecord;
}

export function publishPolicyRecord(policyId: string, actor: string) {
  const records = listPolicyGovernanceRecords();
  const next = records.map((record) => {
    if (record.id !== policyId) return record;
    if (record.benchmarkRequired && (!record.benchmarkPassed || record.lastBenchmarkAccuracy < 95)) {
      return record;
    }
    return {
      ...record,
      environment: "published" as const,
      lifecycleStatus: "published" as const,
      updatedAt: Date.now(),
      auditTrail: [makeAuditEntry(actor, "publish", "Published after benchmark gate passed."), ...record.auditTrail].slice(0, 20),
    };
  });
  writeStorage(STORAGE_KEYS.governance, next);
}

export function rollbackPolicyRecord(policyId: string, actor: string) {
  const records = listPolicyGovernanceRecords();
  const next = records.map((record) => {
    if (record.id !== policyId || record.previousVersions.length === 0) return record;

    const [latestPrevious, ...remaining] = record.previousVersions;
    return {
      ...record,
      title: latestPrevious.title,
      content: latestPrevious.content,
      version: latestPrevious.version,
      lifecycleStatus: latestPrevious.status as PolicyGovernanceRecord["lifecycleStatus"],
      updatedAt: Date.now(),
      previousVersions: remaining,
      auditTrail: [makeAuditEntry(actor, "rollback", `Rolled back to version ${latestPrevious.version}.`), ...record.auditTrail].slice(0, 20),
    };
  });
  writeStorage(STORAGE_KEYS.governance, next);
}

export function getTravelCityClass(location: string) {
  const normalized = location.toLowerCase();
  const classOne = new Set(["delhi", "mumbai", "bangalore", "chennai", "hyderabad", "kolkata", "pune"]);
  return classOne.has(normalized) ? "Class I" : "Class II";
}

export function getTravelEntitlementForGrade(grade: string, location: string) {
  const cityClass = getTravelCityClass(location);
  const normalized = grade.toLowerCase();

  if (["m3h1", "m3", "m2"].includes(normalized)) {
    return cityClass === "Class I"
      ? { cityClass, lodging: "₹6000/day", boarding: "₹1200/day", cab: "Ola / Uber / BluSmart" }
      : { cityClass, lodging: "₹5000/day", boarding: "₹1000/day", cab: "Ola / Uber / BluSmart" };
  }

  if (["m1", "mt", "e2", "e1", "get", "ot"].includes(normalized)) {
    return cityClass === "Class I"
      ? { cityClass, lodging: "₹3400/day", boarding: "₹1000/day", cab: "Ola / Uber / BluSmart / Bus / Metro" }
      : { cityClass, lodging: "₹2300/day", boarding: "₹800/day", cab: "Ola / Uber / BluSmart / Bus / Metro" };
  }

  return cityClass === "Class I"
    ? { cityClass, lodging: "₹8000/day", boarding: "₹1500/day", cab: "Ola / Uber / BluSmart" }
    : { cityClass, lodging: "₹6000/day", boarding: "₹1300/day", cab: "Ola / Uber / BluSmart" };
}

export function getJoiningBenefitSummary(grade: string) {
  const normalized = grade.toLowerCase();
  if (["m3h1", "m3", "m2"].includes(normalized)) {
    return "Service apartment or guest house support, relocation reimbursement, and joining travel benefits apply.";
  }
  if (["m1", "e2", "e1", "get", "ot", "mt"].includes(normalized)) {
    return "Service apartment or guest house support applies. Staying beyond 15 days needs CHRO approval.";
  }
  return "Hotel accommodation, relocation reimbursement, and joining travel support apply for senior grades.";
}

export function getLocalConveyanceEligibility(record: EmployeeRecord) {
  const lowerLocation = record.profile.location.toLowerCase();
  const hasAhmedabadRestriction = lowerLocation === "ahmedabad" && record.profile.companyCar;

  return {
    eligible: !hasAhmedabadRestriction,
    explanation: hasAhmedabadRestriction
      ? "Employees in Ahmedabad with a company car are not reimbursed for local conveyance to Santej, Raipur, Gomtipur, or nearby Ahmedabad units."
      : "You are eligible for local conveyance claims subject to approval rules and supporting documentation.",
    nextStep: "Claim through Orapps → ESMS → Entry → Conveyance Expense with km or bills as applicable.",
  };
}
