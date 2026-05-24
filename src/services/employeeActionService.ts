import {
  EmployeeProfile,
  EmployeeRecord,
  HRTicket,
  SupportedLanguage,
  createHRTicket,
  getEmployeeRecord,
  getJoiningBenefitSummary,
  getLocalConveyanceEligibility,
  getManagerTeam,
  getTravelEntitlementForGrade,
} from "./employeeExperienceService";
import { enrichResponseForExperience } from "./chatExperienceEnhancer";
import { isEmployeeSpecificQuestion, normalizeEmployeeChatText } from "./queryNormalization";
import type { ChatMessage } from "./geminiService";

export interface ActionWorkflowResponse {
  text: string;
  type: "general" | "policy_details" | "action_trigger";
  suggestedQuestions?: string[];
  data?: {
    policyId?: string;
    policyName?: string;
    policyUrl?: string;
    pageNumber?: number;
    confidenceScore?: number;
    source?: string;
    keyPoints?: string[];
    policyVersion?: number;
    effectiveDate?: string;
    lastUpdatedAt?: number;
    governanceStatus?: string;
    clauseReference?: string;
    matchedCriteria?: string[];
    approvalPath?: string[];
    exceptionGuidance?: string;
    documentsRequired?: string[];
    sla?: string;
    actionChecklist?: string[];
    safetyMode?: "standard" | "sensitive" | "high_risk";
    retentionNotice?: string;
    localizedLanguage?: string;
    localizedSummary?: string;
    action?: {
      type: string;
      caseId?: string;
      route?: string;
    };
  };
}

interface KnowledgeAsset {
  id: string;
  name: string;
  content?: string;
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function toHindi(text: string) {
  return text;
}

function toGujarati(text: string) {
  return text;
}

function localize(text: string, language: SupportedLanguage) {
  if (language === "hindi") return toHindi(text);
  if (language === "gujarati") return toGujarati(text);
  return text;
}

function formatDateTime(value: number) {
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function buildSupportQuestions(language: SupportedLanguage, prompts: string[]) {
  return prompts.map((prompt) => localize(prompt, language));
}

function buildActionResponse(
  text: string,
  language: SupportedLanguage,
  payload: ActionWorkflowResponse["data"],
  suggestedQuestions: string[],
  type: ActionWorkflowResponse["type"] = "action_trigger",
  query?: string,
  profile?: EmployeeProfile,
): ActionWorkflowResponse {
  const response: ActionWorkflowResponse = {
    text: localize(text, language),
    type,
    suggestedQuestions: buildSupportQuestions(language, suggestedQuestions),
    data: payload,
  };

  if (!profile) {
    return response;
  }

  return enrichResponseForExperience(response, query ?? text, {
    role: profile.role,
    language,
    employeeId: profile.employeeId,
    name: profile.displayName,
    grade: profile.grade,
    location: profile.location,
    department: profile.department,
    businessUnit: profile.businessUnit,
    manager: profile.managerName,
    workMode: profile.workMode,
  });
}

function createCaseFromConversation(
  record: EmployeeRecord,
  kind: HRTicket["kind"],
  query: string,
  title: string,
  route: string,
  confidentiality: HRTicket["confidentiality"],
) {
  return createHRTicket({
    kind,
    title,
    summary: query,
    confidentiality,
    route,
    priority: kind === "posh" ? "critical" : kind === "whistleblower" ? "high" : "medium",
    employeeUid: record.profile.uid,
    employeeName: record.profile.displayName,
    employeeGrade: record.profile.grade,
    employeeLocation: record.profile.location,
    assignedTo: route,
    transcriptExcerpt: query,
    sourcePolicyId:
      kind === "posh"
        ? "posh-policy"
        : kind === "grievance"
          ? "grievance-mechanism"
          : kind === "whistleblower"
            ? "whistleblower"
            : undefined,
  });
}

function buildLeaveBalanceResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const leave = record.leaveBalances;
  return buildActionResponse(
    `Here is your current leave snapshot:\n\n- Casual Leave: **${leave.casual} days**\n- Earned Leave: **${leave.earned} days**\n- Sick Leave: **${leave.sick} days**\n- Comp Off: **${leave.compOff} day(s)**\n\nApprover: **${record.approverChain.lineManager}**.`,
    language,
    {
      confidenceScore: 0.99,
      source: "Personalized HRIS Snapshot",
      keyPoints: [
        `Casual Leave ${leave.casual} days`,
        `Earned Leave ${leave.earned} days`,
        `Sick Leave ${leave.sick} days`,
      ],
      action: { type: "leave_balance" },
    },
    ["Show my approver chain", "How do I apply for leave?", "Show attendance issues"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildPayslipResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const latest = record.payStubs[0];
  return buildActionResponse(
    `Your latest payslip is for **${latest.month}**.\n\n- Net Pay: **${formatCurrency(latest.netPay)}**\n- Gross Pay: **${formatCurrency(latest.grossPay)}**\n- Status: **${latest.status}**\n\nIf you want, I can also summarize your benefits or reimbursement trend.`,
    language,
    {
      confidenceScore: 0.99,
      source: "Personalized HRIS Snapshot",
      keyPoints: [`Net Pay ${formatCurrency(latest.netPay)}`, `Month ${latest.month}`],
      action: { type: "payslip_lookup" },
    },
    ["Show my benefits", "Show reimbursement trend", "Email my chat transcript to HR"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildBenefitsResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Your current benefits status is:\n\n- Health Plan: **${record.benefits.health}**\n- Dental: **${record.benefits.dental}**\n- Enrollment: **${record.benefits.enrollmentStatus}**\n- Retirement: **${record.benefits.retirement}**`,
    language,
    {
      confidenceScore: 0.99,
      source: "Personalized HRIS Snapshot",
      action: { type: "benefits_lookup" },
    },
    ["Show my latest payslip", "Show my leave balance", "Who is my approver?"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildApproverResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Your current approver chain is:\n\n- Line Manager: **${record.approverChain.lineManager}**\n- BUHR: **${record.approverChain.buhr}**\n- Finance: **${record.approverChain.finance}**\n- Travel Desk: **${record.approverChain.travelDesk}**`,
    language,
    {
      confidenceScore: 0.97,
      source: "Workflow Routing Directory",
      action: { type: "approver_chain" },
    },
    ["Create HR ticket", "Escalate to BUHR", "Show local conveyance eligibility"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildTravelEntitlementResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const entitlement = getTravelEntitlementForGrade(record.profile.grade, record.profile.location);
  return buildActionResponse(
    `Using your profile (**${record.profile.grade}**, **${record.profile.location}**), your likely domestic travel entitlement is:\n\n- City Class: **${entitlement.cityClass}**\n- Lodging: **${entitlement.lodging}**\n- Boarding: **${entitlement.boarding}**\n- Cab: **${entitlement.cab}**\n\nIf you need an exact policy answer for another grade or city, ask that directly.`,
    language,
    {
      confidenceScore: 0.95,
      source: "Profile-Aware Travel Guidance",
      policyId: "domestic-travel",
      policyName: "Domestic Travel Policy",
      policyUrl: "/original-policies/domestic-travel-policy-arvind-limited.pdf",
      pageNumber: 7,
      action: { type: "travel_entitlement" },
    },
    ["What are my local conveyance rules?", "Show travel claim guidance", "Explain in simple words"],
    "policy_details",
    query,
    record.profile,
  );
}

function buildConveyanceResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const eligibility = getLocalConveyanceEligibility(record);
  return buildActionResponse(
    `${eligibility.eligible ? "You are eligible for local conveyance claims." : "There is a reimbursement restriction based on your profile."}\n\n${eligibility.explanation}\n\nNext step: ${eligibility.nextStep}`,
    language,
    {
      confidenceScore: 0.96,
      source: "Profile-Aware Local Conveyance Guidance",
      policyId: "local-conveyance",
      policyName: "Local Conveyance Policy",
      policyUrl: "/original-policies/local-conveyance-policy-arvind-limited.pdf",
      pageNumber: 1,
      action: { type: "local_conveyance" },
    },
    ["Create HR ticket", "Who approves conveyance?", "Show travel entitlement"],
    "policy_details",
    query,
    record.profile,
  );
}

function buildJoiningResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `For your grade (**${record.profile.grade}**), the joining support summary is:\n\n${getJoiningBenefitSummary(record.profile.grade)}\n\nIf you want, I can next show relocation allowance, temporary accommodation, or claim deadlines.`,
    language,
    {
      confidenceScore: 0.95,
      source: "Profile-Aware Joining Guidance",
      policyId: "joining-policy",
      policyName: "Joining Policy",
      policyUrl: "/original-policies/joining-policy-arvind-limited.pdf",
      pageNumber: 2,
      action: { type: "joining_support" },
    },
    ["What is the relocation allowance?", "What accommodation do I get?", "What are the claim deadlines?"],
    "policy_details",
    query,
    record.profile,
  );
}

function buildLeaveApplicationResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `I can help you prepare a leave request for **next Friday**.\n\n- Employee: **${record.profile.displayName}**\n- Approver: **${record.approverChain.lineManager}**\n- Route: **Leave & Attendance**\n- Recommended next step: Submit the request in ESS with a short reason and check balance before approval.\n\nYour current total available leave is **${record.leaveBalances.casual + record.leaveBalances.earned + record.leaveBalances.sick + record.leaveBalances.compOff} days**.`,
    language,
    {
      confidenceScore: 0.96,
      source: "Leave Workflow Assistant",
      action: { type: "leave_request_draft" },
    },
    ["Show my leave balance", "Who is my approver?", "Show attendance issues"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildAttendanceRegularizationResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `I can help you correct a missing punch through attendance regularization.\n\n- Current attendance rate: **${record.attendanceRate}%**\n- Status: **${record.attendanceStatus}**\n- Approver: **${record.approverChain.lineManager}**\n- Next step: Add the date, in/out time, and a short note for approval.\n\nIf the mismatch still remains after one review, raise an HR ticket with a screenshot.`,
    language,
    {
      confidenceScore: 0.97,
      source: "Attendance Workflow Assistant",
      action: { type: "attendance_regularization" },
    },
    ["Show my attendance status", "Create HR ticket", "Show my approver chain"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildPayslipDownloadResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const latest = record.payStubs[0];
  return buildActionResponse(
    `Your payslip export is ready from the current HRIS snapshot.\n\n- Month: **${latest.month}**\n- Net Pay: **${formatCurrency(latest.netPay)}**\n- Gross Pay: **${formatCurrency(latest.grossPay)}**\n- Status: **${latest.status}**\n\nUse the payroll or ESS document route to download the full PDF copy.`,
    language,
    {
      confidenceScore: 0.99,
      source: "Payslip Document Assistant",
      action: { type: "payslip_download" },
    },
    ["Show my latest payslip summary", "Show my benefits", "Create HR ticket"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildDependentUpdateResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const ticket = createCaseFromConversation(record, "hr_ticket", query, "Dependent details update", "Benefits Desk", "confidential");
  return buildActionResponse(
    `I created a dependent-details update request.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Assignment Group: **${ticket.assignmentGroup}**\n- SLA: **${ticket.slaHours} hours**\n- Due By: **${formatDateTime(ticket.dueAt)}**\n\nKeep dependent proof, ID, and any enrollment document ready.`,
    language,
    {
      confidenceScore: 1,
      source: "Employee Data Change Workflow",
      action: { type: "dependent_update_case", caseId: ticket.id, route: ticket.route },
    },
    ["Show my benefits", "Who is my approver?", "Email my chat transcript to HR"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildPayrollComparisonResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const latest = record.payStubs[0];
  const previous = record.payStubs[1];
  if (!previous) {
    return buildActionResponse(
      `I only have one payslip snapshot right now.\n\n- Latest month: **${latest.month}**\n- Net Pay: **${formatCurrency(latest.netPay)}**\n\nIf you want a month-on-month comparison, raise it to Payroll Ops with the earlier payslip attached.`,
      language,
      {
        confidenceScore: 0.85,
        source: "Payroll Comparison Assistant",
        safetyMode: "high_risk",
        action: { type: "payroll_compare" },
      },
      ["Show my latest payslip", "Create HR ticket", "What details should I send to Payroll Ops?"],
      "action_trigger",
      query,
      record.profile,
    );
  }

  const difference = latest.netPay - previous.netPay;
  const direction = difference === 0 ? "the same as" : difference > 0 ? "higher than" : "lower than";
  const detail = difference === 0
    ? `I do **not** see April net pay lower than March in your current snapshot. Both months are **${formatCurrency(latest.netPay)}** net.`
    : `Your **${latest.month}** net pay is **${formatCurrency(Math.abs(difference))}** ${direction} **${previous.month}**.`;

  return buildActionResponse(
    `${detail}\n\n- ${latest.month}: **${formatCurrency(latest.netPay)}** net\n- ${previous.month}: **${formatCurrency(previous.netPay)}** net\n\nFor final payroll root-cause validation, compare deductions or route it to Payroll Ops with both payslips.`,
    language,
    {
      confidenceScore: 0.92,
      source: "Payroll Comparison Assistant",
      safetyMode: "high_risk",
      action: { type: "payroll_compare" },
    },
    ["Show my latest payslip", "Create HR ticket", "What details should I send to Payroll Ops?"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildPayrollInvestigationResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const ticket = createCaseFromConversation(record, "hr_ticket", query, "Payroll discrepancy review", "Payroll Operations", "confidential");
  return buildActionResponse(
    `This is a high-risk payroll topic, so I will not guess the root cause.\n\n- Route: **${ticket.route}**\n- Case ID: **${ticket.id}**\n- SLA: **${ticket.slaHours} hours**\n- Needed for review: **payslip month, issue summary, and supporting screenshot**\n\nFor now, use your latest payslip summary as the baseline and let Payroll Ops validate PF, tax, or deduction lines.`,
    language,
    {
      confidenceScore: 0.94,
      source: "Payroll Safe-Handling Workflow",
      safetyMode: "high_risk",
      action: { type: "payroll_review_case", caseId: ticket.id, route: ticket.route },
    },
    ["Show my latest payslip", "Email my chat transcript to HR", "What details should I send to Payroll Ops?"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildManagerLeaveInsightsResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const teamMembers = getManagerTeam(record.profile.uid);
  const flagged = teamMembers.filter((member) => member.attendanceStatus === "On Leave");
  const avgAttendance = teamMembers.length > 0
    ? Math.round(teamMembers.reduce((sum, member) => sum + member.attendanceRate, 0) / teamMembers.length)
    : 0;

  return buildActionResponse(
    `Here is your team leave and attendance watchlist:\n\n- Team members reviewed: **${teamMembers.length}**\n- Leave risk flagged: **${flagged.length}**\n- Average attendance: **${avgAttendance}%**\n- Employees needing attention: **${flagged.map((member) => member.profile.displayName).join(", ") || "None"}**\n\nRecommended next step: review pending approvals and check whether coverage is needed for the employee on leave.`,
    language,
    {
      confidenceScore: 0.97,
      source: "Manager Service Insights",
      action: { type: "manager_leave_risk" },
    },
    ["Show team attendance gaps", "Show team case trends", "Which team members need approval attention this week?"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildManagerApprovalAttentionResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const teamMembers = getManagerTeam(record.profile.uid);
  const attentionItems = teamMembers.flatMap((member) => {
    const items: string[] = [];
    if (member.attendanceStatus === "On Leave") {
      items.push(`${member.profile.displayName} is currently on leave`);
    }
    if (/pending/i.test(member.travelClaimStatus)) {
      items.push(`${member.profile.displayName} has travel follow-up: ${member.travelClaimStatus}`);
    }
    return items;
  });

  return buildActionResponse(
    `Approval attention summary for this week:\n\n${attentionItems.length > 0 ? attentionItems.map((item) => `- ${item}`).join("\n") : "- No urgent approval blockers detected from the current team snapshot."}\n\nManager follow-up route: **${record.approverChain.lineManager} / ${record.approverChain.buhr}** for escalations.`,
    language,
    {
      confidenceScore: 0.95,
      source: "Manager Approval Watchlist",
      action: { type: "manager_approval_attention" },
    },
    ["Show team leave insights", "Show team case trends", "Escalate to BUHR"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildCandidateScreeningResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Candidate screening checklist for an **HR Operations Analyst** role:\n\n- **Core fit:** HR operations, employee records, HRIS coordination, SLA-driven support\n- **Risk checks:** weak process discipline, low stakeholder ownership, poor data accuracy\n- **Interview focus:** payroll coordination, ticket handling, policy interpretation, and escalation judgment\n- **Recommendation:** shortlist candidates who can explain HR workflows with measurable ownership examples`,
    language,
    {
      confidenceScore: 0.9,
      source: "Recruiting Workflow Assistant",
      action: { type: "candidate_screening" },
    },
    ["Suggest interview questions for an HR analyst role", "Help schedule candidate interviews this week", "Generate a job description for an HR analyst role"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildInterviewSchedulingResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Interview scheduling plan for **4 candidate interviews next week**:\n\n- Lock hiring manager, recruiter, and panel slots first\n- Use **30-45 minute** interview blocks with buffer time\n- Send one consolidated invite per candidate with panel names and meeting link\n- Share reminders **24 hours** before each round\n\nRecommended route: Recruiting Ops or the recruiter owner should confirm panel availability before finalizing slots.`,
    language,
    {
      confidenceScore: 0.9,
      source: "Recruiting Scheduling Assistant",
      action: { type: "interview_scheduling" },
    },
    ["Screen candidates for an HR operations analyst role", "Suggest interview questions for an HR analyst role", "Generate a job description for an HR analyst role"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildInterviewQuestionsResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Suggested interview questions for an **HR Analyst** role:\n\n- Tell me about a time you handled a high-volume employee support queue.\n- How would you investigate a payroll discrepancy raised by an employee?\n- What controls would you use to keep HR data accurate?\n- How do you balance policy compliance with employee experience?\n- What metrics would you track for HR service delivery?`,
    language,
    {
      confidenceScore: 0.91,
      source: "Recruiting Interview Assistant",
      action: { type: "interview_questions" },
    },
    ["Screen candidates for an HR operations analyst role", "Help schedule candidate interviews this week", "Generate a job description for an HR analyst role"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildCrossPolicyComparisonResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `Here is the policy-level comparison:\n\n- **Joining Policy:** focuses on new-joiner relocation support such as temporary accommodation, brokerage, house deposit, notice pay buyout, and joining expense claims.\n- **Talent Mobility Policy:** focuses on internal movement support such as **MAB** and **SIA** during structured mobility or rotation.\n\nIn short, Joining Policy supports **onboarding relocation**, while Talent Mobility supports **internal transfer or rotation** changes.`,
    language,
    {
      confidenceScore: 0.93,
      source: "Cross-Policy Comparison Assistant",
      action: { type: "cross_policy_compare" },
    },
    ["What is the joining claim deadline?", "What is the mobility adjustment benefit for my grade?", "What happens if I transfer and resign within a year?"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildRecoveryComparisonResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  return buildActionResponse(
    `The clearest recovery rule in the current policies is from the **Joining Policy**.\n\nIf an employee quits within **1 year of joining**, recovery can include:\n- **Joining Bonus**\n- **Relocation Expenses**\n- **Notice Pay Buyout**\n- **Variable Pay Reimbursement including brokerage**\n\nFor a transfer or mobility move, review the specific mobility approval terms separately because the same recovery wording is not stated the same way in the Talent Mobility Policy extract used here.`,
    language,
    {
      confidenceScore: 0.9,
      source: "Cross-Policy Recovery Assistant",
      action: { type: "cross_policy_recovery" },
    },
    ["Compare joining relocation benefits vs talent mobility relocation benefits", "What is the joining claim deadline?", "Show mobility support for my grade"],
    "action_trigger",
    query,
    record.profile,
  );
}

function findKnowledgeAssetProof(query: string, knowledgeAssets: KnowledgeAsset[]) {
  const normalized = normalizeEmployeeChatText(query);
  const topicHints = [
    normalized.includes("joining") ? "joining" : "",
    normalized.includes("claim deadline") ? "claimed within one year" : "",
    normalized.includes("brokerage") ? "brokerage" : "",
    normalized.includes("leave") ? "leave" : "",
  ].filter(Boolean);

  for (const asset of knowledgeAssets) {
    const content = asset.content ?? "";
    const lower = content.toLowerCase();
    const matchedHint = topicHints.find((hint) => lower.includes(hint));
    if (!matchedHint) continue;
    const index = lower.indexOf(matchedHint);
    const excerpt = content.slice(Math.max(0, index - 60), Math.min(content.length, index + 180)).replace(/\s+/g, " ").trim();
    return { asset, excerpt };
  }

  return null;
}

function buildUploadedProofResponse(record: EmployeeRecord, language: SupportedLanguage, query: string, knowledgeAssets: KnowledgeAsset[]): ActionWorkflowResponse | null {
  const proof = findKnowledgeAssetProof(query, knowledgeAssets);
  if (!proof) return null;

  return buildActionResponse(
    `The strongest uploaded proof is **${proof.asset.name}**.\n\nRelevant excerpt:\n"${proof.excerpt}"\n\nUse that file as the first supporting document for this HR question.`,
    language,
    {
      confidenceScore: 0.95,
      source: "Uploaded Knowledge Proof Assistant",
      action: { type: "uploaded_proof_lookup" },
    },
    ["Compare this uploaded document with policy", "Open the source policy", "Create HR ticket"],
    "action_trigger",
    query,
    record.profile,
  );
}

function buildAmbiguousTriageResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const normalized = normalizeEmployeeChatText(query);
  const text = normalized.includes("salary")
    ? `I can help, but **salary issue** is too broad to answer safely.\n\nPlease clarify whether this is about **payslip**, **tax deduction**, **PF**, or **net pay change**. If you want, I can also route it directly to Payroll Ops.`
    : normalized.includes("attendance")
      ? `I can help, but **attendance issue** can mean a missing punch, wrong status, or approval delay.\n\nTell me which one it is, or I can start with your current attendance snapshot and approver chain.`
      : normalized.includes("joining")
        ? `I can help, but **joining amount** can refer to joining bonus, brokerage, relocation, or claim deadline.\n\nTell me which part you mean, and I will narrow it down fast.`
        : `I can help, but **reimbursement problem** can fall under travel, local conveyance, joining relocation, or payroll.\n\nTell me which reimbursement type is affected, and I will route you correctly.`;

  return buildActionResponse(
    text,
    language,
    {
      confidenceScore: 0.86,
      source: "Ambiguity Clarifier",
      action: { type: "clarification_triage" },
    },
    ["Show my latest payslip", "Show my attendance status", "Create HR ticket"],
    "general",
    query,
    record.profile,
  );
}

function buildWorkflowCompletionResponse(record: EmployeeRecord, language: SupportedLanguage, query: string): ActionWorkflowResponse {
  const ticket = createCaseFromConversation(record, "hr_ticket", query, "Workflow completion request", "BUHR", "confidential");
  return buildActionResponse(
    `The workflow has been started.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Assignment Group: **${ticket.assignmentGroup}**\n- SLA: **${ticket.slaHours} hours**\n- Due By: **${formatDateTime(ticket.dueAt)}**\n\nNext step: the assigned queue can review, notify the approver, and track this item through closure.`,
    language,
    {
      confidenceScore: 1,
      source: "Workflow Automation Assistant",
      action: { type: "workflow_completion", caseId: ticket.id, route: ticket.route },
    },
    ["Email my chat transcript to HR", "Show my approver chain", "Escalate to BUHR"],
    "action_trigger",
    query,
    record.profile,
  );
}

export function resolveEmployeeActionQuery(
  rawQuery: string,
  profile: EmployeeProfile,
  language: SupportedLanguage,
  knowledgeAssets: KnowledgeAsset[] = [],
  _history: ChatMessage[] = [],
): ActionWorkflowResponse | null {
  const query = normalizeEmployeeChatText(rawQuery);
  const wantsEmployeeSpecificAnswer = isEmployeeSpecificQuestion(rawQuery);
  const record = getEmployeeRecord(profile.uid);

  if (/meri leave balance|mera leave balance|meri chhutti|meri छुट्टी|મારી leave balance|maru leave balance/i.test(rawQuery)) {
    return buildLeaveBalanceResponse(record, language === "english" ? "hindi" : language, rawQuery);
  }

  if (/maru payslip|મારું payslip|મારો payslip|meri payslip|mera payslip/i.test(rawQuery)) {
    return buildPayslipResponse(record, language === "english" ? "gujarati" : language, rawQuery);
  }

  if (/\bapply\b.*\bleave\b|\bbook\b.*\bleave\b|\bleave request\b.*\bnext friday\b|\bapply leave\b.*\bfriday\b/.test(query)) {
    return buildLeaveApplicationResponse(record, language, rawQuery);
  }

  if (/\bmissing punch\b|\battendance regularization\b|\bcorrect\b.*\bpunch\b|\bwrong attendance\b/.test(query)) {
    return buildAttendanceRegularizationResponse(record, language, rawQuery);
  }

  if (/\bdownload\b.*\bpayslip\b|\bpayslip pdf\b|\bopen payslip pdf\b/.test(query)) {
    return buildPayslipDownloadResponse(record, language, rawQuery);
  }

  if (/\bdependent details\b|\bupdate dependent\b|\bchange dependent\b|\badd dependent\b/.test(query)) {
    return buildDependentUpdateResponse(record, language, rawQuery);
  }

  if (/\bapril\b.*\bnet pay\b.*\bmarch\b|\bnet pay lower than march\b|\bpay lower than march\b/.test(query)) {
    return buildPayrollComparisonResponse(record, language, rawQuery);
  }

  if (/\bpf deducted twice\b|\btax higher\b|\bwrong salary\b|\bpayroll discrepancy\b|\bsalary issue\b/.test(query)) {
    return buildPayrollInvestigationResponse(record, language, rawQuery);
  }

  if (/\bretaliat/.test(query) && /\bgrievance\b/.test(query)) {
    const ticket = createCaseFromConversation(record, "grievance", rawQuery, "Grievance retaliation follow-up", "BUHR", "confidential");
    return buildActionResponse(
      `This should be treated as a **confidential grievance retaliation follow-up**.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Priority: **${ticket.priority}**\n- Next step: document the retaliation details and route it for BUHR review immediately.`,
      language,
      {
        confidenceScore: 0.97,
        source: "Employee Relations Workflow",
        action: { type: "grievance_retaliation_case", caseId: ticket.id, route: ticket.route },
      },
      ["Show grievance timelines", "Email my chat transcript to HR", "Escalate to BUHR"],
      "action_trigger",
      rawQuery,
      record.profile,
    );
  }

  if (/\bcompare\b.*\bjoining\b.*\bmobility\b|\bjoining relocation\b.*\btalent mobility\b|\btalent mobility\b.*\bjoining relocation\b/.test(query)) {
    return buildCrossPolicyComparisonResponse(record, language, rawQuery);
  }

  if (/\btransfer\b.*\bresign\b.*\byear\b|\bmove\b.*\bresign\b.*\byear\b|\bwhat gets recovered\b/.test(query)) {
    return buildRecoveryComparisonResponse(record, language, rawQuery);
  }

  if ((profile.role === "manager" || profile.role === "hrbp" || profile.role === "admin") && /\bteam leave\b|\bleave risk\b|\bpending approvals\b/.test(query)) {
    return buildManagerLeaveInsightsResponse(record, language, rawQuery);
  }

  if ((profile.role === "manager" || profile.role === "hrbp" || profile.role === "admin") && /\bapproval attention\b|\bwhich team members\b.*\bapproval\b|\bneed approval\b/.test(query)) {
    return buildManagerApprovalAttentionResponse(record, language, rawQuery);
  }

  if (/\bscreen candidate\b|\bcandidate screening\b|\bhr operations analyst role\b/.test(query)) {
    return buildCandidateScreeningResponse(record, language, rawQuery);
  }

  if (/\bschedule\b.*\binterview\b|\binterview scheduling\b|\b4 candidate interviews\b/.test(query)) {
    return buildInterviewSchedulingResponse(record, language, rawQuery);
  }

  if (/\binterview questions\b|\bsuggest questions\b.*\bhr analyst\b|\bquestions\b.*\bhr analyst\b/.test(query)) {
    return buildInterviewQuestionsResponse(record, language, rawQuery);
  }

  if (/\buploaded file\b|\bwhich file proves\b|\bcompare this uploaded file\b/.test(query)) {
    const proofResponse = buildUploadedProofResponse(record, language, rawQuery, knowledgeAssets);
    if (proofResponse) return proofResponse;
  }

  if (/^(salary issue|joining amount|my reimbursement problem|something wrong in attendance)$/i.test(rawQuery.trim())) {
    return buildAmbiguousTriageResponse(record, language, rawQuery);
  }

  if (/\bcreate\b.*\bcase\b.*\bassign\b|\bnotify approver\b|\btrack sla\b|\bassign it and tell me the sla\b/.test(query)) {
    return buildWorkflowCompletionResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\b(my|current|latest)\b.*\bleave\b|\bleave balance\b|\battendance\b/.test(query))) {
    return buildLeaveBalanceResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\bpayslip\b|\bpay stub\b|\bpaystub\b|\bsalary slip\b/.test(query))) {
    return buildPayslipResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\bbenefit\b|\binsurance\b|\bhealth plan\b|\benrollment\b/.test(query))) {
    return buildBenefitsResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\bapprover\b|\bapproval chain\b|\bwho approves\b|\bmanager\b.*\bapprove\b/.test(query))) {
    return buildApproverResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\btravel entitlement\b|\bmy travel\b|\btravel claim guidance\b/.test(query))) {
    return buildTravelEntitlementResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\blocal conveyance\b|\bconveyance eligibility\b|\breimbursement\b.*\bconveyance\b/.test(query))) {
    return buildConveyanceResponse(record, language, rawQuery);
  }

  if (wantsEmployeeSpecificAnswer && (/\bjoining\b|\brelocation\b|\btemporary accommodation\b|\bpre-joining\b/.test(query))) {
    return buildJoiningResponse(record, language, rawQuery);
  }

  if (/\bcreate\b.*\bhr ticket\b|\braise\b.*\bhr ticket\b|\bescalate to buhr\b/.test(query)) {
    const ticket = createCaseFromConversation(record, "hr_ticket", rawQuery, "Employee support ticket", "BUHR", "confidential");
    return buildActionResponse(
      `I created an HR ticket for you.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Priority: **${ticket.priority}**\n- Status: **${ticket.status}**\n\nA BUHR reviewer can now pick this up.`,
      language,
      {
        confidenceScore: 1,
        source: "HR Case Workflow",
        action: { type: "create_hr_ticket", caseId: ticket.id, route: ticket.route },
      },
      ["Email my chat transcript to HR", "Show my approver chain", "What is the grievance process?"],
      "action_trigger",
      rawQuery,
      record.profile,
    );
  }

  if (/\bgrievance\b.*\b(case|ticket|report)\b|\braise grievance\b|\bfile grievance\b/.test(query)) {
    const ticket = createCaseFromConversation(record, "grievance", rawQuery, "Confidential grievance intake", "BUHR", "confidential");
    return buildActionResponse(
      `I created a confidential grievance case.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Assigned Queue: **${ticket.assignedTo}**\n\nIf you want, I can also export this chat transcript for HR follow-up.`,
      language,
      {
        confidenceScore: 1,
        source: "Grievance Workflow",
        action: { type: "create_grievance_case", caseId: ticket.id, route: ticket.route },
      },
      ["Email my chat transcript to HR", "Show grievance timelines", "Escalate further"],
      "action_trigger",
      rawQuery,
      record.profile,
    );
  }

  if (/\bposh\b.*\b(case|ticket|report)\b|\bsexual harassment\b|\bharassment\b.*\breport\b/.test(query)) {
    const ticket = createCaseFromConversation(record, "posh", rawQuery, "Strictly confidential POSH intake", "AIC", "strictly-confidential");
    return buildActionResponse(
      `I created a strictly confidential POSH intake.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Priority: **${ticket.priority}**\n\nThis should be handled through the confidential AIC route.`,
      language,
      {
        confidenceScore: 1,
        source: "POSH Workflow",
        action: { type: "create_posh_case", caseId: ticket.id, route: ticket.route },
      },
      ["Show POSH reporting steps", "Email my transcript to HR", "What happens next?"],
      "action_trigger",
      rawQuery,
      record.profile,
    );
  }

  if (/\bwhistleblower\b|\bethics helpline\b|\breport ethics\b/.test(query) && /\b(case|ticket|report|raise|file)\b/.test(query)) {
    const ticket = createCaseFromConversation(record, "whistleblower", rawQuery, "Whistleblower / ethics intake", "Ethics Helpline", "strictly-confidential");
    return buildActionResponse(
      `I created a whistleblower intake for confidential follow-up.\n\n- Case ID: **${ticket.id}**\n- Route: **${ticket.route}**\n- Status: **${ticket.status}**`,
      language,
      {
        confidenceScore: 1,
        source: "Ethics Workflow",
        action: { type: "create_whistleblower_case", caseId: ticket.id, route: ticket.route },
      },
      ["Show ethics helpline details", "Email my transcript to HR", "What protections do I have?"],
      "action_trigger",
      rawQuery,
      record.profile,
    );
  }

  return null;
}
