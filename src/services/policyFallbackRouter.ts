import { POLICY_META } from "../data/policies";
import { POLICY_ROUTER_CHUNKS, type PolicyRouterChunk } from "../data/policyRouterChunks";
import { analyzePolicyQuestion } from "./policyQuestionAnalysis";
import { normalizeEmployeeChatText, isKnownUnsupportedQuestion } from "./queryNormalization";

interface RouterResponse {
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
    keyPoints?: string[];
    clauseReference?: string;
    matchedCriteria?: string[];
    clarificationNeeded?: boolean;
    clarificationOptions?: string[];
  };
}

interface RankedRouterChunk {
  chunk: PolicyRouterChunk;
  score: number;
  matched: string[];
}

const STOPWORDS = new Set([
  "about",
  "after",
  "again",
  "also",
  "and",
  "any",
  "are",
  "ask",
  "can",
  "could",
  "does",
  "for",
  "from",
  "have",
  "how",
  "into",
  "like",
  "need",
  "please",
  "policy",
  "should",
  "still",
  "tell",
  "that",
  "the",
  "this",
  "under",
  "what",
  "when",
  "where",
  "which",
  "with",
  "would",
]);

const POLICY_SIGNAL_PATTERNS: Record<string, Array<[RegExp, string, number]>> = {
  "domestic-travel": [
    [/\bdomestic travel\b|\btravel policy\b/, "domestic travel policy", 18],
    [/\bmybiz\b|\bmakemytrip\b|\bflight\b|\bair travel\b|\bhotel\b|\blodging\b|\bboarding\b/, "travel booking or entitlement", 10],
    [/\bsame[- ]day\b|\bfreshen(?:ing)? up\b|\bguest house\b|\blaundry\b|\bnon[- ]reimbursable\b|\balcohol\b|\bmini[- ]bar\b/, "domestic travel rule", 12],
    [/\bclass i\b|\bclass ii\b|\bclass iii\b|\bcity class\b|\bwhat class is\b/, "travel city classification", 10],
  ],
  "local-conveyance": [
    [/\blocal conveyance\b|\bconveyance policy\b/, "local conveyance policy", 20],
    [/\btaxi\b|\bcab\b|\bola\b|\buber\b|\bfare\b|\bsame vehicle\b|\bshared vehicle\b|\bshare\b/, "local cab or fare claim", 14],
    [/\btwo[- ]wheeler\b|\bfour[- ]wheeler\b|\bbike\b|\bscooter\b|\bper km\b/, "local conveyance rate", 14],
    [/\borapps\b|\besms\b|\bconveyance expense\b|\bfile .* claim\b/, "local conveyance claim system", 16],
    [/\bsantej\b|\braipur\b|\bgomtipur\b/, "Ahmedabad local conveyance restriction", 16],
  ],
  "joining-policy": [
    [/\bjoining policy\b|\bnew joiner\b|\bnew recruit\b|\bjoining bonus\b/, "joining policy", 18],
    [/\bpre[- ]joining\b|\bbefore joining\b|\bposting city\b/, "pre-joining visit", 14],
    [/\brelocation\b|\bhousehold goods\b|\bpackers\b|\bdriver wages?\b|\bbrokerage\b|\bnotice pay\b|\bf&f\b|\bfull final\b/, "joining relocation or recovery", 14],
    [/\bleave within one year\b|\bresign.*one year\b|\bquit.*one year\b|\brecovery\b/, "joining recovery", 14],
  ],
  "gender-policy": [
    [/\bgender policy\b|\bgender equality\b|\bgender inclusion\b/, "gender policy", 18],
    [/\bgender discrimination\b|\bgender harassment\b|\bgender identity\b|\bgender expression\b/, "gender concern", 16],
    [/\bequal access\b|\bequal opportunity\b|\bmicroaggression\b/, "gender equality principle", 12],
  ],
  "grievance-mechanism": [
    [/\bgrievance\b|\bcomplaint\b|\bredressal\b/, "grievance mechanism", 16],
    [/\backnowledg|\binvestigation\b|\bresolution\b|\bworking days\b|\bappeal\b/, "grievance timeline", 12],
    [/\banonymous complaint\b|\bfalse grievance\b|\bmalicious complaint\b/, "grievance handling rule", 14],
  ],
  "posh-policy": [
    [/\bposh\b|\bsexual harassment\b|\bworkplace harassment\b|\baic\b|\binternal committee\b/, "POSH policy", 20],
    [/\bcomplainant\b|\brespondent\b|\bconciliation\b|\binterim relief\b|\b90 days\b/, "POSH process", 12],
  ],
  whistleblower: [
    [/\bwhistleblower\b|\bwhistle blower\b|\bethics helpline\b|\bunethical\b|\bfraud\b|\bcorruption\b|\bbribery\b/, "whistleblower policy", 20],
    [/\bretaliation\b|\bvictimization\b|\bconfidentiality\b|\bverifiable evidence\b|\bwrongdoing\b/, "whistleblower protection or evidence", 12],
  ],
  "talent-mobility": [
    [/\btalent mobility\b|\bmobility policy\b|\bijp\b|\bjob rotation\b|\binternal job posting\b/, "talent mobility policy", 20],
    [/\binternal(?:ly)?\b.*\b(move|role|opening|position|transfer)\b|\bmove\b.*\binternal(?:ly)?\b|\banother role\b|\banother position\b/, "internal move or role change", 16],
    [/\bmab\b|\bsia\b|\bsettling[- ]in\b|\btier 1\b|\btier 2\b|\brelocation allowance\b/, "mobility benefit", 14],
    [/\bchro\b|\bexception\b|\bhipo\b|\bsuccession\b/, "mobility governance", 10],
  ],
};

const SUGGESTED_BY_POLICY: Record<string, string[]> = {
  "domestic-travel": [
    "What is the relevant domestic travel rule?",
    "Show domestic travel limits",
    "What is non-reimbursable in travel?",
  ],
  "local-conveyance": [
    "How do I claim local conveyance?",
    "What happens if two people share a cab for local conveyance?",
    "What is the two-wheeler reimbursement rate?",
  ],
  "joining-policy": [
    "What is the pre-joining visit policy?",
    "What happens if I leave within one year of joining?",
    "What relocation expenses are covered?",
  ],
  "gender-policy": [
    "How do I report gender discrimination?",
    "What are the key points of Gender Policy?",
    "Who does the Gender Policy apply to?",
  ],
  "grievance-mechanism": [
    "How do I raise a grievance?",
    "How many days does grievance investigation take?",
    "Can anonymous grievances be considered?",
  ],
  "posh-policy": [
    "How do I file a POSH complaint?",
    "What is the POSH complaint timeline?",
    "Who is on the AIC?",
  ],
  whistleblower: [
    "How do I report an unethical practice?",
    "Is whistleblower identity kept confidential?",
    "What retaliation protection applies?",
  ],
  "talent-mobility": [
    "What is Talent Mobility Policy?",
    "Who approves mobility exceptions?",
    "What benefits apply for mobility?",
  ],
};

function normalize(value: string) {
  return normalizeEmployeeChatText(value)
    .replace(/[^a-z0-9₹/&.+-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(value: string) {
  return Array.from(
    new Set(
      normalize(value)
        .split(/\s+/)
        .filter((token) => token.length > 2 && !STOPWORDS.has(token)),
    ),
  );
}

function getPolicyMeta(policyId: string) {
  return POLICY_META.find((policy) => policy.id === policyId);
}

function scorePolicySignals(policyId: string, normalizedQuery: string, matched: string[]) {
  let score = 0;
  for (const [pattern, label, weight] of POLICY_SIGNAL_PATTERNS[policyId] ?? []) {
    if (pattern.test(normalizedQuery)) {
      score += weight;
      matched.push(label);
    }
  }
  return score;
}

function scoreChunk(chunk: PolicyRouterChunk, normalizedQuery: string, queryTokens: string[]) {
  const matched: string[] = [];
  let score = scorePolicySignals(chunk.policyId, normalizedQuery, matched);
  const text = normalize(`${chunk.policyName} ${chunk.section} ${chunk.chunkType} ${chunk.text} ${chunk.keywords.join(" ")}`);

  for (const token of queryTokens) {
    if (chunk.keywords.includes(token)) {
      score += 4;
      matched.push(token);
    } else if (text.includes(token)) {
      score += 2;
    }
  }

  if (chunk.chunkType === "rule" || chunk.chunkType === "table") {
    score += 3;
  }

  if (normalize(chunk.section).split(/\s+/).some((token) => token.length > 3 && queryTokens.includes(token))) {
    score += 5;
  }

  return { chunk, score, matched: Array.from(new Set(matched)).slice(0, 10) };
}

function rankRouterChunks(query: string): RankedRouterChunk[] {
  const normalizedQuery = normalize(query);
  const queryTokens = tokenize(query);
  const analysis = analyzePolicyQuestion(query);
  const preferredPolicyIds = new Set(analysis.preferredPolicyIds);

  return POLICY_ROUTER_CHUNKS
    .map((chunk) => {
      const ranked = scoreChunk(chunk, normalizedQuery, queryTokens);
      if (preferredPolicyIds.has(chunk.policyId)) {
        ranked.score += analysis.policyLocked ? 24 : 12;
        ranked.matched.push("policy classifier");
      } else if (preferredPolicyIds.size > 0) {
        ranked.score -= 8;
      }
      return ranked;
    })
    .filter((ranked) => ranked.score > 0)
    .sort((left, right) => right.score - left.score || left.chunk.pageNum - right.chunk.pageNum);
}

function aggregatePolicyScores(rankedChunks: RankedRouterChunk[]) {
  const scores = new Map<string, { score: number; top: RankedRouterChunk; count: number }>();
  for (const ranked of rankedChunks.slice(0, 12)) {
    const existing = scores.get(ranked.chunk.policyId);
    if (!existing) {
      scores.set(ranked.chunk.policyId, { score: ranked.score, top: ranked, count: 1 });
      continue;
    }
    existing.score += ranked.score * 0.35;
    existing.count += 1;
    if (ranked.score > existing.top.score) existing.top = ranked;
  }

  return Array.from(scores.values()).sort((left, right) => right.score - left.score);
}

function confidenceFromScores(topScore: number, secondScore: number) {
  if (topScore < 16) return 0.34;
  const margin = Math.max(0, topScore - secondScore);
  return Math.min(0.88, 0.48 + topScore / 140 + margin / 180);
}

export function isKnownUnsupportedPolicyQuestion(query: string) {
  return isKnownUnsupportedQuestion(normalize(query));
}

export function buildPolicyRoutingFallback(query: string): RouterResponse | null {
  const normalizedQuery = normalize(query);
  if (isKnownUnsupportedQuestion(normalizedQuery)) return null;

  const rankedChunks = rankRouterChunks(query);
  if (rankedChunks.length === 0) return null;

  const policyScores = aggregatePolicyScores(rankedChunks);
  const topPolicy = policyScores[0];
  const secondPolicy = policyScores[1];
  if (!topPolicy) return null;

  const confidenceScore = confidenceFromScores(topPolicy.score, secondPolicy?.score ?? 0);
  if (confidenceScore < 0.45) return null;

  const { chunk } = topPolicy.top;
  const alternatives = policyScores
    .slice(1, 3)
    .map((entry) => entry.top.chunk.policyName)
    .filter((name) => name !== chunk.policyName);
  const policyMeta = getPolicyMeta(chunk.policyId);
  const excerpt = chunk.text.length > 650 ? `${chunk.text.slice(0, 650).trim()}...` : chunk.text;
  const alternativeText = alternatives.length > 0 ? `\n\nOther possible policy areas: ${alternatives.join(", ")}.` : "";

  return {
    text: `I could not confirm the exact final answer safely, but this question most likely belongs to **${chunk.policyName}**.\n\nMost relevant section: **${chunk.section}**, Page ${chunk.pageNum}\n\nRelevant policy text:\n${excerpt}${alternativeText}\n\nYou can ask me a more specific question about this policy, or escalate to BUHR if you need an approval decision.`,
    type: "policy_details",
    suggestedQuestions: SUGGESTED_BY_POLICY[chunk.policyId] ?? [
      "Show the relevant policy",
      "Who should approve this?",
      "What is the next step?",
    ],
    data: {
      policyId: chunk.policyId,
      policyName: chunk.policyName,
      policyUrl: policyMeta?.fileUrl ?? chunk.fileUrl,
      pageNumber: chunk.pageNum,
      confidenceScore,
      source: "Policy Router Fallback",
      keyPoints: [chunk.section, ...topPolicy.top.matched.slice(0, 5)],
      clauseReference: `${chunk.section} - Page ${chunk.pageNum}`,
      matchedCriteria: topPolicy.top.matched,
      clarificationNeeded: true,
      clarificationOptions: SUGGESTED_BY_POLICY[chunk.policyId] ?? [],
    },
  };
}
