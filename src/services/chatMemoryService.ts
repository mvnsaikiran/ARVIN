import { POLICY_META } from "../data/policies";
import type { EmployeeProfile, SupportedLanguage } from "./employeeExperienceService";
import { normalizeEmployeeChatText } from "./queryNormalization";

export interface MemoryMessage {
  role: "user" | "model";
  content: string;
  metadata?: {
    policyId?: string;
    policyName?: string;
    keyPoints?: string[];
    action?: {
      type?: string;
    };
  } | null;
  timestamp?: number;
}

export interface MemoryOpenEntities {
  grade?: string;
  location?: string;
  travelClass?: string;
  workflow?: string;
  caseType?: string;
}

export interface SessionMemorySnapshot {
  conversationSummary: string;
  activeTopic: string;
  activePolicyId?: string;
  activePolicyName?: string;
  openEntities: MemoryOpenEntities;
  recentFacts: string[];
}

export interface LongTermMemoryRecord {
  id: string;
  kind: "chat_summary" | "workflow" | "case" | "preference";
  title: string;
  summary: string;
  tags: string[];
  confidence: number;
  timestamp: number;
  sourceChatId?: string;
}

export interface AssistantMemoryContext {
  session: SessionMemorySnapshot;
  longTerm: {
    durableFacts: string[];
    relevantMemories: LongTermMemoryRecord[];
  };
}

interface UserMemoryStore {
  languagePreference?: SupportedLanguage;
  lastActivePolicyId?: string;
  lastActivePolicyName?: string;
  topicCounts: Record<string, number>;
  workflowCounts: Record<string, number>;
  memories: LongTermMemoryRecord[];
  updatedAt: number;
}

interface BuildMemoryContextOptions {
  userUid: string;
  chatId?: string | null;
  messages: MemoryMessage[];
  query: string;
}

interface PersistConversationMemoryOptions {
  userUid: string;
  chatId: string;
  messages: MemoryMessage[];
  profile: EmployeeProfile;
  language: SupportedLanguage;
}

const MEMORY_KEY_PREFIX = "hr_memory_";
const MAX_MEMORY_RECORDS = 24;
const MAX_RELEVANT_MEMORIES = 3;

const POLICY_ALIASES: Array<{ policyId: string; policyName: string; aliases: string[] }> = [
  { policyId: "domestic-travel", policyName: "Domestic Travel Policy", aliases: ["domestic travel policy", "travel policy", "domestic travel"] },
  { policyId: "local-conveyance", policyName: "Local Conveyance Policy", aliases: ["local conveyance policy", "local conveyance"] },
  { policyId: "posh-policy", policyName: "POSH Policy", aliases: ["posh policy", "posh", "sexual harassment policy"] },
  { policyId: "grievance-mechanism", policyName: "Grievance Mechanism Policy", aliases: ["grievance mechanism policy", "grievance policy", "grievance"] },
  { policyId: "gender-policy", policyName: "Gender Policy", aliases: ["gender policy"] },
  { policyId: "whistleblower", policyName: "Whistleblower Policy", aliases: ["whistleblower policy", "whistleblower", "ethics policy"] },
  { policyId: "talent-mobility", policyName: "Talent Mobility Policy", aliases: ["talent mobility policy", "talent mobility", "mobility policy"] },
  { policyId: "joining-policy", policyName: "Joining Policy", aliases: ["joining policy", "joining expense", "joining expenses", "joining claim", "brokerage reimbursement"] },
];

const TOPIC_PATTERNS: Array<{ topic: string; tags: string[]; pattern: RegExp }> = [
  { topic: "Domestic Travel", tags: ["travel", "hotel", "boarding", "lodging"], pattern: /\b(travel|lodging|boarding|hotel|flight|train|fare)\b/ },
  { topic: "Local Conveyance", tags: ["conveyance", "cab", "taxi", "uber", "ola"], pattern: /\b(local conveyance|conveyance|cab|taxi|uber|ola|metro)\b/ },
  { topic: "Leave and Attendance", tags: ["leave", "attendance", "punch", "shift"], pattern: /\b(leave|attendance|punch|regularize|missing punch|shift)\b/ },
  { topic: "Payroll", tags: ["payroll", "salary", "tax", "pf", "pt", "payslip"], pattern: /\b(payroll|salary|net pay|gross pay|payslip|deduction|tax|pf|pt)\b/ },
  { topic: "Benefits", tags: ["benefits", "insurance", "medical", "bonus"], pattern: /\b(benefits|insurance|medical|bonus|enrollment|retirement)\b/ },
  { topic: "Joining", tags: ["joining", "brokerage", "claim"], pattern: /\b(joining|brokerage|joining expense|join date|claim deadline)\b/ },
  { topic: "Talent Mobility", tags: ["mobility", "relocation", "transfer"], pattern: /\b(mobility|relocation|transfer|moving city)\b/ },
  { topic: "Grievance", tags: ["grievance", "retaliation", "complaint"], pattern: /\b(grievance|retaliation|complaint|escalation)\b/ },
  { topic: "POSH", tags: ["posh", "harassment", "safety"], pattern: /\b(posh|harassment|sexual harassment|unsafe)\b/ },
  { topic: "Whistleblower", tags: ["whistleblower", "ethics", "anonymous"], pattern: /\b(whistleblower|ethics helpline|anonymous report)\b/ },
  { topic: "Gender Policy", tags: ["gender", "inclusion"], pattern: /\b(gender policy|gender inclusion|gender)\b/ },
  { topic: "Recruiting", tags: ["candidate", "interview", "job description"], pattern: /\b(candidate|interview|recruiting|job description|jd)\b/ },
];

const LOCATION_PATTERN = /\b(ahmedabad|bangalore|bengaluru|delhi|ncr|mumbai|pune|hyderabad|chennai|kolkata|surat|jaipur|indore|vadodara|rajkot)\b/i;
const GRADE_PATTERN = /\b(bmh9|bmh8|bmh7|bm-h7|director|bmh6|bmh5|bmh4|bmh3|bm-h3|m3h1|m3-h1|m3|m2|m1|mt|e2|e1|ot)\b/i;
const CLASS_PATTERN = /\bclass\s*(iii|ii|i|3|2|1|three|two|one)\b/i;

function hasBrowserStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function getStorageKey(userUid: string) {
  return `${MEMORY_KEY_PREFIX}${userUid}`;
}

function defaultStore(): UserMemoryStore {
  return {
    topicCounts: {},
    workflowCounts: {},
    memories: [],
    updatedAt: Date.now(),
  };
}

function loadUserMemoryStore(userUid: string): UserMemoryStore {
  if (!hasBrowserStorage()) {
    return defaultStore();
  }

  try {
    const raw = window.localStorage.getItem(getStorageKey(userUid));
    if (!raw) {
      return defaultStore();
    }

    const parsed = JSON.parse(raw) as Partial<UserMemoryStore>;
    return {
      languagePreference: parsed.languagePreference,
      lastActivePolicyId: parsed.lastActivePolicyId,
      lastActivePolicyName: parsed.lastActivePolicyName,
      topicCounts: parsed.topicCounts ?? {},
      workflowCounts: parsed.workflowCounts ?? {},
      memories: parsed.memories ?? [],
      updatedAt: parsed.updatedAt ?? Date.now(),
    };
  } catch {
    return defaultStore();
  }
}

function saveUserMemoryStore(userUid: string, store: UserMemoryStore) {
  if (!hasBrowserStorage()) {
    return;
  }

  try {
    window.localStorage.setItem(getStorageKey(userUid), JSON.stringify(store));
  } catch {
    // Ignore quota/storage errors and keep chat usable.
  }
}

function uniqueStrings(values: string[]) {
  return [...new Set(values.filter(Boolean))];
}

function normalizeGrade(rawGrade: string) {
  const normalized = rawGrade.trim().toLowerCase();
  if (normalized === "director") return "Director";
  return normalized.toUpperCase().replace("-", "");
}

function normalizeClass(rawClass: string) {
  const normalized = rawClass.trim().toLowerCase();
  if (normalized === "i" || normalized === "1" || normalized === "one") return "Class I";
  if (normalized === "ii" || normalized === "2" || normalized === "two") return "Class II";
  return "Class III";
}

function capitalizeWord(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function inferPolicyFromText(text: string) {
  const normalized = normalizeEmployeeChatText(text);

  const aliasMatch = POLICY_ALIASES.find((candidate) =>
    candidate.aliases.some((alias) => normalized.includes(alias))
  );

  if (aliasMatch) {
    return { policyId: aliasMatch.policyId, policyName: aliasMatch.policyName };
  }

  const policyMeta = POLICY_META.find((policy) => normalized.includes(policy.name.toLowerCase()));
  if (!policyMeta) {
    return null;
  }

  return { policyId: policyMeta.id, policyName: policyMeta.name };
}

function inferTopicFromMessages(messages: MemoryMessage[]) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const text = normalizeEmployeeChatText(messages[index]?.content ?? "");
    const match = TOPIC_PATTERNS.find((candidate) => candidate.pattern.test(text));
    if (match) {
      return match.topic;
    }
  }

  return "General HR Policy";
}

function inferWorkflow(messages: MemoryMessage[]) {
  const combined = normalizeEmployeeChatText(messages.map((message) => message.content).join(" "));

  if (/\b(apply leave|leave request)\b/.test(combined)) return "leave_request";
  if (/\b(missing punch|attendance regularization|regularize)\b/.test(combined)) return "attendance_regularization";
  if (/\b(payroll correction|salary issue|deduction issue)\b/.test(combined)) return "payroll_correction";
  if (/\b(grievance case|raise grievance|grievance)\b/.test(combined)) return "grievance_case";
  if (/\b(posh complaint|posh)\b/.test(combined)) return "posh_case";
  if (/\b(reimbursement|claim deadline|expense claim)\b/.test(combined)) return "reimbursement_claim";
  if (/\b(update my dependent|data change|update employee data)\b/.test(combined)) return "data_change";
  if (/\b(schedule interview|candidate screening|job description)\b/.test(combined)) return "recruiting_workflow";

  return undefined;
}

function inferCaseType(messages: MemoryMessage[]) {
  const combined = normalizeEmployeeChatText(messages.map((message) => message.content).join(" "));

  if (combined.includes("grievance")) return "grievance";
  if (combined.includes("posh")) return "posh";
  if (combined.includes("whistleblower")) return "whistleblower";
  if (combined.includes("payroll")) return "payroll";
  return undefined;
}

function extractOpenEntities(messages: MemoryMessage[]): MemoryOpenEntities {
  const joined = messages
    .slice(-8)
    .map((message) => message.content)
    .join(" ");

  const gradeMatch = joined.match(GRADE_PATTERN);
  const locationMatch = joined.match(LOCATION_PATTERN);
  const classMatch = joined.match(CLASS_PATTERN);
  const workflow = inferWorkflow(messages);
  const caseType = inferCaseType(messages);

  return {
    grade: gradeMatch ? normalizeGrade(gradeMatch[1]) : undefined,
    location: locationMatch ? capitalizeWord(locationMatch[1] === "bengaluru" ? "bangalore" : locationMatch[1]) : undefined,
    travelClass: classMatch ? normalizeClass(classMatch[1]) : undefined,
    workflow,
    caseType,
  };
}

function collectRecentFacts(messages: MemoryMessage[]) {
  const modelMessages = messages.filter((message) => message.role === "model").slice(-2);
  const facts: string[] = [];

  for (const message of modelMessages) {
    if (message.metadata?.keyPoints?.length) {
      facts.push(...message.metadata.keyPoints.slice(0, 3));
      continue;
    }

    const firstSentence = message.content
      .replace(/\s+/g, " ")
      .split(/(?<=[.!?])\s+/)[0]
      ?.trim();

    if (firstSentence) {
      facts.push(firstSentence.slice(0, 180));
    }
  }

  return uniqueStrings(facts).slice(0, 4);
}

function buildConversationSummary(messages: MemoryMessage[], topic: string, policyName: string | undefined, openEntities: MemoryOpenEntities, recentFacts: string[]) {
  const lastUserMessage = [...messages].reverse().find((message) => message.role === "user" && message.content.trim());
  const summaryParts = [
    policyName ? `Current focus is ${policyName}.` : `Current focus is ${topic}.`,
    lastUserMessage ? `Latest employee ask: "${lastUserMessage.content.trim().slice(0, 160)}".` : "",
    openEntities.grade ? `Grade in context: ${openEntities.grade}.` : "",
    openEntities.location ? `Location in context: ${openEntities.location}.` : "",
    openEntities.workflow ? `Open workflow: ${openEntities.workflow.replace(/_/g, " ")}.` : "",
    recentFacts[0] ? `Recent answer highlight: ${recentFacts[0]}.` : "",
  ].filter(Boolean);

  return summaryParts.join(" ");
}

function buildSessionMemorySnapshot(messages: MemoryMessage[]): SessionMemorySnapshot {
  const latestPolicyFromMetadata = [...messages]
    .reverse()
    .find((message) => message.metadata?.policyId || message.metadata?.policyName);
  const inferredPolicy = latestPolicyFromMetadata?.metadata?.policyId
    ? {
        policyId: latestPolicyFromMetadata.metadata.policyId,
        policyName: latestPolicyFromMetadata.metadata.policyName,
      }
    : inferPolicyFromText(messages.map((message) => message.content).join(" "));

  const activeTopic = inferTopicFromMessages(messages);
  const openEntities = extractOpenEntities(messages);
  const recentFacts = collectRecentFacts(messages);

  return {
    conversationSummary: buildConversationSummary(messages, activeTopic, inferredPolicy?.policyName, openEntities, recentFacts),
    activeTopic,
    activePolicyId: inferredPolicy?.policyId,
    activePolicyName: inferredPolicy?.policyName,
    openEntities,
    recentFacts,
  };
}

function upsertMemoryRecord(records: LongTermMemoryRecord[], nextRecord: LongTermMemoryRecord) {
  const filtered = records.filter((record) => record.id !== nextRecord.id);
  filtered.unshift(nextRecord);
  return filtered
    .sort((left, right) => right.timestamp - left.timestamp)
    .slice(0, MAX_MEMORY_RECORDS);
}

function topEntries(record: Record<string, number>, limit: number) {
  return Object.entries(record)
    .sort((left, right) => right[1] - left[1])
    .slice(0, limit)
    .map(([key]) => key);
}

function scoreMemoryRecord(record: LongTermMemoryRecord, query: string, session: SessionMemorySnapshot) {
  const normalizedQuery = normalizeEmployeeChatText(query);
  const queryTerms = normalizedQuery.split(/\s+/).filter((term) => term.length > 2);
  let score = 0;

  for (const term of queryTerms) {
    if (record.summary.toLowerCase().includes(term)) score += 3;
    if (record.title.toLowerCase().includes(term)) score += 2;
    if (record.tags.some((tag) => tag.includes(term))) score += 2;
  }

  if (session.activePolicyId && record.tags.includes(session.activePolicyId)) score += 6;
  if (session.activeTopic && record.tags.includes(session.activeTopic.toLowerCase())) score += 4;
  if (session.openEntities.workflow && record.tags.includes(session.openEntities.workflow)) score += 4;

  const ageHours = Math.max(1, (Date.now() - record.timestamp) / 36e5);
  score += record.confidence * 4;
  score += Math.max(0, 6 - ageHours / 12);
  return score;
}

export function buildAssistantMemoryContext({
  userUid,
  chatId,
  messages,
  query,
}: BuildMemoryContextOptions): AssistantMemoryContext {
  const session = buildSessionMemorySnapshot(messages);
  const store = loadUserMemoryStore(userUid);

  const relevantMemories = store.memories
    .filter((record) => record.sourceChatId !== chatId)
    .map((record) => ({ record, score: scoreMemoryRecord(record, query, session) }))
    .filter((entry) => entry.score > 5)
    .sort((left, right) => right.score - left.score)
    .slice(0, MAX_RELEVANT_MEMORIES)
    .map((entry) => entry.record);

  const durableFacts = uniqueStrings([
    store.languagePreference ? `Saved language preference: ${store.languagePreference}.` : "",
    store.lastActivePolicyName ? `Most recent policy discussed across chats: ${store.lastActivePolicyName}.` : "",
    topEntries(store.topicCounts, 2).length > 0
      ? `Repeated HR topics from earlier chats: ${topEntries(store.topicCounts, 2).join(", ")}.`
      : "",
    topEntries(store.workflowCounts, 2).length > 0
      ? `Repeated workflow patterns: ${topEntries(store.workflowCounts, 2).map((entry) => entry.replace(/_/g, " ")).join(", ")}.`
      : "",
  ]);

  return {
    session,
    longTerm: {
      durableFacts,
      relevantMemories,
    },
  };
}

export function persistConversationMemory({
  userUid,
  chatId,
  messages,
  profile,
  language,
}: PersistConversationMemoryOptions) {
  const session = buildSessionMemorySnapshot(messages);
  const store = loadUserMemoryStore(userUid);

  store.languagePreference = language;
  if (session.activePolicyId) store.lastActivePolicyId = session.activePolicyId;
  if (session.activePolicyName) store.lastActivePolicyName = session.activePolicyName;
  store.topicCounts[session.activeTopic] = (store.topicCounts[session.activeTopic] ?? 0) + 1;
  if (session.openEntities.workflow) {
    store.workflowCounts[session.openEntities.workflow] = (store.workflowCounts[session.openEntities.workflow] ?? 0) + 1;
  }

  const baseTags = uniqueStrings([
    session.activeTopic.toLowerCase(),
    session.activePolicyId ?? "",
    session.openEntities.workflow ?? "",
    session.openEntities.caseType ?? "",
    profile.grade.toLowerCase(),
    profile.location.toLowerCase(),
  ]);

  store.memories = upsertMemoryRecord(store.memories, {
    id: `chat:${chatId}`,
    kind: "chat_summary",
    title: session.activePolicyName ?? session.activeTopic,
    summary: session.conversationSummary,
    tags: baseTags,
    confidence: 0.84,
    timestamp: Date.now(),
    sourceChatId: chatId,
  });

  if (session.openEntities.workflow || session.openEntities.caseType) {
    store.memories = upsertMemoryRecord(store.memories, {
      id: `workflow:${chatId}`,
      kind: session.openEntities.caseType ? "case" : "workflow",
      title: session.openEntities.caseType
        ? `${capitalizeWord(session.openEntities.caseType)} continuity`
        : `${session.openEntities.workflow?.replace(/_/g, " ")} continuity`,
      summary: session.conversationSummary,
      tags: uniqueStrings([
        ...baseTags,
        session.openEntities.workflow ?? "",
        session.openEntities.caseType ?? "",
      ]),
      confidence: 0.88,
      timestamp: Date.now(),
      sourceChatId: chatId,
    });
  }

  store.memories = upsertMemoryRecord(store.memories, {
    id: "preference:baseline",
    kind: "preference",
    title: `${profile.displayName} baseline`,
    summary: `Employee context usually seen in chats: role ${profile.role}, grade ${profile.grade}, location ${profile.location}, language ${language}.`,
    tags: uniqueStrings([profile.role, profile.grade.toLowerCase(), profile.location.toLowerCase(), language]),
    confidence: 0.95,
    timestamp: Date.now(),
  });

  store.updatedAt = Date.now();
  saveUserMemoryStore(userUid, store);
}
