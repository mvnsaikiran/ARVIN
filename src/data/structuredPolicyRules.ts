import { FULL_TEST_SUITE, type FullTest } from "./fullTestSuite";

export type StructuredPolicyRuleType =
  | "classification"
  | "limit_amount"
  | "timeline"
  | "approval_path"
  | "reporting_route"
  | "anonymity"
  | "eligibility"
  | "reimbursement_rate"
  | "recovery"
  | "exception"
  | "delay_rule"
  | "same_day_exception"
  | "relocation_transport"
  | "women_entitlement"
  | "confidentiality"
  | "retaliation"
  | "metadata"
  | "definition"
  | "benefit"
  | "procedure"
  | "coverage"
  | "reference";

export interface StructuredPolicyRule {
  id: string;
  policyId: string;
  policyName: string;
  section: string;
  clause: string;
  ruleType: StructuredPolicyRuleType;
  conditions: string[];
  answer: string;
  exception?: string;
  page: number;
  keywords: string[];
  sampleQueries: string[];
  category: string;
  subcategory: string;
}

const SOURCE_TO_POLICY_ID: Record<string, string> = {
  "Domestic Travel Policy": "domestic-travel",
  "Talent Mobility Policy": "talent-mobility",
  "POSH Policy": "posh-policy",
  "Grievance Mechanism Policy": "grievance-mechanism",
  "Joining Policy": "joining-policy",
  "Local Conveyance Policy": "local-conveyance",
  "Whistleblower Policy": "whistleblower",
  "Gender Policy": "gender-policy",
};

const STOPWORDS = new Set([
  "a",
  "about",
  "all",
  "am",
  "an",
  "and",
  "any",
  "are",
  "as",
  "at",
  "be",
  "can",
  "clarify",
  "do",
  "does",
  "explain",
  "for",
  "from",
  "help",
  "how",
  "i",
  "in",
  "is",
  "it",
  "know",
  "me",
  "my",
  "need",
  "of",
  "on",
  "or",
  "per",
  "please",
  "policy",
  "tell",
  "the",
  "this",
  "to",
  "under",
  "understand",
  "want",
  "what",
  "when",
  "which",
  "who",
  "with",
]);

function normalizeRuleText(value: string) {
  return value
    .toLowerCase()
    .replace(/â‚¹/g, "rs")
    .replace(/[^a-z0-9\s/-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenizeRuleText(value: string) {
  return normalizeRuleText(value)
    .split(/\s+/)
    .filter((token) => token.length > 2 && !STOPWORDS.has(token));
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function inferRuleType(test: FullTest): StructuredPolicyRuleType {
  const sub = `${test.subcategory} ${test.category}`.toLowerCase();
  const query = test.query.toLowerCase();
  const answer = test.exactAnswer.toLowerCase();
  const combined = `${sub} ${query} ${answer}`;

  if (/anonymous|reasonably clear and specific|verifiable evidence/.test(combined)) return "anonymity";
  if (/same[- ]day|freshening/.test(combined)) return "same_day_exception";
  if (/delay|3 hours|mybiz|cancel or modify|estimated time of departure|\betd\b/.test(combined)) return "delay_rule";
  if (/household goods|packers|50 per km|60 per km|700 km|700 kms|below 700|more than 700/.test(combined)) return "relocation_transport";
  if (/women employees|next higher grade|hotel entitlement.*women|women.*hotel entitlement/.test(combined)) return "women_entitlement";

  if (/classification/.test(sub) || /\bclass i\b|\bclass ii\b|\bclass iii\b/.test(answer)) return "classification";
  if (/lodging|boarding|limit|allowance|mab|sia|amount|rate|entitlement|combined limits/.test(sub)) return "limit_amount";
  if (/timeline|acknowledg|investigation|resolution/.test(sub) || /\bworking days\b/.test(answer)) return "timeline";
  if (/approval|approver|booking|workflow/.test(sub) || /\bwho approves\b|\bapproval\b/.test(query)) return "approval_path";
  if (/reporting|channel|route/.test(sub) || /\bfirst level\b|\bsecond level\b|\bthird level\b/.test(answer)) return "reporting_route";
  if (/eligibility|applicability|coverage/.test(sub) || /\beligible\b|\bapplies to\b|\bcovered\b/.test(answer)) return "eligibility";
  if (/reimbursement rate|per km|conveyance/.test(sub) || /\bper km\b/.test(answer)) return "reimbursement_rate";
  if (/recovery/.test(sub) || /\brecovered\b|\bf&f settlement\b/.test(answer)) return "recovery";
  if (/exception|same-day|delayed flight|women/.test(sub) || /\bhowever\b|\bexception\b/.test(answer)) return "exception";
  if (/confidential/.test(sub) || /\bconfidential\b|\bidentity\b/.test(answer)) return "confidentiality";
  if (/retaliation/.test(sub) || /\bretaliation\b|\bvictimization\b/.test(answer)) return "retaliation";
  if (/effective|issue|policy number|metadata/.test(sub) || /\beffective from\b|\bissue date\b|\bpolicy number\b/.test(answer)) return "metadata";
  if (/definition/.test(sub)) return "definition";
  if (/benefit|mobility|joining|relocation/.test(sub)) return "benefit";
  if (/procedure|process|complaint/.test(sub)) return "procedure";
  if (/scope|coverage/.test(sub)) return "coverage";
  return "reference";
}

function extractException(answer: string) {
  const normalized = answer.replace(/\r/g, "").trim();
  const howeverIndex = normalized.toLowerCase().indexOf("however");
  if (howeverIndex >= 0) {
    return normalized.slice(howeverIndex).split("\n")[0].trim();
  }

  if (/except to the extent required by law/i.test(normalized)) {
    return "Except to the extent required by law.";
  }

  return undefined;
}

function buildRuleKeywords(test: FullTest, queries: string[]) {
  return unique([
    ...test.keyFacts.map((fact) => normalizeRuleText(fact)),
    ...tokenizeRuleText(test.category),
    ...tokenizeRuleText(test.subcategory),
    ...queries.flatMap((query) => tokenizeRuleText(query)),
    ...tokenizeRuleText(test.exactAnswer),
  ]).slice(0, 60);
}

interface RuleAccumulator {
  seed: FullTest;
  queries: Set<string>;
  conditions: Set<string>;
  keywords: Set<string>;
}

const groupedRules = new Map<string, RuleAccumulator>();

for (const test of FULL_TEST_SUITE) {
  const policyId = SOURCE_TO_POLICY_ID[test.source];
  if (!policyId) continue;

  const key = [
    policyId,
    test.category,
    test.subcategory,
    test.page,
    test.exactAnswer,
  ].join("|");

  const existing = groupedRules.get(key);
  if (existing) {
    existing.queries.add(test.query);
    test.keyFacts.forEach((fact) => existing.conditions.add(fact));
    buildRuleKeywords(test, [test.query]).forEach((keyword) => existing.keywords.add(keyword));
    continue;
  }

  groupedRules.set(key, {
    seed: test,
    queries: new Set([test.query]),
    conditions: new Set(test.keyFacts),
    keywords: new Set(buildRuleKeywords(test, [test.query])),
  });
}

const DERIVED_STRUCTURED_POLICY_RULES: StructuredPolicyRule[] = Array.from(groupedRules.values()).map((group, index) => {
  const { seed, queries, conditions, keywords } = group;
  const policyId = SOURCE_TO_POLICY_ID[seed.source];

  return {
    id: `SPR${String(index + 1).padStart(5, "0")}`,
    policyId,
    policyName: seed.source,
    section: seed.category,
    clause: seed.subcategory,
    ruleType: inferRuleType(seed),
    conditions: unique(Array.from(conditions)),
    answer: seed.exactAnswer,
    exception: extractException(seed.exactAnswer),
    page: seed.page,
    keywords: unique(Array.from(keywords)),
    sampleQueries: Array.from(queries).slice(0, 12),
    category: seed.category,
    subcategory: seed.subcategory,
  };
});

const CURATED_STRUCTURED_POLICY_RULES: StructuredPolicyRule[] = [
  {
    id: "SPR-CURATED-001",
    policyId: "whistleblower",
    policyName: "Whistleblower Policy",
    section: "Whistleblower",
    clause: "Anonymous Concerns",
    ruleType: "anonymity",
    conditions: [
      "reasonably clear and specific allegations",
      "vague or unspecified alleged wrongdoings without verifiable evidence may not be undertaken for investigation",
    ],
    answer:
      "Under the Whistleblower Policy, a concern can still be investigated when the allegations are **reasonably clear and specific**. However, **vague or unspecified alleged wrongdoings without verifiable evidence may not be undertaken for investigation**.\n\n*Source: Whistleblower Policy, Page 4*",
    exception: "Vague or unspecified alleged wrongdoings without verifiable evidence may not be undertaken for investigation.",
    page: 4,
    keywords: [
      "anonymous",
      "whistleblower",
      "investigation",
      "reasonably clear and specific",
      "verifiable evidence",
      "complaint",
      "concern",
    ],
    sampleQueries: [
      "Under the whistleblower policy, can an anonymous concern still be taken up for investigation?",
      "Does the whistleblower policy investigate anonymous complaints?",
      "What does the whistleblower policy say about anonymous concerns and investigation?",
    ],
    category: "Whistleblower",
    subcategory: "Anonymous Concerns",
  },
];

export const STRUCTURED_POLICY_RULES: StructuredPolicyRule[] = [
  ...CURATED_STRUCTURED_POLICY_RULES,
  ...DERIVED_STRUCTURED_POLICY_RULES,
];

export const STRUCTURED_POLICY_RULES_BY_ID = new Map(
  STRUCTURED_POLICY_RULES.map((rule) => [rule.id, rule] as const),
);
