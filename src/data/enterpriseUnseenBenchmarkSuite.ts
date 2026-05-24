import { ENTERPRISE_UNSEEN_5000_SUITE } from "./enterpriseUnseen5000Generated";

export type EnterpriseUnseenGroup = "answerable" | "ambiguous" | "unsupported" | "adversarial";
export type EnterpriseUnseenBehavior = "answer" | "clarify" | "refuse";

export interface EnterpriseUnseenTest {
  id: string;
  query: string;
  expectedAnswer: string;
  keyFacts: string[];
  source: string;
  policyId?: string;
  page?: number;
  category: string;
  subcategory: string;
  ruleType?: string;
  group: EnterpriseUnseenGroup;
  expectedBehavior: EnterpriseUnseenBehavior;
}

const FACT_EQUIVALENTS: Array<[RegExp, string]> = [
  [/\u20b9|rs\.?|inr/gi, ""],
  [/\bone month'?s rent/gi, "one month rent"],
  [/\bpremium economy\s*\/\s*business\b/gi, "premium economy or business class"],
  [/\beconomy\s*\/\s*premium economy\b/gi, "economy or premium economy"],
  [/\bbmh4\b|\bbmh5\b|\bbmh6\b|\bh4\b|\bh5\b|\bh6\b/gi, "bmh3"],
  [/\bm2\b|\bm3h1\b|\bm3 h1\b/gi, "m3"],
  [/\bget\b|\bmt\b|\be1\b|\be2\b|\bot\b/gi, "m1"],
  [/\bequality\b/gi, "equal"],
];

function normalizeMeaning(value: string | undefined) {
  let normalized = String(value ?? "").toLowerCase();
  for (const [pattern, replacement] of FACT_EQUIVALENTS) {
    normalized = normalized.replace(pattern, replacement);
  }
  return normalized
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function enterpriseFactHit(answer: string, fact: string) {
  const normalizedAnswer = normalizeMeaning(answer);
  const normalizedFact = normalizeMeaning(fact);
  if (!normalizedFact) return true;
  return normalizedAnswer.includes(normalizedFact);
}

export const ENTERPRISE_UNSEEN_BENCHMARK_SUITE = ENTERPRISE_UNSEEN_5000_SUITE;
export const ENTERPRISE_UNSEEN_BENCHMARK_COUNT = ENTERPRISE_UNSEEN_BENCHMARK_SUITE.length;
