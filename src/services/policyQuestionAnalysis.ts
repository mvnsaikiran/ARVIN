import { normalizeEmployeeChatText } from "./queryNormalization";

export type PolicyQuestionType =
  | "generic"
  | "classification"
  | "metadata"
  | "applicability"
  | "timeline"
  | "reporting_route"
  | "anonymity"
  | "confidentiality"
  | "retaliation"
  | "delay_rule"
  | "same_day_exception"
  | "recovery"
  | "relocation_transport"
  | "reimbursement_rate"
  | "women_entitlement"
  | "approval_path";

export interface PolicyQuestionAnalysis {
  normalizedQuery: string;
  explicitPolicyIds: string[];
  preferredPolicyIds: string[];
  answerType: PolicyQuestionType;
  requiredTerms: string[];
  highlightTerms: string[];
  numericTerms: string[];
  policyLocked: boolean;
  asksSpecificClause: boolean;
  mentionsEmployeePersonalization: boolean;
}

const POLICY_ALIASES: Array<{ policyId: string; name: string; aliases: string[] }> = [
  {
    policyId: "domestic-travel",
    name: "domestic travel policy",
    aliases: ["domestic travel", "travel policy", "mybiz", "flight delay", "same-day return"],
  },
  {
    policyId: "local-conveyance",
    name: "local conveyance policy",
    aliases: ["local conveyance", "conveyance policy", "two-wheeler", "four-wheeler", "bike reimbursement"],
  },
  {
    policyId: "joining-policy",
    name: "joining policy",
    aliases: [
      "joining expenses",
      "joining expense",
      "joining reimbursement",
      "joining bonus",
      "notice pay buyout",
      "brokerage",
      "f&f settlement",
      "full & final settlement",
      "relocation expense",
      "packers",
      "household goods",
    ],
  },
  {
    policyId: "gender-policy",
    name: "gender policy",
    aliases: ["gender discrimination", "gender harassment"],
  },
  {
    policyId: "grievance-mechanism",
    name: "grievance mechanism policy",
    aliases: ["grievance policy", "grievance redressal", "grievance"],
  },
  {
    policyId: "posh-policy",
    name: "posh policy",
    aliases: ["posh", "sexual harassment", "sexual harassment policy", "aic", "internal committee"],
  },
  {
    policyId: "whistleblower",
    name: "whistleblower policy",
    aliases: ["whistleblower", "ethics helpline", "unethical practice", "vigil mechanism", "fraud reporting"],
  },
  {
    policyId: "talent-mobility",
    name: "talent mobility policy",
    aliases: ["talent mobility", "mobility policy", "rotation policy", "ijp", "transfer", "deputation"],
  },
  {
    policyId: "eap",
    name: "employee assistance program",
    aliases: [
      "eap", "1to1", "1to1help", "employee assistance", "counselling", "counseling",
      "mental health", "stress support", "wellbeing", "wellness", "psychological support",
    ],
  },
  {
    policyId: "group-health-insurance",
    name: "group health insurance",
    aliases: ["health insurance", "mediclaim", "hospitalisation", "hospitalization", "cashless claim", "fhpl", "ghi"],
  },
  {
    policyId: "group-personal-accident",
    name: "group personal accident insurance",
    aliases: ["personal accident insurance", "accident insurance", "disability insurance", "gpa"],
  },
  {
    policyId: "group-term-life",
    name: "group term life insurance",
    aliases: ["term life insurance", "life insurance arvind", "death benefit", "gtl", "gti"],
  },
  {
    policyId: "pankh-referral",
    name: "pankh employee referral",
    aliases: ["pankh", "employee referral", "refer a candidate", "referral reward", "referral bonus"],
  },
  {
    policyId: "expense-reimbursement",
    name: "employee expense reimbursement",
    aliases: ["expense reimbursement", "birthday expense", "farewell expense", "late night food reimbursement"],
  },
  {
    policyId: "exit-fnf",
    name: "exit and full final settlement",
    aliases: ["full and final", "fnf settlement", "relieving letter", "experience letter", "resignation process"],
  },
  {
    policyId: "medibuddy",
    name: "medibuddy health wellness",
    aliases: ["medibuddy", "online doctor consultation", "video consultation doctor"],
  },
  {
    policyId: "voluntary-death-contribution",
    name: "voluntary death contribution scheme",
    aliases: ["death contribution", "voluntary death contribution", "vdcs"],
  },
  {
    policyId: "travel-settlement",
    name: "domestic travel expense settlement procedure",
    aliases: ["travel settlement", "settlement procedure", "tour expense", "settle tour", "expense settlement", "my tour dashboard", "create tour expense"],
  },
];

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "any",
  "are",
  "as",
  "at",
  "be",
  "by",
  "can",
  "do",
  "does",
  "for",
  "from",
  "get",
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
  "our",
  "please",
  "tell",
  "that",
  "the",
  "their",
  "there",
  "this",
  "to",
  "under",
  "what",
  "when",
  "where",
  "which",
  "who",
  "will",
  "with",
  "within",
  "would",
  "your",
]);

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function collectExplicitPolicyIds(normalizedQuery: string) {
  const formalNamesFound = POLICY_ALIASES
    .filter((entry) => normalizedQuery.includes(entry.name))
    .map((entry) => entry.policyId);
  
  if (formalNamesFound.length > 0) {
    return unique(formalNamesFound);
  }

  return unique(
    POLICY_ALIASES
      .filter((entry) => entry.aliases.some((alias) => normalizedQuery.includes(alias)))
      .map((entry) => entry.policyId),
  );
}

function inferPolicyIds(normalizedQuery: string, answerType: PolicyQuestionType) {
  const ids: string[] = [];

  if (
    /\bposh\b|\bsexual harassment\b|\bsexually harass(?:ing|ed)?\b|\bharass(?:ing|ment)\b.*\bsexual(?:ly)?\b|\bsexual(?:ly)?\b.*\bharass(?:ing|ment)\b|\bworkplace harassment\b|\baic\b|\binternal committee\b/.test(
      normalizedQuery,
    )
  ) {
    ids.push("posh-policy");
  }
  if (/\bgender\b|\bdiscrimination\b|\bequality\b|\bequity\b|\bdiversity\b|\binclusion\b/.test(normalizedQuery)) {
    ids.push("gender-policy");
  }
  if (/\bwhistleblower\b|\bunethical\b|\bethics helpline\b|\bwrongdoing\b|\bfraud\b|\bbribery\b/.test(normalizedQuery)) {
    ids.push("whistleblower");
  }
  if (/\bgrievance\b|\bcomplaint\b|\bheard\b|\bfairness\b|\bheard\b/.test(normalizedQuery)) {
    ids.push("grievance-mechanism");
  }
  if (
    /\bjoining\b|\bbrokerage\b|\bnotice pay\b|\bf&f\b|\bpackers?\b|\bmovers?\b|\bhousehold goods\b|\bonboarding\b|\brelocat/.test(normalizedQuery) &&
    !/\bmab\b|\bsia\b|\bsettling[- ]in\b|\bone[- ]time\b/.test(normalizedQuery)
  ) {
    ids.push("joining-policy");
  }
  if (
    /\b(bmh9|bmh8|bmh7|bmh6|bmh5|bmh4|bmh3|m3h1|m3|m2|m1|mt|e2|get|e1|ot)\b/.test(normalizedQuery) &&
    /\bcab\b|\bconveyance entitlement\b|\bwhich cab\b|\bwhat cab\b|\bola\b|\buber\b|\bblusmart\b/.test(normalizedQuery)
  ) {
    ids.push("domestic-travel");
  }
  if (
    /\bconveyance\b|\btwo-wheeler\b|\bfour-wheeler\b|\bbike\b|\bscooter\b|\bper km\b/.test(normalizedQuery) ||
    (/\blocal\b/.test(normalizedQuery) && /\btravel\b|\bofficial\b|\btaxi\b|\bcab\b|\bfare\b|\bclaim\b|\breimbursement\b/.test(normalizedQuery)) ||
    (/\btaxi\b|\bcab\b|\bfare\b|\bsame vehicle\b|\bshared vehicle\b|\bshare\b/.test(normalizedQuery) && /\bclaim\b|\breimbursement\b|\breimbursed\b|\bpaid\b|\bpay\b|\bcost\b|\bfare\b/.test(normalizedQuery))
  ) {
    ids.push("local-conveyance");
  }
  if (
    (/\btravel\b/.test(normalizedQuery) && !/\blocal travel\b/.test(normalizedQuery)) ||
    /\bbusiness trip\b|\bofficial trip\b|\bmybiz\b|\bflight\b|\bhotel\b|\bstay\b|\blodging\b|\bboarding\b|\bfood\b|\bmeals?\b|\blaundry\b|\balcohol\b|\bnon[- ]?reimbursable\b|\bsame-day return\b|\bentitlements?\b|\bentitelments?\b/.test(normalizedQuery)
  ) {
    ids.push("domestic-travel");
  }
  if (/\bmobility\b|\brotation\b|\bijp\b|\bmab\b|\bsia\b|\bsettling[- ]in\b/.test(normalizedQuery)) {
    ids.push("talent-mobility");
  }
  if (/\beap\b|\bstress(?:ed|ful)?\b|\bcounsel(?:l?ing)?\b|\bmental health\b|\bwellbeing\b|\bwellness\b|\bemotional support\b|\banxi(?:ous|ety)\b|\bburnout\b|\boverwhel|\b1to1\b/.test(normalizedQuery)) {
    ids.push("eap");
  }
  if (/\bhealth insurance\b|\bmediclaim\b|\bhospitali(?:s|z)ation\b|\bcashless\b|\bfhpl\b|\bghi\b/.test(normalizedQuery)) {
    ids.push("group-health-insurance");
  }
  if (/\bpersonal accident\b|\baccident insurance\b|\bdisability insurance\b|\bgpa\b/.test(normalizedQuery)) {
    ids.push("group-personal-accident");
  }
  if (/\bterm life\b|\blife insurance\b|\bdeath benefit\b|\bgtl\b|\bgti\b/.test(normalizedQuery)) {
    ids.push("group-term-life");
  }
  if (/\bpankh\b|\breferral reward\b|\breferral bonus\b|\brefer.*candidate\b|\bemployee referral\b/.test(normalizedQuery)) {
    ids.push("pankh-referral");
  }
  if (/\bfull.*final\b|\bfull & final\b|\bfnf\b|\brelieving letter\b|\bresignation process\b|\bexperience letter\b/.test(normalizedQuery)) {
    ids.push("exit-fnf");
  }
  if (/\bmedibuddy\b|\bonline doctor\b|\bvideo consult\b/.test(normalizedQuery)) {
    ids.push("medibuddy");
  }
  if (/\bdeath contribution\b|\bvdcs\b|\bvoluntary death\b/.test(normalizedQuery)) {
    ids.push("voluntary-death-contribution");
  }
  if (/\btravel settlement\b|\btour expense\b|\bsettle.*tour\b|\bmy tour dashboard\b|\bcreate tour expense\b/.test(normalizedQuery)) {
    ids.push("travel-settlement");
  }

  // Fallback based on specific answer types
  if (ids.length === 0) {
    switch (answerType) {
      case "timeline":
        ids.push("grievance-mechanism");
        break;
      case "delay_rule":
      case "same_day_exception":
      case "women_entitlement":
        ids.push("domestic-travel");
        break;
      case "recovery":
      case "relocation_transport":
        ids.push("joining-policy");
        break;
      case "reimbursement_rate":
        ids.push("local-conveyance");
        break;
    }
  }

  return unique(ids);
}

function detectAnswerType(normalizedQuery: string): PolicyQuestionType {
  if (/\bcity classification\b|\bwhich city class\b|\bwhat class is\b|\bclass .* for travel\b|\bclassified as\b/.test(normalizedQuery)) {
    return "classification";
  }

  if (/\beffective date\b|\beffective from\b|\bissue date\b|\bpolicy number\b/.test(normalizedQuery)) {
    return "metadata";
  }

  if (/\bwho does it apply to\b|\bwho is covered\b|\bapplies to\b|\bapplicable to\b|\bapplicability\b|\bscope\b/.test(normalizedQuery)) {
    return "applicability";
  }

  if (/\bnext reporting level\b|\bafter buhr\b|\breporting level\b|\breporting route\b|\bescalation route\b|\bwhich level after\b/.test(normalizedQuery)) {
    return "reporting_route";
  }

  if (/\banonymous\b/.test(normalizedQuery)) {
    return "anonymity";
  }

  if (/\bconfidential\b|\bconfidentiality\b|\bidentity\b|\bsecrecy\b/.test(normalizedQuery)) {
    return "confidentiality";
  }

  if (/\bretaliation\b|\bvictimization\b|\badverse personnel action\b|\bprotected from\b/.test(normalizedQuery)) {
    return "retaliation";
  }

  if (/\backnowledg|\binvestigation\b|\bresolution\b|\bworking days\b|\boutcome\b/.test(normalizedQuery)) {
    return "timeline";
  }

  if (/\bdelay(?:ed)?\b.*\b3 hours\b|\b3 hours\b.*\bdelay(?:ed)?\b|\bcancel\b.*\bmybiz\b|\bmodify\b.*\bmybiz\b/.test(normalizedQuery)) {
    return "delay_rule";
  }

  if (/\bsame[- ]day return\b|\bfreshening up\b|\bguest[- ]house\b.*\bsame day\b|\bguest house\b.*\bsame day\b|\bhotel\b.*\bsame day\b/.test(normalizedQuery)) {
    return "same_day_exception";
  }

  if (/\bquits within 1 year\b|\bwithin one year\b|\bresigns within one year\b|\bresigns within 1 year\b|\bf&f settlement\b|\bfinal settlement\b|\brecovered\b|\brecovery applies\b/.test(normalizedQuery)) {
    return "recovery";
  }

  if (/\bhousehold goods\b|\bpackers\b|\bbelow 700\b|\bless than 700\b|\bmore than 700\b|\b50 per km\b|\b60 per km\b/.test(normalizedQuery)) {
    return "relocation_transport";
  }

  if (
    /\bbike\b|\btwo-wheeler\b|\bfour-wheeler\b|\bper km\b|\breimbursement calculated\b/.test(normalizedQuery) ||
    (/\btaxi\b|\bcab\b|\bfare\b|\bsame vehicle\b|\bshared vehicle\b|\bshare\b/.test(normalizedQuery) && /\bclaim\b|\breimbursement\b|\breimbursed\b|\bpaid\b|\bpay\b|\bcost\b|\bfare\b/.test(normalizedQuery))
  ) {
    return "reimbursement_rate";
  }

  if (/\b(woman|women)\b.*\b(next higher grade|hotel entitlement|book.*hotel)\b|\b(woman|women)\s+employee\b/.test(normalizedQuery)) {
    return "women_entitlement";
  }

  if (/timeline|how long|within.*days|acknowledg|investigation|resolution|period/.test(normalizedQuery)) return "timeline";
  if (/approval|authority|who approves|who can|authorize|workflow|route|head of|chro|ceo/.test(normalizedQuery)) return "approval_path";
  if (/reporting|channel|route|contact/.test(normalizedQuery)) return "reporting_route";
  if (/entitlement|entitelment|allowance|limit|boarding|lodging|hotel|stay|food|meals/.test(normalizedQuery)) return "generic"; // Will be refined by grounding scoring

  return "generic";
}

function buildRequiredTerms(normalizedQuery: string, answerType: PolicyQuestionType) {
  const baseTerms: string[] = [];

  switch (answerType) {
    case "classification":
      baseTerms.push("classified", "class", "city");
      break;
    case "timeline":
      if (/\backnowledg/.test(normalizedQuery)) baseTerms.push("acknowledged", "working days");
      if (/\binvestigation\b/.test(normalizedQuery)) baseTerms.push("investigation", "working days");
      if (/\bresolution\b|\boutcome\b/.test(normalizedQuery)) baseTerms.push("outcome", "working days");
      break;
    case "reporting_route":
      baseTerms.push("first level", "second level", "third level", "fourth level", "buhr", "line manager", "hod");
      break;
    case "anonymity":
      baseTerms.push("anonymous", "investigation", "sufficient information", "reasonably clear and specific", "verifiable evidence");
      break;
    case "confidentiality":
      baseTerms.push("confidential", "identity");
      break;
    case "retaliation":
      baseTerms.push("retaliation", "victimization", "protected");
      break;
    case "delay_rule":
      baseTerms.push("delayed", "3 hours", "mybiz", "cancel", "modify");
      break;
    case "same_day_exception":
      baseTerms.push("same day", "freshening up", "guest house", "service apartment", "hotel accommodation");
      break;
    case "recovery":
      baseTerms.push("quits within 1 year", "full final settlement", "full & final settlement", "joining bonus", "relocation expense", "brokerage");
      break;
    case "relocation_transport":
      baseTerms.push("household goods", "packers", "700", "50 per km", "60 per km", "actuals whichever is lesser");
      break;
    case "reimbursement_rate":
      baseTerms.push("two-wheeler", "four-wheeler", "per km", "reimbursement");
      break;
    case "women_entitlement":
      baseTerms.push("women employees", "next higher grade", "hotel");
      break;
    case "approval_path":
      baseTerms.push("approval", "reporting manager", "bm grade");
      break;
    default:
      break;
  }

  if (normalizedQuery.includes("after buhr")) {
    baseTerms.push("buhr", "line manager");
  }

  return unique(baseTerms);
}

function buildHighlightTerms(normalizedQuery: string) {
  return unique(
    normalizedQuery
      .split(/\s+/)
      .map((token) => token.replace(/[^a-z0-9/-]/g, ""))
      .filter((token) => {
        if (token.length >= 3) return !STOPWORDS.has(token) || /^(kitna|batao|milega|dikhao|maru|meri|mera|kahan|kaise|kise|contact|helpline)$/.test(token);
        // Protect grades and city numbers
        return /^(m1|m2|m3|e1|e2|ot|mt|h4|h5|h6|h7|h8|h9|1|2|3)$/.test(token);
      }),
  );
}

function buildNumericTerms(normalizedQuery: string) {
  const matches: string[] = normalizedQuery.match(/\b\d+\b/g) ?? [];
  if (/\bone year\b/.test(normalizedQuery)) matches.push("1");
  if (/\bthree hours\b/.test(normalizedQuery)) matches.push("3");
  if (/\b700 kms?\b/.test(normalizedQuery)) matches.push("700");
  return unique(matches);
}

export function analyzePolicyQuestion(rawQuery: string): PolicyQuestionAnalysis {
  const normalizedQuery = normalizeEmployeeChatText(rawQuery)
    .replace(/[?!.:,()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const answerType = detectAnswerType(normalizedQuery);
  const explicitPolicyIds = collectExplicitPolicyIds(normalizedQuery);
  const preferredPolicyIds = unique([...explicitPolicyIds, ...inferPolicyIds(normalizedQuery, answerType)]);
  const mentionsEmployeePersonalization = /\bmy\b|\bfor me\b|\bmy grade\b|\bmy location\b|\bmy profile\b/.test(normalizedQuery);
  const policyLocked =
    explicitPolicyIds.length === 1 ||
    (preferredPolicyIds.length === 1 && /\bunder the\b|\baccording to\b|\bas per\b|\busing only the\b|\bfrom the\b|\bonly the\b/.test(normalizedQuery));
  const asksSpecificClause =
    answerType !== "generic" ||
    /\bnext\b|\bafter\b|\bwithin\b|\bmore than\b|\bless than\b|\bbelow\b|\babove\b|\ballowed\b|\bnot eligible\b|\brecovered\b|\bcalculated\b|\bhow (to|do)\b|\bwhat is\b|\bprocess\b|\brule\b|\bentitlement\b|\blimit\b/.test(normalizedQuery);

  return {
    normalizedQuery,
    explicitPolicyIds,
    preferredPolicyIds,
    answerType,
    requiredTerms: buildRequiredTerms(normalizedQuery, answerType),
    highlightTerms: buildHighlightTerms(normalizedQuery),
    numericTerms: buildNumericTerms(normalizedQuery),
    policyLocked,
    asksSpecificClause,
    mentionsEmployeePersonalization,
  };
}

export function shouldPreferPolicyGrounding(rawQuery: string) {
  const analysis = analyzePolicyQuestion(rawQuery);

  if (analysis.policyLocked) {
    return true;
  }

  if (analysis.mentionsEmployeePersonalization && analysis.answerType === "generic") {
    return false;
  }

  return analysis.asksSpecificClause && analysis.preferredPolicyIds.length > 0;
}

import { GoogleGenAI } from "@google/genai";

let _ai: GoogleGenAI | null = null;
function getGenAIClient(): GoogleGenAI {
  if (!_ai) {
    const key =
      (typeof process !== "undefined" && (process.env?.GEMINI_API_KEY || "")) ||
      ((import.meta as any)?.env?.VITE_GEMINI_API_KEY ?? "") ||
      ((import.meta as any)?.env?.GEMINI_API_KEY ?? "");
    _ai = new GoogleGenAI({ apiKey: key });
  }
  return _ai;
}

export const ROUTER_RESPONSE_SCHEMA = {
  type: "OBJECT",
  properties: {
    explicitPolicyIds: {
      type: "ARRAY",
      items: { type: "STRING" }
    },
    preferredPolicyIds: {
      type: "ARRAY",
      items: { type: "STRING" }
    },
    answerType: {
      type: "STRING",
      enum: [
        "generic", "classification", "metadata", "applicability", "timeline",
        "reporting_route", "anonymity", "confidentiality", "retaliation",
        "delay_rule", "same_day_exception", "recovery", "relocation_transport",
        "reimbursement_rate", "women_entitlement", "approval_path"
      ]
    },
    requiredTerms: {
      type: "ARRAY",
      items: { type: "STRING" }
    },
    highlightTerms: {
      type: "ARRAY",
      items: { type: "STRING" }
    },
    numericTerms: {
      type: "ARRAY",
      items: { type: "STRING" }
    },
    policyLocked: { type: "BOOLEAN" },
    asksSpecificClause: { type: "BOOLEAN" },
    mentionsEmployeePersonalization: { type: "BOOLEAN" }
  },
  required: [
    "explicitPolicyIds",
    "preferredPolicyIds",
    "answerType",
    "requiredTerms",
    "highlightTerms",
    "numericTerms",
    "policyLocked",
    "asksSpecificClause",
    "mentionsEmployeePersonalization"
  ]
} as const;

export async function analyzePolicyQuestionLLM(rawQuery: string): Promise<PolicyQuestionAnalysis> {
  const fallbackResult = analyzePolicyQuestion(rawQuery);
  try {
    const key =
      (typeof process !== "undefined" && (process.env?.GEMINI_API_KEY || "")) ||
      ((import.meta as any)?.env?.VITE_GEMINI_API_KEY ?? "") ||
      ((import.meta as any)?.env?.GEMINI_API_KEY ?? "");
    if (!key) {
      return fallbackResult;
    }

    const client = getGenAIClient();
    const prompt = `You are a high-fidelity HR Policy Intent Parser.
Analyze the user's HR query and structure the result as JSON matching the provided schema.

Employee Query: "${rawQuery}"

Rules:
- explicitPolicyIds: Policy IDs explicitly mentioned (e.g., "domestic-travel", "local-conveyance", "joining-policy", "gender-policy", "posh-policy", "whistleblower", "talent-mobility", "grievance-mechanism").
- preferredPolicyIds: Policy IDs that this query is likely asking about.
- answerType: one of the enum values describing the core intent.
- requiredTerms, highlightTerms, numericTerms: keywords and numbers to focus on for retrieval.
- policyLocked: true if the query is strictly bound to a single policy.
- asksSpecificClause: true if it asks for a specific rule, amount, limit, or process.
- mentionsEmployeePersonalization: true if it refers to "my grade", "my location", "my allowance", "for me", etc.`;

    const contentResp = await client.models.generateContent({
      model: "gemini-2.0-flash",
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      config: {
        temperature: 0.0,
        responseMimeType: "application/json",
        responseSchema: ROUTER_RESPONSE_SCHEMA as any,
      },
    });

    const text = contentResp.text ?? "";
    if (!text.trim()) return fallbackResult;
    const parsed = JSON.parse(text);
    return {
      normalizedQuery: fallbackResult.normalizedQuery,
      ...parsed
    };
  } catch (err) {
    console.warn("LLM Router failed or timed out, falling back to regex parser:", err);
    return fallbackResult;
  }
}
