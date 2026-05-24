import { POLICY_META } from "../data/policies";
import {
  findLearningCaseMatch,
  getJoiningBenefitSummary,
  getPolicyGovernanceSnapshot,
  getTravelCityClass,
  getTravelEntitlementForGrade,
  type SupportedLanguage,
} from "./employeeExperienceService";
import { COMMON_CITY_ALIASES, isEmployeeSpecificQuestion, normalizeEmployeeChatText } from "./queryNormalization";

export interface PersonalizationContextLike {
  role?: string;
  language?: string;
  employeeId?: string;
  name?: string;
  grade?: string;
  location?: string;
  department?: string;
  businessUnit?: string;
  manager?: string;
  workMode?: string;
}

export interface EnhancedResponseData {
  policyId?: string;
  policyName?: string;
  policyUrl?: string;
  pageNumber?: number;
  confidenceScore?: number;
  source?: string;
  highlightTerms?: string[];
  keyPoints?: string[];
  policyVersion?: number;
  effectiveDate?: string;
  lastUpdatedAt?: number;
  governanceStatus?: string;
  clauseReference?: string;
  matchedCriteria?: string[];
  clarificationNeeded?: boolean;
  clarificationOptions?: string[];
  scenarioTitle?: string;
  scenarioComparison?: Array<{ label: string; current: string; hypothetical: string }>;
  approvalPath?: string[];
  exceptionGuidance?: string;
  documentsRequired?: string[];
  sla?: string;
  actionChecklist?: string[];
  safetyMode?: "standard" | "sensitive" | "high_risk";
  retentionNotice?: string;
  policyChanges?: string[];
  learnedFromCaseId?: string;
  localizedLanguage?: string;
  localizedSummary?: string;
  action?: {
    type: string;
    caseId?: string;
    route?: string;
  };
}

export interface ChatExperienceResponse {
  text: string;
  type: "general" | "policy_details" | "error";
  suggestedQuestions?: string[];
  data?: EnhancedResponseData;
}

interface ExperienceResponseLike {
  text: string;
  type: string;
  suggestedQuestions?: string[];
  data?: EnhancedResponseData;
}

const KNOWN_CITIES = Array.from(
  new Set([
    "ahmedabad",
    "bangalore",
    "delhi",
    "mumbai",
    "pune",
    "chennai",
    "hyderabad",
    "kolkata",
    "surat",
    "rajkot",
    "vadodara",
    "kochi",
    "mysore",
    ...Object.keys(COMMON_CITY_ALIASES),
  ]),
);

const GRADE_PATTERN = /\b(bmh9|bmh8|h8|bmh7|bm-h7|director|bmh6|h6|bmh5|h5|bmh4|h4|bmh3|bm-h3|m3h1|m3-h1|m3|m2|m1|mt|e2|get|e1|ot)\b/i;

function findPolicyMeta(policyId?: string, policyName?: string) {
  return POLICY_META.find((policy) =>
    (policyId && policy.id === policyId) ||
    (policyName && policy.name.toLowerCase() === policyName.toLowerCase()),
  );
}

function formatDate(dateValue?: string | number) {
  if (!dateValue) return undefined;
  const date = typeof dateValue === "number" ? new Date(dateValue) : new Date(dateValue);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function canonicalizeGrade(rawGrade?: string | null) {
  if (!rawGrade) return null;
  const normalized = rawGrade.trim().toLowerCase();
  switch (normalized) {
    case "director":
      return "Director";
    case "bm-h7":
      return "BMH7";
    case "bm-h3":
      return "BMH3";
    case "m3-h1":
      return "M3H1";
    default:
      return normalized.toUpperCase().replace("-", "");
  }
}

function extractTargetGrade(query: string) {
  const match = query.match(/(?:promoted to|grade changes? to|grade change to|move to grade|becomes?|for)\s+(bmh9|bmh8|h8|bmh7|bm-h7|director|bmh6|h6|bmh5|h5|bmh4|h4|bmh3|bm-h3|m3h1|m3-h1|m3|m2|m1|mt|e2|get|e1|ot)\b/i)
    ?? query.match(GRADE_PATTERN);
  return canonicalizeGrade(match?.[1] ?? null);
}

function extractTargetCity(query: string) {
  const normalized = normalizeEmployeeChatText(query);
  const directMatch = KNOWN_CITIES.find((city) =>
    normalized.includes(`move to ${city}`) ||
    normalized.includes(`shift to ${city}`) ||
    normalized.includes(`relocate to ${city}`) ||
    normalized.includes(`in ${city}`),
  );

  if (!directMatch) return null;
  return directMatch === "ncr" ? "NCR" : directMatch.charAt(0).toUpperCase() + directMatch.slice(1);
}

function buildLocalizationSummary(language: string | undefined, response: ExperienceResponseLike) {
  if (!language || language === "english") return undefined;

  const summaryPoints = response.data?.keyPoints?.slice(0, 3) ?? [];
  const policyName = response.data?.policyName ?? "HR policy";
  const keyPointText = summaryPoints.length > 0 ? summaryPoints.join(", ") : response.text.split("\n")[0];

  if (language === "hindi") {
    return `हिंदी सारांश: यह उत्तर ${policyName} पर आधारित है। मुख्य बिंदु: ${keyPointText}.`;
  }

  if (language === "gujarati") {
    return `ગુજરાતી સારાંશ: આ જવાબ ${policyName} પર આધારિત છે. મુખ્ય મુદ્દા: ${keyPointText}.`;
  }

  return undefined;
}

function buildActionChecklist(policyId: string | undefined, query: string, userContext: PersonalizationContextLike) {
  const normalized = normalizeEmployeeChatText(query);
  const checklists: Record<string, string[]> = {
    "domestic-travel": [
      "Check that the trip is business-related and within the eligible policy scope.",
      `Get approval from ${userContext.manager ?? "your reporting manager"} before final booking.`,
      "Book through myBiz and keep hotel, cab, and meal proofs ready for settlement.",
    ],
    "local-conveyance": [
      "Confirm whether your location and company car status affect eligibility.",
      "Submit the claim in Orapps / ESMS with distance or bill support.",
      "Keep manager approval and the trip purpose ready for audit.",
    ],
    "talent-mobility": [
      "Confirm the target grade, source city, and destination city before calculating benefit impact.",
      "Check whether CHRO or CEO approval is required for any exception.",
      "Keep relocation bills, rent proofs, and movement timeline ready.",
    ],
    "joining-policy": [
      "Confirm claim deadlines from your date of joining before submitting expenses.",
      "Keep relocation, transport, and notice-pay documents ready.",
      "Check whether any recovery applies if you exit within the defined period.",
    ],
    "posh-policy": [
      "Preserve messages, dates, witnesses, and any supporting evidence.",
      "Use the confidential route that feels safest for you right now.",
      "If urgent, escalate immediately instead of waiting for a complete write-up.",
    ],
    "grievance-mechanism": [
      "Write a short factual summary with dates, people involved, and desired resolution.",
      "Choose BUHR or Ethics Helpline based on confidentiality needs.",
      "Track the case ID and escalation timeline after filing.",
    ],
    whistleblower: [
      "Use the Ethics Helpline route if anonymity or retaliation risk matters.",
      "Keep the complaint factual and specific.",
      "Avoid sharing the report broadly outside the formal channel.",
    ],
    "gender-policy": [
      "Note the incident details, any witnesses, and prior escalation attempts.",
      "Choose the safest reporting route for you.",
      "Escalate through Ethics Helpline if direct local escalation feels unsafe.",
    ],
  };

  if (policyId && checklists[policyId]) return checklists[policyId];

  if (/\bleave|attendance\b/.test(normalized)) {
    return [
      "Check your live balance or attendance snapshot first.",
      `Confirm whether ${userContext.manager ?? "your manager"} needs to approve the next step.`,
      "Raise an HR ticket if the mismatch remains after one review.",
    ];
  }

  return [
    "Confirm the exact policy, grade, and location before you act.",
    "Keep supporting proof ready if this needs approval or reimbursement.",
    "Escalate to HR if any part of the policy still looks ambiguous.",
  ];
}

function buildApprovalPath(policyId?: string, userContext?: PersonalizationContextLike) {
  switch (policyId) {
    case "domestic-travel":
      return {
        approvalPath: [
          `${userContext?.manager ?? "Reporting manager"} approval`,
          "myBiz / travel desk booking validation",
          "Expense settlement audit",
        ],
        exceptionGuidance: "Higher-cost exceptions usually need BM-grade or higher approval before booking.",
        documentsRequired: ["Travel purpose", "Approved itinerary", "Bills and invoices"],
        sla: "Booking approval: same day to 1 business day. Settlement: within 15 days of trip completion.",
      };
    case "local-conveyance":
      return {
        approvalPath: [`${userContext?.manager ?? "Reporting manager"} approval`, "ESMS claim review", "Finance reimbursement posting"],
        exceptionGuidance: "Location-specific restrictions, especially Ahmedabad company-car cases, should be reviewed before submission.",
        documentsRequired: ["Distance details or bills", "Business purpose", "Manager approval"],
        sla: "Standard reimbursement review: 3 to 5 business days.",
      };
    case "talent-mobility":
      return {
        approvalPath: ["Business HR review", "Mobility policy validation", "CHRO / CEO exception approval if needed"],
        exceptionGuidance: "Managers cannot block mobility under normal policy; exception authority sits with CHRO or CEO.",
        documentsRequired: ["Transfer confirmation", "Source and destination city", "Relocation proofs"],
        sla: "Mobility exception review: 3 to 7 business days.",
      };
    case "joining-policy":
      return {
        approvalPath: ["HR operations verification", "Hiring / BUHR confirmation", "Payroll or reimbursement release"],
        exceptionGuidance: "Any extension beyond standard deadlines should be routed through HR operations with documented justification.",
        documentsRequired: ["DOJ proof", "Expense bills", "Transport / relocation documents"],
        sla: "Joining reimbursement review: 5 to 7 business days after document-complete submission.",
      };
    case "posh-policy":
      return {
        approvalPath: ["Confidential intake", "AIC review", "Protected investigation workflow"],
        exceptionGuidance: "Use the most confidential route available immediately if safety or retaliation is a concern.",
        documentsRequired: ["Written complaint or email", "Evidence if available", "Incident timeline"],
        sla: "Sensitive-case triage should begin immediately after intake.",
      };
    case "grievance-mechanism":
      return {
        approvalPath: ["BUHR or Ethics Helpline intake", "Investigation review", "Escalation if unresolved"],
        exceptionGuidance: "Anonymous reporting may be possible via the Ethics Helpline if enough detail is supplied.",
        documentsRequired: ["Issue summary", "Dates and names", "Any evidence or prior escalation notes"],
        sla: "Initial triage: 1 to 2 business days.",
      };
    case "whistleblower":
      return {
        approvalPath: ["Ethics Helpline intake", "Independent review", "Protected follow-up"],
        exceptionGuidance: "Use the helpline if confidentiality or retaliation risk is material.",
        documentsRequired: ["Specific allegation summary", "Evidence if available"],
        sla: "Initial ethics intake: immediate acknowledgment through the official channel.",
      };
    case "gender-policy":
      return {
        approvalPath: ["BUHR / line manager route", "Ethics escalation if needed", "Formal review"],
        exceptionGuidance: "Use Ethics Helpline if local reporting feels unsafe or compromised.",
        documentsRequired: ["Incident notes", "Witness names if any", "Prior escalation details"],
        sla: "Initial review: 1 to 3 business days depending on route.",
      };
    default:
      return undefined;
  }
}

export function buildClarificationResponse(query: string, userContext: PersonalizationContextLike): ChatExperienceResponse | null {
  const normalized = normalizeEmployeeChatText(query);
  const wantsEmployeeSpecificAnswer = isEmployeeSpecificQuestion(query);
  if (normalized.length < 6) return null;

  const hasExplicitPolicyName =
    /\b(domestic travel policy|local conveyance policy|joining policy|gender policy|grievance mechanism policy|posh policy|whistleblower policy|talent mobility policy)\b/.test(normalized);
  const hasPolicyLockPhrase =
    /\bunder the\b|\busing only the\b|\bin the\b|\bas per the\b|\baccording to(?: the)?\b|\bfrom the\b|\bplease use the\b|\buse the\b|\bi need the exact\b/.test(normalized);
  const hasRuleSeekingIntent =
    /\bexact rule\b|\bclarify this rule\b|\banswer this exact point\b|\bprecise rule\b|\bpolicy wording\b|\banswer this exactly\b|\bexact .* wording\b|\brule under\b|\bthis exact rule\b|\bthis point\b|\btell me clearly\b|\bedge cases?\b/.test(normalized);
  const isPolicyLockedExactRule = hasExplicitPolicyName && hasPolicyLockPhrase && hasRuleSeekingIntent;
  const isSpecificPolicyLockedQuestion =
    hasExplicitPolicyName &&
    hasPolicyLockPhrase &&
    /\b(laundry|guest house|address|location|alcohol|cigarette|mini-bar|web check-in|spouse|dependent|women|female|booking|book|tool|mybiz|advance|days|claim|claims|submit|settlement|deadline|reimbursable|covered|class|city|driver|wages|pre-joining|accommodation|recovery|leave within|investigate|same[- ]day|bike|scooter|two-wheeler|per km)\b/.test(normalized);

  const isDirectIntentQuestion = /\b(goal|objective|purpose|transformation|aim|mission|vision|role|who is|who can|authority|approve|approval|exception)\b/.test(normalized);

  if (isPolicyLockedExactRule || isSpecificPolicyLockedQuestion || isDirectIntentQuestion) {
    return null;
  }

  if (/^(policy|travel policy|leave policy|joining policy|mobility policy)$/.test(normalized)) {
    return {
      text: "I can help with that. Which exact topic do you want first: entitlement, approval path, reimbursement claim, or exception handling?",
      type: "general",
      suggestedQuestions: [
        wantsEmployeeSpecificAnswer ? "Show my travel entitlement" : "Show travel entitlement",
        "Explain approval path for reimbursements",
        "What exceptions are allowed under mobility policy?",
      ],
      data: {
        confidenceScore: 1,
        source: "Clarification Engine",
        clarificationNeeded: true,
        clarificationOptions: ["entitlement", "approval path", "reimbursement claim", "exception handling"],
        safetyMode: "standard",
      },
    };
  }

  if (/\btravel\b/.test(normalized) && !/\b(class|city|grade|booking|claim|approval|cab|hotel|lodging|boarding|flight|train)\b/.test(normalized)) {
    return {
      text: `I can make the answer more accurate if you tell me one thing: do you want the **entitlement**, **booking rule**, **claim timeline**, or **approval path**${wantsEmployeeSpecificAnswer && userContext.grade ? ` for ${userContext.grade}` : ""}?`,
      type: "general",
      suggestedQuestions: [
        `${wantsEmployeeSpecificAnswer ? "Show my travel entitlement" : "Show travel entitlement"}${wantsEmployeeSpecificAnswer && userContext.location ? ` in ${userContext.location}` : ""}`,
        "Explain travel booking rules",
        "What is the travel claim timeline?",
      ],
      data: {
        confidenceScore: 1,
        source: "Clarification Engine",
        clarificationNeeded: true,
        clarificationOptions: ["entitlement", "booking rule", "claim timeline", "approval path"],
      },
    };
  }

  if (/\bmobility\b/.test(normalized) && !/\b(mab|sia|grade|city|allowance|relocation|approval)\b/.test(normalized)) {
    return {
      text: "To answer that accurately, do you want the mobility benefit amount, relocation support, or the exception / approval route?",
      type: "general",
      suggestedQuestions: [
        `What is the mobility adjustment benefit for ${wantsEmployeeSpecificAnswer ? (userContext.grade ?? "M2") : "M2"}?`,
        "Explain relocation support under mobility policy",
        "Who can approve a mobility exception?",
      ],
      data: {
        confidenceScore: 1,
        source: "Clarification Engine",
        clarificationNeeded: true,
        clarificationOptions: ["benefit amount", "relocation support", "exception route"],
      },
    };
  }

  return null;
}

export function buildScenarioSimulationResponse(query: string, userContext: PersonalizationContextLike): ChatExperienceResponse | null {
  const normalized = normalizeEmployeeChatText(query);
  const wantsEmployeeSpecificAnswer = isEmployeeSpecificQuestion(query);
  const isScenario = /\bwhat if\b|\bif i\b|\bif my\b|\bif we\b/.test(normalized);
  if (!isScenario) return null;

  const targetGrade = extractTargetGrade(normalized);
  const targetCity = extractTargetCity(normalized);
  const currentGrade = wantsEmployeeSpecificAnswer ? (canonicalizeGrade(userContext.grade ?? null) ?? "M2") : null;
  const currentCity = wantsEmployeeSpecificAnswer ? (userContext.location ?? "Ahmedabad") : null;

  if ((/\btravel|lodging|boarding|cab|conveyance\b/.test(normalized)) && (targetGrade || targetCity || wantsEmployeeSpecificAnswer)) {
    const nextGrade = targetGrade ?? currentGrade ?? "M2";
    const nextCity = targetCity ?? currentCity ?? "Ahmedabad";
    const currentTravel = getTravelEntitlementForGrade(currentGrade ?? nextGrade, currentCity ?? nextCity);
    const nextTravel = getTravelEntitlementForGrade(nextGrade, nextCity);

    return {
      text:
        `${wantsEmployeeSpecificAnswer ? `Scenario simulation for **${currentGrade} / ${currentCity}** vs **${nextGrade} / ${nextCity}**:` : `Scenario simulation for **${nextGrade} / ${nextCity}** based on the policy question:`}\n\n` +
        `${wantsEmployeeSpecificAnswer ? `- Current lodging: **${currentTravel.lodging}**\n` : ""}` +
        `- Hypothetical lodging: **${nextTravel.lodging}**\n` +
        `${wantsEmployeeSpecificAnswer ? `- Current boarding: **${currentTravel.boarding}**\n` : ""}` +
        `- Hypothetical boarding: **${nextTravel.boarding}**\n` +
        `${wantsEmployeeSpecificAnswer ? `- Current cab guidance: **${currentTravel.cab}**\n` : ""}` +
        `- Hypothetical cab guidance: **${nextTravel.cab}**\n\n` +
        `${wantsEmployeeSpecificAnswer ? "This is a profile-aware simulation, so confirm the final route with the current policy version before submitting a claim." : "This is a policy-based simulation from the details in your question, so confirm any final exception route before submitting a claim."}`,
      type: "policy_details",
      suggestedQuestions: [
        "Explain the approval path for this scenario",
        "What documents would I need for this change?",
        "Show the exact policy source for this scenario",
      ],
      data: {
        policyId: "domestic-travel",
        policyName: "Domestic Travel Policy",
        confidenceScore: 0.96,
        source: "Scenario Simulator",
        keyPoints: [
          ...(wantsEmployeeSpecificAnswer ? [`Current: ${currentGrade} in ${currentTravel.cityClass}`] : []),
          `Hypothetical: ${nextGrade} in ${nextTravel.cityClass}`,
          `${wantsEmployeeSpecificAnswer ? "Lodging changes" : "Policy estimate"} from ${currentTravel.lodging} to ${nextTravel.lodging}`,
        ],
        scenarioTitle: "What-if entitlement simulation",
        scenarioComparison: [
          { label: "Lodging", current: wantsEmployeeSpecificAnswer ? currentTravel.lodging : "Policy baseline", hypothetical: nextTravel.lodging },
          { label: "Boarding", current: wantsEmployeeSpecificAnswer ? currentTravel.boarding : "Policy baseline", hypothetical: nextTravel.boarding },
          { label: "Cab", current: wantsEmployeeSpecificAnswer ? currentTravel.cab : "Policy baseline", hypothetical: nextTravel.cab },
          { label: "City class", current: wantsEmployeeSpecificAnswer ? currentTravel.cityClass : "From asked city", hypothetical: nextTravel.cityClass },
        ],
      },
    };
  }

  if ((/\bjoining|relocation\b/.test(normalized)) && (targetGrade || targetCity || wantsEmployeeSpecificAnswer)) {
    const nextGrade = targetGrade ?? currentGrade ?? "M2";
    return {
      text:
        `${wantsEmployeeSpecificAnswer ? `Here is the joining-policy simulation for **${currentGrade}** vs **${nextGrade}**:` : `Here is the joining-policy simulation for **${nextGrade}** based on the question:`}\n\n` +
        `${wantsEmployeeSpecificAnswer ? `- Current support: **${getJoiningBenefitSummary(currentGrade ?? nextGrade)}**\n` : ""}` +
        `- Hypothetical support: **${getJoiningBenefitSummary(nextGrade)}**\n\n` +
        `If this move also changes location, verify the final claim route and deadlines before submitting expenses.`,
      type: "policy_details",
      suggestedQuestions: [
        "What documents would this relocation need?",
        "Show joining claim deadlines",
        "Explain the approval path for joining support",
      ],
      data: {
        policyId: "joining-policy",
        policyName: "Joining Policy",
        confidenceScore: 0.94,
        source: "Scenario Simulator",
        scenarioTitle: "What-if joining support simulation",
        scenarioComparison: [
          ...(wantsEmployeeSpecificAnswer ? [{ label: "Current grade", current: currentGrade ?? nextGrade, hypothetical: nextGrade }] : []),
          { label: "Support", current: wantsEmployeeSpecificAnswer ? getJoiningBenefitSummary(currentGrade ?? nextGrade) : "Policy baseline", hypothetical: getJoiningBenefitSummary(nextGrade) },
        ],
      },
    };
  }

  return null;
}

export function buildPolicyDiffResponse(query: string): ChatExperienceResponse | null {
  const normalized = normalizeEmployeeChatText(query);
  if (!/\bwhat changed\b|\bwhat is new\b|\bdiff\b|\bdifference\b|\bversion\b|\bupdated\b/.test(normalized)) {
    return null;
  }

  const policy = POLICY_META.find((item) => normalized.includes(item.name.toLowerCase().replace(/ policy/g, "")) || normalized.includes(item.id));
  if (!policy) return null;

  const governance = getPolicyGovernanceSnapshot(policy.id, policy.name);
  if (!governance) return null;

  const previous = governance.previousVersions[0];
  const changes = [
    `Current version: v${governance.version}`,
    previous ? `Previous version available: v${previous.version}` : "No previous version snapshot stored yet",
    `Current lifecycle: ${governance.lifecycleStatus}`,
    `Effective date: ${formatDate(governance.effectiveDate) ?? governance.effectiveDate}`,
    governance.auditTrail[0] ? `Latest governance note: ${governance.auditTrail[0].note}` : "No recent governance note available",
  ];

  return {
    text:
      `Here is the latest change view for **${policy.name}**:\n\n` +
      changes.map((item) => `- ${item}`).join("\n") +
      `\n\nUse this as a governance diff summary. If you need a clause-level legal diff, review the prior version snapshot before publishing.`,
    type: "policy_details",
    suggestedQuestions: [
      `Does the latest ${policy.name} affect my grade?`,
      `What is the approval path under ${policy.name}?`,
      `Open the latest ${policy.name} source`,
    ],
    data: {
      policyId: policy.id,
      policyName: policy.name,
      source: "Policy Change Explainer",
      confidenceScore: 0.95,
      policyChanges: changes,
      policyVersion: governance.version,
      effectiveDate: governance.effectiveDate,
      lastUpdatedAt: governance.updatedAt,
      governanceStatus: governance.lifecycleStatus,
    },
  };
}

export function buildLearningCaseResponse(query: string): ChatExperienceResponse | null {
  const match = findLearningCaseMatch(query);
  if (!match) return null;

  const policyMeta = findPolicyMeta(match.policyId);
  return {
    text: `${match.approvedAnswer}\n\nThis answer is reinforced by a previously approved HR resolution pattern, so it is a good starting point. Please still verify any final policy exception before action.`,
    type: "policy_details",
    suggestedQuestions: [
      "Show the policy source for this answer",
      "Explain the approval path",
      "What documents would I need?",
    ],
    data: {
      policyId: match.policyId,
      policyName: policyMeta?.name,
      policyUrl: policyMeta?.fileUrl,
      source: "Approved Case Learning",
      confidenceScore: Math.min(0.97, match.confidence),
      learnedFromCaseId: match.id,
      keyPoints: ["Matched against approved HR answer memory", "Use as trusted starting guidance"],
    },
  };
}

export function buildHighRiskGuardrailResponse(query: string, policyId?: string): ChatExperienceResponse | null {
  const normalized = normalizeEmployeeChatText(query);

  if (/\bpayroll|salary issue|wrong salary|tax deduction|pf issue\b/.test(normalized)) {
    return {
      text: "This is a high-risk payroll topic, and I do not want to guess. Please verify the exact payroll period and raise it to Payroll Ops or BUHR with the payslip month, issue summary, and any supporting screenshot.",
      type: "error",
      suggestedQuestions: ["Show my latest payslip", "Create HR ticket", "What details should I send to Payroll Ops?"],
      data: {
        confidenceScore: 0.4,
        source: "High-Risk Guardrail",
        safetyMode: "high_risk",
        retentionNotice: "High-risk topics should be reviewed through the formal HR or payroll route before action.",
        actionChecklist: [
          "Confirm the exact month and component affected.",
          "Attach your payslip or supporting screenshot.",
          "Escalate through Payroll Ops or BUHR instead of relying on a guessed answer.",
        ],
      },
    };
  }

  if (/\bposh|harassment|sexual harassment|whistleblower|ethics complaint|grievance\b/.test(normalized) && !policyId) {
    return {
      text: "This looks sensitive, so I want to keep the answer safe and non-speculative. If you want, I can help you choose the correct reporting route now: BUHR, AIC / POSH route, or Ethics Helpline.",
      type: "error",
      suggestedQuestions: [
        "Show the POSH reporting route",
        "Show grievance reporting steps",
        "What is the ethics helpline?",
      ],
      data: {
        confidenceScore: 0.45,
        source: "High-Risk Guardrail",
        safetyMode: "sensitive",
        retentionNotice: "Sensitive topics should use the most confidential formal route available.",
      },
    };
  }

  return null;
}

export function enrichResponseForExperience<T extends ExperienceResponseLike>(
  response: T,
  query: string,
  userContext: PersonalizationContextLike,
): T {
  const wantsEmployeeSpecificAnswer = isEmployeeSpecificQuestion(query);
  const nextData: EnhancedResponseData = { ...(response.data ?? {}) };
  const policyMeta = findPolicyMeta(nextData.policyId, nextData.policyName);
  const governance = getPolicyGovernanceSnapshot(nextData.policyId, nextData.policyName);
  const approval = buildApprovalPath(nextData.policyId, userContext);

  if (policyMeta && !nextData.policyUrl) {
    nextData.policyUrl = policyMeta.fileUrl;
  }

  if (nextData.pageNumber && !nextData.clauseReference) {
    nextData.clauseReference = `Page ${nextData.pageNumber}`;
  }

  if (governance) {
    nextData.policyVersion ??= governance.version;
    nextData.effectiveDate ??= governance.effectiveDate;
    nextData.lastUpdatedAt ??= governance.updatedAt;
    nextData.governanceStatus ??= governance.lifecycleStatus;
  }

  if (approval) {
    nextData.approvalPath ??= approval.approvalPath;
    nextData.exceptionGuidance ??= approval.exceptionGuidance;
    nextData.documentsRequired ??= approval.documentsRequired;
    nextData.sla ??= approval.sla;
  }

  nextData.actionChecklist ??= buildActionChecklist(nextData.policyId, query, userContext);

  if (!nextData.safetyMode) {
    nextData.safetyMode = /posh|grievance|whistleblower|gender/.test(nextData.policyId ?? "") ? "sensitive" : "standard";
  }

  if (nextData.safetyMode !== "standard" && !nextData.retentionNotice) {
    nextData.retentionNotice = "Use the formal confidential route for final action and avoid relying on memory alone for sensitive cases.";
  }

  nextData.localizedLanguage = userContext.language;
  nextData.localizedSummary ??= buildLocalizationSummary(userContext.language, { ...response, data: nextData });

  if (wantsEmployeeSpecificAnswer) {
    const matchedCriteria = [
      userContext.grade ? `grade=${userContext.grade}` : "",
      userContext.location ? `location=${userContext.location}` : "",
      userContext.role ? `role=${userContext.role}` : "",
    ].filter(Boolean);

    if (matchedCriteria.length > 0) {
      nextData.matchedCriteria ??= matchedCriteria;
    }
  }

  return {
    ...response,
    data: nextData,
  } as T;
}
