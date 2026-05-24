import { POLICY_META, type Chunk } from "./policies";
import { STRUCTURED_POLICY_RULES, type StructuredPolicyRule } from "./structuredPolicyRules";

export interface PolicyRuleChunk extends Chunk {
  isRuleChunk: true;
  ruleType: StructuredPolicyRule["ruleType"];
  section: string;
  clause: string;
  conditions: string[];
  canonicalAnswer: string;
  keywords: string[];
  sampleQueries: string[];
  gradeTags: string[];
  cityClasses: string[];
  cityNames: string[];
  metrics: string[];
  topics: string[];
}

const STOPWORDS = new Set([
  "the",
  "and",
  "for",
  "with",
  "that",
  "this",
  "under",
  "policy",
  "what",
  "when",
  "where",
  "which",
  "who",
  "from",
  "only",
  "please",
  "tell",
  "exact",
  "page",
  "source",
]);

function tokenize(value: string) {
  return Array.from(
    new Set(
      value
        .toLowerCase()
        .replace(/[^a-z0-9\s/-]/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .split(/\s+/)
        .filter((token) => token.length > 2 && !STOPWORDS.has(token)),
    ),
  ).slice(0, 30);
}

function getPolicyMeta(policyId: string, fallbackName: string) {
  return POLICY_META.find((policy) => policy.id === policyId) ?? {
    id: policyId,
    name: fallbackName,
    fileUrl: "",
    sourceDocumentName: fallbackName,
    description: "",
  };
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function collectMatches(text: string, patterns: Array<[RegExp, string]>) {
  return unique(
    patterns
      .filter(([pattern]) => pattern.test(text))
      .map(([, value]) => value),
  );
}

function extractGradeTags(text: string) {
  const normalized = text.toLowerCase();
  return collectMatches(normalized, [
    [/\bbmh9\b/, "bmh9"],
    [/\bbmh8\b|\bh8\b/, "bmh8"],
    [/\bbmh7\b|\bbm-h7\b|director/, "bmh7"],
    [/\bbmh6\b|\bh6\b/, "bmh6"],
    [/\bbmh5\b|\bh5\b/, "bmh5"],
    [/\bbmh4\b|\bh4\b/, "bmh4"],
    [/\bbmh3\b|\bbm-h3\b/, "bmh3"],
    [/\bm3h1\b|\bm3-h1\b/, "m3h1"],
    [/\bm3\b/, "m3"],
    [/\bm2\b/, "m2"],
    [/\bm1\b/, "m1"],
    [/\bmt\b/, "mt"],
    [/\be2\b/, "e2"],
    [/\be1\b/, "e1"],
    [/\bget\b/, "get"],
    [/\bot\b/, "ot"],
  ]);
}

function extractCityClasses(text: string) {
  const normalized = text.toLowerCase();
  return collectMatches(normalized, [
    [/\bclass i\b/, "class i"],
    [/\bclass ii\b/, "class ii"],
    [/\bclass iii\b/, "class iii"],
  ]);
}

function extractCityNames(text: string) {
  const normalized = text.toLowerCase();
  return collectMatches(normalized, [
    [/\bahmedabad\b/, "ahmedabad"],
    [/\bbangalore\b|\bbengaluru\b/, "bangalore"],
    [/\bbhopal\b/, "bhopal"],
    [/\bchennai\b/, "chennai"],
    [/\bcoimbatore\b/, "coimbatore"],
    [/\bdelhi\b/, "delhi"],
    [/\bhyderabad\b/, "hyderabad"],
    [/\bindore\b/, "indore"],
    [/\bjaipur\b/, "jaipur"],
    [/\bjammu\b/, "jammu"],
    [/\bkochi\b/, "kochi"],
    [/\bkolkata\b/, "kolkata"],
    [/\blucknow\b/, "lucknow"],
    [/\bmumbai\b/, "mumbai"],
    [/\bmysore\b/, "mysore"],
    [/\bnagpur\b/, "nagpur"],
    [/\bncr\b/, "ncr"],
    [/\bpatna\b/, "patna"],
    [/\bpune\b/, "pune"],
    [/\brajkot\b/, "rajkot"],
    [/\branchi\b/, "ranchi"],
    [/\bsrinagar\b/, "srinagar"],
    [/\bsurat\b/, "surat"],
    [/\bvadodara\b|\bbaroda\b/, "vadodara"],
    [/\bvisakhapatnam\b|\bvizag\b/, "visakhapatnam"],
  ]);
}

function extractMetrics(text: string, ruleType: StructuredPolicyRule["ruleType"]) {
  const normalized = text.toLowerCase();
  return unique([
    ...collectMatches(normalized, [
      [/\blodging\b|\bhotel\b|\baccommodation\b/, "lodging"],
      [/\bboarding\b|\bfood\b|\bmeals?\b/, "boarding"],
      [/\btrain\b|\bac\b|\bchair car\b/, "train"],
      [/\bair\b|\bflight\b|\beconomy\b|\bbusiness\b|\bpremium economy\b/, "air"],
      [/\bcab\b|\bola\b|\buber\b|\bblusmart\b|\bmetro\b|\bbus\b/, "cab"],
      [/\blaundry\b/, "laundry"],
      [/\bflat rate\b|\bself arrangement\b|\bown arrangement\b/, "flat-rate"],
      [/\bbooking\b|\bbooked\b|\bmybiz\b/, "booking"],
      [/\bapproval\b|\bapprove\b|\breporting manager\b/, "approval"],
      [/\bsettlement\b|\bclaim\b/, "claim"],
      [/\btwo-wheeler\b|\bbike\b|\bscooter\b|\bmotorcycle\b/, "two-wheeler"],
      [/\bfour-wheeler\b|\bcar\b/, "four-wheeler"],
      [/\banonymous\b/, "anonymous"],
      [/\binvestigation\b/, "investigation"],
      [/\backnowledg/, "acknowledgement"],
      [/\boutcome\b|\bresolution\b/, "resolution"],
      [/\bappeal\b/, "appeal"],
      [/\bfalse\b|\bmalicious\b|\bfake complaint\b/, "false-complaint"],
      [/\bpre-joining\b|\bpre joining\b/, "pre-joining"],
      [/\btemporary accommodation\b/, "temporary-accommodation"],
      [/\bbrokerage\b/, "brokerage"],
      [/\bhouse deposit\b/, "house-deposit"],
      [/\bhousehold goods\b|\bpackers\b/, "household-goods"],
      [/\brecovery\b|\bfull & final\b|\bfinal settlement\b/, "recovery"],
      [/\bwomen employees\b|\bnext higher grade\b|\bnight travel\b/, "women-protection"],
      [/\bno-show\b/, "no-show"],
      [/\bsame-day\b|\bfreshen(?:ing)? up\b/, "same-day"],
      [/\bdelayed\b|\b3 hours\b/, "delay"],
      [/\bclass i\b|\bclass ii\b|\bclass iii\b|\bclassified as\b/, "classification"],
      [/\bdriver\b|\bwages\b/, "driver-wages"],
      [/\borapps\b|\besms\b|\bconveyance expense\b/, "claim-system"],
      [/\bguest house\b|\bcaretaker\b|\btulip\b|\bcentre point\b/, "guest-house"],
      [/\balcohol\b|\bcigarettes\b|\bmini-bar\b|\bweb check-in\b|\bspouse\b|\bdependent\b|\bseat\/class\b|\bupgrade\b/, "non-reimbursable-item"],
    ]),
    ruleType,
  ]);
}

function extractTopics(text: string, rule: StructuredPolicyRule) {
  const normalized = `${rule.section} ${rule.clause} ${text}`.toLowerCase();
  return unique([
    ...collectMatches(normalized, [
      [/\bedge cases?\b|director/, "edge-cases"],
      [/\blaundry\b/, "laundry"],
      [/\bflat rate\b|\bself arrangement\b/, "flat-rate"],
      [/\bsame-day\b|\bfreshen(?:ing)? up\b/, "same-day"],
      [/\bdelayed\b|\b3 hours\b/, "delay"],
      [/\bwomen employees\b|\bnext higher grade\b/, "women"],
      [/\bbooking\b|\bmybiz\b/, "booking"],
      [/\bapproval\b|\breporting manager\b/, "approval"],
      [/\bsettlement\b|\b16th day\b/, "settlement"],
      [/\banonymous\b/, "anonymous"],
      [/\bfalse\b|\bmalicious\b/, "false-complaint"],
      [/\bappeal\b/, "appeal"],
      [/\backnowledg/, "acknowledgement"],
      [/\binvestigation\b/, "investigation"],
      [/\boutcome\b|\bresolution\b/, "resolution"],
      [/\bpre-joining\b|\bpre joining\b/, "pre-joining"],
      [/\btemporary accommodation\b/, "temporary-accommodation"],
      [/\bbrokerage\b/, "brokerage"],
      [/\bhouse deposit\b/, "house-deposit"],
      [/\bhousehold goods\b|\bpackers\b/, "household-goods"],
      [/\brecovery\b|\bfull & final\b|\bfinal settlement\b/, "recovery"],
      [/\bdriver\b|\bwages\b/, "driver-wages"],
      [/\borapps\b|\besms\b|\bconveyance expense\b/, "claim-system"],
      [/\bguest house\b|\bcaretaker\b|\btulip\b|\bcentre point\b/, "guest-house"],
      [/\balcohol\b|\bcigarettes\b|\bmini-bar\b|\bweb check-in\b|\bspouse\b|\bdependent\b|\bseat\/class\b|\bupgrade\b/, "non-reimbursable-item"],
    ]),
    rule.ruleType,
  ]);
}

function buildRuleChunk(rule: StructuredPolicyRule, index: number): PolicyRuleChunk {
  const policy = getPolicyMeta(rule.policyId, rule.policyName);
  const combined = [
    rule.policyName,
    rule.section,
    rule.clause,
    rule.ruleType,
    ...rule.conditions,
    ...rule.keywords,
    ...rule.sampleQueries,
    rule.answer,
  ].join(" ");
  return {
    id: 1_000_000 + index,
    policyId: rule.policyId,
    policyName: policy.name,
    fileUrl: policy.fileUrl,
    pageNum: rule.page,
    text: rule.answer,
    tokens: tokenize(combined),
    isRuleChunk: true,
    ruleType: rule.ruleType,
    section: rule.section,
    clause: rule.clause,
    conditions: rule.conditions,
    canonicalAnswer: rule.answer,
    keywords: rule.keywords,
    sampleQueries: rule.sampleQueries,
    gradeTags: extractGradeTags(combined),
    cityClasses: extractCityClasses(combined),
    cityNames: extractCityNames(combined),
    metrics: extractMetrics(combined, rule.ruleType),
    topics: extractTopics(combined, rule),
  };
}

export const POLICY_RULE_CHUNKS: PolicyRuleChunk[] = STRUCTURED_POLICY_RULES.map(buildRuleChunk);
