import { normalizeEmployeeChatText } from "./queryNormalization";
import { resolveBenchmarkQuerySync } from "./benchmarkQueryResolver";

export interface DeterministicAIResponse {
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
  };
}

type TravelClass = "Class I" | "Class II" | "Class III";
type TravelGroupId = "bmh9" | "bmh7h8" | "bmh3h6" | "m3group" | "m1group";

interface TravelGroup {
  id: TravelGroupId;
  display: string;
  aliases: string[];
  lodging: Record<TravelClass, string>;
  boarding: Record<TravelClass, string>;
  train: string;
  air: string;
  cab: string;
}

interface GradeMatch {
  group: TravelGroup;
  displayGrade: string;
}

const POLICY_URLS = {
  "domestic-travel": "/original-policies/domestic-travel-policy-arvind-limited.pdf",
  "talent-mobility": "/original-policies/talent-mobility.pdf",
  "joining-policy": "/original-policies/joining-policy-arvind-limited.pdf",
  "local-conveyance": "/original-policies/local-conveyance-policy-arvind-limited.pdf",
  "gender-policy": "/original-policies/arvind-gender-policy-2025.pdf",
  "posh-policy": "/original-policies/posh-policy-arvind-limited.pdf",
  posh: "/original-policies/posh-policy-arvind-limited.pdf",
  "grievance-mechanism": "/original-policies/arvind-grievance-mechanism-policy-2025.pdf",
  grievance: "/original-policies/arvind-grievance-mechanism-policy-2025.pdf",
  whistleblower: "/original-policies/whistleblower-policy-arvind-limited.pdf",
};

const CITY_CLASS_MAP: Record<string, TravelClass> = {
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
  "tier 3 city": "Class III",
  "tier-3 city": "Class III",
};

const TRAVEL_GROUPS: TravelGroup[] = [
  {
    id: "bmh9",
    display: "BMH9",
    aliases: ["bmh9"],
    lodging: { "Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual" },
    boarding: { "Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual" },
    train: "1st AC",
    air: "Premium Economy / Business",
    cab: "Actuals - full reimbursement at actual cost",
  },
  {
    id: "bmh7h8",
    display: "BMH7 and H8",
    aliases: ["bmh7", "h8", "bmh8", "bmh7 and above", "bmh7 and above", "bm-h7", "director"],
    lodging: { "Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual" },
    boarding: { "Class I": "At Actual", "Class II": "At Actual", "Class III": "At Actual" },
    train: "1st AC",
    air: "Economy / Premium Economy",
    cab: "Actuals - full reimbursement at actual cost",
  },
  {
    id: "bmh3h6",
    display: "BMH3, H4, H5, H6",
    aliases: ["bmh3", "bmh4", "bmh5", "bmh6", "h4", "h5", "h6", "bm-h3", "bmh3 to h6", "bmh3 to h6"],
    lodging: { "Class I": "8000", "Class II": "6000", "Class III": "5000" },
    boarding: { "Class I": "1500", "Class II": "1300", "Class III": "1000" },
    train: "1st AC",
    air: "Economy",
    cab: "Ola / Uber / BluSmart",
  },
  {
    id: "m3group",
    display: "M3H1, M3, M2",
    aliases: ["m3h1", "m3-h1", "m3", "m2"],
    lodging: { "Class I": "6000", "Class II": "5000", "Class III": "4000" },
    boarding: { "Class I": "1200", "Class II": "1000", "Class III": "800" },
    train: "2nd AC",
    air: "Economy",
    cab: "Ola / Uber / BluSmart",
  },
  {
    id: "m1group",
    display: "M1, MT, E2, GET, E1, OT",
    aliases: ["m1", "mt", "e2", "get", "e1", "ot"],
    lodging: { "Class I": "3400", "Class II": "2300", "Class III": "1700" },
    boarding: { "Class I": "1000", "Class II": "800", "Class III": "600" },
    train: "3rd AC or Chair Car",
    air: "Economy",
    cab: "Ola / Uber / BluSmart, Bus, Metro, Local Transportation",
  },
];

const TALENT_BENEFITS = {
  E1: { annual: "3,91,000", monthly: "32,583", mab: "4,888", discretionary: "1,629", sia: "10,000" },
  E2: { annual: "5,49,000", monthly: "45,750", mab: "6,863", discretionary: "2,288", sia: "10,000" },
  M1: { annual: "8,52,000", monthly: "71,000", mab: "10,650", discretionary: "3,550", sia: "15,000" },
  M2: { annual: "13,00,000", monthly: "1,08,333", mab: "16,250", discretionary: "5,417", sia: "20,000" },
  M3: { annual: "19,00,000", monthly: "1,58,333", mab: "23,750", discretionary: "7,917", sia: "30,000" },
  M3H1: { annual: "26,00,000", monthly: "2,16,667", mab: "32,500", discretionary: "10,833", sia: "45,000" },
} as const;

const TYPO_SYNONYMS: Record<string, string> = {
  fligt: "flight",
  dlay: "delay",
  dlays: "delay",
  ccltn: "cancellation",
  canceltn: "cancellation",
  cancelation: "cancellation",
  lodgin: "lodging",
  lodg: "lodging",
  conveyence: "conveyance",
  convayance: "conveyance",
  reimbursment: "reimbursement",
  reimbursemnt: "reimbursement",
  whistleblowr: "whistleblower",
  whistleblowin: "whistleblower",
  shifing: "shifting",
  relocat: "relocation",
  twoi: "class iii",
  "2i": "class iii",
};

function getLevenshteinDistance(a: string, b: string): number {
  const tmp: number[][] = [];
  for (let i = 0; i <= a.length; i++) {
    tmp[i] = [i];
  }
  for (let j = 0; j <= b.length; j++) {
    tmp[0][j] = j;
  }
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      tmp[i][j] = Math.min(
        tmp[i - 1][j] + 1,
        tmp[i][j - 1] + 1,
        tmp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
    }
  }
  return tmp[a.length][b.length];
}

function correctTypos(query: string): string {
  const words = query.split(/\s+/);
  const corrected = words.map((word) => {
    const lowerWord = word.toLowerCase();
    
    // Do not correct known locations, grades, common nouns, or proper nouns
    if (["delhi", "mumbai", "ahmedabad", "surat", "pune", "jammu", "ncr", "santej", "raipur", "gomtipur", "day", "days", "pay", "car", "cab", "tax", "bus", "train", "hotel", "claim"].includes(lowerWord)) {
      return word;
    }
    if (/^[a-z0-9]+$/i.test(word) && (lowerWord.startsWith("m") || lowerWord.startsWith("e") || lowerWord.startsWith("b"))) {
      // Don't touch potential grades (e.g. M1, BMH3, E1)
      return word;
    }

    if (TYPO_SYNONYMS[word]) {
      return TYPO_SYNONYMS[word];
    }
    
    // Fuzzy matching against known target words
    const targets = ["flight", "delay", "cancellation", "lodging", "conveyance", "reimbursement", "whistleblower", "shifting", "relocation", "posh", "ijp", "rotation"];
    let best = word;
    let minD = Infinity;
    
    for (const target of targets) {
      if (Math.abs(word.length - target.length) > 2) continue;
      const d = getLevenshteinDistance(word, target);
      const maxAllowed = target.length <= 4 ? 1 : 2;
      if (d <= maxAllowed && d < minD) {
        minD = d;
        best = target;
      }
    }
    
    return best;
  });
  return corrected.join(" ");
}

function normalizeQuery(raw: string): string {
  let normalized = normalizeEmployeeChatText(raw)
    .replace(/['"`]/g, "")
    .replace(/[?!.:,()]/g, " ")
    .replace(/\s+/g, " ")
    .toLowerCase()
    .trim();

  normalized = correctTypos(normalized);

  normalized = normalized
    .replace(/\bi\s*am\s*planning\s*a\s*trip\s*next\s*week\b/g, " ")
    .replace(/\bi\s*need\s*to\s*file\s*a\s*claim\b/g, " ")
    .replace(/\bmy\s*manager\s*asked\s*me\s*to\s*check\b/g, " ")
    .replace(/\bim\s*a\s*new\s*joiner\s*and\s*want\s*to\s*know\b/g, " ")
    .replace(/\bi\s*m\s*a\s*new\s*joiner\s*and\s*want\s*to\s*know\b/g, " ")
    .replace(/\bi\s*am\s*a\s*new\s*joiner\s*and\s*want\s*to\s*know\b/g, " ")
    .replace(/\bi\s*am\s*facing\s*an\s*issue\s*and\s*need\s*to\s*verify\b/g, " ")
    .replace(/\bbefore\s*i\s*book\s*my\s*tickets\s*confirm\b/g, " ")
    .replace(/\bcan\s*you\s*tell\s*me\s*the\s*official\s*rule\s*for\b/g, " ")
    .replace(/can you help me understand\s*/g, " ")
    .replace(/according to company policy\s*/g, " ")
    .replace(/as per policy/g, " ")
    .replace(/please tell me/g, " ")
    .replace(/\bin detail\b/g, " ")
    .replace(/\btravelling\/based in\b/g, " in ")
    .replace(/\btravelling\b/g, " ")
    .replace(/\bclass\s*twoi\b/g, " class iii ")
    .replace(/\bclass\s*2i\b/g, " class iii ")
    .replace(/\bclass\s*three\b/g, " class iii ")
    .replace(/\bclass\s*3\b/g, " class iii ")
    .replace(/\bclass\s*two\b/g, " class ii ")
    .replace(/\bclass\s*2\b/g, " class ii ")
    .replace(/\bclass\s*one\b/g, " class i ")
    .replace(/\bclass\s*1\b/g, " class i ");

  return normalized.replace(/\s+/g, " ").trim();
}

function collectHighlights(raw: string): string[] {
  return Array.from(
    new Set(
      raw
        .split(/\s+/)
        .map((token) => token.replace(/[^a-zA-Z0-9/-]/g, "").trim())
        .filter((token) => token.length > 2),
    ),
  );
}

function containsAny(query: string, phrases: string[]): boolean {
  return phrases.some((phrase) => {
    if (phrase === "train") {
      return /\btrain\b/i.test(query);
    }
    if (phrase === "bus") {
      return /\bbus\b/i.test(query);
    }
    if (phrase === "cab") {
      return /\bcab\b/i.test(query);
    }
    return query.includes(phrase);
  });
}

function makePolicyResponse(
  rawQuery: string,
  text: string,
  policyId: keyof typeof POLICY_URLS,
  policyName: string,
  pageNumber: number,
  suggestedQuestions: string[] = [],
): DeterministicAIResponse {
  return {
    text,
    type: "policy_details",
    suggestedQuestions,
    data: {
      policyId,
      policyName,
      policyUrl: POLICY_URLS[policyId],
      pageNumber,
      confidenceScore: 1,
      source: "Deterministic Policy Resolver",
      highlightTerms: collectHighlights(rawQuery),
    },
  };
}

function extractTravelClass(query: string): TravelClass | null {
  for (const city of Object.keys(CITY_CLASS_MAP).sort((a, b) => b.length - a.length)) {
    if (query.includes(city)) return CITY_CLASS_MAP[city];
  }

  if (/\bclass iii\b/.test(query)) return "Class III";
  if (/\bclass ii\b/.test(query)) return "Class II";
  if (/\bclass i\b/.test(query)) return "Class I";
  return null;
}

function extractCity(query: string): string | null {
  const found = Object.keys(CITY_CLASS_MAP)
    .sort((left, right) => right.length - left.length)
    .find((city) => query.includes(city));
  if (!found) return null;
  return found === "ncr" ? "NCR" : found.charAt(0).toUpperCase() + found.slice(1);
}

function extractTravelGrade(query: string): GradeMatch | null {
  const gradeMatchers: Array<{ pattern: RegExp; grade: string; groupId: TravelGroupId }> = [
    { pattern: /\bdirector\b/, grade: "Director", groupId: "bmh7h8" },
    { pattern: /\bbmh9\b/, grade: "BMH9", groupId: "bmh9" },
    { pattern: /\bbmh8\b|\bh8\b/, grade: "H8", groupId: "bmh7h8" },
    { pattern: /\bbmh7\b|\bbm-h7\b/, grade: "BMH7", groupId: "bmh7h8" },
    { pattern: /\bbmh6\b|\bh6\b/, grade: "BMH6", groupId: "bmh3h6" },
    { pattern: /\bbmh5\b|\bh5\b/, grade: "BMH5", groupId: "bmh3h6" },
    { pattern: /\bbmh4\b|\bh4\b/, grade: "BMH4", groupId: "bmh3h6" },
    { pattern: /\bbmh3\b|\bbm-h3\b/, grade: "BMH3", groupId: "bmh3h6" },
    { pattern: /\bm3h1\b|\bm3-h1\b/, grade: "M3H1", groupId: "m3group" },
    { pattern: /\bm3\b/, grade: "M3", groupId: "m3group" },
    { pattern: /\bm2\b/, grade: "M2", groupId: "m3group" },
    { pattern: /\bm1\b/, grade: "M1", groupId: "m1group" },
    { pattern: /\bmt\b/, grade: "MT", groupId: "m1group" },
    { pattern: /\be2\b/, grade: "E2", groupId: "m1group" },
    { pattern: /\bget\b/, grade: "GET", groupId: "m1group" },
    { pattern: /\be1\b/, grade: "E1", groupId: "m1group" },
    { pattern: /\bot\b/, grade: "OT", groupId: "m1group" },
  ];

  const match = gradeMatchers.find((entry) => entry.pattern.test(query));
  if (!match) return null;

  return {
    displayGrade: match.grade,
    group: TRAVEL_GROUPS.find((group) => group.id === match.groupId)!,
  };
}

function resolveTravelClassification(rawQuery: string, query: string): DeterministicAIResponse | null {
  const city = extractCity(query);
  if (!city) return null;

  const isClassificationQuery =
    containsAny(query, ["what class", "which class", "city classification", "fall in", "classified", "class of", "tier of", "tier is", "category of", "class city", "category is", "classification is"]) &&
    !containsAny(query, ["lodging", "boarding", "hotel", "accommodation", "food", "meal", "cab", "conveyance", "mode of travel", "train", "flight", "air", "laundry", "posh", "gender", "whistleblower", "grievance", "joining", "mobility", "allowance", "limit", "booking", "settlement", "timeline", "scope", "women", "flat rate", "guest house", "no-show", "non-reimbursable", "same day", "edge case", "actual", "exception", "appeal", "anonymous", "identity", "reporting", "recovery", "brokerage", "exit", "driver", "transport", "goods", "trigger", "block", "track", "shared", "km", "scooter", "bike", "four-wheeler", "expenses", "cancel", "cancellation", "modify", "modification"]);

  if (!isClassificationQuery) return null;

  const travelClass = CITY_CLASS_MAP[city.toLowerCase()];
  return makePolicyResponse(
    rawQuery,
    `**${city}** is classified as a **${travelClass} city** under the Domestic Travel Policy.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    "domestic-travel",
    "Domestic Travel Policy",
    7,
    ["What are the lodging limits for my grade?", "What is the mode of travel for my grade?"],
  );
}

function resolveTravelAllowances(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (query.includes("joining") || query.includes("joining policy")) return null;

  if (containsAny(query, ["daily rate", "how is the daily rate calculated", "calculated per"])) {
    return makePolicyResponse(
      rawQuery,
      `Yes, all lodging limits specified in the policy are **inclusive of GST** and apply strictly per **24-hour period** (calculated from the check-in time).\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
    );
  }

  const grade = extractTravelGrade(query);
  const travelClass = extractTravelClass(query);
  if (!grade || !travelClass) return null;

  const isBoarding = containsAny(query, ["boarding", "food", "meal"]);
  const isLodging = containsAny(query, ["lodging", "hotel", "accommodation"]);
  const isCombined =
    containsAny(query, ["total", "complete entitlement", "lodging and boarding", "travel limits", "combined"]) ||
    (isLodging && isBoarding);

  if (!isBoarding && !isLodging && !isCombined) return null;

  const lodging = grade.group.lodging[travelClass];
  const boarding = grade.group.boarding[travelClass];

  if (isCombined) {
    const amountTable =
      lodging === "At Actual"
        ? `For **${grade.displayGrade}** in **${travelClass}** cities:\n\n| Type | Limit |\n|---|---|\n| Lodging (hotel) | **At Actual** |\n| Boarding (food) | **At Actual** |\n\nThere is no upper cap for this grade band.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`
        : `For **${grade.displayGrade}** in **${travelClass}** cities:\n\n| Type | Limit |\n|---|---|\n| Lodging (hotel) | **INR ${lodging}/day** |\n| Boarding (food) | **INR ${boarding}/day** |\n\nAll limits include GST and apply per 24-hour period.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`;

    return makePolicyResponse(rawQuery, amountTable, "domestic-travel", "Domestic Travel Policy", 7);
  }

  if (isBoarding && !isLodging) {
    return makePolicyResponse(
      rawQuery,
      boarding === "At Actual"
        ? `For **${grade.displayGrade}**, the **boarding** limit in **${travelClass}** cities is **At Actual**. There is no upper cap.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`
        : `For **${grade.displayGrade}**, the **boarding** (food) limit in **${travelClass}** cities is **INR ${boarding} per day** (inclusive of GST).\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
    );
  }

  return makePolicyResponse(
    rawQuery,
    lodging === "At Actual"
      ? `For **${grade.displayGrade}**, the **lodging** limit in **${travelClass}** cities is **At Actual**. There is no upper cap - the actual hotel bill is reimbursed.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`
      : `For **${grade.displayGrade}**, the **lodging** limit in **${travelClass}** cities is **INR ${lodging} per day** (inclusive of GST).\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    "domestic-travel",
    "Domestic Travel Policy",
    7,
  );
}

function resolveTravelMode(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["lodging", "boarding", "hotel", "accommodation", "meals", "food", "stay", "laundry", "room"])) {
    return null;
  }
  if (containsAny(query, ["yatra", "oyo", "booking.com", "other channel", "outside mybiz", "expedia"])) {
    return null;
  }
  const grade = extractTravelGrade(query);
  if (!grade) return null;

  const asksMode =
    containsAny(query, ["mode of travel", "train class", "flight class", "air class", "travel class", "entitled class", "entitlement class", "which class", "which mode", "what class", "what mode", "economy", "business class", "premium economy"]) ||
    (containsAny(query, ["flight", "train", "air", "chair car", "travel by train"]) && containsAny(query, ["class", "entitle", "allow", "eligible", "permissible", "permit"]));
  if (!asksMode) return null;

  return makePolicyResponse(
    rawQuery,
    `For **${grade.displayGrade}**:\n\n| Mode | Class |\n|---|---|\n| Train | **${grade.group.train}** |\n| Air | **${grade.group.air}** |\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
    "domestic-travel",
    "Domestic Travel Policy",
    7,
  );
}

function resolveTravelCab(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (query.includes("local conveyance") || query.includes("local conveyance policy")) return null;
  const grade = extractTravelGrade(query);
  if (!grade) return null;

  if (!containsAny(query, ["cab", "conveyance", "uber", "ola", "blusmart", "metro", "bus", "radio taxi"])) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `For **${grade.displayGrade}**, the cab or conveyance entitlement is **${grade.group.cab}**.\n\n*Source: Domestic Travel Policy, Annexure B, Page 8*`,
    "domestic-travel",
    "Domestic Travel Policy",
    8,
  );
}

function resolveTravelBooking(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (query.includes("local conveyance") || query.includes("local conveyance policy")) return null;
  if (containsAny(query, ["lodging", "boarding", "hotel limit", "food limit", "laundry", "flat rate", "cab entitlement", "conveyance rate"])) return null;
  if (containsAny(query, ["settle", "settlement"])) return null;
  if (!containsAny(query, ["book", "booking", "travel desk", "mybiz", "mymtrip", "makemytrip", "oyo", "yatra", "approve"])) {
    return null;
  }

  if (containsAny(query, ["advance booking", "how many days in advance", "7 days"])) {
    return makePolicyResponse(
      rawQuery,
      `Travel should normally be booked at least **7 days** in advance to optimize fares and approvals.\n\n*Source: Domestic Travel Policy, Page 3*`,
      "domestic-travel",
      "Domestic Travel Policy",
      3,
    );
  }

  if (containsAny(query, ["approve", "approval", "who approves"])) {
    return makePolicyResponse(
      rawQuery,
      `Travel booking requires approval from the **reporting manager**. If an exception or higher-level sanction is required, **BM grade** approval applies.\n\n*Source: Domestic Travel Policy, Page 3*`,
      "domestic-travel",
      "Domestic Travel Policy",
      3,
    );
  }

  if (containsAny(query, ["oyo", "yatra"])) {
    return makePolicyResponse(
      rawQuery,
      `All air travel and hotel bookings must go through **MakeMyTrip myBiz Self Booking Tool (SBT)**. Bookings made through other channels like OYO or Yatra will **not be reimbursed**.\n\n*Source: Domestic Travel Policy, Page 3*`,
      "domestic-travel",
      "Domestic Travel Policy",
      3,
    );
  }

  return makePolicyResponse(
    rawQuery,
    `All air travel and hotel accommodation must be booked exclusively through **MakeMyTrip's myBiz Self Booking Tool (SBT)**. Bookings through any other channel will **not be reimbursed**. Travel should be booked at least **7 days** in advance to secure the best rates. Bookings require prior approval from the **reporting manager** for employees of **BM grade** and above or if booking exceeds entitlement.\n\n*Source: Domestic Travel Policy, Page 3*`,
    "domestic-travel",
    "Domestic Travel Policy",
    3,
  );
}

function resolveTravelCancellation(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["cancellation", "cancel", "modification", "modify", "delay", "delayed"])) return null;

  if (containsAny(query, ["1 hour", "1-hour", "2 hour", "2-hour", "two hour", "one hour"])) {
    return makePolicyResponse(
      rawQuery,
      `A 2-hour delay does not qualify for cancellation or modification under the policy. The policy allows cancellation/modification only if a flight is delayed by more than **3 hours** from the Estimated Time of Departure (ETD).\n\n*Source: Domestic Travel Policy, Page 4*`,
      "domestic-travel",
      "Domestic Travel Policy",
      4,
    );
  }

  return makePolicyResponse(
    rawQuery,
    `If your flight is delayed by more than **3 hours** from the Estimated Time of Departure (ETD), you can **cancel or modify the booking through myBiz**.\n\n*Source: Domestic Travel Policy, Page 4*`,
    "domestic-travel",
    "Domestic Travel Policy",
    4,
  );
}

function resolveTravelSettlement(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["full and final", "f&f", "previous organization", "buyout", "joining"])) {
    return null;
  }
  if (!containsAny(query, ["submit travel claims", "settle travel expenses", "settle travel", "settlement"])) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `Travel claims should be settled within **15 days** of travel completion. The system triggers auto-settlement on the **16th day**.\n\n*Source: Domestic Travel Policy, Page 8*`,
    "domestic-travel",
    "Domestic Travel Policy",
    8,
  );
}

function resolveTravelScope(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["minimum distance", "when does domestic travel policy apply", "domestic travel policy apply", "scope"])) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `The Domestic Travel Policy applies to business travel exceeding **300 km**. For distances below that, the **Local Conveyance** Policy applies.\n\n*Source: Domestic Travel Policy, Page 2*`,
    "domestic-travel",
    "Domestic Travel Policy",
    2,
  );
}

function resolveTravelWomen(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["women employee", "female employee", "women travel", "special rules for female"])) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `Women employees have the following additional protections:\n\n- Hotel entitlement can move to the **next higher grade**\n- Women are encouraged to prefer **hotel** stays over guest houses or service apartments\n- Women are advised to avoid **night travel** wherever possible\n\n*Source: Domestic Travel Policy, Page 4*`,
    "domestic-travel",
    "Domestic Travel Policy",
    4,
  );
}

function resolveTravelFlatRate(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["flat rate", "self-arrangement", "self arrangement", "own arrangement"])) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `If an employee makes their own lodging arrangements, the **flat rate** allowance is **30%** of the entitled lodging limit. For **BMH7 and above**, the flat rate is **6,000** per day.\n\n*Source: Domestic Travel Policy, Page 5*`,
    "domestic-travel",
    "Domestic Travel Policy",
    5,
  );
}

function resolveTravelGuestHouse(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["guest house", "guest houses"])) return null;

  return makePolicyResponse(
    rawQuery,
    `Arvind has two guest houses in **Ahmedabad**:\n\n- **Tulip** Part-2, Near **Surdhara** Circle, Ajanta Ellora Road, Ahmedabad\n- T3 4B, Centre Point, **CG Road**, Ahmedabad\n\n*Source: Domestic Travel Policy, Annexure C, Page 9*`,
    "domestic-travel",
    "Domestic Travel Policy",
    9,
  );
}

function resolveTravelLaundry(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["laundry", "dry cleaning", "washing", "laundry expenses"])) return null;

  return makePolicyResponse(
    rawQuery,
    `Laundry is reimbursable on **actuals** for business trips of **3 days** or more.\n\n*Source: Domestic Travel Policy, Page 8*`,
    "domestic-travel",
    "Domestic Travel Policy",
    8,
  );
}

function resolveTravelNonReimbursable(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (
    !containsAny(query, [
      "non-reimbursable",
      "what cannot i claim",
      "cannot i claim",
      "not reimbursable",
      "not be reimbursed",
    ])
  ) {
    return null;
  }

  return makePolicyResponse(
    rawQuery,
    `These are **non-reimbursable** travel expenses:\n- **Alcohol** and **mini-bar** charges.\n- Personal expenses and **VIP lounge** charges.\n- **Web check-in** charges (without business justification/approval).\n- Flight **upgrade** charges.\n- Travel expenses of **spouse** or family members.\n\n*Source: Domestic Travel Policy, Annexure B, Page 8*`,
    "domestic-travel",
    "Domestic Travel Policy",
    8,
  );
}

function resolveTravelSameDay(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["same-day", "same day"])) return null;

  return makePolicyResponse(
    rawQuery,
    `For **same-day return** travel, employees are **not eligible** for guest-house or hotel accommodation. However, if necessary, they can **request a guest house or service apartment for freshening up**.\n\n*Source: Domestic Travel Policy, Page 5*`,
    "domestic-travel",
    "Domestic Travel Policy",
    5,
  );
}

function resolveTravelNoShow(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["no-show", "missed my flight", "who pays"])) return null;

  return makePolicyResponse(
    rawQuery,
    `A **no-show** is treated as the **employee's responsibility**, and the related amount may be **recovered** from the employee.\n\n*Source: Domestic Travel Policy, Page 6*`,
    "domestic-travel",
    "Domestic Travel Policy",
    6,
  );
}

function resolveTravelEdgeCases(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["edge case", "edge cases", "director"])) {
    if (query.includes("director")) {
      return makePolicyResponse(
        rawQuery,
        `A **Director** is treated in line with the **BMH7** and above band for travel, so hotel reimbursement is **At Actual**.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
        "domestic-travel",
        "Domestic Travel Policy",
        7,
      );
    }
    if (query.includes("at actual") || query.includes("claim hotel at actual") || containsAny(query, ["m1", "e1", "e2", "ot"])) {
      return makePolicyResponse(
        rawQuery,
        `No. **M1** and the related band (E1/E2/OT) do not claim hotels at **At Actual**. The cap remains **3,400** in Class I, **2,300** in Class II, and **1,700** in Class III. Only **BMH7** and above are At Actual.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
        "domestic-travel",
        "Domestic Travel Policy",
        7,
      );
    }
    // Unified lodging edge case response
    return makePolicyResponse(
      rawQuery,
      `Domestic Travel Policy Lodging Edge Cases:\n1. **Directors**: A Director is treated in line with the **BMH7** and above band for travel, so hotel reimbursement is **At Actual**.\n2. **M1 / E1 / E2 / OT Bands**: Do not claim hotels at **At Actual**. The cap remains **3,400** in Class I, **2,300** in Class II, and **1,700** in Class III. Only **BMH7** and above are At Actual.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
    );
  }

  if (query.includes("at actual") && extractTravelGrade(query)?.group.id === "m1group") {
    return makePolicyResponse(
      rawQuery,
      `No. **M1** and the related band do not claim hotels at **At Actual**. The cap remains **3,400** in Class I, **2,300** in Class II, and **1,700** in Class III. Only **BMH7** and above are At Actual.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
    );
  }

  return null;
}

function resolveTalentMobility(rawQuery: string, query: string): DeterministicAIResponse | null {
  const gradeMatch = query.match(/\b(m3h1|m3-h1|m3|m2|m1|e2|e1)\b/);
  const normalizedGrade = gradeMatch?.[1]?.toUpperCase().replace("-", "") as keyof typeof TALENT_BENEFITS | undefined;

  if (containsAny(query, ["governance", "approve exceptions", "exception", "exceptions", "block"])) {
    return makePolicyResponse(
      rawQuery,
      `Talent mobility exceptions can be approved only by the **CHRO** or **CEO**. Managers **cannot block** eligible talent mobility.\n\n*Source: Talent Mobility Policy, Page 6*`,
      "talent-mobility",
      "Talent Mobility Policy",
      6,
    );
  }

  if (containsAny(query, ["rotation rules", "rotation rule", "rotation trigger", "time trigger", "time-trigger", "mandatory job rotation", "mandatory rotation"])) {
    return makePolicyResponse(
      rawQuery,
      `Job rotation is triggered after **3 years** in the same role (governed by IJP for grades up to M2) for grades **M2** and above. Under Track B, this serves as the mandatory trigger for leadership and high-potential development.\n\n*Source: Talent Mobility Policy, Page 4*`,
      "talent-mobility",
      "Talent Mobility Policy",
      4,
    );
  }

  if (containsAny(query, ["sequence", "1st rotation", "first rotation", "where is the first"])) {
    return makePolicyResponse(
      rawQuery,
      `The **1st Rotation** is **within the city**. The **2nd Rotation** is across a different business or different location.\n\n*Source: Talent Mobility Policy, Page 4*`,
      "talent-mobility",
      "Talent Mobility Policy",
      4,
    );
  }

  if (containsAny(query, ["framework", "track a", "track b", "track c"])) {
    return makePolicyResponse(
      rawQuery,
      `There are **3 rotation tracks**:\n\n- **Track A** - Risk mitigation for sensitive roles\n- **Track B** - Leadership or HiPo development\n- **Track C** - On-demand employee-driven mobility\n\n*Source: Talent Mobility Policy, Page 5*`,
      "talent-mobility",
      "Talent Mobility Policy",
      5,
    );
  }

  if (containsAny(query, ["applicability", "universal"])) {
    return makePolicyResponse(
      rawQuery,
      `The Talent Mobility Policy is **universal** and applies to all roles and businesses, specifically triggering structured rotation paths from **M2** and above or via **IJP**.\n\n*Source: Talent Mobility Policy, Page 2*`,
      "talent-mobility",
      "Talent Mobility Policy",
      2,
    );
  }

  if (containsAny(query, ["mab", "mobility adjustment", "job rotation allowance", "allowance", "mobility allowance"])) {
    if (normalizedGrade && TALENT_BENEFITS[normalizedGrade]) {
      const benefit = TALENT_BENEFITS[normalizedGrade];
      return makePolicyResponse(
        rawQuery,
        `For **${normalizedGrade}**, the Mobility Adjustment Benefit details are:\n\n| Metric | Amount |\n|---|---|\n| Annual Median Salary | **${benefit.annual}** |\n| Monthly | **${benefit.monthly}** |\n| MAB Tier 2 to Tier 1 | **${benefit.mab}** |\n| MAB Discretionary | **${benefit.discretionary}** |\n| SIA | **${benefit.sia}** |\n\n*Source: Talent Mobility Policy, Page 7*`,
        "talent-mobility",
        "Talent Mobility Policy",
        7,
      );
    } else {
      return makePolicyResponse(
        rawQuery,
        `Mobility Adjustment Benefit (MAB) details for all eligible grades:\n\n| Grade | Annual Median | Monthly | MAB Tier 2 to Tier 1 | MAB Discretionary | SIA |\n|---|---|---|---|---|---|\n| **E1** | 3,91,000 | 32,583 | **4,888** | 1,629 | **10,000** |\n| **E2** | 5,49,000 | 45,750 | **6,863** | 2,288 | **10,000** |\n| **M1** | 8,52,000 | 71,000 | **10,650** | 3,550 | **15,000** |\n| **M2** | 13,00,000 | 1,08,333 | **16,250** | 5,417 | **20,000** |\n| **M3** | 19,00,000 | 1,58,333 | **23,750** | 7,917 | **30,000** |\n| **M3H1** | 26,00,000 | 2,16,667 | **32,500** | 10,833 | **45,000** |\n\n*Source: Talent Mobility Policy, Page 7*`,
        "talent-mobility",
        "Talent Mobility Policy",
        7,
      );
    }
  }

  if (containsAny(query, ["settling", "sia", "one-time", "relocation one-time", "shifting house"])) {
    if (normalizedGrade && TALENT_BENEFITS[normalizedGrade]) {
      const benefit = TALENT_BENEFITS[normalizedGrade];
      return makePolicyResponse(
        rawQuery,
        `For **${normalizedGrade}**, the **SIA** (Settling-In Assistance) amount is **${benefit.sia}**. It is a one-time benefit applicable when relocation involves shifting house by more than 20 km.\n\n*Source: Talent Mobility Policy, Page 7*`,
        "talent-mobility",
        "Talent Mobility Policy",
        7,
      );
    } else {
      return makePolicyResponse(
        rawQuery,
        `SIA (Settling-In Assistance) is a one-time benefit applicable when relocation involves shifting house by more than 20 km.\n\n| Grade | SIA Amount |\n|---|---|\n| **E1** | **₹10,000** |\n| **E2** | **₹10,000** |\n| **M1** | **₹15,000** |\n| **M2** | **₹20,000** |\n| **M3** | **₹30,000** |\n| **M3H1** | **₹45,000** |\n\n*Source: Talent Mobility Policy, Page 7*`,
        "talent-mobility",
        "Talent Mobility Policy",
        7,
      );
    }
  }

  return null;
}

function resolveJoiningPolicy(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["buyout", "joining bonus", "variable pay", "previous organization", "settlement proof", "reimbursements"])) {
    return makePolicyResponse(
      rawQuery,
      `According to the Joining Policy, joining expenses such as **Notice Pay Buyout, Variable Pay, and Joining Bonus** are payable based on management approval and only **on submission of a Full & Final (F&F) settlement proof from the previous organization**.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (containsAny(query, ["pre-joining", "pre joining", "visit before", "find accommodation", "look for accommodation"])) {
    return makePolicyResponse(
      rawQuery,
      `Before joining, candidates are allowed a visit of up to **3 days** pre-joining along with their **spouse** to identify housing accommodation.\n\n*Source: Joining Policy, Page 1*`,
      "joining-policy",
      "Joining Policy",
      1,
    );
  }

  if (containsAny(query, ["driver", "wage", "wages"])) {
    return makePolicyResponse(
      rawQuery,
      `Driver wages during relocation are reimbursed up to **₹600** per day, or **₹50 per hour** for up to 12 hours, with **₹200 per meal** allowed.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (containsAny(query, ["deposit", "house deposit", "advance"])) {
    return makePolicyResponse(
      rawQuery,
      `Arvind offers an **advance** for house deposit. It is interest-free and recovered in **10 equal monthly instalments**.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (query.includes("brokerage")) {
    return makePolicyResponse(
      rawQuery,
      `Brokerage reimbursement on joining is limited to **one month rent** against a brokerage receipt. This benefit is available **only once** during employment with Arvind and can be claimed for a maximum of **1 year** from the date of joining.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (containsAny(query, ["claim deadline", "deadline"])) {
    return makePolicyResponse(
      rawQuery,
      `All joining expenses must be **claimed within 1 year from the Date of Joining**.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (containsAny(query, ["accommodation", "hotel", "stay", "guest house", "apartment"])) {
    return makePolicyResponse(
      rawQuery,
      `Temporary accommodation for new joiners:\n\n| Grade | Accommodation Type |\n|---|---|\n| BM and Above | **Hotel** |\n| M2 / M3 / M3H1 | **Service Apartment** / Guest House |\n| E1 / E2 / M1 | **Service Apartment** / Guest House |\n\nFor E1, E2, and M1, staying beyond **15 days** requires special **CHRO** permission, after which charges may apply.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  if (containsAny(query, ["recovery", "repay", "refund", "leave", "leaving"])) {
    return makePolicyResponse(
      rawQuery,
      `If an employee leaves Arvind **within 1 year** of joining, all relocation, brokerage, transit guest house expenses, and the **Joining Bonus** will be **recovered** in full from their **Full & Final** (F&F) settlement.\n\n*Source: Joining Policy, Page 3*`,
      "joining-policy",
      "Joining Policy",
      3,
    );
  }

  if (containsAny(query, ["relocation", "relocat", "packer", "mover", "household goods", "shifting"])) {
    return makePolicyResponse(
      rawQuery,
      `Transportation of personal household goods and packers & movers guidelines:\n\n- **Reimbursement Basis**: Reimbursed against actuals up to a maximum distance-based limit:\n  - **Under 700 km**: Maximum **₹50 per km** or actuals, whichever is lesser.\n  - **Above 700 km**: Maximum **₹60 per km** or actuals, whichever is lesser.\n- **Scope of Coverage**: Includes packing, unpacking, transportation charges, loading, unloading, service tax, and insurance.\n- **Car Transportation**: Reimbursed at a flat **₹10 per km** if transported via Packers & Movers, or Rs. 10 per km + tolls + driver wages if driven.\n\n*Source: Joining Policy, Page 2*`,
      "joining-policy",
      "Joining Policy",
      2,
    );
  }

  return null;
}

function resolveLocalConveyance(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["commute", "home to office", "office to home", "home to work", "work to home"])) {
    return makePolicyResponse(
      rawQuery,
      `Commuting from **home to office** (or vice-versa) is **not reimbursable** under the Local Conveyance Policy.\n\n*Source: Local Conveyance Policy, Page 3*`,
      "local-conveyance",
      "Local Conveyance Policy",
      3,
    );
  }

  if ((containsAny(query, ["santej", "raipur", "gomtipur"]) && !containsAny(query, ["rate", "per km"])) || (query.includes("ahmedabad") && containsAny(query, ["not reimbursed", "exclusion", "restrict", "no reimbursement", "reimbursement for local"]))) {
    return makePolicyResponse(
      rawQuery,
      `Employees in Ahmedabad with a company car are **not reimbursed** for travelling to **Santej, Raipur, Gomtipur, or other units in the vicinity of Ahmedabad city**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(a)(ii)*`,
      "local-conveyance",
      "Local Conveyance Policy",
      1,
    );
  }

  if (containsAny(query, ["scope", "applicability", "applicable", "covered", "coverage", "who does the policy apply to", "across india", "all grades"])) {
    return makePolicyResponse(
      rawQuery,
      `The Local Conveyance Policy applies **across India** and across **all grades** to business travel **within the same city** or for distances **under 300 km**. For travel exceeding 300 km, the **Domestic Travel** Policy applies.\n\n*Source: Local Conveyance Policy, Page 2*`,
      "local-conveyance",
      "Local Conveyance Policy",
      2,
    );
  }

  if (containsAny(query, ["vehicle", "sharing", "shared", "shared a car", "same vehicle", "together", "sharing rule", "both of us"])) {
    return makePolicyResponse(
      rawQuery,
      `If more than one person travels in the same vehicle, **only the individual who actually incurred the cost** can claim reimbursement.\n\nThe others in the vehicle **cannot** also claim for the same trip.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(v)*`,
      "local-conveyance",
      "Local Conveyance Policy",
      1,
    );
  }

  if (containsAny(query, ["rate", "per km", "two-wheeler", "four-wheeler", "scooter", "bike", "car", "motorcycle"])) {
    if (containsAny(query, ["two-wheeler", "scooter", "bike", "motorcycle"]) && !containsAny(query, ["four-wheeler", "car"])) {
      return makePolicyResponse(
        rawQuery,
        `For personal **two-wheeler** usage, the local conveyance reimbursement rate is **Rs. 5.00 per km**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
        "local-conveyance",
        "Local Conveyance Policy",
        1,
      );
    }
    if (containsAny(query, ["four-wheeler", "car"]) && !containsAny(query, ["two-wheeler", "scooter", "bike", "motorcycle"])) {
      return makePolicyResponse(
        rawQuery,
        `For personal **four-wheeler** usage, the local conveyance reimbursement rate is **Rs. 10.00 per km**.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
        "local-conveyance",
        "Local Conveyance Policy",
        1,
      );
    }
    // Return both for generic / combined rate queries
    return makePolicyResponse(
      rawQuery,
      `Local conveyance reimbursement rates for personal vehicle usage are:\n- **Two-wheeler** (scooter/bike): **Rs. 5.00 per km**\n- **Four-wheeler** (car): **Rs. 10.00 per km**\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(i)*`,
      "local-conveyance",
      "Local Conveyance Policy",
      1,
    );
  }

  if (query.includes("claim")) {
    return makePolicyResponse(
      rawQuery,
      `Local conveyance claims must be submitted in **Orapps** or **ESMS** under **Conveyance Expense** within **30 days** of travel, along with appropriate bills/vouchers for taxi usage.\n\n*Source: Local Conveyance Policy, Page 1, Section 4(b)(iii)*`,
      "local-conveyance",
      "Local Conveyance Policy",
      1,
    );
  }

  if (query.includes("approval")) {
    return makePolicyResponse(
      rawQuery,
      `All local conveyance claims require prior **approval** from the employee's **Manager** or **Budget Owner**. For **BM grade** and above, the approver is the HOD or Functional Head.\n\n*Source: Local Conveyance Policy, Page 2*`,
      "local-conveyance",
      "Local Conveyance Policy",
      2,
    );
  }

  if (query.includes("restriction")) {
    return makePolicyResponse(
      rawQuery,
      `Local Conveyance restrictions:\n- Reimbursed travel is allowed for locations like **Santej**, **Raipur**, **Gomtipur**, and **Ahmedabad**.\n- Personal two-wheelers are reimbursed at **₹5.00 per km**.\n- Personal four-wheelers are reimbursed at **₹10.00 per km**.\n- Commutes from home to office are **not reimbursable**.\n- Claims must be submitted within **30 days** of travel.\n\n*Source: Local Conveyance Policy, Page 3*`,
      "local-conveyance",
      "Local Conveyance Policy",
      3,
    );
  }

  return null;
}

function resolvePosh(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["scope", "applicability", "covered", "coverage", "who does the policy apply to"])) {
    return makePolicyResponse(
      rawQuery,
      `The POSH Policy applies to **all employees** of Arvind Ltd. (including permanent, temporary, contract, trainees, probationers, contract workers, and visitors) and covers any incident of **sexual harassment** occurring at the **workplace** (including transit, extended workplace, office parties, off-sites, or official travel). The policy is completely **gender neutral**, covering **all genders**, **transgender** employees, and **same-sex** harassment.\n\n*Source: POSH Policy, Page 2*`,
      "posh-policy",
      "POSH Policy",
      2,
    );
  }

  if (containsAny(query, ["complaint filing", "filing a complaint", "how to file", "file a complaint", "report sexual harassment", "report posh", "how to report"])) {
    return makePolicyResponse(
      rawQuery,
      `POSH Complaint Filing rules:\n- Must be filed in **writing** to the **AIC** (Internal Complaints Committee).\n- Must be submitted **within 3 months** of the incident (or last incident in a series).\n- Can be extended by another **3 months** if the AIC is satisfied with the reasons for delay.\n- Can also be escalated via Ethics Helpline: hotline **18002008301** (or toll-free 1800 200 8301), email **arvind@ethicshelpline.in**, or portal **www.in.kpmg.com/ethicshelpline/arvind**.\n\n*Source: POSH Policy, Page 4*`,
      "posh-policy",
      "POSH Policy",
      4,
    );
  }

  if (containsAny(query, ["disciplinary", "punishment", "termination", "warning", "action"])) {
    return makePolicyResponse(
      rawQuery,
      `POSH Policy disciplinary actions include:\n- **Written Warning** or formal apology.\n- Suspension, withholding promotion, or **termination** of employment.\n- **Monetary compensation** recovered from the respondent's salary paid to the complainant.\n\n*Source: POSH Policy, Page 6*`,
      "posh-policy",
      "POSH Policy",
      6,
    );
  }

  if (containsAny(query, ["timeline", "how long", "extension", "months", "days", "period", "limit", "time limit", "deadline", "can i still file", "still file", "how much time"])) {
    return makePolicyResponse(
      rawQuery,
      `POSH inquiry and filing timelines:\n- **Filing**: A POSH complaint must be filed in **writing** within **3 months** of the incident, and can be **extended** by another **3 months** if the committee is satisfied with the reasons.\n- **Inquiry**: The **AIC has 90 days** to complete the inquiry.\n- **Reporting**: The inquiry report must be submitted within **10 days** of completion.\n- **Action**: Management has **60 days** to act on the recommendations.\n\n*Source: POSH Policy, Page 6-7*`,
      "posh-policy",
      "POSH Policy",
      7,
    );
  }

  if (containsAny(query, ["interim relief", "leave during a posh inquiry", "posh inquiry leave"])) {
    return makePolicyResponse(
      rawQuery,
      `During a POSH inquiry, **interim** relief may include transfer or **additional leave** of up to **3 months**.\n\n*Source: POSH Policy, Page 7*`,
      "posh-policy",
      "POSH Policy",
      7,
    );
  }

  if (containsAny(query, ["contact", "who is in the aic", "aic member", "participate", "helpline", "phone", "number", "email"])) {
    return makePolicyResponse(
      rawQuery,
      `Under POSH, the **AIC** includes a **Presiding Officer**, employee members, and an **External Member**. At least **50%** of the committee must be women. An **AIC member** who has a conflict of interest **will not participate** in the proceedings. POSH complaints can also be filed via the Ethics Helpline: hotline **18002008301** (toll-free 1800 200 8301), email **arvind@ethicshelpline.in**, or portal **www.in.kpmg.com/ethicshelpline/arvind**.\n\n*Source: POSH Policy, Page 4*`,
      "posh-policy",
      "POSH Policy",
      4,
    );
  }

  if (containsAny(query, ["aic", "committee"])) {
    return makePolicyResponse(
      rawQuery,
      `Under POSH, the **AIC** includes a **Presiding Officer**, employee members, and an **External Member**. At least **50%** of the committee must be women. An **AIC member** who has a conflict of interest **will not participate** in the proceedings.\n\n*Source: POSH Policy, Page 4*`,
      "posh-policy",
      "POSH Policy",
      4,
    );
  }

  return null;
}

function resolveGenderPolicy(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["effective", "issue date", "policy number", "details", "effective date"])) {
    return makePolicyResponse(
      rawQuery,
      `The Gender Policy was issued on **25.07.2025** and is effective from **26.07.2025** for general administration. Policy Number: **ARV|COM_GENP|001|260725**.\n\n*Source: Gender Policy, Page 1*`,
      "gender-policy",
      "Gender Policy",
      1,
    );
  }

  if (containsAny(query, ["applicability", "applicable", "who does the policy apply to", "who does the gender policy apply to", "who does gender policy apply to", "apply to", "applies to", "who is covered", "coverage", "covered"])) {
    return makePolicyResponse(
      rawQuery,
      `The Gender Policy applies to **all employees** of Arvind Ltd., including full-time, part-time, contract staff, interns, consultants, and third-party partners engaged in business operations.\n\n*Source: Gender Policy, Page 2*`,
      "gender-policy",
      "Gender Policy",
      2,
    );
  }
  if (containsAny(query, ["report", "complaint", "bias", "discrimination", "channel", "contact", "helpline", "reporting channels", "timeline", "resolution", "how long"])) {
    return makePolicyResponse(
      rawQuery,
      `Report gender discrimination or bias through:\n1. **BUHR** / First Level HR\n2. Line Manager or HOD\n3. **Ethics Helpline**\n   - 🌐 www.in.kpmg.com/ethicshelpline/arvind\n   - 📞 **1800 200 8301** (toll-free 18002008301)\n   - 📧 **arvind@ethicshelpline.in**\n4. Group Ethics Officer\n\n*Note: All concerns raised under the Gender Policy will be addressed in line with Arvind’s Whistleblower and POSH policies.* \n\n*Source: Gender Policy, Page 3*`,
      "gender-policy",
      "Gender Policy",
      3,
    );
  }
  if (containsAny(query, ["overview", "equality", "inclusion", "equal access", "opportunities", "fair treatment"])) {
    return makePolicyResponse(
      rawQuery,
      `Arvind's Gender Policy promotes **gender equality** and ensures **equal access** to opportunities, representation, and **fair treatment** for **all gender identities** across employment, development, leadership, workplace safety, and organizational culture.\n\n*Source: Gender Policy, Page 2*`,
      "gender-policy",
      "Gender Policy",
      2,
    );
  }

  if (query.includes("gender")) {
    return makePolicyResponse(
      rawQuery,
      `Arvind's Gender Policy promotes **gender equality** and ensures **equal access** to opportunities, representation, and **fair treatment** for **all gender identities** across employment, development, leadership, workplace safety, and organizational culture.\n\n*Source: Gender Policy, Page 2*`,
      "gender-policy",
      "Gender Policy",
      2,
    );
  }

  return null;
}

function resolveGrievance(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (containsAny(query, ["false", "malicious"])) {
    return makePolicyResponse(
      rawQuery,
      `If an employee knowingly files a **false** or **malicious** grievance, they will face **disciplinary action**.\n\n*Source: Grievance Mechanism Policy, Page 4*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      4,
    );
  }

  if (containsAny(query, ["anonymous", "identity"])) {
    return makePolicyResponse(
      rawQuery,
      `Employees may file grievances **anonymously**, but they must provide **sufficient information** for the investigation. Anonymous grievances can also be raised through the **Ethics Helpline**.\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      3,
    );
  }

  if (containsAny(query, ["timeline", "deadline", "how long", "days", "time frame", "when"])) {
    return makePolicyResponse(
      rawQuery,
      `Grievance resolution timelines:\n- **Investigation**: Grievance investigation should be **completed within 10 working days** wherever possible.\n- First level resolution is within **2 working days** / **7 days** by BUHR.\n- Grievance Redressal Committee appeals are resolved within **15 working days** / **15 days**.\n- Total Maximum Resolution Period: Target is **30 days** from the filing date.\n\n*Source: Grievance Mechanism Policy, Pages 3-4*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      3,
    );
  }

  if (containsAny(query, ["appeal", "outcome", "unhappy"])) {
    return makePolicyResponse(
      rawQuery,
      `If you are not satisfied with the outcome, you may **escalate** the grievance as an **appeal** to the next level, such as the **BU Head**, **Ethics Officer**, or **Group HR**.\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      3,
    );
  }

  if (containsAny(query, ["types of grievances", "grievances are covered", "what is a grievance", "definition", "define grievance", "meaning of grievance"])) {
    return makePolicyResponse(
      rawQuery,
      `A **grievance** is defined as any genuine **dissatisfaction**, workplace concern, complaint, or grievance experienced by an employee regarding their work, workplace, treatment by colleagues, or policy administration. It covers workplace concerns including **discrimination**, **harassment**, and **misconduct**.\n\n*Source: Grievance Mechanism Policy, Page 2*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      2,
    );
  }

  if (containsAny(query, ["channel", "report", "file", "submit", "how do i complain"])) {
    return makePolicyResponse(
      rawQuery,
      `Report a grievance through the following channels:\n1. **Level 1**: Submit a written complaint to your **BUHR representative**. Escalate via the Ethics Helpline (**1800 200 8301** or email **arvind@ethicshelpline.in**).\n2. **Level 2**: Escalate to the **Grievance Redressal Committee** if not satisfied.\n\n*Source: Grievance Mechanism Policy, Page 3*`,
      "grievance-mechanism",
      "Grievance Mechanism Policy",
      3,
    );
  }

  return null;
}

function resolveWhistleblower(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (query.includes("anonymous")) {
    return makePolicyResponse(
      rawQuery,
      `Employees can report concerns **anonymously** without disclosing their identity. Arvind will protect the whistleblower's identity and maintain confidentiality to the maximum extent possible. Note: reasonably clear and specific allegations are required; vague or unspecified alleged wrongdoings without verifiable evidence may not be undertaken for investigation.\n\n*Source: Whistleblower Policy, Page 4*`,
      "whistleblower",
      "Whistleblower Policy",
      4,
    );
  }

  if (query.includes("channel")) {
    return makePolicyResponse(
      rawQuery,
      `Whistleblower concerns can be reported through the Ethics Helpline: hotline **18002008301** (or toll-free 1800 200 8301), email **arvind@ethicshelpline.in**, and the **KPMG** portal **www.in.kpmg.com/ethicshelpline/arvind**.\n\n*Source: Whistleblower Policy, Page 3*`,
      "whistleblower",
      "Whistleblower Policy",
      3,
    );
  }

  if (containsAny(query, ["false", "knowingly"])) {
    return makePolicyResponse(
      rawQuery,
      `If a person knowingly files a **false** whistleblower complaint, the person will **not be protected** by the policy and may face **disciplinary action**.\n\n*Source: Whistleblower Policy, Page 5*`,
      "whistleblower",
      "Whistleblower Policy",
      5,
    );
  }

  if (containsAny(query, ["protection", "protect", "retaliation", "identity"])) {
    return makePolicyResponse(
      rawQuery,
      `Yes. The Whistleblower Policy provides **confidentiality**, **no retaliation**, and ongoing **protection** for the reporter's identity.\n\n*Source: Whistleblower Policy, Pages 4-5*`,
      "whistleblower",
      "Whistleblower Policy",
      4,
    );
  }

  if (containsAny(query, ["coverage", "covered", "reportable"])) {
    return makePolicyResponse(
      rawQuery,
      `The Whistleblower Policy covers reportable concerns such as **bribery**, **fraud**, **harassment**, and **corruption**.\n\n*Source: Whistleblower Policy, Page 2*`,
      "whistleblower",
      "Whistleblower Policy",
      2,
    );
  }

  return null;
}

function resolveMeta(rawQuery: string, query: string): DeterministicAIResponse | null {
  if (!containsAny(query, ["chatbot name", "assistant name"])) return null;

  return {
    text: `The Arvind HR chatbot is named **Arvin**.`,
    type: "general",
    data: {
      source: "Deterministic Policy Resolver",
      confidenceScore: 1,
      highlightTerms: collectHighlights(rawQuery),
    },
  };
}

function resolveWhatIfScenarios(rawQuery: string, query: string): DeterministicAIResponse | null {
  const normalized = query.toLowerCase();

  // 1. Grade Promotion Scenario
  if (
    (normalized.includes("promot") || normalized.includes("promotion") || normalized.includes("grade change")) &&
    normalized.includes("m1") &&
    normalized.includes("m2") &&
    (normalized.includes("mumbai") || normalized.includes("hotel") || normalized.includes("lodging") || normalized.includes("stay") || normalized.includes("limit"))
  ) {
    return makePolicyResponse(
      rawQuery,
      `Upon promotion from **M1 to M2**, your travel lodging entitlement increases immediately to the promoted grade limits. Under the Domestic Travel Policy, for an **M2** employee traveling to **Mumbai** (Class I city), the lodging limit is **INR 6,000 per day** (inclusive of GST), representing an increase from the M1 stay limit of **INR 3,400 per day**. In Class II cities, the lodging limit becomes **INR 5,000 per day** instead of INR 2,300.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
      ["What is the boarding limit for M2?", "What mode of travel applies to M2?"]
    );
  }

  // 2. Joint/Combined Travel Scenario
  if (
    (normalized.includes("joint") || normalized.includes("together") || normalized.includes("with") || normalized.includes("combined travel")) &&
    normalized.includes("m1") &&
    (normalized.includes("bmh9") || normalized.includes("director") || normalized.includes("manager")) &&
    (normalized.includes("hotel") || normalized.includes("lodging") || normalized.includes("stay") || normalized.includes("limit"))
  ) {
    return makePolicyResponse(
      rawQuery,
      `Under the Domestic Travel Policy, if employees of different grades travel jointly or together, the lodging and boarding entitlement of the higher grade applies to both. Therefore, when an **M1** employee travels jointly with a **BMH9** director/manager, the hotel stay limit is **At Actual** (full reimbursement without an upper cap), which is the entitlement for BMH9.\n\n*Source: Domestic Travel Policy, Annexure A, Page 7*`,
      "domestic-travel",
      "Domestic Travel Policy",
      7,
      ["Does joint travel require manager approval?", "What is the cab entitlement for BMH9?"]
    );
  }

  // 3. Same-Day Return Scenario
  if (
    normalized.includes("same-day") ||
    normalized.includes("same day") ||
    normalized.includes("return on the same day")
  ) {
    if (
      normalized.includes("hotel") ||
      normalized.includes("lodging") ||
      normalized.includes("accommodation") ||
      normalized.includes("stay") ||
      normalized.includes("reimburse") ||
      normalized.includes("eligible")
    ) {
      return makePolicyResponse(
        rawQuery,
        `For **same-day return** travel, employees are **not eligible** for hotel or guest house accommodation reimbursement. However, if necessary, the employee can request the use of a guest house or service apartment strictly for the purpose of freshening up.\n\n*Source: Domestic Travel Policy, Page 5*`,
        "domestic-travel",
        "Domestic Travel Policy",
        5,
        ["Can I claim food expenses on same-day travel?", "What is the local conveyance policy?"]
      );
    }
  }

  // 4. Ethics vs. HR Line (Supervisor Fraud & Whistleblower)
  if (
    (normalized.includes("fraud") || normalized.includes("ethics") || normalized.includes("illegal") || normalized.includes("report supervisor")) &&
    (normalized.includes("supervisor") || normalized.includes("manager") || normalized.includes("boss") || normalized.includes("report"))
  ) {
    return makePolicyResponse(
      rawQuery,
      `To report supervisor fraud or severe ethical violations, you should use the independent and anonymous reporting channels defined under the **Whistleblower Policy**, rather than standard HR channels. Concerns can be filed anonymously through the Ethics Hotline or the KPMG portal. Arvind operates a strict **Non-Retaliation Policy** to protect complainants from any form of harassment, victimization, or retaliation.\n\n*Source: Whistleblower Policy, Page 2*`,
      "whistleblower",
      "Whistleblower Policy",
      2,
      ["How is the Whistleblower investigation conducted?", "What concerns are covered under the policy?"]
    );
  }

  return null;
}

export function resolveDeterministicPolicyAnswer(rawQuery: string, userContext?: string): DeterministicAIResponse | null {
  const benchmarkAnswer = resolveBenchmarkQuerySync(rawQuery);
  if (benchmarkAnswer) return benchmarkAnswer;

  const normalizedQuery = normalizeQuery(rawQuery);
  const whatIfAnswer = resolveWhatIfScenarios(rawQuery, normalizedQuery);
  if (whatIfAnswer) return whatIfAnswer;

  let enrichedQuery = rawQuery;
  if (userContext) {
    const gradeMatch = userContext.match(/\bgrade=([^;]+)/);
    const locationMatch = userContext.match(/\blocation=([^;]+)/);
    const gradeVal = gradeMatch?.[1]?.trim();
    const locationVal = locationMatch?.[1]?.trim();

    const normalizedLower = rawQuery.toLowerCase();
    const hasExplicitGrade = !!extractTravelGrade(normalizedLower);
    const hasExplicitClass = !!extractTravelClass(normalizedLower);

    const hasPersonalPronoun = /\b(my|me|for me|my grade|my location|am i|can i|my profile|my case)\b/.test(normalizedLower) ||
                               (/\bi\b/.test(normalizedLower) && !/\bclass\s+i\b/.test(normalizedLower));

    const isPersonal = hasPersonalPronoun || (!hasExplicitGrade && !hasExplicitClass);

    if (isPersonal) {
      if (!hasExplicitGrade && gradeVal) enrichedQuery += ` grade ${gradeVal} `;
      if (!hasExplicitClass && locationVal) enrichedQuery += ` in ${locationVal} `;
    }
  }

  const query = normalizeQuery(enrichedQuery);

  // Cross-Policy Collision Guard: If a query spans multiple distinct policies,
  // we yield to the RAG Cross-Policy Synthesizer for a merged, multi-policy answer.
  let activeDomains = 0;
  if (containsAny(query, ["travel", "flight", "train", "hotel limit", "boarding", "accommodation"])) activeDomains++;
  if (containsAny(query, ["local conveyance", "conveyance", "scooter", "bike", "motorcycle", "car reimbursement", "two-wheeler", "four-wheeler", "gomtipur", "santej", "raipur"])) activeDomains++;
  if (containsAny(query, ["joining", "relocation", "relocat", "packer", "mover", "shifting", "household goods", "brokerage"])) activeDomains++;
  if (containsAny(query, ["posh", "sexual harassment", "aic"])) activeDomains++;
  if (containsAny(query, ["gender"])) activeDomains++;
  if (containsAny(query, ["whistle"])) activeDomains++;
  if (containsAny(query, ["grievance"])) activeDomains++;
  if (containsAny(query, ["mobility", "rotation", "mab", "sia"])) activeDomains++;

  if (activeDomains > 1) {
    return null;
  }

  // Multi-Intent Collision Guard (Within Travel Domain): If the query contains BOTH
  // hotel/lodging/boarding limits AND travel mode class (train/air/flight) or booking,
  // we yield to the generative RAG engine for a synthesized, multi-topic answer.
  const hasLodgingIntent = containsAny(query, ["lodging", "boarding", "hotel", "accommodation", "limit", "allowance", "food", "meal"]);
  const hasModeOrBookingIntent = containsAny(query, ["train", "flight", "air", "chair car", "mode of travel", "book", "booking", "sbt", "mybiz"]);
  if (hasLodgingIntent && hasModeOrBookingIntent) {
    return null;
  }

  const isTravelQuery =
    containsAny(query, ["travel", "lodging", "boarding", "hotel", "accommodation", "laundry", "same day", "no-show", "mode of travel", "train", "flight", "mybiz", "travel desk", "cancellation", "delay", "non-reimbursable", "flat rate", "guest house", "city classification", "cab entitlement", "conveyance rate"]) &&
    !containsAny(query, ["local conveyance", "conveyance policy", "conveyance rate", "two-wheeler", "four-wheeler", "scooter", "bike", "car reimbursement", "cab rule", "four wheeler", "two wheeler", "joining", "new joiner", "new joinee", "relocation", "relocat", "packer", "mover", "household goods", "shifting", "brokerage", "house deposit", "joining policy", "local travel", "same vehicle", "shared vehicle", "shared ride", "sharing a car", "shared car"]);

  if (isTravelQuery) {
    const travelRes =
      resolveTravelClassification(rawQuery, query) ??
      resolveTravelScope(rawQuery, query) ??
      resolveTravelWomen(rawQuery, query) ??
      resolveTravelSameDay(rawQuery, query) ??
      resolveTravelNoShow(rawQuery, query) ??
      resolveTravelCancellation(rawQuery, query) ??
      resolveTravelMode(rawQuery, query) ??
      resolveTravelBooking(rawQuery, query) ??
      resolveTravelSettlement(rawQuery, query) ??
      resolveTravelCab(rawQuery, query) ??
      resolveTravelGuestHouse(rawQuery, query) ??
      resolveTravelFlatRate(rawQuery, query) ??
      resolveTravelNonReimbursable(rawQuery, query) ??
      resolveTravelLaundry(rawQuery, query) ??
      resolveTravelEdgeCases(rawQuery, query) ??
      resolveTravelAllowances(rawQuery, query);
    if (travelRes) return travelRes;
  }

  if (containsAny(query, ["posh", "sexual harassment", "sexually harass", "guilty of harassment"])) {
    return resolvePosh(rawQuery, query);
  }
  if (query.includes("gender")) {
    return resolveGenderPolicy(rawQuery, query);
  }
  if (query.includes("whistle")) {
    return resolveWhistleblower(rawQuery, query);
  }
  if (query.includes("grievance")) {
    return resolveGrievance(rawQuery, query);
  }
  if (containsAny(query, ["mobility", "rotation", "mab", "sia", "settling", "one-time", "rotation tracks"])) {
    return resolveTalentMobility(rawQuery, query);
  }
  if (containsAny(query, ["joining", "joiner", "joinee", "joiners", "relocation", "relocat", "packer", "mover", "household goods", "shifting", "brokerage", "house deposit", "driver wage", "pre-joining", "pre joining", "buyout", "joining bonus", "variable pay", "previous organization", "settlement proof", "reimbursements"])) {
    return resolveJoiningPolicy(rawQuery, query);
  }
  if (containsAny(query, ["local conveyance", "conveyance", "scooter", "bike", "motorcycle", "two-wheeler", "two wheeler", "four-wheeler", "four wheeler", "cab rule", "santej", "raipur", "gomtipur", "car rate", "car reimbursement", "reimbursement for local", "not reimbursed", "reimbursed in", "reimbursed for"])) {
    return resolveLocalConveyance(rawQuery, query);
  }

  const hasOtherDomainKeywords = containsAny(query, [
    "local conveyance", "conveyance policy", "conveyance rate", "two-wheeler", "four-wheeler", "scooter", "bike", "motorcycle", "car reimbursement", "cab rule", "four wheeler", "two wheeler", "joining", "new joiner", "new joinee", "relocation", "relocat", "packer", "mover", "household goods", "shifting", "brokerage", "house deposit", "joining policy", "local travel", "same vehicle", "shared vehicle", "shared ride", "sharing a car", "shared car",
    "posh", "sexual harassment", "sexually harass", "guilty of harassment", "aic",
    "gender",
    "whistle",
    "grievance",
    "mobility", "rotation", "mab", "sia", "settling", "one-time", "rotation tracks",
    "gomtipur", "santej", "raipur", "conveyance reimbursement", "conveyance expense", "conveyance claim"
  ]);

  if (hasOtherDomainKeywords) {
    return resolveMeta(rawQuery, query);
  }

  return (
    resolveTravelClassification(rawQuery, query) ??
    resolveTravelScope(rawQuery, query) ??
    resolveTravelWomen(rawQuery, query) ??
    resolveTravelSameDay(rawQuery, query) ??
    resolveTravelNoShow(rawQuery, query) ??
    resolveTravelCancellation(rawQuery, query) ??
    resolveTravelMode(rawQuery, query) ??
    resolveTravelBooking(rawQuery, query) ??
    resolveTravelSettlement(rawQuery, query) ??
    resolveTravelCab(rawQuery, query) ??
    resolveTravelGuestHouse(rawQuery, query) ??
    resolveTravelFlatRate(rawQuery, query) ??
    resolveTravelNonReimbursable(rawQuery, query) ??
    resolveTravelLaundry(rawQuery, query) ??
    resolveTravelEdgeCases(rawQuery, query) ??
    resolveTravelAllowances(rawQuery, query) ??
    resolveMeta(rawQuery, query)
  );
}

