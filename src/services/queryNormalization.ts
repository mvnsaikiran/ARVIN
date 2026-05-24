export const COMMON_CITY_ALIASES: Record<string, string[]> = {
  ahmedabad: ["ahmendabad", "ahmedbad", "ahmdabad", "amdavad"],
  bangalore: ["bengaluru"],
};

const COMMON_CHAT_REPLACEMENTS: Array<[RegExp, string]> = [
  [/\bwhat\s+abt\b/g, "what about"],
  [/\bwat\b/g, "what"],
  [/\bwht\b/g, "what"],
  [/\bhw\b/g, "how"],
  [/\babt\b/g, "about"],
  [/\bfr\b/g, "for"],
  [/\bpls\b/g, "please"],
  [/\bplz\b/g, "please"],
  [/\bu\b/g, "you"],
  [/\bur\b/g, "your"],
  [/^\s*n\b/g, " and"],
  [/\ballownace\b/g, "allowance"],
  [/\balowance\b/g, "allowance"],
  [/\ballowence\b/g, "allowance"],
  [/\blimt\b/g, "limit"],
  [/\blodgng\b/g, "lodging"],
  [/\blodgin\b/g, "lodging"],
  [/\bloding\b/g, "lodging"],
  [/\bconveynce\b/g, "conveyance"],
  [/\bconvayance\b/g, "conveyance"],
  [/\breimbersement\b/g, "reimbursement"],
  [/\breimbursment\b/g, "reimbursement"],
  [/\baccomodation\b/g, "accommodation"],
  [/\baccomodations\b/g, "accommodations"],
  [/\bharasment\b/g, "harassment"],
  [/\bgreivance\b/g, "grievance"],
  [/\bmoblity\b/g, "mobility"],
  [/\bwhistle\s+blower\b/g, "whistleblower"],
  [/\bposhh\b/g, "posh"],
  [/\bsimpl\b/g, "simple"],
  [/\bwrds\b/g, "words"],
  [/\bclass\s*1i\b/g, "class ii"],
  [/\bclass\s*i1\b/g, "class ii"],
  [/\bclass\s*2i\b/g, "class iii"],
  [/\bclass\s*twoi\b/g, "class iii"],
];

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const CITY_CLASS_MAPPING: Record<string, string> = {
  mumbai: "class i",
  delhi: "class i",
  bangalore: "class i",
  hyderabad: "class i",
  chennai: "class i",
  kolkata: "class i",
  ahmedabad: "class i",
  pune: "class i",
  santej: "class iii",
  jammu: "class iii",
  surat: "class ii",
  jaipur: "class ii",
  lucknow: "class ii",
  kanpur: "class ii",
  nagpur: "class ii",
  indore: "class ii",
  bhopal: "class ii",
  vadodara: "class ii",
};

export function normalizeEmployeeChatText(text: string): string {
  let normalized = ` ${text.toLowerCase()} `;

  for (const [pattern, replacement] of COMMON_CHAT_REPLACEMENTS) {
    normalized = normalized.replace(pattern, replacement);
  }

  for (const [canonical, aliases] of Object.entries(COMMON_CITY_ALIASES)) {
    for (const alias of aliases) {
      normalized = normalized.replace(new RegExp(`\\b${escapeRegExp(alias)}\\b`, "g"), canonical);
    }
  }

  // Inject Implicit HR City Class for Vector Grounding (Fixes Loophole #1)
  for (const [city, cityClass] of Object.entries(CITY_CLASS_MAPPING)) {
    if (new RegExp(`\\b${city}\\b`).test(normalized) && !normalized.includes(cityClass)) {
      normalized = normalized.replace(new RegExp(`\\b${city}\\b`, "g"), `${city} (${cityClass})`);
    }
  }

  return normalized.replace(/\s+/g, " ").trim();
}

export function isEmployeeSpecificQuestion(text: string): boolean {
  const normalized = normalizeEmployeeChatText(text);

  return (
    /\b(my|mine|for me|for my|applicable to me|apply to me|based on my|my grade|my location|my profile|my case)\b/.test(normalized) ||
    /\b(am i eligible|can i claim|do i get|what do i get|what is my|show me my|my current|my latest)\b/.test(normalized)
  );
}

export function isKnownUnsupportedQuestion(normalizedQuery: string): boolean {
  return /\b(work from home|wfh|internet reimbursement|broadband|wifi|mobile bill|phone bill|data card|netflix|spotify|prime video|streaming|subscription|gym|fitness|membership|credit card|personal laundry|dry cleaning|clothing|suit|apparel|loan|loans|pf|provident fund|salary advance|salary increment|appraisal|increment|performance bonus|salary hike|leave application|medical insurance|health insurance)\b/.test(normalizedQuery);
}

