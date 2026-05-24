import { POLICY_META, formatTableChunkText } from "../data/policies";
import { POLICY_ROUTER_CHUNKS, type PolicyRouterChunk } from "../data/policyRouterChunks";
import { getDynamicChunks } from "./policyIngestionService";
import { embedText, type AIResponse } from "./geminiService";
import { analyzePolicyQuestion, type PolicyQuestionAnalysis } from "./policyQuestionAnalysis";
import { buildPolicyRoutingFallback, isKnownUnsupportedPolicyQuestion } from "./policyFallbackRouter";
import { normalizeEmployeeChatText } from "./queryNormalization";
import { resolveDeterministicPolicyAnswer } from "./deterministicPolicyResolver";
import { resolveGroundedPolicyAnswer } from "./policyQuestionGrounder";
import { resolveStructuredPolicyRule } from "./structuredRuleEngine";

const BACKEND_BASE_URL = "http://127.0.0.1:8001";

type Answerability = "ANSWERABLE" | "PARTIALLY_ANSWERABLE" | "NOT_ANSWERABLE" | "NEEDS_EMPLOYEE_DETAIL";

interface RankedPolicyChunk {
  chunk: PolicyRouterChunk;
  bm25Rank?: number;
  semanticRank?: number;
  rrfScore: number;
  rerankScore: number;
  matchedTerms: string[];
}

interface AnswerabilityResult {
  label: Answerability;
  reason: string;
}

interface PolicyCitation {
  policyId: string;
  policyName: string;
  policyUrl: string;
  sourceDocumentName: string;
  pageNumber: number;
  clauseReference: string;
  source: string;
}

const STOPWORDS = new Set([
  "a",
  "about",
  "again",
  "all",
  "also",
  "am",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "can",
  "could",
  "do",
  "does",
  "for",
  "from",
  "get",
  "give",
  "have",
  "how",
  "i",
  "if",
  "in",
  "is",
  "it",
  "me",
  "my",
  "of",
  "on",
  "or",
  "please",
  "policy",
  "should",
  "tell",
  "that",
  "the",
  "this",
  "to",
  "under",
  "want",
  "what",
  "when",
  "where",
  "which",
  "who",
  "with",
  "would",
]);

// ---------------------------------------------------------------------------
// Grade & city normalisation helpers
// ---------------------------------------------------------------------------
const GRADE_ALIASES: Record<string, string[]> = {
  bmh9: ["bmh9", "bm-h9", "bmh 9"],
  bmh8: ["bmh8", "bm-h8", "bmh 8"],
  bmh7: ["bmh7", "bm-h7", "bmh 7"],
  bmh6: ["bmh6", "bm-h6", "bmh 6"],
  bmh5: ["bmh5", "bm-h5", "bmh 5"],
  bmh4: ["bmh4", "bm-h4", "bmh 4"],
  bmh3: ["bmh3", "bm-h3", "bmh 3"],
  m3h1: ["m3h1", "m3-h1", "m3 h1"],
  m3:   ["m3"],
  m2:   ["m2"],
  m1:   ["m1"],
  mt:   ["mt"],
  e2:   ["e2"],
  get:  ["get"],
  e1:   ["e1"],
  ot:   ["ot"],
};

const CITY_CLASS_MAP: Record<string, string> = {
  mumbai: "class i", delhi: "class i", bangalore: "class i",
  chennai: "class i", hyderabad: "class i", kolkata: "class i",
  pune: "class i", ahmedabad: "class i",
  surat: "class ii", jaipur: "class ii", lucknow: "class ii",
  nagpur: "class ii", bhopal: "class ii", patna: "class ii",
  ranchi: "class ii", indore: "class ii",
};

function extractGradeFromText(text: string): string | null {
  const normalized = text.toLowerCase();
  for (const [grade, aliases] of Object.entries(GRADE_ALIASES)) {
    if (aliases.some(a => normalized.includes(a))) return grade;
  }
  return null;
}

function extractCityClassFromText(text: string): string | null {
  const normalized = text.toLowerCase();
  for (const [city, cls] of Object.entries(CITY_CLASS_MAP)) {
    if (normalized.includes(city)) return cls;
  }
  if (/class\s*i(?!i)/.test(normalized)) return "class i";
  if (/class\s*ii(?!i)/.test(normalized)) return "class ii";
  if (/class\s*iii/.test(normalized)) return "class iii";
  return null;
}

/** Boost score for chunks whose text explicitly mentions the employee's grade or city class */
function gradeAndCityBoost(
  chunk: PolicyRouterChunk,
  employeeGrade: string | null,
  employeeCityClass: string | null,
): number {
  // DISABLE grade and city boost to prevent it from completely overpowering the semantic match.
  // When a user asks about furniture/relocation, the fact that they are "Grade M2" should not 
  // artificially force the "M2 Travel Entitlement Table" to outrank the relocation policy.
  return 0;
}

const QUERY_EXPANSIONS: Array<[RegExp, string[]]> = [
  [/\bposh\b|\bsexual\b|\bharassment\b|\baic\b/, ["posh", "sexual", "harassment", "complaint", "committee", "aic"]],
  [/\bgender\b|\bdiscrimination\b|\binclusion\b|\bequality\b/, ["gender", "discrimination", "equality", "inclusion", "bias"]],
  [/\bgrievance\b|\bcomplaint\b|\bredressal\b/, ["grievance", "complaint", "redressal", "acknowledgment", "resolution"]],
  [/\bwhistleblower\b|\bfraud\b|\bbribery\b|\bethics\b|\bretaliation\b/, ["whistleblower", "ethics", "fraud", "retaliation", "confidentiality"]],
  [/\btravel\b|\bflight\b|\bhotel\b|\blodging\b|\bboarding\b|\bmybiz\b|\bbusiness trip\b/, ["travel", "mybiz", "flight", "hotel", "lodging", "boarding"]],
  [/\bcab\b|\btaxi\b|\bconveyance\b|\bola\b|\buber\b|\bblusmart\b/, ["cab", "taxi", "conveyance", "ola", "uber", "blusmart"]],
  [/\bjoining\b|\brelocation\b|\bnotice pay\b|\bbrokerage\b|\bhousehold\b/, ["joining", "relocation", "notice", "brokerage", "household", "goods"]],
  [/\bmobility\b|\bijp\b|\binternal role\b|\banother role\b|\btransfer\b/, ["mobility", "ijp", "internal", "role", "transfer", "mab", "sia"]],
  [/\banonymous\b/, ["anonymous", "identity", "complaint"]],
  [/\bconfidential\b|\bidentity\b/, ["confidentiality", "identity", "protected"]],
  [/\bapprove\b|\bapproval\b|\bauthority\b/, ["approval", "authority", "manager", "chro", "committee"]],
  [/\btimeline\b|\bdays\b|\bhow long\b/, ["timeline", "days", "acknowledgment", "investigation", "resolution"]],
  [/\blimit\b|\bamount\b|\brate\b|\bentitlement\b|\breimbursement\b|\bclaim\b/, ["limit", "amount", "rate", "entitlement", "reimbursement", "claim"]],
  [/\bpaisa\b|\bmoney\b|\bfinance\b|\bfunds\b/, ["limit", "amount", "rate", "entitlement", "reimbursement", "claim"]],
  [/\broom\s*expense\b|\broom\b|\bhotel\b|\bstay\b|\blodg\b|\baccommodation\b/, ["lodging", "boarding", "hotel", "stay", "accommodation"]],
  [/\bkhana\b|\bfood\b|\bmeal\b/, ["boarding", "meals", "food"]],
  [/\bghumna\b|\btravel\b|\bjourney\b/, ["travel", "conveyance", "cab", "journey"]],
];

function normalize(value: string) {
  return normalizeEmployeeChatText(value)
    .replace(/â€”|—|–/g, "-")
    .replace(/₹/g, "rs ")
    .replace(/[^a-z0-9/&.+-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(value: string) {
  return normalize(value)
    .split(/\s+/)
    .filter((token) => token.length > 2 && !STOPWORDS.has(token));
}

function expandedTokens(query: string) {
  const normalized = normalize(query);
  const tokens = new Set(tokenize(normalized));
  for (const [pattern, additions] of QUERY_EXPANSIONS) {
    if (pattern.test(normalized)) {
      additions.forEach((token) => tokens.add(token));
    }
  }
  return Array.from(tokens);
}

function chunkSearchText(chunk: PolicyRouterChunk) {
  return normalize(`${chunk.policyName} ${chunk.section} ${chunk.chunkType} ${chunk.text} ${chunk.keywords.join(" ")}`);
}

function keywordScore(queryTokens: string[], chunk: PolicyRouterChunk) {
  const text = chunkSearchText(chunk);
  let score = 0;
  const matched: string[] = [];

  for (const token of queryTokens) {
    if (chunk.keywords.includes(token)) {
      score += 5;
      matched.push(token);
      continue;
    }
    if (text.includes(token)) {
      score += token.length > 4 ? 3 : 1;
      matched.push(token);
    }
  }

  if (chunk.chunkType === "table" && /\b(limit|amount|rate|entitlement|reimbursement|claim|grade|class)\b/.test(queryTokens.join(" "))) {
    score += 8;
  }
  if (chunk.chunkType === "rule" && /\b(rule|allowed|eligible|must|shall|approval|report|complaint|timeline)\b/.test(queryTokens.join(" "))) {
    score += 6;
  }

  return { score, matched: Array.from(new Set(matched)) };
}

function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (!vecA || !vecB || vecA.length !== vecB.length || vecA.length === 0) return 0;
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

function semanticScore(queryTokens: string[], chunk: PolicyRouterChunk, queryEmbedding?: number[]) {
  if (queryEmbedding && queryEmbedding.length > 0 && chunk.embedding && chunk.embedding.length > 0) {
    const similarity = cosineSimilarity(queryEmbedding, chunk.embedding);
    return { score: Math.max(0, similarity * 2), matched: [] }; 
  }

  const chunkTokens = new Set(tokenize(`${chunk.policyName} ${chunk.section} ${chunk.text} ${chunk.keywords.join(" ")}`));
  let overlap = 0;
  const matched: string[] = [];

  for (const token of queryTokens) {
    if (chunkTokens.has(token)) {
      overlap += 1;
      matched.push(token);
    }
  }

  const queryNorm = Math.sqrt(Math.max(queryTokens.length, 1));
  const chunkNorm = Math.sqrt(Math.max(chunkTokens.size, 1));
  return { score: overlap / (queryNorm * chunkNorm), matched };
}

function reciprocalRankFusion(rank?: number) {
  return rank === undefined ? 0 : 1 / (60 + rank);
}

function policyLockBoost(query: string, chunk: PolicyRouterChunk) {
  const analysis = analyzePolicyQuestion(query);
  if (analysis.policyLocked && analysis.preferredPolicyIds.includes(chunk.policyId)) return 24;
  if (analysis.preferredPolicyIds.includes(chunk.policyId)) return 12;
  if (analysis.preferredPolicyIds.length > 0) return -10;
  return 0;
}

function rerank(query: string, candidates: RankedPolicyChunk[]) {
  const normalizedQuery = normalize(query);
  const asksTableFact = /\b(limit|amount|rate|entitlement|grade|class|city|boarding|lodging|cab|mab|sia|per km)\b/.test(normalizedQuery);
  const asksSensitive = /\b(posh|sexual harassment|gender|grievance|whistleblower|fraud|retaliation|confidential|anonymous)\b/.test(normalizedQuery);
  const asksProcess = /\b(how do|report|raise|file|submit|channel|timeline|investigation|resolution|approval)\b/.test(normalizedQuery);

  return candidates
    .map((candidate) => {
      let score = candidate.rrfScore * 1000 + policyLockBoost(query, candidate.chunk);
      const text = chunkSearchText(candidate.chunk);

      if (asksTableFact && candidate.chunk.chunkType === "table") score += 16;
      if (asksProcess && candidate.chunk.chunkType === "rule") score += 12;
      if (asksSensitive && /\b(posh|gender|grievance|whistleblower|ethics|complaint|harassment|retaliation|confidential|anonymous)\b/.test(text)) {
        score += 10;
      }
      if (/\banonymous\b/.test(normalizedQuery)) {
        if (/\banonymous\b/.test(text)) score += 28;
        if (/\bnot entertained\b|\bnot accepted\b|\bnot be entertained\b/.test(text)) score += 22;
        if (!/\banonymous\b/.test(text)) score -= 14;
      }
      if (/\bconfidential\b|\bidentity\b|\bprotected\b|\bprotection\b/.test(normalizedQuery)) {
        if (/\bconfidentiality\b|\bconfidential\b|\bidentity\b|\bprotected\b|\bprotection\b/.test(text)) score += 26;
        if (/\bretaliation\b|\bvictimization\b|\badverse personnel action\b/.test(text)) score += 10;
        if (!/\bconfidentiality\b|\bconfidential\b|\bidentity\b|\bprotected\b|\bprotection\b/.test(text)) score -= 10;
      }
      if (/\bretaliation\b|\bvictimization\b/.test(normalizedQuery)) {
        if (/\bretaliation\b|\bvictimization\b|\badverse personnel action\b/.test(text)) score += 24;
      }
      if (normalize(candidate.chunk.section).split(/\s+/).some((token) => token.length > 3 && normalizedQuery.includes(token))) {
        score += 8;
      }
      if (candidate.matchedTerms.length >= 3) score += Math.min(candidate.matchedTerms.length, 10);

      return { ...candidate, rerankScore: score };
    })
    .sort((left, right) => right.rerankScore - left.rerankScore);
}

export async function hybridPolicySearch(
  query: string,
  topK = 8,
  preComputedAnalysis?: PolicyQuestionAnalysis,
  employeeGrade?: string | null,
  employeeCityClass?: string | null,
): Promise<RankedPolicyChunk[]> {
  const queryTokens = expandedTokens(query);
  if (queryTokens.length === 0) return [];
  
  const queryEmbedding = await embedText(query);

  const analysis = preComputedAnalysis ?? analyzePolicyQuestion(query);
  const preferredPolicyIds = analysis?.preferredPolicyIds ?? [];
  const isLocked = analysis?.policyLocked ?? false;

  // Resolve grade/city from query text if not provided by caller
  const resolvedGrade = employeeGrade ?? extractGradeFromText(query);
  const resolvedCityClass = employeeCityClass ?? extractCityClassFromText(query);

  const allChunks = [...POLICY_ROUTER_CHUNKS, ...getDynamicChunks()];
  const searchPool = isLocked && preferredPolicyIds.length > 0
    ? allChunks.filter(c => preferredPolicyIds.includes(c.policyId))
    : allChunks;

  // STRICTLY SEMANTIC: Disable keyword/BM25 matching entirely per user request
  const keywordRanked: Array<{ chunk: PolicyRouterChunk; score: number; matched: string[] }> = [];

  const semanticRanked = searchPool
    .map((chunk) => {
      const result = semanticScore(queryTokens, chunk, queryEmbedding);
      const gcBoost = gradeAndCityBoost(chunk, resolvedGrade, resolvedCityClass);
      return { chunk, score: result.score + policyLockBoost(query, chunk) / 100 + gcBoost / 100, matched: result.matched };
    })
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 40);

  const merged = new Map<number, RankedPolicyChunk>();
  keywordRanked.forEach((entry, index) => {
    merged.set(entry.chunk.id, {
      chunk: entry.chunk,
      bm25Rank: index + 1,
      rrfScore: reciprocalRankFusion(index + 1),
      rerankScore: 0,
      matchedTerms: entry.matched,
    });
  });
  semanticRanked.forEach((entry, index) => {
    const existing = merged.get(entry.chunk.id);
    if (existing) {
      existing.semanticRank = index + 1;
      existing.rrfScore += reciprocalRankFusion(index + 1);
      existing.matchedTerms = Array.from(new Set([...existing.matchedTerms, ...entry.matched]));
      return;
    }
    merged.set(entry.chunk.id, {
      chunk: entry.chunk,
      semanticRank: index + 1,
      rrfScore: reciprocalRankFusion(index + 1),
      rerankScore: 0,
      matchedTerms: entry.matched,
    });
  });

  return rerank(query, Array.from(merged.values())).slice(0, topK);
}

function getPolicyMeta(policyId: string) {
  return POLICY_META.find((policy) => policy.id === policyId);
}

function resolveChunkPolicyUrl(chunk: PolicyRouterChunk) {
  return chunk.fileUrl || getPolicyMeta(chunk.policyId)?.fileUrl || "";
}

function buildCitationsFromChunks(rankedChunks: RankedPolicyChunk[], limit = 6): PolicyCitation[] {
  const citations = new Map<string, PolicyCitation>();

  for (const entry of rankedChunks) {
    const chunk = entry.chunk;
    const key = `${chunk.policyId}:${chunk.section}:${chunk.pageNum}`;
    if (citations.has(key)) continue;

    citations.set(key, {
      policyId: chunk.policyId,
      policyName: chunk.policyName,
      policyUrl: resolveChunkPolicyUrl(chunk),
      sourceDocumentName: chunk.sourceDocumentName,
      pageNumber: chunk.pageNum,
      clauseReference: `${chunk.section} - Page ${chunk.pageNum}`,
      source: chunk.sourceDocumentName || chunk.policyName,
    });

    if (citations.size >= limit) break;
  }

  return Array.from(citations.values());
}

function detectAnswerability(query: string, rankedChunks: RankedPolicyChunk[]): AnswerabilityResult {
  const normalizedQuery = normalize(query);
  const top = rankedChunks[0];

  if (isKnownUnsupportedPolicyQuestion(query)) {
    return {
      label: "NOT_ANSWERABLE",
      reason: "The question asks about WFH/mobile/internet reimbursement, which is not present in the loaded policy set.",
    };
  }

  if (/\b(my|for me|my grade|my location)\b/.test(normalizedQuery) && /\b(lodging|boarding|cab|entitlement|allowance|limit)\b/.test(normalizedQuery) && !/\b(bmh9|bmh8|bmh7|bmh6|bmh5|bmh4|bmh3|m3h1|m3|m2|m1|mt|e2|get|e1|ot|ahmedabad|delhi|mumbai|class i|class ii|class iii)\b/.test(normalizedQuery)) {
    return {
      label: "NEEDS_EMPLOYEE_DETAIL",
      reason: "The answer depends on grade/location or city class.",
    };
  }

  if (!top || top.matchedTerms.length === 0 && top.rerankScore < 5) {
    return {
      label: "NOT_ANSWERABLE",
      reason: "No retrieved policy chunk matched the question strongly enough.",
    };
  }

  if (top.rerankScore < 10) {
    return {
      label: "PARTIALLY_ANSWERABLE",
      reason: "The retrieved policy area is related, but the exact answer is not fully isolated.",
    };
  }

  return {
    label: "ANSWERABLE",
    reason: "The top retrieved chunk contains matching policy terms and metadata.",
  };
}

function buildUnsupportedResponse(reason: string): AIResponse {
  return {
    text:
      "This is not clearly mentioned in the available Arvind policy documents. Please contact your BUHR for confirmation." +
      "\n\nFor ethics or sensitive concerns, you may also use the Ethics Helpline: **1800 200 8301**, **www.in.kpmg.com/ethicshelpline/arvind**.",
    type: "error",
    suggestedQuestions: [
      "Show the relevant policy",
      "How do I contact BUHR?",
      "How do I report an ethics concern?",
    ],
    data: {
      confidenceScore: 0.25,
      source: "Production RAG Answerability",
      keyPoints: [reason],
    },
  };
}

function buildNeedsDetailResponse(reason: string): AIResponse {
  return {
    text: "I can answer this from the policy, but I need one detail first: please share the relevant **grade**, **location/city**, or **city class**.",
    type: "general",
    suggestedQuestions: [
      "My grade is M2 and location is Ahmedabad",
      "Show M3 lodging and boarding limits",
      "Which city class is Ahmedabad?",
    ],
    data: {
      confidenceScore: 0.6,
      source: "Production RAG Answerability",
      clarificationNeeded: true,
      clarificationOptions: ["grade", "location/city", "city class"],
      keyPoints: [reason],
    },
  };
}

function expandToParentContext(chunk: PolicyRouterChunk): string {
  const siblingChunks = [...POLICY_ROUTER_CHUNKS, ...getDynamicChunks()].filter(
    c => c.policyId === chunk.policyId && 
         c.section === chunk.section && 
         Math.abs(c.pageNum - chunk.pageNum) <= 1
  );
  
  if (siblingChunks.length <= 1) {
    return chunk.text;
  }
  
  siblingChunks.sort((a, b) => a.pageNum - b.pageNum || a.id - b.id);
  return siblingChunks.map(c => c.text).join("\n\n---\n\n");
}

function cleanExcerpt(text: string, maxLength = 900) {
  const cleaned = text
    .replace(/â€”/g, "-")
    .replace(/â€™/g, "'")
    .replace(/â€œ|â€/g, "\"")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.length > maxLength ? `${cleaned.slice(0, maxLength).trim()}...` : cleaned;
}

export function applyCRAGReflection(text: string, sourceChunks: RankedPolicyChunk[]): string {
  // Build a set of all valid numbers present in the source chunks
  const sourceNumbers = new Set<string>();
  for (const entry of sourceChunks) {
    const numbers = entry.chunk.text.replace(/[,₹]/g, "").match(/\b\d+\b/g);
    if (numbers) {
      numbers.forEach(n => {
        if (n.length >= 2) sourceNumbers.add(n);
      });
    }
  }

  // Extract all numbers from the generated response
  const generatedNumbers = text.replace(/[,₹]/g, "").match(/\b\d+\b/g) ?? [];
  let correctedText = text;

  for (const num of generatedNumbers) {
    if (num.length < 2) continue; // ignore single-digit common numbers
    
    // If the number is a hallucination (not in source chunks), look for a highly likely correction
    if (!sourceNumbers.has(num)) {
      let bestCorrection = "";
      let minDistance = Infinity;
      
      for (const validNum of sourceNumbers) {
        if (Math.abs(validNum.length - num.length) > 1) continue;
        const diff = Math.abs(Number(validNum) - Number(num));
        if (diff < minDistance) {
          minDistance = diff;
          bestCorrection = validNum;
        }
      }
      
      // Self-correct if we found a very close valid match
      if (bestCorrection && minDistance <= 500) {
        console.warn(`[CRAG Verification] Hallucination detected! Corrected incorrect number ${num} to ${bestCorrection}.`);
        const regex = new RegExp(`\\b${num}\\b`, "g");
        correctedText = correctedText.replace(regex, bestCorrection);
      }
    }
  }
  
  return correctedText;
}

export function buildExtractiveAnswer(query: string, rankedChunks: RankedPolicyChunk[], answerability: AnswerabilityResult): AIResponse {
  const citations = buildCitationsFromChunks(rankedChunks);

  // Identify unique policies represented in the top 3 ranked chunks
  const uniquePoliciesInTop = Array.from(new Set(rankedChunks.slice(0, 3).map(c => c.chunk.policyId)));

  if (uniquePoliciesInTop.length > 1) {
    // Generate cross-policy synthesized answer
    let synthesizedText = "### 🌐 Cross-Policy Synthesized Information\n\n";
    synthesizedText += "Your query spans multiple HR policies. Here are the relevant sections synthesized for you:\n\n";
    
    uniquePoliciesInTop.forEach(policyId => {
      const chunksForPolicy = rankedChunks.filter(c => c.chunk.policyId === policyId);
      const firstChunk = chunksForPolicy[0].chunk;
      synthesizedText += `#### 📄 ${firstChunk.policyName} (Section: ${firstChunk.section}, Page: ${firstChunk.pageNum})\n`;
      
      chunksForPolicy.forEach(c => {
        const text = c.chunk.text;
        const isTable = text.includes("table belongs") || text.includes("|");
        const processed = isTable ? formatTableChunkText(text) : cleanExcerpt(text);
        synthesizedText += `${processed}\n\n`;
      });
      synthesizedText += "---\n\n";
    });
    
    // Trim trailing separators
    synthesizedText = synthesizedText.replace(/---\n\n$/, "");
    
    const top = rankedChunks[0];
    const policyMeta = getPolicyMeta(top.chunk.policyId);
    
    return {
      text: applyCRAGReflection(synthesizedText, rankedChunks),
      type: "policy_details",
      suggestedQuestions: [
        "Compare policy details",
        "Who can approve exceptions?",
        "How do I submit claims?"
      ],
      data: {
        policyId: top.chunk.policyId,
        policyName: top.chunk.policyName,
        policyUrl: resolveChunkPolicyUrl(top.chunk) || policyMeta?.fileUrl,
        sourceDocumentName: top.chunk.sourceDocumentName,
        pageNumber: top.chunk.pageNum,
        confidenceScore: 0.92,
        source: "Cross-Policy Synthesizer",
        keyPoints: rankedChunks.map(c => `${c.chunk.policyName}: ${c.chunk.section} (Page ${c.chunk.pageNum})`),
        clauseReference: "Multiple Policies",
        matchedCriteria: Array.from(new Set(rankedChunks.flatMap(c => c.matchedTerms))).slice(0, 8),
        citations,
      }
    };
  }

  // Single clean policy document response is always preferred for high readability.

  // Standard single-policy response path
  const top = rankedChunks[0];
  const policyMeta = getPolicyMeta(top.chunk.policyId);
  const confidence = answerability.label === "ANSWERABLE" ? Math.min(0.95, 0.62 + top.rerankScore / 120) : 0.58;
  const sourceLine = `${top.chunk.policyName}, ${top.chunk.section}, Page ${top.chunk.pageNum}`;
  const otherSections = rankedChunks
    .slice(1, 3)
    .filter((entry) => entry.chunk.policyId === top.chunk.policyId)
    .map((entry) => `${entry.chunk.section} (Page ${entry.chunk.pageNum})`);

  const parentContextText = expandToParentContext(top.chunk);
  const isTable = parentContextText.includes("table belongs") || parentContextText.includes("|");
  const processedText = isTable ? formatTableChunkText(parentContextText) : cleanExcerpt(parentContextText);

  const standardText = 
    `According to **${top.chunk.policyName}**, the most relevant policy section is **${top.chunk.section}**.\n\n` +
    `${processedText}\n\n` +
    `*Source: ${sourceLine}*`;

  // Apply CRAG Reflection on standard text!
  const cragCorrectedText = applyCRAGReflection(standardText, rankedChunks);

  return {
    text: cragCorrectedText,
    type: "policy_details",
    suggestedQuestions: [
      `Show more from ${top.chunk.policyName}`,
      "What is the approval path?",
      "What documents are required?",
    ],
    data: {
      policyId: top.chunk.policyId,
      policyName: top.chunk.policyName,
      policyUrl: resolveChunkPolicyUrl(top.chunk) || policyMeta?.fileUrl,
      sourceDocumentName: top.chunk.sourceDocumentName,
      pageNumber: top.chunk.pageNum,
      confidenceScore: confidence,
      source: "Production Hybrid RAG",
      keyPoints: [
        `answerability:${answerability.label}`,
        `section:${top.chunk.section}`,
        `chunk_type:${top.chunk.chunkType}`,
        ...otherSections,
      ],
      clauseReference: `${top.chunk.section} - Page ${top.chunk.pageNum}`,
      matchedCriteria: top.matchedTerms.slice(0, 8),
      citations,
    },
  };
}

export async function resolveProductionRagAnswer(
  query: string,
  userContext?: string,
  preComputedAnalysis?: PolicyQuestionAnalysis,
  employeeId?: string,
): Promise<AIResponse | null> {
  // Parse grade and city from userContext (e.g. "Grade: M1, City: Ahmedabad")
  const contextText = `${query} ${userContext ?? ""}`;
  const employeeGrade = extractGradeFromText(contextText);
  const employeeCityClass = extractCityClassFromText(contextText);
  if (query.trim().length < 3) return null;

  if (isKnownUnsupportedPolicyQuestion(query)) {
    return buildUnsupportedResponse("Unsupported policy topic");
  }

  // 1. PRIMARY PATH: Use the Python hybrid + LightRAG backend first.
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        query,
        employeeId: employeeId || "local-user-001",
        memory_context: userContext || "",
      }),
    });

    if (response.ok) {
      const result = await response.json();
      if (result && result.text) {
        result.text = applyCRAGReflection(result.text, await hybridPolicySearch(query, 8, preComputedAnalysis));
      }
      return result as AIResponse;
    }
  } catch (err) {
    console.warn("Python Hybrid + LightRAG backend unreachable, falling back to local heuristic engine.", err);
  }

  // 2. FALLBACK PATHS: Local Heuristics & Offline Redundant Rules (DISABLED to enable full semantic AI)
  // const deterministic = resolveDeterministicPolicyAnswer(query, userContext);
  // if (deterministic) return deterministic;

  // const groundedRule = resolveGroundedPolicyAnswer(query);
  // if (groundedRule) return groundedRule;

  // const structuredRule = resolveStructuredPolicyRule(query);
  // if (structuredRule) return structuredRule;

  const rankedChunks = await hybridPolicySearch(query, 8, preComputedAnalysis, employeeGrade, employeeCityClass);
  const answerability = detectAnswerability(query, rankedChunks);

  if (answerability.label === "NEEDS_EMPLOYEE_DETAIL") {
    return buildNeedsDetailResponse(answerability.reason);
  }

  if (answerability.label === "NOT_ANSWERABLE") {
    const route = buildPolicyRoutingFallback(query);
    if (route) return route;
    return buildUnsupportedResponse(answerability.reason);
  }

  if (answerability.label === "PARTIALLY_ANSWERABLE") {
    // Relaxed guardrail: allow the LLM to attempt a generative answer even if confidence is partial
    // const route = buildPolicyRoutingFallback(query);
    // if (route) return route;
  }

  return buildExtractiveAnswer(query, rankedChunks, answerability);
}
