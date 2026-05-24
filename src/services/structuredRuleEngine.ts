import { POLICY_META } from "../data/policies";
import {
  STRUCTURED_POLICY_RULES,
  type StructuredPolicyRule,
  type StructuredPolicyRuleType,
} from "../data/structuredPolicyRules";
import { analyzePolicyQuestion } from "./policyQuestionAnalysis";
import { normalizeEmployeeChatText } from "./queryNormalization";

export interface RankedPolicyRule {
  rule: StructuredPolicyRule;
  score: number;
  matchedCriteria: string[];
}

export interface StructuredRuleAnswer {
  text: string;
  type: "general" | "policy_details" | "error";
  suggestedQuestions?: string[];
  data?: {
    policyId?: string;
    policyName?: string;
    policyUrl?: string;
    pageNumber?: number;
    confidenceScore?: number;
    source?: string;
    highlightTerms?: string[];
    keyPoints?: string[];
    clauseReference?: string;
    matchedCriteria?: string[];
  };
}

const RULE_TYPE_SYNONYMS: Record<StructuredPolicyRuleType, string[]> = {
  classification: ["class", "city", "classification"],
  limit_amount: ["limit", "allowance", "entitlement", "rate", "amount", "mab", "sia"],
  timeline: ["timeline", "days", "working days", "when", "how long", "acknowledge", "investigation", "resolution"],
  approval_path: ["approve", "approval", "who approves", "manager", "workflow", "route"],
  reporting_route: ["reporting", "level", "route", "channel", "escalation", "buhr", "hod"],
  anonymity: ["anonymous", "concern", "complaint", "investigation", "verifiable evidence"],
  eligibility: ["eligible", "eligibility", "applies", "covered", "scope", "who"],
  reimbursement_rate: ["reimbursement", "per km", "rate", "bike", "car"],
  recovery: ["recover", "recovery", "f&f", "final settlement", "quit", "one year"],
  exception: ["exception", "however", "same-day", "delay", "freshening", "women"],
  delay_rule: ["delay", "delayed", "3 hours", "mybiz", "cancel", "modify"],
  same_day_exception: ["same day", "same-day", "freshening", "guest house", "service apartment"],
  relocation_transport: ["household goods", "packers", "700 km", "50 per km", "60 per km", "actuals"],
  women_entitlement: ["women", "next higher grade", "hotel entitlement"],
  confidentiality: ["confidential", "identity", "secrecy", "privacy"],
  retaliation: ["retaliation", "victimization", "protected", "discrimination"],
  metadata: ["effective date", "issue date", "policy number", "effective from"],
  definition: ["definition", "means", "refers to"],
  benefit: ["benefit", "support", "assistance", "relocation"],
  procedure: ["procedure", "process", "complaint", "file", "raise"],
  coverage: ["coverage", "scope", "included", "applies"],
  reference: ["policy", "rule"],
};

const SUGGESTIONS_BY_POLICY: Record<string, string[]> = {
  "domestic-travel": [
    "Show domestic travel limits",
    "What is the delayed-flight rule?",
    "What is the same-day return rule?",
  ],
  "local-conveyance": [
    "What is the two-wheeler reimbursement rate?",
    "What is the four-wheeler reimbursement rate?",
    "Who approves local conveyance claims?",
  ],
  "joining-policy": [
    "What is the household-goods reimbursement rule?",
    "What happens if someone quits within one year?",
    "What are the joining claim deadlines?",
  ],
  "gender-policy": [
    "How do I report gender discrimination?",
    "Who is the next reporting level after BUHR?",
    "Is confidentiality maintained under the Gender Policy?",
  ],
  "grievance-mechanism": [
    "How do I raise a grievance?",
    "Within how many days should HR acknowledge it?",
    "Can anonymous grievances be considered?",
  ],
  "posh-policy": [
    "How do I file a POSH complaint?",
    "Are anonymous POSH complaints entertained?",
    "What confidentiality protections apply?",
  ],
  whistleblower: [
    "Is the whistleblower identity kept confidential?",
    "What retaliation protection applies?",
    "How can I follow up on a whistleblower concern?",
  ],
  "talent-mobility": [
    "What is the mobility adjustment benefit for M2?",
    "What is settling-in assistance?",
    "Who approves mobility exceptions?",
  ],
};

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

const TOKEN_STOPWORDS = new Set([
  "the",
  "and",
  "for",
  "with",
  "from",
  "that",
  "this",
  "what",
  "when",
  "where",
  "which",
  "who",
  "can",
  "does",
  "under",
  "policy",
  "please",
  "tell",
  "using",
  "only",
  "just",
  "your",
  "about",
]);

function normalizeForMatching(value: string) {
  return normalizeEmployeeChatText(value)
    .replace(/[-/]/g, " ")
    .replace(/[?!.:,()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(value: string) {
  return normalizeForMatching(value)
    .split(/\s+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 2 && !TOKEN_STOPWORDS.has(token));
}

function overlaps(queryTokens: string[], haystack: string[]) {
  const hay = new Set(haystack);
  return queryTokens.filter((token) => hay.has(token));
}

function findPhraseMatches(normalizedText: string, phrases: string[]) {
  return phrases.filter((phrase) => {
    const normalizedPhrase = normalizeForMatching(phrase);
    return normalizedPhrase.length > 0 && normalizedText.includes(normalizedPhrase);
  });
}

function mapQuestionTypeToRuleTypes(answerType: ReturnType<typeof analyzePolicyQuestion>["answerType"]) {
  switch (answerType) {
    case "metadata":
      return ["metadata"];
    case "applicability":
      return ["eligibility", "coverage"];
    case "timeline":
      return ["timeline"];
    case "reporting_route":
      return ["reporting_route", "procedure"];
    case "anonymity":
      return ["anonymity", "confidentiality", "procedure"];
    case "confidentiality":
      return ["confidentiality"];
    case "retaliation":
      return ["retaliation"];
    case "delay_rule":
      return ["delay_rule", "exception", "procedure"];
    case "same_day_exception":
      return ["same_day_exception", "exception", "procedure"];
    case "recovery":
      return ["recovery", "benefit"];
    case "relocation_transport":
      return ["relocation_transport", "benefit", "limit_amount", "reimbursement_rate"];
    case "reimbursement_rate":
      return ["reimbursement_rate", "limit_amount"];
    case "women_entitlement":
      return ["women_entitlement", "exception", "limit_amount", "eligibility"];
    case "approval_path":
      return ["approval_path", "procedure"];
    default:
      return [];
  }
}

function buildRuleSearchText(rule: StructuredPolicyRule) {
  return [
    rule.policyName,
    rule.section,
    rule.clause,
    rule.ruleType,
    ...rule.conditions,
    ...rule.keywords,
    ...rule.sampleQueries,
    rule.answer,
    rule.exception ?? "",
  ].join(" ");
}

const RULE_SEARCH_TEXT = new Map(STRUCTURED_POLICY_RULES.map((rule) => [rule.id, tokenize(buildRuleSearchText(rule))] as const));

export function rankStructuredPolicyRules(rawQuery: string, limit = 5): RankedPolicyRule[] {
  const analysis = analyzePolicyQuestion(rawQuery);
  const normalizedQuery = normalizeForMatching(analysis.normalizedQuery);
  const queryTokens = unique([
    ...analysis.highlightTerms,
    ...analysis.numericTerms,
    ...tokenize(analysis.normalizedQuery),
  ]);
  const preferredRuleTypes = mapQuestionTypeToRuleTypes(analysis.answerType);

  const ranked = STRUCTURED_POLICY_RULES.map((rule) => {
    const criteria: string[] = [];
    let score = 0;
    const normalizedRuleText = normalizeForMatching(buildRuleSearchText(rule));

    if (analysis.preferredPolicyIds.includes(rule.policyId)) {
      score += analysis.policyLocked ? 24 : 12;
      criteria.push("policy-lock");
    } else if (analysis.preferredPolicyIds.length > 0) {
      score -= 10;
    }

    if (preferredRuleTypes.includes(rule.ruleType)) {
      score += 18;
      criteria.push(`rule-type:${rule.ruleType}`);
    } else if (preferredRuleTypes.length > 0 && analysis.answerType !== "generic") {
      score -= 10;
    }

    const ruleTokens = RULE_SEARCH_TEXT.get(rule.id) ?? [];
    const overlappingTokens = overlaps(queryTokens, ruleTokens);
    if (overlappingTokens.length > 0) {
      score += overlappingTokens.length * 2;
      criteria.push(`tokens:${overlappingTokens.slice(0, 8).join(",")}`);
    }

    const overlappingConditions = overlaps(queryTokens, rule.conditions.flatMap((condition) => tokenize(condition)));
    if (overlappingConditions.length > 0) {
      score += overlappingConditions.length * 5;
      criteria.push(`conditions:${overlappingConditions.slice(0, 6).join(",")}`);
    }

    const requiredPhraseMatches = findPhraseMatches(normalizedRuleText, analysis.requiredTerms);
    if (requiredPhraseMatches.length > 0) {
      score += requiredPhraseMatches.length * 8;
      criteria.push(`required:${requiredPhraseMatches.slice(0, 4).join(",")}`);
    } else if (analysis.policyLocked && analysis.requiredTerms.length > 0 && analysis.answerType !== "generic") {
      score -= 18;
    }

    const typeSynonyms = RULE_TYPE_SYNONYMS[rule.ruleType] ?? [];
    const overlappingSynonyms = typeSynonyms.filter((synonym) => normalizedQuery.includes(normalizeForMatching(synonym)));
    if (overlappingSynonyms.length > 0) {
      score += overlappingSynonyms.length * 3;
      criteria.push(`intent:${overlappingSynonyms.slice(0, 5).join(",")}`);
    }

    for (const number of analysis.numericTerms) {
      if (rule.answer.includes(number) || rule.conditions.some((condition) => condition.includes(number))) {
        score += 5;
        criteria.push(`number:${number}`);
      }
    }

    if (rule.sampleQueries.some((query) => normalizeEmployeeChatText(query) === analysis.normalizedQuery)) {
      score += 30;
      criteria.push("sample-query-exact");
    }

    return {
      rule,
      score,
      matchedCriteria: criteria,
    };
  })
    .filter((entry) => entry.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score;
      return left.rule.page - right.rule.page;
    });

  return ranked.slice(0, limit);
}

function buildPolicyUrl(policyId: string) {
  return POLICY_META.find((policy) => policy.id === policyId)?.fileUrl;
}

function computeConfidence(top: RankedPolicyRule | undefined, second: RankedPolicyRule | undefined) {
  if (!top) return 0;
  const margin = top.score - (second?.score ?? 0);
  if (top.score >= 42 && margin >= 10) return 0.99;
  if (top.score >= 34 && margin >= 7) return 0.96;
  if (top.score >= 26 && margin >= 5) return 0.9;
  return 0.72;
}

function looksUnsafeToAnswer(top: RankedPolicyRule | undefined, second: RankedPolicyRule | undefined) {
  if (!top) return true;
  const margin = top.score - (second?.score ?? 0);
  return top.score < 18 || margin < 3;
}

function passesRuleGroundingCheck(rule: StructuredPolicyRule, analysis: ReturnType<typeof analyzePolicyQuestion>) {
  if (analysis.answerType === "generic") {
    return true;
  }

  const normalizedRuleText = normalizeForMatching(buildRuleSearchText(rule));
  const requiredMatches = findPhraseMatches(normalizedRuleText, analysis.requiredTerms);
  const preferredRuleTypes = mapQuestionTypeToRuleTypes(analysis.answerType);

  if (analysis.policyLocked && analysis.requiredTerms.length > 0 && requiredMatches.length === 0) {
    return false;
  }

  if (preferredRuleTypes.length > 0 && !preferredRuleTypes.includes(rule.ruleType) && requiredMatches.length === 0) {
    return false;
  }

  switch (analysis.answerType) {
    case "same_day_exception":
      return /same day|freshening|guest house|service apartment/.test(normalizedRuleText);
    case "delay_rule":
      return /3 hours|mybiz|cancel|modify|delayed/.test(normalizedRuleText);
    case "anonymity":
      return /anonymous|reasonably clear and specific|verifiable evidence|sufficient information/.test(normalizedRuleText);
    case "recovery":
      return /full final settlement|full & final settlement|recovered|joining bonus/.test(normalizedRuleText);
    case "relocation_transport":
      return /household goods|packers|50 per km|60 per km|700/.test(normalizedRuleText);
    default:
      return true;
  }
}

export function resolveStructuredPolicyRule(rawQuery: string): StructuredRuleAnswer | null {
  const queryLower = rawQuery.toLowerCase();
  const hasLodgingIntent = /\b(lodging|boarding|hotel|accommodation|limit|allowance|food|meal)\b/i.test(queryLower);
  const hasModeOrBookingIntent = /\b(train|flight|air|chair car|mode of travel|book|booking|sbt|mybiz)\b/i.test(queryLower);
  
  if (hasLodgingIntent && hasModeOrBookingIntent) {
    return null;
  }

  const analysis = analyzePolicyQuestion(rawQuery);
  if (analysis.preferredPolicyIds.length === 0 && analysis.answerType === "generic") {
    return null;
  }

  const ranked = rankStructuredPolicyRules(rawQuery, 3);
  const top = ranked[0];
  const second = ranked[1];
  if (!top || looksUnsafeToAnswer(top, second)) {
    return null;
  }

  if (!passesRuleGroundingCheck(top.rule, analysis)) {
    return null;
  }

  const confidence = computeConfidence(top, second);
  const rule = top.rule;

  return {
    text: rule.answer,
    type: "policy_details",
    suggestedQuestions: SUGGESTIONS_BY_POLICY[rule.policyId] ?? [],
    data: {
      policyId: rule.policyId,
      policyName: rule.policyName,
      policyUrl: buildPolicyUrl(rule.policyId),
      pageNumber: rule.page,
      confidenceScore: confidence,
      source: "Structured Policy Rule Engine",
      highlightTerms: analysis.highlightTerms.slice(0, 12),
      keyPoints: rule.conditions.slice(0, 6),
      clauseReference: `${rule.section} • ${rule.clause} • Page ${rule.page}`,
      matchedCriteria: unique([
        `section:${rule.section}`,
        `clause:${rule.clause}`,
        ...top.matchedCriteria,
      ]).slice(0, 10),
    },
  };
}

export function buildStructuredRuleContext(rawQuery: string, limit = 4) {
  const ranked = rankStructuredPolicyRules(rawQuery, limit);
  if (ranked.length === 0) {
    return "";
  }

  return ranked
    .map(({ rule, matchedCriteria }, index) => {
      return [
        `[RULE ${index + 1}] ${rule.policyName} | ${rule.section} | ${rule.clause} | Page ${rule.page}`,
        `Type: ${rule.ruleType}`,
        `Conditions: ${rule.conditions.join("; ")}`,
        `Keywords: ${rule.keywords.slice(0, 20).join(", ")}`,
        `Matched by: ${matchedCriteria.join("; ")}`,
        `Canonical answer: ${rule.answer.replace(/\s+/g, " ").trim()}`,
      ].join("\n");
    })
    .join("\n\n");
}
