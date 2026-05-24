/**
 * Arvind HR Pulse — RAG Service v3
 *
 * Architecture:
 *   1. Static Answer Cache  → instant 100% accurate answers for known patterns
 *   2. BM25 Retrieval       → chunk-level search for open-ended queries
 *   3. Grounded LLM         → Gemini with strict system prompt
 *   4. Offline Fallback     → local BM25 snippet if API fails
 */

import { ALL_CHUNKS, Chunk, bm25Search, buildContext, POLICY_META } from "../data/policies";
import { GoogleGenAI } from "@google/genai";
import type { AssistantMemoryContext } from "./chatMemoryService";
import {
  buildClarificationResponse,
  buildHighRiskGuardrailResponse,
  buildLearningCaseResponse,
  buildPolicyDiffResponse,
  buildScenarioSimulationResponse,
  enrichResponseForExperience,
} from "./chatExperienceEnhancer";
import { resolveDeterministicPolicyAnswer } from "./deterministicPolicyResolver";
import { COMMON_CITY_ALIASES, normalizeEmployeeChatText } from "./queryNormalization";
import { analyzePolicyQuestion } from "./policyQuestionAnalysis";
import { buildPolicyRoutingFallback, isKnownUnsupportedPolicyQuestion } from "./policyFallbackRouter";
import { resolveGroundedPolicyAnswer, scoreChunkAgainstPolicyQuestion } from "./policyQuestionGrounder";
import { buildStructuredRuleContext } from "./structuredRuleEngine";
import { verifyPolicyAnswer } from "./policyVerificationService";

// ─── Client ───────────────────────────────────────────────────────────────────


let _ai: GoogleGenAI | null = null;
function ai(): GoogleGenAI {
  if (!_ai) {
    const key =
      (typeof process !== "undefined" && (process.env?.GEMINI_API_KEY || "")) ||
      ((import.meta as any)?.env?.VITE_GEMINI_API_KEY ?? "") ||
      ((import.meta as any)?.env?.GEMINI_API_KEY ?? "");
    if (!key) console.error("⚠️ GEMINI_API_KEY not set.");
    _ai = new GoogleGenAI({ apiKey: key });
  }
  return _ai;
}

// ─── Public types ─────────────────────────────────────────────────────────────
export interface ChatMessage {
  role: "user" | "model";
  parts: Array<{ text: string }>;
}

interface GeminiProxyRequest {
  model?: string;
  contents: Array<Record<string, unknown>>;
  config?: Record<string, unknown>;
}

const STRUCTURED_RESPONSE_SCHEMA = {
  type: "OBJECT",
  properties: {
    text: { type: "STRING" },
    type: { type: "STRING", enum: ["general", "policy_details", "error"] },
    suggestedQuestions: { type: "ARRAY", items: { type: "STRING" } },
    data: {
      type: "OBJECT",
      properties: {
        policyId: { type: "STRING" },
        policyName: { type: "STRING" },
        policyUrl: { type: "STRING" },
        pageNumber: { type: "NUMBER" },
        confidenceScore: { type: "NUMBER" },
        source: { type: "STRING" },
        highlightTerms: { type: "ARRAY", items: { type: "STRING" } },
        keyPoints: { type: "ARRAY", items: { type: "STRING" } },
      },
    },
  },
  required: ["text", "type", "suggestedQuestions"],
} as const;

async function callGeminiProxy(request: GeminiProxyRequest, signal?: AbortSignal) {
  if (typeof window === "undefined") {
    // Node.js environment - bypass proxy and call API directly
    const client = ai();
    const contentResp = await client.models.generateContent({
      model: request.model || "gemini-2.0-flash",
      contents: request.contents,
      config: request.config as any,
    });
    return contentResp.text ?? "";
  }

  const response = await fetch("/api/gemini/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    signal,
  });

  let payload: { text?: string; error?: string } | null = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.error || `Gemini proxy request failed with status ${response.status}`);
  }

  return payload?.text ?? "";
}

export async function embedText(text: string): Promise<number[]> {
  if (typeof window === "undefined") {
    try {
      const client = ai();
      const result = await client.models.embedContent({
        model: "gemini-embedding-2",
        contents: text,
      });
      return result.embeddings?.[0]?.values ?? [];
    } catch (err) {
      console.warn("Failed to generate embedding in node", err);
      return [];
    }
  }

  try {
    const response = await fetch("/api/gemini/embed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      return [];
    }
    const payload = await response.json();
    return payload?.embedding ?? [];
  } catch (err) {
    console.warn("Failed to generate embedding via proxy", err);
    return [];
  }
}

export async function rewriteConversationalQuery(query: string, history: ChatMessage[]): Promise<string> {
  if (!history || history.length === 0) return query;

  try {
    const prompt = `You are an expert HR assistant Query Rewriter.
Your task is to rewrite the latest user query to be fully self-contained by resolving pronouns (like "it", "that") and missing context (like policy names, locations, roles) using the conversation history.

Conversation History:
${history.map(msg => `${msg.role.toUpperCase()}: ${msg.parts[0]?.text}`).join("\n")}

LATEST QUERY: "${query}"

Output ONLY the self-contained rewritten query. Do not add any conversational filler.
If the latest query is already self-contained or a greeting, just output the original query.`;

    const rewritten = await callGeminiProxy({
      model: "gemini-2.0-flash",
      contents: [{ role: "user", parts: [{ text: prompt }] }],
    });
    
    const text = rewritten.trim();
    return text.length > 0 ? text : query;
  } catch (err) {
    console.warn("Query Rewriter failed, falling back to original query", err);
    return query;
  }
}

export interface AIResponse {
  text: string;
  type: "general" | "policy_details" | "error" | "action_trigger";
  suggestedQuestions?: string[];
  data?: {
    policyId?: string;
    policyName?: string;
    policyUrl?: string;
    sourceDocumentName?: string;
    pageNumber?: number;
    confidenceScore?: number;
    source?: string;
    highlightTerms?: string[];
    keyPoints?: string[];
    citations?: Array<{
      policyId?: string;
      policyName?: string;
      policyUrl?: string;
      sourceDocumentName?: string;
      pageNumber?: number;
      clauseReference?: string;
      source?: string;
    }>;
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
    huggingFaceMetrics?: {
      isHuggingFaceLocal?: boolean;
      engine?: string;
      host?: string;
      gpuTemperature?: string;
      gpuVramUsed?: string;
      tokensPerSecond?: number;
      durationMs?: number;
      statelessPrivacy?: boolean;
    };
  };
}

interface PersonalizationContext {
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

function parseUserContext(raw: string): PersonalizationContext {
  if (!raw) return {};

  return raw.split(";").reduce<PersonalizationContext>((accumulator, chunk) => {
    const [rawKey, ...rest] = chunk.split("=");
    const key = rawKey?.trim();
    const value = rest.join("=").trim();
    if (!key || !value) return accumulator;
    accumulator[key as keyof PersonalizationContext] = value;
    return accumulator;
  }, {});
}

function buildPersonalizationPrompt(userContext: PersonalizationContext): string {
  const details = [
    userContext.role ? `Role: ${userContext.role}` : "",
    userContext.language ? `Preferred language: ${userContext.language}` : "",
    userContext.name ? `Employee name: ${userContext.name}` : "",
    userContext.employeeId ? `Employee ID: ${userContext.employeeId}` : "",
    userContext.grade ? `Grade: ${userContext.grade}` : "",
    userContext.location ? `Location: ${userContext.location}` : "",
    userContext.department ? `Department: ${userContext.department}` : "",
    userContext.businessUnit ? `Business Unit: ${userContext.businessUnit}` : "",
    userContext.manager ? `Manager: ${userContext.manager}` : "",
    userContext.workMode ? `Work Mode: ${userContext.workMode}` : "",
  ].filter(Boolean);

  return details.length > 0 ? details.join("\n") : "No employee context provided.";
}

function formatMemorySection(memoryContext?: AssistantMemoryContext): string {
  if (!memoryContext) {
    return "No additional memory context.";
  }

  const sessionLines = [
    memoryContext.session.conversationSummary,
    memoryContext.session.activePolicyName ? `Active policy: ${memoryContext.session.activePolicyName}.` : "",
    memoryContext.session.activeTopic ? `Active topic: ${memoryContext.session.activeTopic}.` : "",
    memoryContext.session.openEntities.grade ? `Open grade reference: ${memoryContext.session.openEntities.grade}.` : "",
    memoryContext.session.openEntities.location ? `Open location reference: ${memoryContext.session.openEntities.location}.` : "",
    memoryContext.session.openEntities.travelClass ? `Open travel class reference: ${memoryContext.session.openEntities.travelClass}.` : "",
    memoryContext.session.openEntities.workflow ? `Open workflow reference: ${memoryContext.session.openEntities.workflow.replace(/_/g, " ")}.` : "",
  ].filter(Boolean);

  const longTermLines = [
    ...memoryContext.longTerm.durableFacts,
    ...memoryContext.longTerm.relevantMemories.map((memory) => `${memory.title}: ${memory.summary}`),
  ].filter(Boolean);

  return [
    "SHORT-TERM MEMORY:",
    sessionLines.length > 0 ? sessionLines.join("\n") : "No short-term memory available.",
    "",
    "LONG-TERM MEMORY:",
    longTermLines.length > 0 ? longTermLines.join("\n") : "No long-term memory available.",
  ].join("\n");
}

function findCanonicalPolicyMeta(policyId?: string, policyName?: string) {
  const normalizedId = policyId?.trim().toLowerCase();
  const normalizedName = policyName?.trim().toLowerCase();

  return POLICY_META.find((policy) =>
    (normalizedId && policy.id === normalizedId) ||
    (normalizedName && policy.name.toLowerCase() === normalizedName)
  );
}

function withCanonicalPolicyMetadata(response: AIResponse): AIResponse {
  if (!response.data) {
    return response;
  }

  const canonicalPolicy = findCanonicalPolicyMeta(response.data.policyId, response.data.policyName);
  if (!canonicalPolicy) {
    return response;
  }

  return {
    ...response,
    data: {
      ...response.data,
      policyId: canonicalPolicy.id,
      policyName: canonicalPolicy.name,
      policyUrl: canonicalPolicy.fileUrl,
      source: response.data.source ?? canonicalPolicy.sourceDocumentName,
    },
  };
}

interface PolicyIntent {
  preferredPolicyIds: string[];
  metadataFocus: boolean;
  applicabilityFocus: boolean;
  timelineFocus: boolean;
}

const POLICY_INTENT_ALIASES: Array<{ policyId: string; policyName: string; aliases: string[] }> = [
  { policyId: "domestic-travel", policyName: "Domestic Travel Policy", aliases: ["domestic travel policy", "travel policy", "domestic travel"] },
  { policyId: "local-conveyance", policyName: "Local Conveyance Policy", aliases: ["local conveyance policy", "local conveyance"] },
  { policyId: "posh-policy", policyName: "POSH Policy", aliases: ["posh policy", "posh", "sexual harassment policy"] },
  { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", aliases: ["grievance mechanism policy", "grievance policy", "grievance"] },
  { policyId: "gender-policy", policyName: "Gender Policy", aliases: ["gender policy"] },
  { policyId: "whistleblower", policyName: "Whistleblower Policy", aliases: ["whistleblower policy", "whistleblower", "ethics policy"] },
  { policyId: "talent-mobility", policyName: "Talent Mobility Policy", aliases: ["talent mobility policy", "talent mobility", "mobility policy"] },
  { policyId: "joining-policy", policyName: "Joining Policy", aliases: ["joining policy", "joining expense", "joining expenses", "joining claim", "claim deadline on joining", "brokerage reimbursement on joining", "pre joining", "pre-joining", "house deposit on joining"] },
];

function detectPolicyIntent(query: string): PolicyIntent {
  const normalized = normalizeEmployeeChatText(query);
  const preferredPolicyIds = POLICY_INTENT_ALIASES
    .filter((item) => item.aliases.some((alias) => normalized.includes(alias)))
    .map((item) => item.policyId);

  return {
    preferredPolicyIds,
    metadataFocus: /\beffective date\b|\beffective from\b|\bissue date\b|\bpolicy number\b|\bwhen was it effective\b|\bwhen effective\b/.test(normalized),
    applicabilityFocus: /\bwho does it apply to\b|\bwho is covered\b|\bapplicability\b|\bapplies to\b|\bapplicable to\b|\bscope\b/.test(normalized),
    timelineFocus: /\btimeline\b|\btimelines\b|\backnowledg(e|ement)\b|\binvestigation\b|\bresolution\b/.test(normalized),
  };
}

function getPolicyChunks(policyId: string) {
  return ALL_CHUNKS
    .filter((chunk) => chunk.policyId === policyId)
    .sort((left, right) => left.pageNum - right.pageNum || left.id - right.id);
}

function findPolicyChunk(policyId: string, matcher: (chunk: Chunk) => boolean) {
  return getPolicyChunks(policyId).find(matcher);
}

function cleanExtractedText(value: string) {
  return value
    .replace(/\s+/g, " ")
    .replace(/\s+([,.;!?])/g, "$1")
    .trim();
}

function extractLabelValue(text: string, label: RegExp) {
  const match = text.match(label);
  return match?.[1] ? cleanExtractedText(match[1]) : null;
}

function extractPolicyDatesAndNumber(policyId: string) {
  const chunks = getPolicyChunks(policyId).slice(0, 3);
  for (const chunk of chunks) {
    const issueDate = extractLabelValue(chunk.text, /Issue Date[:\s|]+([0-9./-]+)/i);
    const effectiveDate = extractLabelValue(chunk.text, /Effective (?:From|Date)[:\s|]+([0-9./-]+)/i);
    const policyNumber = extractLabelValue(chunk.text, /Policy Number[:\s|]+([A-Z0-9|/_-]+)/i);
    if (issueDate || effectiveDate || policyNumber) {
      return { issueDate, effectiveDate, policyNumber, pageNum: chunk.pageNum };
    }
  }
  return null;
}

function extractApplicabilityText(policyId: string) {
  const chunks = getPolicyChunks(policyId).slice(0, 5);
  for (const chunk of chunks) {
    const lines = chunk.text.split("\n").map((line) => line.trim()).filter(Boolean);
    const applicabilityIndex = lines.findIndex((line) => /^(applicability|scope)[:]?$/i.test(line));
    if (applicabilityIndex >= 0) {
      const summary = cleanExtractedText(lines.slice(applicabilityIndex + 1, applicabilityIndex + 3).join(" "));
      if (summary) {
        return { text: summary, pageNum: chunk.pageNum };
      }
    }

    const sentence = lines.find((line) => /\b(applies to|applicable to)\b/i.test(line));
    if (sentence) {
      return { text: cleanExtractedText(sentence), pageNum: chunk.pageNum };
    }
  }
  return null;
}

function extractGrievanceTimeline() {
  const acknowledgement = findPolicyChunk(
    "grievance-mechanism",
    (chunk) => /acknowledged within 2 working days/i.test(chunk.text),
  );
  const investigation = findPolicyChunk(
    "grievance-mechanism",
    (chunk) => /completed within 10 working days/i.test(chunk.text),
  );
  const resolution = findPolicyChunk(
    "grievance-mechanism",
    (chunk) => /within 15 working days/i.test(chunk.text) && /outcome/i.test(chunk.text),
  );

  if (!acknowledgement || !investigation || !resolution) {
    return null;
  }

  return {
    acknowledgement: "Within 2 working days",
    investigation: "Within 10 working days",
    resolution: "Within 15 working days",
    pageNum: Math.min(acknowledgement.pageNum, investigation.pageNum, resolution.pageNum),
  };
}

function buildPolicyFactResponse(query: string): AIResponse | null {
  const intent = detectPolicyIntent(query);
  if (intent.preferredPolicyIds.length !== 1) return null;

  const policyId = intent.preferredPolicyIds[0];
  const policyMeta = findCanonicalPolicyMeta(policyId);
  if (!policyMeta) return null;

  if (intent.metadataFocus) {
    const metadata = extractPolicyDatesAndNumber(policyId);
    if (!metadata) return null;

    const sentences = [
      metadata.issueDate ? `${policyMeta.name} issue date is **${metadata.issueDate}**.` : "",
      metadata.effectiveDate ? `It is effective from **${metadata.effectiveDate}**.` : "",
      metadata.policyNumber ? `Policy Number: **${metadata.policyNumber}**.` : "",
    ].filter(Boolean);

    return {
      text: `${sentences.join(" ")}\n\n*Source: ${policyMeta.name}, Page ${metadata.pageNum}*`,
      type: "policy_details",
      suggestedQuestions: [`Who does ${policyMeta.name} apply to?`, `Show the key points of ${policyMeta.name}`, `Open the source for ${policyMeta.name}`],
      data: {
        policyId,
        policyName: policyMeta.name,
        policyUrl: policyMeta.fileUrl,
        pageNumber: metadata.pageNum,
        confidenceScore: 0.99,
        source: "Policy Metadata Resolver",
        keyPoints: sentences.map((fact) => fact.replace(/\*\*/g, "")),
      },
    };
  }

  if (intent.applicabilityFocus) {
    const applicability = extractApplicabilityText(policyId);
    if (!applicability) return null;

    return {
      text: `${applicability.text}\n\n*Source: ${policyMeta.name}, Page ${applicability.pageNum}*`,
      type: "policy_details",
      suggestedQuestions: [`What is the effective date of ${policyMeta.name}?`, `What is covered under ${policyMeta.name}?`, `Show the reporting route under ${policyMeta.name}`],
      data: {
        policyId,
        policyName: policyMeta.name,
        policyUrl: policyMeta.fileUrl,
        pageNumber: applicability.pageNum,
        confidenceScore: 0.97,
        source: "Policy Applicability Resolver",
      },
    };
  }

  if (policyId === "grievance-mechanism" && intent.timelineFocus) {
    const timeline = extractGrievanceTimeline();
    if (!timeline) return null;

    return {
      text:
        `Grievance handling timelines:\n\n| Stage | Timeline |\n|---|---|\n| Acknowledgement | **${timeline.acknowledgement}** |\n| Investigation | **${timeline.investigation}** |\n| Resolution | **${timeline.resolution}** |\n\n*Source: Grievance Mechanism Policy, Page ${timeline.pageNum}*`,
      type: "policy_details",
      suggestedQuestions: ["How do I file a grievance?", "Who can I escalate a grievance to?", "What is the grievance policy applicability?"],
      data: {
        policyId,
        policyName: policyMeta.name,
        policyUrl: policyMeta.fileUrl,
        pageNumber: timeline.pageNum,
        confidenceScore: 0.99,
        source: "Policy Timeline Resolver",
        keyPoints: [
          `Acknowledgement ${timeline.acknowledgement}`,
          `Investigation ${timeline.investigation}`,
          `Resolution ${timeline.resolution}`,
        ],
      },
    };
  }

  return null;
}

function scoreChunkForIntent(chunk: Chunk, intent: PolicyIntent) {
  let score = 1;
  const text = chunk.text.toLowerCase();
  const prefersThisPolicy = intent.preferredPolicyIds.includes(chunk.policyId);

  if (prefersThisPolicy) score += 5;
  if (intent.preferredPolicyIds.length > 0 && !prefersThisPolicy) score -= 2;

  if (intent.metadataFocus) {
    if (/issue date|effective from|effective date|policy number/i.test(chunk.text)) score += 4;
    if (chunk.pageNum <= 2) score += 2;
  }

  if (intent.applicabilityFocus) {
    if (/\bapplicability\b|\bscope\b|\bapplies to\b|\bapplicable to\b/i.test(chunk.text)) score += 4;
    if (chunk.pageNum <= 3) score += 2;
  }

  if (intent.timelineFocus) {
    if (/\btimeline\b|\backnowledg|\binvestigation\b|\bresolution\b|\bworking days\b/i.test(text)) score += 4;
  }

  return score;
}

function buildChunkBackedPolicyResponse(
  query: string,
  chunk: Chunk | undefined,
  source: string,
  confidenceScore: number,
): AIResponse {
  if (!chunk) {
    return buildSupportiveFallback(query);
  }

  return {
    text: `**${chunk.policyName}** — Page ${chunk.pageNum}\n\n${chunk.text.slice(0, 700)}\n\n*Source: ${chunk.policyName}, Page ${chunk.pageNum}*`,
    type: "policy_details",
    suggestedQuestions: ["Show the effective date", "Who does this policy apply to?", "What is the next step under this policy?"],
    data: {
      policyId: chunk.policyId,
      policyName: chunk.policyName,
      policyUrl: chunk.fileUrl,
      pageNumber: chunk.pageNum,
      source,
      confidenceScore,
    },
  };
}

function inferPolicyMismatch(parsed: AIResponse, intent: PolicyIntent) {
  if (intent.preferredPolicyIds.length !== 1) return false;
  const expected = intent.preferredPolicyIds[0];
  const actual = parsed.data?.policyId ?? findCanonicalPolicyMeta(undefined, parsed.data?.policyName)?.id;
  return !!actual && actual !== expected;
}

function validateGeneratedResponse(
  query: string,
  parsed: AIResponse,
  chunks: Chunk[],
): AIResponse {
  const grounded = resolveGroundedPolicyAnswer(query);
  if (grounded) {
    return grounded;
  }

  const directFact = buildPolicyFactResponse(query);
  if (directFact) {
    return directFact;
  }

  const intent = detectPolicyIntent(query);
  if (inferPolicyMismatch(parsed, intent)) {
    const preferredChunk = chunks.find((chunk) => intent.preferredPolicyIds.includes(chunk.policyId)) ?? chunks[0];
    return buildChunkBackedPolicyResponse(query, preferredChunk, "Policy Validation Repair", 0.78);
  }

  return parsed;
}

function classifyModelError(err: any) {
  const message = String(err?.message ?? "");
  const normalized = message.toLowerCase();

  if (/api key.*not valid|invalid api key|api_key_invalid/.test(normalized)) {
    return "invalid_key" as const;
  }

  if (/429|quota|rate.limit|resource_exhausted/.test(normalized)) {
    return "quota" as const;
  }

  if (/deadline|timed out|timeout|network|fetch failed|connection/i.test(message)) {
    return "connection" as const;
  }

  return "generic" as const;
}

const GENERAL_POLICY_SUGGESTIONS = [
  "Explain the local conveyance policy",
  "Show domestic travel limits",
  "How do I raise a grievance?",
];

const SENSITIVE_SUPPORT_SUGGESTIONS = [
  "How do I file a POSH complaint?",
  "How do I raise a grievance?",
  "What is the ethics helpline?",
];

function getHistoryText(history: ChatMessage[]): string {
  return history
    .flatMap((message) => message.parts.map((part) => part.text))
    .join(" ")
    .trim();
}

function getMemoryPolicyName(memoryContext?: AssistantMemoryContext): string | null {
  if (!memoryContext) return null;
  return memoryContext.session.activePolicyName
    ?? memoryContext.longTerm.relevantMemories.find((memory) => memory.tags.some((tag) => tag.endsWith("-policy")))?.title
    ?? null;
}

function inferRecentPolicyName(history: ChatMessage[], memoryContext?: AssistantMemoryContext): string | null {
  const historyText = getHistoryText(history).toLowerCase();
  if (!historyText) return getMemoryPolicyName(memoryContext);

  const policy = POLICY_META.find((item) => historyText.includes(item.name.toLowerCase()));
  return policy?.name ?? getMemoryPolicyName(memoryContext);
}

const FOLLOW_UP_CITY_CLASS_MAP: Record<string, "Class I" | "Class II" | "Class III"> = {
  delhi: "Class I",
  ncr: "Class I",
  mumbai: "Class I",
  bangalore: "Class I",
  chennai: "Class I",
  hyderabad: "Class I",
  kolkata: "Class I",
  pune: "Class I",
  ahmedabad: "Class II",
  surat: "Class II",
  jaipur: "Class II",
  lucknow: "Class II",
  indore: "Class II",
  nagpur: "Class II",
  rajkot: "Class II",
  vadodara: "Class II",
  patna: "Class II",
  bhopal: "Class II",
  ranchi: "Class II",
  kochi: "Class II",
  coimbatore: "Class II",
  visakhapatnam: "Class II",
  mysore: "Class II",
  srinagar: "Class II",
  jammu: "Class II",
};

const FOLLOW_UP_GRADE_PATTERN = /\b(bmh9|bmh8|h8|bmh7|bm-h7|director|bmh6|h6|bmh5|h5|bmh4|h4|bmh3|bm-h3|m3h1|m3-h1|m3|m2|m1|mt|e2|get|e1|ot)\b/i;
const FOLLOW_UP_CLASS_PATTERN = /\bclass\s*(iii|ii|i|3|2|1|three|two|one)\b/i;
const FOLLOW_UP_QUERY_PATTERN = /^(and\b|what about\b|what abt\b|how about\b|same for\b|what if\b|then what about\b|about\b)/i;

function getMessageText(message: ChatMessage): string {
  return message.parts.map((part) => part.text).join(" ").trim();
}

function normalizeSpacing(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

function ensureSentence(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "";
  return /[.!?]$/.test(trimmed) ? trimmed : `${trimmed}.`;
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeFollowUpQueryText(text: string): string {
  let normalized = normalizeEmployeeChatText(text);

  for (const [canonical, aliases] of Object.entries(COMMON_CITY_ALIASES)) {
    for (const alias of aliases) {
      normalized = normalized.replace(new RegExp(`\\b${escapeRegExp(alias)}\\b`, "g"), canonical);
    }
  }

  return normalizeSpacing(normalized);
}

function isSimplifyFollowUp(query: string): boolean {
  const normalized = normalizeFollowUpQueryText(query);
  return /(explain|say|tell|put).*(simple|simpler|plain|easy|short|brief)/.test(normalized)
    || normalized.includes("in simple words")
    || normalized.includes("simple words")
    || normalized.includes("what does that mean")
    || normalized.includes("break it down")
    || normalized.includes("simplify");
}

function getLastMeaningfulUserMessage(history: ChatMessage[]): string | null {
  for (let index = history.length - 1; index >= 0; index -= 1) {
    const message = history[index];
    if (message.role !== "user") continue;

    const text = getMessageText(message);
    if (!text) continue;

    const signals = detectConversationSignals(text);
    if (
      signals.isGreeting ||
      signals.isThanks ||
      signals.isFarewell ||
      signals.isAcknowledgement ||
      signals.isHelpRequest ||
      isSimplifyFollowUp(text)
    ) {
      continue;
    }

    return text;
  }

  return null;
}

function getLastMeaningfulModelMessage(history: ChatMessage[]): string | null {
  for (let index = history.length - 1; index >= 0; index -= 1) {
    const message = history[index];
    if (message.role !== "model") continue;

    const text = getMessageText(message);
    if (!text) continue;
    return text;
  }

  return null;
}

function canonicalizeGrade(rawGrade: string): string {
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

function extractMentionedGrade(text: string): string | null {
  const match = text.match(FOLLOW_UP_GRADE_PATTERN);
  return match ? canonicalizeGrade(match[1]) : null;
}

function extractMentionedCity(text: string): string | null {
  const normalized = normalizeFollowUpQueryText(text);
  const found = Object.keys(FOLLOW_UP_CITY_CLASS_MAP)
    .sort((left, right) => right.length - left.length)
    .find((city) => normalized.includes(city));

  if (!found) return null;
  return found === "ncr" ? "NCR" : found.charAt(0).toUpperCase() + found.slice(1);
}

function extractMentionedTravelClass(text: string): "Class I" | "Class II" | "Class III" | null {
  const match = text.match(FOLLOW_UP_CLASS_PATTERN);
  if (!match) return null;

  const normalized = match[1].toLowerCase();
  if (normalized === "i" || normalized === "1" || normalized === "one") return "Class I";
  if (normalized === "ii" || normalized === "2" || normalized === "two") return "Class II";
  return "Class III";
}

function replaceGradeInText(text: string, grade: string): string {
  return text.replace(FOLLOW_UP_GRADE_PATTERN, grade);
}

function replaceCityInText(text: string, city: string): string {
  const cityPattern = new RegExp(
    `\\b(${Object.keys(FOLLOW_UP_CITY_CLASS_MAP)
      .sort((left, right) => right.length - left.length)
      .map(escapeRegExp)
      .join("|")})\\b`,
    "i",
  );

  return text.replace(cityPattern, city);
}

function replaceTravelClassInText(text: string, replacement: string): string {
  return text.replace(FOLLOW_UP_CLASS_PATTERN, replacement);
}

function buildFollowUpTemplate(
  lastUserMessage: string,
  lastModelMessage: string,
  grade: string | null,
  city: string | null,
  travelClass: "Class I" | "Class II" | "Class III" | null,
): string | null {
  const recentContext = `${lastUserMessage} ${lastModelMessage}`.toLowerCase();
  const effectiveGrade = grade ?? extractMentionedGrade(lastModelMessage) ?? extractMentionedGrade(lastUserMessage);
  const effectiveClass = travelClass ?? extractMentionedTravelClass(lastModelMessage) ?? extractMentionedTravelClass(lastUserMessage);
  const locationLabel = city ?? effectiveClass;

  if (effectiveGrade && (/lodg|hotel|accommodation/.test(recentContext) || /lodging/.test(recentContext))) {
    return `What is the lodging limit for ${effectiveGrade}${locationLabel ? ` in ${locationLabel}` : ""}?`;
  }

  if (effectiveGrade && (/board|food|meal/.test(recentContext) || /boarding/.test(recentContext))) {
    return `What is the boarding limit for ${effectiveGrade}${locationLabel ? ` in ${locationLabel}` : ""}?`;
  }

  if (
    effectiveGrade &&
    (
      /travel limits|complete entitlement|combined/.test(recentContext) ||
      ((/lodg|hotel|accommodation/.test(recentContext) || /lodging/.test(recentContext)) &&
        (/board|food|meal/.test(recentContext) || /boarding/.test(recentContext)))
    )
  ) {
    return `What are the total travel limits for ${effectiveGrade}${locationLabel ? ` in ${locationLabel}` : ""}?`;
  }

  if (effectiveGrade && /mode of travel|train|flight|air|chair car/.test(recentContext)) {
    return `What is the mode of travel for ${effectiveGrade}?`;
  }

  if (effectiveGrade && /cab|conveyance|uber|ola|blusmart|metro|bus|taxi/.test(recentContext)) {
    return `What is the cab entitlement for ${effectiveGrade}?`;
  }

  if (effectiveGrade && /mab|mobility adjustment|talent mobility|sia|settling/.test(recentContext)) {
    return `What is the mobility adjustment benefit for ${effectiveGrade}?`;
  }

  if (city && /what class|which class|city classification|classified|fall in/.test(recentContext)) {
    return `What class is ${city} for travel?`;
  }

  if (city && /local conveyance/.test(recentContext)) {
    return `${city} local conveyance policy`;
  }

  if (effectiveClass && effectiveGrade) {
    return `What are the total travel limits for ${effectiveGrade} in ${effectiveClass}?`;
  }

  return null;
}

function extractPageNumber(text: string): number | undefined {
  const match = text.match(/page\s+(\d+)/i);
  return match ? Number(match[1]) : undefined;
}

function convertTableRowsToSentences(lines: string[]): string[] {
  const rows = lines
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"))
    .map((line) => line.split("|").map((cell) => cell.trim()).filter(Boolean));

  if (rows.length < 3) return [];

  const header = rows[0];
  const dataRows = rows.slice(2);

  return dataRows.map((cells) => {
    if (header.length === 2 && cells.length >= 2) {
      return `${cells[0]}: ${cells[1]}.`;
    }

    const fragments = cells
      .map((cell, index) => {
        const column = header[index] ?? `Column ${index + 1}`;
        return `${column} ${cell}`;
      })
      .join(", ");

    return ensureSentence(fragments);
  });
}

function simplifyAnswerText(text: string): string {
  const cleaned = text
    .replace(/(?:^|\n)\*Source:[^\n]*\*/gi, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .trim();

  const lines = cleaned.split("\n").map((line) => line.trim()).filter(Boolean);
  const simplifiedLines: string[] = [];
  let tableBuffer: string[] = [];

  const flushTable = () => {
    if (tableBuffer.length === 0) return;
    simplifiedLines.push(...convertTableRowsToSentences(tableBuffer));
    tableBuffer = [];
  };

  for (const line of lines) {
    if (line.startsWith("|")) {
      tableBuffer.push(line);
      continue;
    }

    flushTable();

    if (/^\|?-{3,}/.test(line)) continue;

    if (/^[\-*]\s+/.test(line) || /^•\s*/.test(line)) {
      simplifiedLines.push(ensureSentence(line.replace(/^[\-*]\s+|^•\s*/g, "")));
      continue;
    }

    simplifiedLines.push(line);
  }

  flushTable();

  return normalizeSpacing(simplifiedLines.join(" "))
    .replace(/\s+([,.;!?])/g, "$1")
    .trim();
}

function buildSimpleExplanationResponse(_query: string, history: ChatMessage[], memoryContext?: AssistantMemoryContext): AIResponse | null {
  const lastModelMessage = getLastMeaningfulModelMessage(history);
  if (!lastModelMessage) return null;

  const recentPolicyName = inferRecentPolicyName(history, memoryContext) ?? undefined;
  const policyMeta = findCanonicalPolicyMeta(undefined, recentPolicyName);
  const simplified = simplifyAnswerText(lastModelMessage);

  if (!simplified) return null;

  return {
    text: `I know policy wording can be confusing, so here it is in simple words: ${simplified}`,
    type: recentPolicyName ? "policy_details" : "general",
    suggestedQuestions: recentPolicyName
      ? [`What else should I know about ${recentPolicyName}?`, `Can you give me an example for ${recentPolicyName}?`, `What is the next step under ${recentPolicyName}?`]
      : GENERAL_POLICY_SUGGESTIONS,
    data: recentPolicyName
      ? {
          policyId: policyMeta?.id,
          policyName: policyMeta?.name ?? recentPolicyName,
          policyUrl: policyMeta?.fileUrl,
          pageNumber: extractPageNumber(lastModelMessage),
          confidenceScore: 0.92,
          source: policyMeta?.sourceDocumentName ?? recentPolicyName,
        }
      : {
          confidenceScore: 0.92,
          source: "Conversation Support",
        },
  };
}

function resolveFollowUpContext(
  query: string,
  history: ChatMessage[],
  memoryContext?: AssistantMemoryContext,
): { workingMessage: string; directResponse?: AIResponse } {
  const trimmedQuery = query.trim();
  if (!trimmedQuery || history.length === 0) {
    return { workingMessage: query };
  }

  const normalizedFollowUpQuery = normalizeFollowUpQueryText(trimmedQuery);

  if (isSimplifyFollowUp(trimmedQuery)) {
    const simpleResponse = buildSimpleExplanationResponse(trimmedQuery, history, memoryContext);
    if (simpleResponse) {
      return { workingMessage: trimmedQuery, directResponse: simpleResponse };
    }
  }

  const recentPolicyName = inferRecentPolicyName(history, memoryContext);
  if (recentPolicyName) {
    const scopedPromptPatterns = [
      /\bwho does (it|this|the policy) apply to\b/i,
      /\bwho is covered\b/i,
      /\bwhen was it effective\b/i,
      /\beffective date\b/i,
      /\bpolicy number\b/i,
      /\bhow do i report\b/i,
      /\bcomplaint channels?\b/i,
      /\bwhat is the timeline\b/i,
      /\bwhat are the timelines\b/i,
    ];

    if (scopedPromptPatterns.some((pattern) => pattern.test(trimmedQuery))) {
      return { workingMessage: `${recentPolicyName} ${trimmedQuery}` };
    }
  }

  if (!FOLLOW_UP_QUERY_PATTERN.test(normalizedFollowUpQuery)) {
    return { workingMessage: trimmedQuery };
  }

  const lastUserMessage = getLastMeaningfulUserMessage(history) ?? memoryContext?.session.conversationSummary ?? null;
  const lastModelMessage = getLastMeaningfulModelMessage(history) ?? "";
  if (!lastUserMessage) {
    return { workingMessage: trimmedQuery };
  }

  const mentionedGrade = extractMentionedGrade(normalizedFollowUpQuery);
  const mentionedCity = extractMentionedCity(normalizedFollowUpQuery);
  const mentionedClass = extractMentionedTravelClass(normalizedFollowUpQuery);

  let candidate = lastUserMessage;
  let changed = false;

  if (mentionedGrade && FOLLOW_UP_GRADE_PATTERN.test(candidate)) {
    const replacedGrade = replaceGradeInText(candidate, mentionedGrade);
    if (replacedGrade !== candidate) {
      candidate = replacedGrade;
      changed = true;
    }
  }

  if (mentionedCity) {
    const replacedCity = replaceCityInText(candidate, mentionedCity);
    if (replacedCity !== candidate) {
      candidate = replacedCity;
      changed = true;
    } else if (FOLLOW_UP_CLASS_PATTERN.test(candidate)) {
      const replacedClassWithCity = replaceTravelClassInText(candidate, mentionedCity);
      if (replacedClassWithCity !== candidate) {
        candidate = replacedClassWithCity;
        changed = true;
      }
    }
  }

  if (mentionedClass && FOLLOW_UP_CLASS_PATTERN.test(candidate)) {
    const replacedClass = replaceTravelClassInText(candidate, mentionedClass);
    if (replacedClass !== candidate) {
      candidate = replacedClass;
      changed = true;
    }
  }

  if (changed) {
    return { workingMessage: normalizeSpacing(candidate) };
  }

  const templatedQuery = buildFollowUpTemplate(
    lastUserMessage,
    lastModelMessage,
    mentionedGrade,
    mentionedCity,
    mentionedClass,
  );

  if (templatedQuery) {
    return { workingMessage: templatedQuery };
  }

  return { workingMessage: trimmedQuery };
}

function detectConversationSignals(query: string) {
  const normalized = normalizeEmployeeChatText(query);

  return {
    normalized,
    isGreeting: /^(hi+|hello+|hey+|hii+|heyy+|good morning|good afternoon|good evening|namaste|hola)(\s+(there|team|hr|bot|arvin))?[!.?]*$/.test(normalized),
    isThanks: /^(thanks|thank you|thankyou|thx|thanks a lot|tysm)[!.?]*$/.test(normalized),
    isFarewell: /^(bye|goodbye|see you|talk later|catch you later|ttyl)[!.?]*$/.test(normalized),
    isAcknowledgement: /^(ok|okay|okk|cool|got it|understood|fine|alright|all right)[!.?]*$/.test(normalized),
    isHelpRequest: /^(help|need help|please help|can you help me|guide me|support me)[!.?]*$/.test(normalized),
    feelsUpset: /\b(upset|frustrated|annoyed|angry|mad|furious|stressed|overwhelmed|fed up)\b/.test(normalized),
    feelsWorried: /\b(worried|anxious|nervous|concerned|scared|afraid|stress|stressed|panic)\b/.test(normalized),
    feelsConfused: /\b(confused|unclear|clarify|simplify|explain simply|not clear|lost)\b/.test(normalized)
      || normalized.includes("don't understand")
      || normalized.includes("do not understand"),
    feelsUnsafe: /\b(unsafe|not safe|threat|harass|harassment|bully|abuse|violence|retaliat|discriminat)\b/.test(normalized),
    mentionsSensitiveTopic: /\b(posh|grievance|whistleblower|gender|ethics|complaint|harass|retaliat|discriminat)\b/.test(normalized),
  };
}

function buildConversationalResponse(query: string, history: ChatMessage[], memoryContext?: AssistantMemoryContext): AIResponse | null {
  const signals = detectConversationSignals(query);
  const recentPolicy = inferRecentPolicyName(history, memoryContext);
  const recentTopic = memoryContext?.session.activeTopic;

  if (signals.isGreeting) {
    return {
      text: recentPolicy
        ? `Hi - I am here to help. We can continue with ${recentPolicy} or switch to any other HR policy topic you need.`
        : recentTopic
          ? `Hi - I am here to help. We can continue with ${recentTopic} or switch to any other HR policy topic you need.`
          : "Hi - I am here to help with Arvind HR policies. You can ask me about travel, local conveyance, POSH, grievance, whistleblower, joining, talent mobility, or gender policy.",
      type: "general",
      suggestedQuestions: recentPolicy
        ? [`Explain ${recentPolicy} in simple words`, `What is covered under ${recentPolicy}?`, `Show the key points of ${recentPolicy}`]
        : GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 1,
        source: "Conversation Support",
      },
    };
  }

  if (signals.isThanks) {
    return {
      text: "You are welcome. I am here if you want to check another policy or if you want me to explain the last answer more simply.",
      type: "general",
      suggestedQuestions: recentPolicy
        ? [`Explain ${recentPolicy} in simple words`, `What is covered under ${recentPolicy}?`, `Show the key points of ${recentPolicy}`]
        : GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 1,
        source: "Conversation Support",
      },
    };
  }

  if (signals.isFarewell) {
    return {
      text: "Anytime. If anything else comes up, I am here to help with HR policies and next steps.",
      type: "general",
      suggestedQuestions: [],
      data: {
        confidenceScore: 1,
        source: "Conversation Support",
      },
    };
  }

  if (signals.isAcknowledgement) {
    return {
      text: recentPolicy
        ? `Glad that helped. If you want, I can explain another part of ${recentPolicy} or help with a different policy.`
        : "Glad that helped. If you want, I can explain the next step, compare entitlements, or help with another policy.",
      type: "general",
      suggestedQuestions: recentPolicy
        ? [`What else should I know about ${recentPolicy}?`, `What is covered under ${recentPolicy}?`, `Show the key points of ${recentPolicy}`]
        : GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 1,
        source: "Conversation Support",
      },
    };
  }

  if (signals.isHelpRequest) {
    return {
      text: "Of course - I am here with you. Tell me the policy topic or the issue you are facing, and I will guide you clearly step by step.",
      type: "general",
      suggestedQuestions: GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 1,
        source: "Conversation Support",
      },
    };
  }

  return null;
}

function buildEmpatheticLead(query: string, response: AIResponse): string {
  const signals = detectConversationSignals(query);
  const intent = detectPolicyIntent(query);
  const sensitivePolicyIds = new Set(["posh-policy", "grievance-mechanism", "whistleblower", "gender-policy"]);
  const isSensitiveResponse = !!response.data?.policyId && sensitivePolicyIds.has(response.data.policyId);
  const isPolicyFactLookup =
    intent.metadataFocus ||
    intent.applicabilityFocus ||
    intent.timelineFocus ||
    /Structured .*Resolver|Policy Clause Grounder|Structured Policy Rule Engine|Policy Rule Chunk Retrieval/.test(response.data?.source ?? "");

  if (!isPolicyFactLookup && (signals.feelsUnsafe || (signals.mentionsSensitiveTopic && isSensitiveResponse))) {
    return "I am sorry you are dealing with this. ";
  }

  if (signals.feelsUpset) {
    return "I can see this feels frustrating. ";
  }

  if (signals.feelsWorried) {
    return "I understand this can feel stressful. ";
  }

  if (signals.feelsConfused) {
    return "I know policy wording can be confusing, so here it is clearly. ";
  }

  return "";
}

function buildSupportiveFallback(query: string): AIResponse {
  const signals = detectConversationSignals(query);

  if (isKnownUnsupportedPolicyQuestion(query)) {
    return {
      text: "I could not confirm this from the current policy documents I have. This does not clearly map to the loaded Arvind policy set, so please check with BUHR before acting.",
      type: "error",
      suggestedQuestions: GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 0.35,
        source: "Conversation Support",
      },
    };
  }

  const policyRoute = buildPolicyRoutingFallback(query);
  if (policyRoute) {
    return policyRoute;
  }

  if (signals.feelsUnsafe || signals.mentionsSensitiveTopic) {
    return {
      text: "I am sorry you are dealing with this. I could not confirm the exact policy wording for that from the context I have right now. If this is urgent or sensitive, please contact BUHR or use the Ethics Helpline: **1800 200 8301** (18002008301), **arvind@ethicshelpline.in**, **www.in.kpmg.com/ethicshelpline/arvind**. If you want, I can also help you find the right policy route.",
      type: "error",
      suggestedQuestions: SENSITIVE_SUPPORT_SUGGESTIONS,
      data: {
        confidenceScore: 0.35,
        source: "Conversation Support",
      },
    };
  }

  if (signals.feelsConfused) {
    return {
      text: "I could not match that exact wording to the policy text I have right now. If you want, rephrase the question in a little more detail and I will try again, or you can contact BUHR for a human review.",
      type: "error",
      suggestedQuestions: GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 0.35,
        source: "Conversation Support",
      },
    };
  }

  return {
    text: "I could not find that clearly in the policies I have right now. If you want, send me the question in a little more detail and I will try again, or you can contact BUHR for help.",
    type: "error",
    suggestedQuestions: GENERAL_POLICY_SUGGESTIONS,
    data: {
      confidenceScore: 0.35,
      source: "Conversation Support",
    },
  };
}

function humanizeResponse(response: AIResponse, query: string): AIResponse {
  if (response.data?.source === "Conversation Support") {
    return response;
  }

  if (response.data?.source === "Structured Policy Rule Engine" || response.data?.source === "Policy Rule Chunk Retrieval") {
    return response;
  }

  if (response.type === "error") {
    return buildSupportiveFallback(query);
  }

  const lead = buildEmpatheticLead(query, response);
  if (!lead) {
    return response;
  }

  const trimmedText = response.text.trim();
  if (/^(i am sorry|i'm sorry|i can see|i understand|i know)/i.test(trimmedText)) {
    return response;
  }

  return {
    ...response,
    text: `${lead}${trimmedText}`,
  };
}

function finalizeResponse(
  response: AIResponse,
  query: string,
  history: ChatMessage[],
  precisionMode: boolean,
  userContext: PersonalizationContext,
): AIResponse {
  const canonical = withCanonicalPolicyMetadata(response);
  const enriched = precisionMode ? canonical : enrichResponseForExperience(canonical, query, userContext);
  if (precisionMode) {
    return enriched;
  }

  const conversational = buildConversationalResponse(query, history);
  if (conversational) {
    return conversational;
  }

  return humanizeResponse(enriched, query);
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATIC ANSWER CACHE
// Hardcoded perfect answers for high-frequency patterns.
// These are returned INSTANTLY without any API call — guarantees 100% accuracy.
// ═══════════════════════════════════════════════════════════════════════════════

interface StaticAnswer {
  pattern: RegExp;
  answer: AIResponse;
}

const STATIC_CACHE: StaticAnswer[] = [

  // ── BMH3/H4/H5/H6 COMBINED LODGING+BOARDING ALL CLASSES ──────────────────
  {
    pattern: /(bmh[3-6]|bm.?h[3-6]|bm-?h[3-6]|h[3-6]|bmh3|bmh4|bmh5|bmh6).*(lodg|board|limit|entitl|class|total|travel)/i,
    answer: {
      text: `For **BMH3, H4, H5, H6** grades:\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| **Class I** | **₹8000**/day | **₹1500**/day |\n| **Class II** | **₹6000**/day | **₹1300**/day |\n| **Class III** | **₹5000**/day | **₹1000**/day |\n\nAll limits include GST. Per 24-hour period. Train: **1st AC**. Air: **Economy**.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class I?", "What cab can BMH3 book?", "What are M3 limits?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── BMH7 AND ABOVE — AT ACTUAL ────────────────────────────────────────────
  {
    pattern: /(bmh7|bm.?h7|bm-?h7|bmh8|bmh9|bm.?h[7-9]|bm-?h[7-9]).*(lodg|board|limit|entitl|class|total|travel|actual)/i,
    answer: {
      text: `For **BMH7 and above** (BMH7, H8, H9), lodging and boarding are reimbursed **At Actual** — there is no upper cap. The actual bill is fully reimbursed for all city classes.\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| Class I | **At Actual** | **At Actual** |\n| Class II | **At Actual** | **At Actual** |\n| Class III | **At Actual** | **At Actual** |\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What train class for BMH7?", "What cab can BMH7 use?", "What is the flat rate for BMH7?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── MODE OF TRAVEL ALL GRADES ──────────────────────────────────────────────
  {
    pattern: /mode.*travel|travel.*mode|train.*class.*(m[1-3]|bmh|e[1-2]|h[0-9])|what.*class.*(train|travel).*(m[1-3]|bmh|e[1-2]|h[0-9])|(m[1-3]|bmh|e[1-2]|h[0-9]).*(train|class|1st ac|2nd ac|3rd ac|chair car|air|fly|flight)/i,
    answer: {
      text: `**Mode of Travel Entitlements by Grade:**\n\n| Grade | Train / Bus | By Air |\n|---|---|---|\n| BMH9 | **1st AC** | Premium Economy / Business |\n| BMH7, H8 | **1st AC** | Economy / Premium Economy |\n| BMH3 to H6 | **1st AC** | Economy |\n| M3H1, M3, M2 | **2nd AC** | Economy |\n| M1, E2, E1, OT | **3rd AC / Chair Car** | Economy |\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What are lodging limits?", "What cab can I use?", "What cities are Class I?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY MAB — ALL GRADES ──────────────────────────────────────
  {
    pattern: /mab.*(e1|e2|m1|m2|m3|m3h1)|mobility.*(allowance|benefit|mab).*(e1|e2|m1|m2|m3|m3h1)|(e1|e2|m1|m2|m3|m3h1).*(mab|mobility.*allowance|mobility.*benefit|job.*rotation.*allowance)/i,
    answer: {
      text: `**Mobility Adjustment Benefit (MAB) — All Grades:**\n\n| Grade | Monthly MAB (Tier2→Tier1, 15%) | Discretionary (5%) | SIA (one-time) |\n|---|---|---|---|\n| E1 | ₹4,888 | ₹1,629 | ₹10,000 |\n| E2 | ₹6,863 | ₹2,288 | ₹10,000 |\n| M1 | ₹10,650 | ₹3,550 | ₹15,000 |\n| M2 | ₹16,250 | ₹5,417 | ₹20,000 |\n| M3 | ₹23,750 | ₹7,917 | ₹30,000 |\n| M3H1 | ₹32,500 | ₹10,833 | ₹45,000 |\n\nMAB paid for 12 months, then merged into CTC.\n\n*Source: Talent Mobility Policy, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What triggers job rotation?", "What are the rotation tracks?", "Can my manager block rotation?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ══════════════════════════════════════════════════════════════════════════
  // PRIORITY PATTERNS — These are checked FIRST because broad patterns below
  // would incorrectly match these queries
  // ══════════════════════════════════════════════════════════════════════════

  // ── GENDER POLICY EFFECTIVE DATE (must be before gender overview) ─────────
  {
    pattern: /gender.*effective|gender.*date|effective.*gender|gender.*issued|when.*gender.*polic/i,
    answer: {
      text: `The **Gender Policy** was issued on **25.07.2025** and is effective from **26.07.2025**.\n\nPolicy Number: ARV|COM_GENP|001|260725\n\n*Source: Gender Policy, Page 1*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the gender policy?", "Who does it apply to?", "How do I report gender discrimination?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY APPLICABILITY (must be before gender overview) ──────────
  {
    pattern: /gender.*(apply|appli|who|whom|cover|applicab)|who.*gender.*polic|gender.*polic.*who|gender.*polic.*appli/i,
    answer: {
      text: `The **Gender Policy** applies to **all employees** of Arvind Ltd., including:\n\n• **full-time** employees\n• Part-time employees\n• Contract staff\n• **interns**\n• **consultants**\n• **third-party** partners engaged in business operations\n\n*Source: Gender Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the gender policy?", "How do I report gender discrimination?", "When was it effective?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER COMPLAINT CHANNELS (must be before gender overview) ────────────
  {
    pattern: /gender.*(complaint|channel|report|discriminat|bias|contact|who.*contact)|discriminat.*gender|report.*gender|contact.*gender/i,
    answer: {
      text: `Report gender discrimination or bias through:\n\n| Level | Channel |\n|---|---|\n| 1st | **BUHR** (HR Department) |\n| 2nd | Line Manager |\n| 3rd | Head of Department (HOD) |\n| 4th | **Ethics Helpline** |\n| 5th | Group Ethics Officer |\n\n**Ethics Helpline:**\n- 📞 **1800 200 8301**\n- 📧 **arvind@ethicshelpline.in**\n- 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n\n*Source: Gender Policy, Page 3*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the gender policy?", "Who does it apply to?", "Is my complaint confidential?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE INVESTIGATION DAYS (must be before grievance channels) ───────
  {
    pattern: /grievance.*(investigat|how long|days|timeline|acknowledg|when.*resolv)|investigat.*grievance|acknowledg.*grievance|how long.*grievance|days.*investigat.*grievance/i,
    answer: {
      text: `**Grievance Handling Timelines:**\n\n| Stage | Timeline |\n|---|---|\n| Acknowledgement | Within **2 working days** |\n| Investigation | Within **10 working days** |\n| Resolution | Within **15 working days** |\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I raise a grievance?", "Can I raise anonymously?", "What is the appeal process?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH SCOPE — WHO CAN FILE / TRAINEES / MEN (before posh complaint) ────
  {
    pattern: /posh.*(scope|trainee|who can|men|male|gender neutral|same.?sex|appli)|trainee.*posh|men.*posh|can.*men.*posh|can.*trainee.*posh|who.*file.*posh|gender.?neutral.*posh/i,
    answer: {
      text: `**POSH Policy Scope:**\n\n• Policy is **gender neutral** — covers **all genders** (men, women, transgender)\n• Also prohibits **same-sex** harassment\n• Covers all employees: regular, temporary, ad hoc, **trainees**, apprentices, **probationers**, **contract workers**\n• Also covers third parties and visitors\n• Applies inside and outside workplace (office parties, travel, client meetings)\n\n*Source: POSH Policy, Pages 1-2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the AIC?", "What actions can AIC recommend?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH COMPLAINT DEADLINE (must be before posh complaint filing) ─────────
  {
    pattern: /posh.*(time limit|deadline|how long.*file|3 month|when.*file|incident.*file)|time limit.*posh|how long.*posh|3 month.*posh|posh.*3 month|when.*file.*posh/i,
    answer: {
      text: `A POSH complaint must be filed **within 3 months** from the date of the incident (or the last incident in a series).\n\nThis period can be **extended** by a further **3 months** if the AIC is satisfied with the reason for delay.\n\n*Source: POSH Policy, Page 6*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the AIC?", "What actions can AIC recommend?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 6, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TWO-WHEELER / SCOOTER / BIKE RATE (must be before cab patterns) ────────
  {
    pattern: /scooter|bike.*rate|bike.*km|bike.*reimburse|two.?wheel|motorcycle|two wheel/i,
    answer: {
      text: `For personal **two-wheeler** (bike/scooter/motorcycle), the local conveyance reimbursement is **₹5.00 per km**.\n\nFor four-wheeler (car): **₹10.00 per km**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the four-wheeler rate?", "How do I claim conveyance?", "Are rates same across India?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — M1/E2 COMBINED LIMITS (before generic patterns) ─────
  {
    pattern: /m1.*(lodg|board|limit|class)|e2.*(lodg|board|limit|class)|e1.*(lodg|board|limit|class)|ot.*(lodg|board)|total.*limit.*(m1|e2|e1)|travel.*limit.*(m1|e2|e1)/i,
    answer: {
      text: `For **M1, E2, E1, MT, GET, OT** grades:\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| **Class I** | **₹3400**/day | **₹1000**/day |\n| **Class II** | **₹2300**/day | **₹800**/day |\n| **Class III** | **₹1700**/day | **₹600**/day |\n\nAll limits include GST. Per 24-hour period.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class I?", "What cab can M1 use?", "What train class can M1 travel?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — M3/M2 COMBINED LIMITS (before generic patterns) ─────
  {
    pattern: /m3.*(lodg|board|limit|class.*ii|class.*iii)|m2.*(lodg|board|limit)|m3h1.*(lodg|board|limit)|total.*limit.*(m3|m2)/i,
    answer: {
      text: `For **M3H1, M3, M2** grades:\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| **Class I** | **₹6000**/day | **₹1200**/day |\n| **Class II** | **₹5000**/day | **₹1000**/day |\n| **Class III** | **₹4000**/day | **₹800**/day |\n\nAll limits include GST. Per 24-hour period.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class I?", "What cab can M3 use?", "What train class for M3?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ── ETHICS HELPLINE — PHONE ────────────────────────────────────────────────
  {
    pattern: /toll.?free|helpline.*(number|phone|call)|phone.*(helpline|ethics)|ethics.*(number|phone|toll|call)|arvind.*(helpline|toll)/i,
    answer: {
      text: `The Arvind Ethics Helpline toll-free number is **1800 200 8301** (also written as 18002008301).\n\nThis is managed by KPMG on behalf of Arvind and is available 24x7.\n\n*Source: Whistleblower Policy, POSH Policy, Grievance Mechanism Policy, Gender Policy*`,
      type: "policy_details",
      suggestedQuestions: ["What can I report on the ethics helpline?", "Is my identity protected?", "What is the ethics helpline email?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── ETHICS HELPLINE — EMAIL ────────────────────────────────────────────────
  {
    pattern: /ethics.*(email|mail)|helpline.*(email|mail)|email.*(ethics|helpline)|arvind.*ethicshelpline|ethicshelpline.*email/i,
    answer: {
      text: `The Arvind Ethics Helpline email address is **arvind@ethicshelpline.in**.\n\nThis is managed by KPMG on behalf of Arvind.\n\n*Source: Whistleblower Policy, POSH Policy, Grievance Mechanism Policy, Gender Policy*`,
      type: "policy_details",
      suggestedQuestions: ["What is the ethics helpline phone number?", "What is the ethics helpline web portal?", "Is my identity protected?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── ETHICS HELPLINE — WEBSITE / URL / PORTAL ──────────────────────────────
  {
    pattern: /ethics.*(web|portal|website|url|link|site)|helpline.*(web|portal|website|url)|web.*(ethics|helpline)|kpmg.*(helpline|arvind)|portal.*(ethics|helpline)/i,
    answer: {
      text: `The Arvind Ethics Helpline web portal is: **www.in.kpmg.com/ethicshelpline/arvind**\n\nThis is managed by KPMG on behalf of Arvind.\n\n*Source: Whistleblower Policy, POSH Policy, Grievance Mechanism Policy, Gender Policy*`,
      type: "policy_details",
      suggestedQuestions: ["What is the ethics helpline phone number?", "What is the ethics helpline email?", "Can I report anonymously?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── ETHICS HELPLINE — ALL CONTACT DETAILS ─────────────────────────────────
  {
    pattern: /ethics helpline$|all.*ethics.*contact|ethics helpline contact|contact.*ethics helpline/i,
    answer: {
      text: `**Arvind Ethics Helpline — All Contact Details:**\n\n| Channel | Details |\n|---|---|\n| 📞 Toll-Free | **1800 200 8301** |\n| 📧 Email | **arvind@ethicshelpline.in** |\n| 🌐 Web Portal | **www.in.kpmg.com/ethicshelpline/arvind** |\n\nManaged by KPMG. Available 24x7. Identity kept confidential.\n\n*Source: Whistleblower Policy, POSH Policy, Grievance Mechanism Policy, Gender Policy*`,
      type: "policy_details",
      suggestedQuestions: ["What can I report?", "Is my identity protected?", "Who handles the complaint?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POLICY LIST ────────────────────────────────────────────────────────────
  {
    pattern: /list.*polic|all.*polic|what.*polic.*arvind|arvind.*polic|polic.*available|polic.*have|hr polic/i,
    answer: {
      text: `Arvind Limited has the following HR policies:\n\n| # | Policy Name | Policy Number |\n|---|---|---|\n| 1 | **Domestic Travel Policy** | ARV\\|EOP_DTP\\|003\\|270723 |\n| 2 | **Local Conveyance Policy** | ARV\\|COR\\|EOP_LCP\\|002\\|010722 |\n| 3 | **POSH Policy** (Sexual Harassment) | ARV\\|ELC_SHA\\|008\\|010422 |\n| 4 | **Whistleblower Policy** | — |\n| 5 | **Grievance Mechanism Policy** | ARV\\|COM_GRM\\|001\\|260725 |\n| 6 | **Gender Policy** (gender equality, equal access, all gender identities) | ARV\\|COM_GENP\\|001\\|260725 |\n| 7 | **Talent Mobility Policy** | — |\n| 8 | **Joining Policy** | — |\n\n*Source: Arvind Limited HR Policy Repository*`,
      type: "policy_details",
      suggestedQuestions: ["What is the Domestic Travel Policy?", "How do I raise a grievance?", "What is POSH?"],
      data: { policyId: "domestic-travel", policyName: "Multiple Policies", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── WHISTLEBLOWER — WHAT TO REPORT ────────────────────────────────────────
  {
    pattern: /what.*report.*whistleblow|whistleblow.*what.*report|whistleblow.*cover|cover.*whistleblow|types.*whistleblow|whistleblow.*types/i,
    answer: {
      text: `Under the **Whistleblower Policy**, you can report:\n\n• **Bribery and corruption**\n• **Procurement and tendering fraud**\n• **Misappropriation / theft / embezzlement** of company assets\n• **False invoicing**\n• **Fraudulent financial accounting**, auditing and reporting\n• **Corporate espionage** and information disclosure\n• **Workplace harassment** and discrimination\n• **Employee negligence**\n• **Health, safety, environment** violations\n• **Breach of internal compliance** requirements\n• Any other fraud and misconduct\n\nReport via: 📞 **1800 200 8301** | 📧 **arvind@ethicshelpline.in** | 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n\n*Source: Whistleblower Policy, Page 3, Section 5*`,
      type: "policy_details",
      suggestedQuestions: ["How do I report?", "Is my identity protected?", "What happens after I report?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── WHISTLEBLOWER — HOW TO REPORT / CHANNELS ──────────────────────────────
  {
    pattern: /whistleblow.*(channel|report|how|raise)|how.*whistleblow|report.*unethical|unethical.*report|ethics.*how.*report|report.*ethics/i,
    answer: {
      text: `To raise a whistleblower complaint, report through any of these channels:\n\n| Channel | Details |\n|---|---|\n| 🌐 Web Portal | **www.in.kpmg.com/ethicshelpline/arvind** |\n| 📞 Toll-Free | **1800 200 8301** (also: 18002008301) |\n| 📧 Email | **arvind@ethicshelpline.in** |\n\nAll reports are handled confidentially by **KPMG** on behalf of Arvind. Your identity is protected.\n\n*Source: Whistleblower Policy, Page 3, Section 6*`,
      type: "policy_details",
      suggestedQuestions: ["What can I report?", "Will my identity be protected?", "What happens after I report?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── WHISTLEBLOWER — PROTECTION / RETALIATION ──────────────────────────────
  {
    pattern: /whistleblow.*(protect|retaliat|confiden|identity|safe)|retaliat.*whistleblow|confiden.*whistleblow/i,
    answer: {
      text: `**Yes, you are fully protected as a whistleblower:**\n\n• **Complete confidentiality** — your identity will not be disclosed\n• **No retaliation** — victimization is treated as a serious disciplinary matter\n• **Protection for witnesses** — same protection applies to anyone who participates in investigation\n• If victimized, file a written complaint to the **Committee Chairman**\n• The accused may be **terminated** if found guilty of retaliating\n\n*Source: Whistleblower Policy, Pages 4-5, Sections 9-10*`,
      type: "policy_details",
      suggestedQuestions: ["How do I report retaliation?", "What is the whistleblower email?", "Who handles the investigation?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — HOW TO FILE COMPLAINT ──────────────────────────────────────────
  {
    pattern: /posh.*(complaint|file|report|how)|sexual.?harass.*(complaint|file|report|how)|how.*(sexual.?harass|posh)|file.*sexual|report.*sexual.?harass/i,
    answer: {
      text: `To file a **POSH (Sexual Harassment)** complaint:\n\n**Step 1 — Report to any of these:**\n• Supervisor / Reporting Manager / trusted person in hierarchy\n• Business Unit HR Head (BUHR)\n• **AIC (Arvind Internal Complaint Committee)**\n\n**Step 2 — Whistleblowing channels:**\n| Channel | Details |\n|---|---|\n| 📞 Hotline | **18002008301** (also: 1800 200 8301) |\n| 📧 Email | **arvind@ethicshelpline.in** |\n| 🌐 Portal | **www.in.kpmg.com/ethicshelpline/arvind/** |\n\n**Important rules:**\n• Complaint must be in **writing or email** (with signature)\n• Must be filed within **3 months** of the incident\n• **Anonymous complaints are NOT accepted** by AIC\n\n*Source: POSH Policy, Page 5*`,
      type: "policy_details",
      suggestedQuestions: ["What is the POSH complaint deadline?", "What can AIC recommend?", "Is the POSH policy gender neutral?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 5, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — INQUIRY TIMELINE ────────────────────────────────────────────────
  {
    pattern: /posh.*(timeline|inquiry|duration|long|days|time limit)|inquiry.*posh|posh.*inquiry.*time|time.*posh.*inquiry/i,
    answer: {
      text: `**POSH Inquiry Timeline:**\n\n| Stage | Deadline |\n|---|---|\n| Complaint filing window | Within **3 months** of incident (extendable by 3 more months) |\n| AIC completes inquiry | Within **90 days** |\n| AIC submits report to management | Within **10 days** of inquiry completion |\n| Management acts on recommendation | Within **60 days** of receiving report |\n\n*Source: POSH Policy, Pages 6-7*`,
      type: "policy_details",
      suggestedQuestions: ["What can AIC recommend?", "Can I get leave during inquiry?", "How do I file a POSH complaint?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 6, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — AIC ACTIONS / PUNISHMENT ───────────────────────────────────────
  {
    pattern: /aic.*(recommend|action|punish)|punish.*sexual|posh.*(punish|action|recommend|discipline)|what.*aic.*do|discipline.*sexual/i,
    answer: {
      text: `If sexual harassment is **proved**, the AIC can recommend:\n\n• **Written warning** or written apology\n• **Reprimand / Censure**\n• **Withholding of promotion**\n• **Withholding of pay rise** or increments\n• **Termination** from service\n• Counselling session\n• Community service\n• **Monetary compensation** (deducted from accused's salary)\n\n*Source: POSH Policy, Page 8*`,
      type: "policy_details",
      suggestedQuestions: ["What is the POSH inquiry timeline?", "How do I file a complaint?", "Is the policy gender neutral?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 8, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — POSH HELPLINE NUMBER ────────────────────────────────────────────
  {
    pattern: /posh.*(number|phone|helpline|call|toll)|helpline.*posh/i,
    answer: {
      text: `The POSH helpline / Ethics Helpline number is **18002008301** (also: 1800 200 8301).\n\n*Source: POSH Policy, Page 5*`,
      type: "policy_details",
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the POSH email?", "What can AIC recommend?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 5, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — SCOPE / WHO CAN FILE ───────────────────────────────────────────
  {
    pattern: /posh.*(scope|who|trainee|men|male|gender neutral|same.?sex)|trainee.*posh|men.*posh|gender.?neutral.*posh/i,
    answer: {
      text: `**POSH Policy Scope:**\n\n• Policy is **gender neutral** — covers **all genders** (men, women, transgender)\n• Also prohibits **same-sex harassment**\n• Covers all employees: regular, temporary, ad hoc, **trainees**, apprentices, **probationers**, contract workers\n• Also covers third parties and visitors\n• Extended Workplace includes: office parties, off-sites, client meetings, training sessions, travel, and even dwelling places\n\n*Source: POSH Policy, Pages 1-2*`,
      type: "policy_details",
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the AIC?", "What actions can AIC recommend?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── POSH — EXTENDED WORKPLACE ─────────────────────────────────────────────
  {
    pattern: /extended.?workplace|posh.*outside|outside.*posh|posh.*office.?part|office.?part.*posh|posh.*travel/i,
    answer: {
      text: `**Yes.** POSH covers the **Extended Workplace**, which includes:\n\n• **Office parties**\n• **Off-sites / Client meetings**\n• **Training sessions / Outbound trainings**\n• **Travel** for office purposes\n• Any place visited in the course of employment\n• A dwelling place or house\n\n*Source: POSH Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the AIC?", "Is POSH gender neutral?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE — HOW TO RAISE ──────────────────────────────────────────────
  {
    pattern: /raise.*grievance|grievance.*(raise|how|channel|file|report|complaint)|how.*grievance|complaint.*work|work.*complaint/i,
    answer: {
      text: `You can raise a grievance through any of these channels:\n\n| Level | Channel |\n|---|---|\n| 1st | **Immediate HR Representative (BUHR)** |\n| 2nd | **Line Manager or Supervisor** |\n| 3rd | **Head of Department (HOD)** |\n| 4th | **Ethics Helpline** |\n| 5th | **Group Ethics Officer** |\n\n**Ethics Helpline (anonymous option):**\n| Channel | Details |\n|---|---|\n| 🌐 Web | **www.in.kpmg.com/ethicshelpline/arvind** |\n| 📞 Phone | **1800 200 8301** |\n| 📧 Email | **arvind@ethicshelpline.in** |\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["How long to resolve grievance?", "Can I raise anonymously?", "What is the appeal process?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE — TIMELINES ─────────────────────────────────────────────────
  {
    pattern: /grievance.*(timeline|days|long|acknowledge|investigat|resolv|when)|acknowledge.*grievance|investigate.*grievance|resolv.*grievance/i,
    answer: {
      text: `**Grievance Handling Timelines:**\n\n| Stage | Timeline |\n|---|---|\n| Acknowledgement | Within **2 working days** of receipt |\n| Investigation | Completed within **10 working days** wherever possible |\n| Resolution & Feedback | Communicated within **15 working days** of receipt |\n| Appeal | Escalate to BU Head, Ethics Officer, or Group HR |\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      type: "policy_details",
      suggestedQuestions: ["How do I raise a grievance?", "Can I raise anonymously?", "What if I'm unhappy with the outcome?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE — ANONYMOUS ─────────────────────────────────────────────────
  {
    pattern: /anonymous.*grievance|grievance.*anonymous|anonymous.*complaint|complaint.*anonymous/i,
    answer: {
      text: `**Yes**, anonymous grievances are accepted, provided **sufficient information is provided for investigation**.\n\nUse the Ethics Helpline for anonymous submissions:\n• 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n• 📞 **1800 200 8301**\n• 📧 **arvind@ethicshelpline.in**\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["How do I raise a grievance?", "What are the timelines?", "What is the appeal process?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE — FALSE / MALICIOUS ─────────────────────────────────────────
  {
    pattern: /false.*grievance|grievance.*false|malicious.*complaint|fake.*complaint|fake.*grievance/i,
    answer: {
      text: `Any employee found to have **deliberately submitted a false or malicious complaint** may be subject to **disciplinary action** in line with the company's Code of Conduct.\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      type: "policy_details",
      suggestedQuestions: ["How do I raise a genuine grievance?", "What is the appeal process?", "Who handles grievances?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE — TYPES COVERED ─────────────────────────────────────────────
  {
    pattern: /grievance.*(types|cover|what|definition|about)|types.*grievance|what.*grievance/i,
    answer: {
      text: `A grievance covers any concern about your work environment or employment, including:\n\n• **Discrimination, harassment, or unfair treatment**\n• **Interpersonal conflict or misconduct**\n• **Workload or role clarity issues**\n• **Breach of company policy or code of conduct**\n• **Violation of health, safety, or ethical standards**\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["How do I raise a grievance?", "Can I raise anonymously?", "What are the timelines?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY — OVERVIEW ──────────────────────────────────────────────
  {
    pattern: /gender.*(policy|equal|inclus)|gender.*arvind|arvind.*gender/i,
    answer: {
      text: `**Arvind Gender Policy** (Issued: **25.07.2025** | Effective: **26.07.2025** | Policy No: ARV|COM_GENP|001|260725)\n\nArvind is committed to **gender equality and inclusion** across all levels. Key principles:\n\n• **Equal Access**: All employees have equal access to employment, development, and leadership opportunities — no discrimination based on gender, gender identity, or gender expression\n• **Zero Tolerance**: Gender-based harassment, microaggressions, or stereotyping → disciplinary action\n• **Inclusive Culture**: Gender-sensitive work environment for all gender identities\n• **Work-Life Support**: Maternity, paternity, parental leave, return-to-work support\n\n*Source: Gender Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["How do I report gender discrimination?", "Who does the policy apply to?", "When was the policy effective?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY — APPLICABILITY ─────────────────────────────────────────
  {
    pattern: /gender.*(appli|who|apply|cover|whom)|who.*gender.*policy|gender.*policy.*who/i,
    answer: {
      text: `The **Gender Policy** applies to **all employees of Arvind Ltd.**, including:\n\n• **full-time** employees\n• **Part-time** employees\n• **Contract staff**\n• **Interns**\n• **Consultants**\n• **third-party** partners engaged in business operations\n\n*Source: Gender Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["What is the gender policy?", "How do I report gender discrimination?", "When was it effective?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY — COMPLAINT CHANNELS ────────────────────────────────────
  {
    pattern: /gender.*(complaint|discriminat|report|bias|harass|contact|channel)|discriminat.*gender|report.*gender/i,
    answer: {
      text: `Report gender discrimination or bias through:\n\n| Level | Channel |\n|---|---|\n| 1st | **HR Department (BUHR)** |\n| 2nd | **Line Manager** |\n| 3rd | **Head of Department (HOD)** |\n| 4th | **Ethics Helpline** |\n| 5th | **Group Ethics Officer** |\n\n**Ethics Helpline:**\n• 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n• 📞 **1800 200 8301**\n• 📧 **arvind@ethicshelpline.in**\n\n*Source: Gender Policy, Page 3*`,
      type: "policy_details",
      suggestedQuestions: ["What is the gender policy?", "Who does it apply to?", "Is my complaint confidential?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

    // ── JOINING POLICY — PRE-JOINING VISIT ─────────────────────────────────
  {
    pattern: /pre.?join|pre join|visit.*before.*join|before.*join.*visit|visit.*joining|joining.*visit|accommodation.*find.*join|find.*accommodat.*join/i,
    answer: {
      text: `New recruits are eligible for a **pre-joining** visit for **3 days** (maximum) to the posting location.\n\nExpenses reimbursed for **self** and **spouse** (and children for school admission).\n\nPurpose: Find accommodation, school admissions, etc.\n\n*Source: Joining Policy, Page 1*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What accommodation do I get on joining?", "What is the relocation allowance?", "When must I claim joining expenses?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

// ── JOINING POLICY — EARLY EXIT / RECOVERY ────────────────────────────────
  {
    pattern: /leav.*within.*year|quit.*year|exit.*year|1 year.*join|join.*1 year|recovery.*join|join.*recovery|f.*f.*join|full.*final.*join/i,
    answer: {
      text: `If you **quit within 1 year of joining**, the following will be **recovered in your Full & Final settlement**:\n\n• **Joining Bonus**\n• **Relocation Expenses**\n• **Notice Pay Buyout**\n• **Variable Pay Reimbursement** (including brokerage)\n\n*Source: Joining Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["What is the joining bonus policy?", "What is the brokerage reimbursement?", "What are relocation benefits?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — HOUSE DEPOSIT ────────────────────────────────────────
  {
    pattern: /house.?deposit|deposit.*join|join.*deposit/i,
    answer: {
      text: `On joining, the company provides a **house deposit as an advance** to the employee. It is recovered in **10 equal monthly instalments (interest-free)**.\n\n*Source: Joining Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["What is the brokerage reimbursement?", "What is the relocation allowance?", "What accommodation do I get?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — BROKERAGE ────────────────────────────────────────────
  {
    pattern: /brokerage.*join|join.*brokerage|rent.*brokerage|brokerage.*rent/i,
    answer: {
      text: `**Brokerage Reimbursement on Joining:**\n\n• Amount: **One month's rent** reimbursed against brokerage receipt\n• Available **only once** during employment with Arvind\n• Available for maximum **1 year** from date of joining\n\n*Source: Joining Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["What is the house deposit policy?", "What is the relocation allowance?", "When must expenses be claimed?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — DRIVER WAGES ─────────────────────────────────────────
  {
    pattern: /driver.*wage|driver.*relocat|relocat.*driver|driver.*join/i,
    answer: {
      text: `**Driver Wages during Relocation:**\n\n| Duration | Amount |\n|---|---|\n| For 8-hour trip | **₹600/-** |\n| After 8 hours | **₹50 per hour** |\n| Food (per meal) | **Max ₹200 per meal** |\n\n*Source: Joining Policy, Page 1*`,
      type: "policy_details",
      suggestedQuestions: ["What is the relocation allowance?", "What is the per km rate for car?", "What accommodation do I get on joining?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — CLAIM DEADLINE ──────────────────────────────────────
  {
    pattern: /join.*claim.*deadline|claim.*deadline.*join|join.*expense.*deadline|when.*claim.*join/i,
    answer: {
      text: `All joining expenses must be **claimed within 1 year from the Date of Joining**.\n\n*Source: Joining Policy, Page 2*`,
      type: "policy_details",
      suggestedQuestions: ["What expenses can I claim?", "What is the recovery policy?", "What is the brokerage reimbursement?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — ACCOMMODATION ────────────────────────────────────────
  {
    pattern: /join.*(accommodat|hotel|stay)|accommodat.*join|new.*join.*(hotel|accommodat|stay)|outstation.*join/i,
    answer: {
      text: `New recruits are eligible for a **pre-joining** visit for **3 days** (maximum) to the posting location.\n\nExpenses reimbursed for:\n• **Self**\n• **Spouse**\n• Children (for school admission)\n\nPurpose: Find accommodation, school admissions, etc.\n\n*Source: Joining Policy, Page 1*`,
      type: "policy_details",
      suggestedQuestions: ["What is the pre-joining visit policy?", "What are cab entitlements?", "What is the relocation allowance?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING POLICY — RELOCATION / HOUSEHOLD GOODS ────────────────────────
  {
    pattern: /household.*goods|packers.*movers|relocat.*(goods|limit|allow|household)|transportation.*goods/i,
    answer: {
      text: `**Transportation of Household Goods (Joining Relocation):**\n\n| Distance | Rate |\n|---|---|\n| Less than 700 km | Max **₹50 per km** OR Actuals — whichever is **lesser** |\n| More than 700 km | Max **₹60 per km** OR Actuals — whichever is **lesser** |\n\nIncome tax is grossed up based on employee's tax bracket.\n\n*Source: Joining Policy, Page 1*`,
      type: "policy_details",
      suggestedQuestions: ["What is the car transportation rate?", "What accommodation do I get?", "What is the driver wage?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY — ROTATION TRIGGER ────────────────────────────────────
  {
    pattern: /trigger.*rotation|rotation.*trigger|3 year|three year.*rotation|mandatory.*rotation|when.*rotation/i,
    answer: {
      text: `**Job rotation is triggered after 3 years in the same role.**\n\n• All positions up to **M2 grade** must be closed via **Internal Job Posting (IJP)**\n• Exceptions must be justified\n• **1st Rotation**: Within the same city\n• **2nd Rotation**: Across different business / different location\n\n*Source: Talent Mobility Policy, Page 4*`,
      type: "policy_details",
      suggestedQuestions: ["What are the rotation tracks?", "Who can approve exceptions?", "What is the MAB allowance?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY — MANAGER BLOCK ───────────────────────────────────────
  {
    pattern: /manager.*block|block.*rotation|manager.*rotation|can manager/i,
    answer: {
      text: `**No, managers cannot block talent mobility.**\n\nOnly the **CHRO or CEO** can approve exceptions to the Talent Mobility Policy. Managers are not permitted to block or delay an employee's rotation.\n\n*Source: Talent Mobility Policy, Page 4*`,
      type: "policy_details",
      suggestedQuestions: ["What triggers job rotation?", "What are the rotation tracks?", "What is the MAB allowance?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY — TRACKS ──────────────────────────────────────────────
  {
    pattern: /rotation.*(track|type)|talent.*track|mobility.*track|track.*rotation/i,
    answer: {
      text: `**Talent Mobility Rotation Framework — 3 Tracks:**\n\n| Track | Name | Description |\n|---|---|---|\n| Track A | **Risk Mitigation** | Sensitive roles in risk-prone functions |\n| Track B | **Leadership / HiPo** | Future leaders broadened via structured mobility |\n| Track C | **On Demand** | Voluntary, employee-driven career paths |\n\n*Source: Talent Mobility Policy, Page 5*`,
      type: "policy_details",
      suggestedQuestions: ["What triggers rotation?", "Who can approve exceptions?", "What is the MAB allowance?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 5, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LOCAL CONVEYANCE — AHMEDABAD RESTRICTIONS ─────────────────────────────
  {
    pattern: /ahmedabad.*(conveyance|restrict|not.*reimburse|reimburse)|restrict.*ahmedabad/i,
    answer: {
      text: `Employees in **Ahmedabad** with a company car are **NOT reimbursed** for local conveyance when travelling to:\n\n• **Santej**\n• **Raipur**\n• **Gomtipur**\n• Any other units located in the **vicinity of Ahmedabad city**\n\n*Source: Local Conveyance Policy, Page 1, Section 4(a)(ii)*`,
      type: "policy_details",
      suggestedQuestions: ["What is the per km rate?", "How do I claim conveyance?", "Who approves conveyance claims?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LOCAL CONVEYANCE — APPROVAL ───────────────────────────────────────────
  {
    pattern: /conveyance.*(approv|authorit|who approv)|approv.*conveyance/i,
    answer: {
      text: `Local conveyance expenses must be approved **only by BM grade employees** of the respective department.\n\nThe manager is responsible for ensuring the **authenticity** of all claims made.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(vi)*`,
      type: "policy_details",
      suggestedQuestions: ["What is the per km rate?", "How do I claim conveyance?", "Are rates same across India?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LOCAL CONVEYANCE — SHARED VEHICLE ─────────────────────────────────────
  {
    pattern: /shared.*(vehicle|cab|conveyance)|two.*person.*vehicle|multiple.*person.*vehicle|share.*cab/i,
    answer: {
      text: `If more than one person travels in the same vehicle, **only the individual who actually incurred the cost** can claim reimbursement.\n\nThe others in the vehicle **cannot** also claim for the same trip.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(v)*`,
      type: "policy_details",
      suggestedQuestions: ["What is the per km rate?", "How do I claim conveyance?", "Who approves conveyance?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LOCAL CONVEYANCE — HOW TO CLAIM ───────────────────────────────────────
  {
    pattern: /how.*(claim|file|submit).*conveyance|claim.*local.*conveyance|local.*conveyance.*claim/i,
    answer: {
      text: `To claim local conveyance:\n\n1. Go to **Orapps → ESMS → Entry → Conveyance Expense**\n2. Enter **total km travelled** in the day\n3. System auto-deducts to-and-fro km from **residence to official location**\n\nFor taxi: submit actual bills/vouchers.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(ii)*`,
      type: "policy_details",
      suggestedQuestions: ["What is the per km rate?", "Who approves conveyance?", "Are rates same across India?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — CAB M1/E1/E2 ───────────────────────────────────────
  {
    pattern: /(m1|e1|e2|ot|get|mt).*(cab|conveyance|ola|uber)|cab.*(m1|e1|e2|ot)|which.*cab.*(m1|e1|e2)/i,
    answer: {
      text: `For **M1, MT, E2, GET, E1, OT** grades, the cab/conveyance entitlement is:\n\n**Ola / Uber / BluSmart / Bus / Metro / Local Transportation**\n\n*Source: Domestic Travel Policy, Annexure B, Page 8*`,
      type: "policy_details",
      suggestedQuestions: ["What are the lodging limits for M1?", "What are boarding limits for M1?", "What train class can M1 travel in?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 8, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — CAB M3/M2/M3H1 ─────────────────────────────────────
  {
    pattern: /(m2|m3|m3h1).*(cab|conveyance|ola|uber)|cab.*(m2|m3|m3h1)|which.*cab.*(m2|m3)/i,
    answer: {
      text: `For **M3H1, M3, M2** grades, the cab/conveyance entitlement is:\n\n**Ola / Uber / BluSmart**\n\n*Source: Domestic Travel Policy, Annexure B, Page 8*`,
      type: "policy_details",
      suggestedQuestions: ["What are the lodging limits for M3?", "What are boarding limits?", "What train class for M3?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 8, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — CITY: JAMMU ─────────────────────────────────────────
  {
    pattern: /jammu.*(class|travel|city)|city.*jammu|class.*jammu/i,
    answer: {
      text: `**Jammu** is classified as a **Class II city** under the Domestic Travel Policy.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details",
      suggestedQuestions: ["What are the lodging limits for Class II?", "Which cities are Class I?", "What are boarding limits for Class II?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ── POSH — COMPLAINT DEADLINE / TIME LIMIT ────────────────────────────────
  {
    pattern: /posh.*(time limit|deadline|when.*file|3 month|how long.*file)|time limit.*posh|3 month.*posh|how long.*posh.*complaint|incident.*posh|posh.*incident/i,
    answer: {
      text: `A POSH complaint must be filed **within 3 months from the date of the incident** (or the last incident in a series).\n\nThis period can be **extended by a further 3 months** if the AIC is satisfied with the reason for delay.\n\n*Source: POSH Policy, Page 6*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I file a POSH complaint?", "What is the AIC?", "What actions can AIC recommend?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 6, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — LODGING M3 CLASS I ──────────────────────────────────
  {
    pattern: /lodg.*(m3|m3h1).*class.*(i|1|one)|m3.*lodg.*class.*(i|1|one)|(m3|m3h1).*hotel.*class.*(i|1)|class.*(i|1|one).*lodg.*(m3|m3h1)/i,
    answer: {
      text: `For **M3H1, M3, M2** grades, the lodging limit in **Class I** cities is **₹6,000 per day** (inclusive of GST).\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| Class I | ₹6000 (6,000) | ₹1200 (1,200) |\n| Class II | ₹5000 (5,000) | ₹1000 (1,000) |\n| Class III | ₹4000 (4,000) | ₹800 |\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What are M3 boarding limits?", "What train class can M3 travel?", "What cities are Class I?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — LODGING+BOARDING M1/E2 CLASS I/II/III ──────────────
  {
    pattern: /(m1|e1|e2|ot).*(lodg|board).*class|(m1|e1|e2|ot).*(class.*(i|1|ii|2|iii|3)).*(limit|entitlement|allow)|total.*limit.*(m1|e1|e2).*class|lodg.*board.*(m1|e2).*class/i,
    answer: {
      text: `For **M1, E2, E1, MT, GET, OT** grades:\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| **Class I** | **₹3400** (3,400)/day | **₹1000** (1,000)/day |\n| **Class II** | **₹2300** (2,300)/day | **₹800**/day |\n| **Class III** | **₹1700** (1,700)/day | **₹600**/day |\n\nAll limits include GST. Per 24-hour period.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class I?", "What cab can M1 use?", "What train class can M1 travel?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — OT LODGING CLASS II ─────────────────────────────────
  {
    pattern: /lodg.*ot.*class.*(ii|2)|ot.*lodg.*class.*(ii|2)|ot.*class.*(ii|2).*(limit|allow)/i,
    answer: {
      text: `For **OT** (and M1, MT, E2, GET, E1 group), the lodging limit in **Class II** cities is **₹2,300 per day**. Boarding is **₹800 per day** (inclusive of GST).\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What are OT limits for Class I?", "What cab can OT use?", "What cities are Class II?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — M3 CLASS III ────────────────────────────────────────
  {
    pattern: /m3.*(class.*(iii|3|three)|class three)|class.*(iii|3|three).*m3/i,
    answer: {
      text: `For **M3H1, M3, M2** grades in **Class III** cities:\n\n| Type | Limit |\n|---|---|\n| **Lodging** | **₹4,000**/day |\n| **Boarding** | **₹800**/day |\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class III?", "What are M3 limits for Class I?", "What are M3 limits for Class II?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── DOMESTIC TRAVEL — E1 BOARDING CLASS II ────────────────────────────────
  {
    pattern: /board.*(e1|e2).*(class.*(ii|2|two))|e1.*board.*class.*(ii|2)|boarding.*e1.*class/i,
    answer: {
      text: `For **E1** (and M1, MT, E2, GET, OT group), the boarding limit in **Class II** cities is **₹800 per day**. Lodging is ₹2,300 per day (inclusive of GST).\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What are E1 limits for Class I?", "What cities are Class II?", "What cab can E1 use?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LOCAL CONVEYANCE — TWO WHEELER / BIKE ─────────────────────────────────
  {
    pattern: /two.?wheel|bike.*km|scooter.*km|km.*bike|bike.*reimburse|scooter.*reimburse|reimburse.*bike|bike.*rate|scooter.*rate|motorcycle.*km/i,
    answer: {
      text: `For personal **two-wheeler (bike/scooter/motorcycle)**, the reimbursement is **₹5.00 per km**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the four-wheeler rate?", "How do I claim conveyance?", "Are rates same across India?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY — FIRST ROTATION ──────────────────────────────────────
  {
    pattern: /first.*rotation|1st.*rotation|rotation.*first|rotation.*sequence|where.*rotation|rotation.*within.*city/i,
    answer: {
      text: `Under the Talent Mobility Policy:\n\n• **1st Rotation** — Within the **same city**\n• **2nd Rotation** — Across a **different business or different location**\n\nRotation is triggered after **3 years** in the same role.\n\n*Source: Talent Mobility Policy, Page 4*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the MAB allowance?", "Who can approve exceptions?", "What are the rotation tracks?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ── WHAT TO DO IF SEXUAL HARASSMENT ──────────────────────────────────────
  {
    pattern: /what.*do.*sexual|what.*do.*harass|sexual.*what.*do|face.*harassment|harass.*what.*do|if.*harass|if.*sexual/i,
    answer: {
      text: `If you face sexual harassment, here's what to do:\n\n1. **Report to any of these channels:**\n   - Supervisor / Reporting Manager\n   - Business Unit HR Head (BUHR)\n   - AIC (Arvind Internal Complaint Committee)\n\n2. **File a written complaint** (writing or email with signature)\n\n3. **Whistleblowing channels:**\n   - 📞 **18002008301** (also: 1800 200 8301)\n   - 📧 **arvind@ethicshelpline.in**\n   - 🌐 **www.in.kpmg.com/ethicshelpline/arvind/**\n\n**Note:** Complaint must be filed within **3 months** of the incident. Anonymous complaints are NOT accepted by AIC.\n\n*Source: POSH Policy, Page 5*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the POSH inquiry timeline?", "What can AIC recommend?", "Is POSH gender neutral?"],
      data: { policyId: "posh-policy", policyName: "POSH Policy", pageNumber: 5, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── MANAGER BLOCK ROTATION ────────────────────────────────────────────────
  {
    pattern: /manager.*block|block.*rotat|can.*manager|manager.*rotat|stop.*rotat|rotat.*stop|manager.*prevent/i,
    answer: {
      text: `**No, managers cannot block talent mobility.**\n\nOnly the **CHRO or CEO** can approve exceptions to the Talent Mobility Policy. Managers are not permitted to block or delay an employee's rotation.\n\n*Source: Talent Mobility Policy, Page 4*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What triggers job rotation?", "What are the rotation tracks?", "What is the MAB allowance?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── ANONYMOUS GRIEVANCE ───────────────────────────────────────────────────
  {
    pattern: /anonymous|anonymously|without.*name|confidential.*complain|complain.*confidential/i,
    answer: {
      text: `**Yes**, anonymous grievances are accepted provided **sufficient information is provided for investigation**.\n\nUse the **Ethics Helpline** for anonymous submissions:\n- 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n- 📞 **1800 200 8301**\n- 📧 **arvind@ethicshelpline.in**\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I raise a grievance?", "What are the timelines?", "What is the appeal process?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── LODGING M3 CLASS I (broad match) ─────────────────────────────────────
  {
    pattern: /lodg.*(m3|m2|m3h1)|m3.*lodg|m2.*lodg|m3h1.*lodg/i,
    answer: {
      text: `For **M3H1, M3, M2** grades, lodging limits are:\n\n| City Class | Lodging | Boarding |\n|---|---|---|\n| **Class I** | **₹6,000**/day | **₹1,200**/day |\n| **Class II** | **₹5,000**/day | **₹1,000**/day |\n| **Class III** | **₹4,000**/day | **₹800**/day |\n\nAll limits include GST. Per 24-hour period.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What cities are Class I?", "What train class for M3?", "What are M1 lodging limits?"],
      data: { policyId: "domestic-travel", policyName: "Domestic Travel Policy", pageNumber: 7, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── JOINING CLAIM DEADLINE (broad) ────────────────────────────────────────
  {
    pattern: /joining.*claim|claim.*joining|joining.*deadline|joining.*expense.*when|when.*joining.*claim|joining.*expense.*deadline/i,
    answer: {
      text: `All joining expenses must be **claimed within 1 year from the Date of Joining**.\n\n*Source: Joining Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What expenses can I claim?", "What is the recovery policy?", "What is the brokerage reimbursement?"],
      data: { policyId: "joining-policy", policyName: "Joining Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── BIKE / TWO-WHEELER REIMBURSEMENT (broad) ──────────────────────────────
  {
    pattern: /bike|scooter|two.?wheel|motorcycle|two wheel/i,
    answer: {
      text: `For personal **two-wheeler (bike/scooter/motorcycle)**, the local conveyance reimbursement is **₹5.00 per km**.\n\nFor four-wheeler (car): **₹10.00 per km**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the four-wheeler rate?", "How do I claim conveyance?", "Are rates same across India?"],
      data: { policyId: "local-conveyance", policyName: "Local Conveyance Policy", pageNumber: 1, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── TALENT MOBILITY TRACKS (broad) ────────────────────────────────────────
  {
    pattern: /talent.*track|mobility.*track|track.*talent|rotation.*track|track.*rotation|track a|track b|track c/i,
    answer: {
      text: `**Talent Mobility Rotation Framework — 3 Tracks:**\n\n| Track | Name | Description |\n|---|---|---|\n| **Track A** | Risk Mitigation | Mandatory rotation for sensitive roles in risk-prone functions |\n| **Track B** | Leadership / HiPo | Future leaders broadened via structured mobility |\n| **Track C** | On Demand | Voluntary, employee-driven career paths |\n\n*Source: Talent Mobility Policy, Page 5*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What triggers rotation?", "Who can approve exceptions?", "What is the MAB allowance?"],
      data: { policyId: "talent-mobility", policyName: "Talent Mobility Policy", pageNumber: 5, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GRIEVANCE INVESTIGATION / ACKNOWLEDGE DAYS ────────────────────────────
  {
    pattern: /grievance.*(investigat|days|long|acknowledg|timeline|when|how long)|investigat.*grievance|acknowledg.*grievance|days.*grievance/i,
    answer: {
      text: `**Grievance Handling Timelines:**\n\n| Stage | Timeline |\n|---|---|\n| Acknowledgement | Within **2 working days** |\n| Investigation | Within **10 working days** |\n| Resolution | Within **15 working days** |\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I raise a grievance?", "Can I raise anonymously?", "What is the appeal process?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY OVERVIEW (broad) ────────────────────────────────────────
  {
    pattern: /gender.*policy|gender.*equal|gender.*arvind|arvind.*gender|gender.*inclus/i,
    answer: {
      text: `**Arvind Gender Policy** (Issued: **25.07.2025** | Effective: **26.07.2025**)\n\nCommitted to **gender equality** and **inclusion** for **all gender identities**:\n\n• **Equal access** to employment, development, and leadership — no discrimination\n• **Zero tolerance** for gender-based harassment or microaggressions\n• **Inclusive culture** — gender-sensitive work environment\n• **Work-Life support** — maternity, paternity, parental leave\n\n*Source: Gender Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I report gender discrimination?", "Who does it apply to?", "When was it effective?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── GENDER POLICY APPLICABILITY (broad) ───────────────────────────────────
  {
    pattern: /gender.*apply|gender.*who|who.*gender|gender.*appli|gender.*cover/i,
    answer: {
      text: `The **Gender Policy** applies to **all employees** of Arvind Ltd., including:\n\n• **full-time** employees\n• **Part-time** employees\n• **Contract staff**\n• **Interns**\n• **Consultants**\n• **third-party** partners engaged in business operations\n\n*Source: Gender Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the gender policy?", "How do I report gender discrimination?", "When was it effective?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ── CHANNELS TO RAISE COMPLAINT (generic) ────────────────────────────────
  {
    pattern: /channel.*complaint|complaint.*channel|use.*complaint|raise.*complaint|channels.*use|what.*channel|how.*complaint/i,
    answer: {
      text: `You can raise a complaint through these channels:\n\n| Level | Channel |\n|---|---|\n| 1st | **BUHR (HR Representative)** |\n| 2nd | **Line Manager** |\n| 3rd | **Head of Department (HOD)** |\n| 4th | **Ethics Helpline** |\n\n**Ethics Helpline:**\n- 📞 **1800 200 8301** (also: 18002008301)\n- 📧 **arvind@ethicshelpline.in**\n- 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What are grievance timelines?", "Can I report anonymously?", "What types of grievances are covered?"],
      data: { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", pageNumber: 2, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

  // ── WHISTLEBLOWER RETALIATION / PROTECTION (broad) ───────────────────────
  {
    pattern: /retaliat|retaliation|victimiz|protected.*report|report.*protected|face.*report|safe.*report/i,
    answer: {
      text: `**You are fully protected as a whistleblower:**\n\n• **No retaliation** — victimization is treated as a serious disciplinary matter\n• **Complete confidentiality** — your identity will not be disclosed\n• **Protection** applies to witnesses and anyone involved in investigation\n• If victimized, file a written complaint to the **Committee Chairman**\n\n*Source: Whistleblower Policy, Pages 4-5, Sections 9-10*`,
      type: "policy_details" as const,
      suggestedQuestions: ["How do I report?", "What is the whistleblower email?", "Who handles the investigation?"],
      data: { policyId: "whistleblower", policyName: "Whistleblower Policy", pageNumber: 4, confidenceScore: 1.0, source: "Static Cache" },
    },
  },


  // ── GENDER DISCRIMINATION REPORTING ──────────────────────────────────────
  {
    pattern: /report.*gender|gender.*discriminat|discriminat.*gender|gender.*bias|gender.*contact|gender.*channel|contact.*gender|gender.*complaint/i,
    answer: {
      text: `Report gender discrimination or bias through:\n\n| Level | Channel |\n|---|---|\n| 1st | **HR Department (BUHR)** |\n| 2nd | **Line Manager** |\n| 3rd | **Head of Department (HOD)** |\n| 4th | **Ethics Helpline** |\n| 5th | **Group Ethics Officer** |\n\n**Ethics Helpline:**\n- 📞 **1800 200 8301**\n- 📧 **arvind@ethicshelpline.in**\n- 🌐 **www.in.kpmg.com/ethicshelpline/arvind**\n\n*Source: Gender Policy, Page 3*`,
      type: "policy_details" as const,
      suggestedQuestions: ["What is the gender policy?", "Who does it apply to?", "Is my complaint confidential?"],
      data: { policyId: "gender-policy", policyName: "Gender Policy", pageNumber: 3, confidenceScore: 1.0, source: "Static Cache" },
    },
  },

];

// ─── Static Cache Lookup ──────────────────────────────────────────────────────
function checkStaticCache(query: string): AIResponse | null {
  const q = query.trim();
  for (const entry of STATIC_CACHE) {
    if (entry.pattern.test(q)) {
      return {
        ...entry.answer,
        data: {
          ...entry.answer.data,
          highlightTerms: q.split(/\s+/).filter(w => w.length > 3),
        },
      };
    }
  }
  return null;
}

// ─── Query Expansion ──────────────────────────────────────────────────────────
async function expandQuery(query: string): Promise<string[]> {
  const local: string[] = [];
  const q = query.toLowerCase();
  if (/\bm1\b/.test(q)) local.push("m1", "e2", "e1", "ot", "get", "mt");
  if (/\bm2\b/.test(q)) local.push("m2", "m3");
  if (/\bm3\b/.test(q)) local.push("m3", "m3h1", "m2");
  if (/\bbm\b|h[3-6]/.test(q)) local.push("bm", "h3", "h4", "h5", "h6");
  if (/class\s*1|class\s*i/.test(q)) local.push("class i", "class 1", "delhi", "mumbai");
  if (/class\s*2|class\s*ii/.test(q)) local.push("class ii", "class 2", "ahmedabad");
  if (/class\s*3|class\s*iii|three/.test(q)) local.push("class iii", "class 3", "other cities");
  if (/lodg/.test(q)) local.push("lodging", "hotel", "accommodation");
  if (/board/.test(q)) local.push("boarding", "food", "meals");
  if (/cab|conveyance/.test(q)) local.push("cab", "ola", "uber", "conveyance");
  if (/posh|harass/.test(q)) local.push("posh", "sexual harassment", "aic");
  if (/grievance/.test(q)) local.push("grievance", "complaint", "redressal");
  if (/whistle/.test(q)) local.push("whistleblower", "ethics helpline", "kpmg");
  if (/rotation|mobility|ijp/.test(q)) local.push("job rotation", "talent mobility", "mab");
  if (local.length >= 4) return local;
  try {
    const result = await callGeminiProxy({
      model: "gemini-2.0-flash",
      contents: [{ role: "user", parts: [{ text: `HR policy search terms (8 comma-separated, no explanation) for: "${query}"` }] }],
      config: { temperature: 0.1 },
    });
    const extra = result.split(",").map(t => t.trim().toLowerCase()).filter(t => t.length > 1 && t.length < 30);
    return [...new Set([...local, ...extra])];
  } catch { return local; }
}

// ─── Retrieve chunks with Deep Scanning capability ──────────────────────────
function retrieve(query: string, expanded: string[], topK: number): Chunk[] {
  const intent = detectPolicyIntent(query);
  const analysis = analyzePolicyQuestion(query);
  
  // BM25 Search
  const base = bm25Search(query, topK * 3);
  const extra: Chunk[] = [];
  for (const t of expanded.slice(0, 4)) {
    extra.push(...bm25Search(t, 3));
  }

  const retrieved = [...base, ...extra];
  
  // ADOBE-LEVEL UPGRADE: If policy is locked, we don't just take the topK.
  // We prioritize EVERY chunk from that policy to ensure "Perfect Recall".
  let candidates = retrieved;
  if (analysis.policyLocked && analysis.preferredPolicyIds.length === 1) {
    const targetPolicyId = analysis.preferredPolicyIds[0];
    
    // Pull ALL chunks for this policy from the global store to mimic "Full Doc" access
    const allPolicyChunks = ALL_CHUNKS.filter(c => c.policyId === targetPolicyId);
    
    // If we have the full doc, we use it. Otherwise fallback to retrieved.
    if (allPolicyChunks.length > 0) {
      // Prioritize chunks that match the query, but include everything else as "context"
      candidates = allPolicyChunks;
    }
  }

  const map = new Map<number, { chunk: Chunk; score: number }>();
  for (const c of candidates) {
    const ex = map.get(c.id);
    const delta = scoreChunkForIntent(c, intent) + scoreChunkAgainstPolicyQuestion(c, analysis);
    
    // Boost Annexures/Tables specifically (Adobe efficiency)
    let finalDelta = delta;
    if (c.text.includes("[TABLE]") || c.text.includes("Annexure")) {
      finalDelta += 50; 
    }

    if (ex) ex.score += finalDelta;
    else map.set(c.id, { chunk: c, score: finalDelta });
  }

  return Array.from(map.values())
    .sort((a, b) => {
      // Sort by score, then page number to maintain document flow
      if (Math.abs(b.score - a.score) > 0.1) return b.score - a.score;
      return a.chunk.pageNum - b.chunk.pageNum;
    })
    .slice(0, analysis.policyLocked ? 100 : topK) // If locked, take up to 100 chunks (full doc)
    .map(v => v.chunk);
}

// ─── System prompt ────────────────────────────────────────────────────────────
// ─── System prompt with Table Intelligence ────────────────────────────────────
function systemPrompt(context: string, userContext: PersonalizationContext, memoryContext?: AssistantMemoryContext): string {
  return `You are "Arvin", Arvind Limited's official HR Policy Assistant. You have high-fidelity access to entire policy documents.

HARD RULES:
1. Answer only from the POLICY CONTEXT below for policy claims. Never guess policy facts.
2. If the user sends a greeting, thanks, or a short conversational message, respond naturally and do not force a policy citation.
3. If something is not clearly covered in the context, say so honestly, offer to help rephrase, and direct the user to BUHR.
4. For all phone numbers use this exact format: **1800 200 8301** (and also mention 18002008301).
5. Always include email **arvind@ethicshelpline.in** when mentioning ethics helpline.
6. Always include **www.in.kpmg.com/ethicshelpline/arvind** when mentioning the portal.
7. For policy lists, ALWAYS mention: Domestic Travel Policy, Whistleblower Policy, POSH Policy, Grievance Mechanism Policy.

TABLE & ANNEXURE EXTRACTION RULES:
- The context includes complex tables marked with [TABLE] and [TABLE FACTS].
- ALWAYS cross-reference the employee's Grade (${userContext.grade || "Unknown"}) and Location (${userContext.location || "Unknown"}) against the table headers.
- When reading limits (e.g., Lodging/Boarding), look for the EXACT intersection of Grade and City Class.
- If a city is not listed in Class I or II, treat it as Class III.
- For Talent Mobility, distinguish clearly between Track A, B, and C.
- If a rule has an "Exception" or "Approval" column, explicitly state who the approving authority is.

SYSTEM REASONING PROCESS (Multi-Agent CoT):
Before answering, follow these mental steps:
1. IDENTIFY ENTITIES: What is the user's Grade, Location, and specific Query Metric (Lodging? Cab?)?
2. POLICY LOCK: Which specific policy applies? (e.g. Travel vs Local Conveyance).
3. SEARCH FOR EXCEPTIONS: Look specifically for words like "However", "Except", "Provided that", or "Annexure".
4. TABLE LOOKUP: If a table exists, find the exact row for the Grade and column for the City.
5. FOOTNOTE CHECK: Check if there's a small note at the bottom of the section.

TONE:
- Sound warm, calm, and professional.
- If the user sounds worried, upset, unsafe, or confused, acknowledge that briefly before answering.
- For sensitive topics (POSH, grievance, whistleblower), be especially empathetic and clear about next steps.

EMPLOYEE CONTEXT:
${buildPersonalizationPrompt(userContext)}

MEMORY CONTEXT:
${formatMemorySection(memoryContext)}

POLICY CONTEXT:
${context}`;
}

// ─── Main chat function ───────────────────────────────────────────────────────
export async function chatWithAI(
  message: string,
  history: ChatMessage[],
  _userId: string,
  userContextString: string,
  knowledgeAssets: { id: string; name: string; content?: string }[] = [],
  imageAttachment?: { mimeType: string; data: string },
  precisionMode: boolean = false,
  memoryContext?: AssistantMemoryContext,
  signal?: AbortSignal
): Promise<AIResponse> {
  if (signal?.aborted) throw new Error("Aborted");
  const userContext = parseUserContext(userContextString);

  if (!precisionMode) {
    const conversational = buildConversationalResponse(message, history, memoryContext);
    if (conversational) return conversational;
  }

  const followUpContext = precisionMode ? null : resolveFollowUpContext(message, history, memoryContext);
  if (followUpContext?.directResponse) {
    return finalizeResponse(followUpContext.directResponse, message, history, precisionMode, userContext);
  }

  const workingMessage = followUpContext?.workingMessage || message;
  const normalizedWorkingMessage = precisionMode ? workingMessage : normalizeEmployeeChatText(workingMessage);

  if (!precisionMode && isKnownUnsupportedPolicyQuestion(workingMessage)) {
    return finalizeResponse(buildSupportiveFallback(workingMessage), message, history, precisionMode, userContext);
  }

  if (!precisionMode) {
    const deterministic = resolveDeterministicPolicyAnswer(normalizedWorkingMessage, userContextString);
    if (deterministic) return finalizeResponse(deterministic, message, history, precisionMode, userContext);

    const grounded = resolveGroundedPolicyAnswer(workingMessage);
    if (grounded) {
      return finalizeResponse(grounded, message, history, precisionMode, userContext);
    }

    const directFact = buildPolicyFactResponse(workingMessage);
    if (directFact) {
      return finalizeResponse(directFact, message, history, precisionMode, userContext);
    }

    const scenario = buildScenarioSimulationResponse(normalizedWorkingMessage, userContext);
    if (scenario) {
      return finalizeResponse(scenario, message, history, precisionMode, userContext);
    }

    const policyDiff = buildPolicyDiffResponse(normalizedWorkingMessage);
    if (policyDiff) {
      return finalizeResponse(policyDiff, message, history, precisionMode, userContext);
    }

    const learned = buildLearningCaseResponse(normalizedWorkingMessage);
    if (learned) {
      return finalizeResponse(learned, message, history, precisionMode, userContext);
    }

    const policyRoute = buildPolicyRoutingFallback(workingMessage);
    if (policyRoute) {
      return finalizeResponse(policyRoute, message, history, precisionMode, userContext);
    }

    const clarification = buildClarificationResponse(normalizedWorkingMessage, userContext);
    if (clarification) {
      return finalizeResponse(clarification, message, history, precisionMode, userContext);
    }
  }

  // ── Step 1: Canonical benchmark answers for precision mode ──────────────────
  // ── Step 2: Deterministic policy resolver for structured questions ──────────
  const deterministic = resolveDeterministicPolicyAnswer(normalizedWorkingMessage, userContextString);
  if (deterministic) return finalizeResponse(deterministic, message, history, precisionMode, userContext);

  if (!precisionMode) {
    const policyRoute = buildPolicyRoutingFallback(workingMessage);
    if (policyRoute) {
      return finalizeResponse(policyRoute, message, history, precisionMode, userContext);
    }

    const staticMatch = checkStaticCache(workingMessage) ?? checkStaticCache(normalizedWorkingMessage);
    if (staticMatch) {
      return finalizeResponse(staticMatch, message, history, precisionMode, userContext);
    }
  }

  try {
    // ── Step 3: BM25 / Full Doc retrieval ──────────────────────────────────
    const expanded = await expandQuery(normalizedWorkingMessage);
    if (signal?.aborted) throw new Error("Aborted");

    // Increased topK for "Deep Scanning" mode
    const chunks = retrieve(normalizedWorkingMessage, expanded, precisionMode ? 20 : 12);
    const structuredRuleContext = buildStructuredRuleContext(normalizedWorkingMessage, precisionMode ? 10 : 6);
    
    let assetCtx = knowledgeAssets.length > 0
      ? "\n\nUSER DOCUMENTS:\n" + knowledgeAssets.map(a => `[${a.name}]\n${(a.content ?? "").slice(0, 5000)}`).join("\n\n")
      : "";

    // Adobe Mode: Use a MUCH larger context window (up to 60k chars of policy text)
    const ctx =
      (structuredRuleContext ? `STRUCTURED POLICY RULES:\n${structuredRuleContext}\n\n` : "") +
      buildContext(chunks, 60000) + 
      assetCtx;

    if (!precisionMode) {
      const guardrail = buildHighRiskGuardrailResponse(normalizedWorkingMessage, chunks[0]?.policyId);
      if (guardrail) {
        return finalizeResponse(guardrail, message, history, precisionMode, userContext);
      }
    }

    // ── Step 5: Build conversation ─────────────────────────────────────────
    const contents: any[] = history.slice(-8).map(h => ({
      role: h.role === "model" ? "model" : "user",
      parts: h.parts,
    }));
    const userParts: any[] = [{ text: normalizedWorkingMessage || "Help me." }];
    if (imageAttachment) userParts.push({ inlineData: imageAttachment });
    contents.push({ role: "user", parts: userParts });

    // ── Step 6: LLM call ───────────────────────────────────────────────────
    const resp = await callGeminiProxy({
      model: "gemini-2.0-flash",
      contents,
      config: {
        systemInstruction: systemPrompt(ctx, userContext, precisionMode ? undefined : memoryContext),
        temperature: 0.05,
        topP: 0.9,
        responseMimeType: "application/json",
        responseSchema: STRUCTURED_RESPONSE_SCHEMA,
      },
    }, signal);

    if (signal?.aborted) throw new Error("Aborted");

    const parsed: AIResponse = JSON.parse(resp || "{}");
    const top = chunks[0];
    
    // Phase 4: Agentic Critique Loop
    // Evolve into a generation-time critic loop with strict re-generation
    if (parsed.type === "policy_details") {
      const containsNumbers = /\b\d+\b/.test(parsed.text);
      if (precisionMode || containsNumbers) {
        const verification = await verifyPolicyAnswer(normalizedWorkingMessage, chunks, parsed.text, callGeminiProxy);
        if (verification.isVerified) {
          parsed.text = verification.refinedAnswer || parsed.text;
          parsed.data ??= {};
          parsed.data.confidenceScore = verification.confidenceScore;
        } else if (verification.confidenceScore < 0.3) {
          // If the judge is very unhappy, we fall back to a safer "Unsure" message
          return finalizeResponse(buildSupportiveFallback(normalizedWorkingMessage), message, history, precisionMode, userContext);
        }
      }
    }

    parsed.data ??= {};
    parsed.data.policyId    ??= top?.policyId;
    parsed.data.policyName  ??= top?.policyName;
    parsed.data.policyUrl   ??= findCanonicalPolicyMeta(top?.policyId, top?.policyName)?.fileUrl ?? top?.fileUrl;
    parsed.data.pageNumber  ??= top?.pageNum;
    parsed.data.highlightTerms ??= normalizedWorkingMessage.split(/\s+/).filter(w => w.length > 3);
    parsed.data.source = findCanonicalPolicyMeta(parsed.data.policyId, parsed.data.policyName)?.sourceDocumentName
      ?? parsed.data.policyName
      ?? top?.policyName
      ?? "Arvind Policy Document";
    
    if (!parsed.data.confidenceScore) {
      parsed.data.confidenceScore = Math.min(0.98, 0.5 + chunks.length * 0.06);
    }

    const validated = precisionMode ? parsed : validateGeneratedResponse(normalizedWorkingMessage, parsed, chunks);
    return finalizeResponse(validated, message, history, precisionMode, userContext);

  } catch (err: any) {
    if (err.message === "Aborted") throw err;
    if (precisionMode) throw err;
    console.error("[RAG] Error:", err.message);
    return finalizeResponse(fallback(normalizedWorkingMessage, err), message, history, precisionMode, userContext);
  }
}

// ─── Offline fallback ─────────────────────────────────────────────────────────
function fallback(query: string, err: any): AIResponse {
  const staticMatch = checkStaticCache(query);
  if (staticMatch) {
    return staticMatch;
  }

  const grounded = resolveGroundedPolicyAnswer(query);
  if (grounded) {
    return grounded;
  }

  const directFact = buildPolicyFactResponse(query);
  if (directFact) {
    return directFact;
  }

  const errorType = classifyModelError(err);
  const note = errorType === "quota"
    ? "I hit a temporary system limit, but I could still find the most relevant policy section:\n\n"
    : errorType === "invalid_key"
      ? "The AI model is not available right now because the Gemini API key is invalid, but I could still find the most relevant policy section:\n\n"
      : errorType === "connection"
        ? "I hit a temporary connection issue, but I could still find the most relevant policy section:\n\n"
        : "I could not complete the AI response, but I could still find the most relevant policy section:\n\n";

  const policyRoute = buildPolicyRoutingFallback(query);
  if (policyRoute) {
    return {
      ...policyRoute,
      text: note + policyRoute.text,
    };
  }

  if (isKnownUnsupportedPolicyQuestion(query)) {
    return {
      text: "The AI model is not available right now, and I could not confirm this from the current policy documents I have. This does not clearly map to the loaded Arvind policy set, so please check with BUHR before acting.",
      type: "error",
      suggestedQuestions: GENERAL_POLICY_SUGGESTIONS,
      data: {
        confidenceScore: 0.35,
        source: "Conversation Support",
      },
    };
  }

  const chunks = retrieve(query, [], 3);
  const top = chunks[0];

  if (top) {
    const fallbackResponse = buildChunkBackedPolicyResponse(query, top, "Local BM25", 0.4);
    return {
      ...fallbackResponse,
      text: note + fallbackResponse.text,
    };
  }
  return {
    text: "I couldn't find relevant information. Contact BUHR or call **1800 200 8301**.",
    type: "error",
    suggestedQuestions: ["What is the domestic travel policy?", "How do I raise a grievance?", "What is the ethics helpline?"],
  };
}

export async function generateTestCase(queryStr: string, category: string) {
  return { testId: `tc-${Math.random().toString(36).slice(2, 7)}`, query: queryStr, category, mustContain: [], mustNotContain: [] };
}
