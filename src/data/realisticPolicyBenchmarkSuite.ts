import { FULL_TEST_SUITE, type FullTest } from "./fullTestSuite";

const TARGET_TOTAL = 7000;
const EXCLUDED_SOURCES = new Set(["System"]);

const NATURAL_VARIANT_BUILDERS = [
  (query: string) => query,
  (query: string) => `${stripTerminalPunctuation(query)}`,
  (query: string) => `${normalizeSpaces(query.toLowerCase())}${ensureQuestionMark(query)}`,
  (query: string) => `As per Arvind policy, ${toQuestionBody(query)}?`,
  (query: string) => `Need clarity on ${toQuestionBody(query)}?`,
  (query: string) => `Can you confirm ${toQuestionBody(query)}?`,
  (query: string) => `Please explain ${toQuestionBody(query)}?`,
  (query: string) => `Quick check: ${toQuestionBody(query)}?`,
];

function normalizeSpaces(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function stripTerminalPunctuation(value: string): string {
  return normalizeSpaces(value).replace(/[?!.]+$/g, "");
}

function ensureQuestionMark(value: string): string {
  return /[?]$/.test(value.trim()) ? "" : "?";
}

function toQuestionBody(query: string): string {
  let value = stripTerminalPunctuation(query);
  value = value.replace(/^can you help me understand:\s*/i, "");
  value = value.replace(/^i want to know\s*/i, "");
  value = value.replace(/^according to company policy,\s*/i, "");
  value = value.replace(/^according to policy,\s*/i, "");
  value = value.replace(/^as per policy\s*/i, "");
  value = value.replace(/^please tell me\s*/i, "");
  return normalizeSpaces(value);
}

function buildRealisticVariant(baseQuery: string, variantIndex: number): string {
  const builder = NATURAL_VARIANT_BUILDERS[variantIndex % NATURAL_VARIANT_BUILDERS.length];
  const candidate = normalizeSpaces(builder(baseQuery));
  return candidate.endsWith("?") ? candidate : `${candidate}?`;
}

const BASE_SUITE = FULL_TEST_SUITE.filter((test) => !EXCLUDED_SOURCES.has(test.source));

function allocateExtras(totalNeeded: number, sourceCounts: Record<string, number>): Record<string, number> {
  const totalBase = Object.values(sourceCounts).reduce((sum, count) => sum + count, 0);
  const allocations: Record<string, number> = {};
  let assigned = 0;

  for (const [source, count] of Object.entries(sourceCounts)) {
    const raw = (count / totalBase) * totalNeeded;
    const floor = Math.floor(raw);
    allocations[source] = floor;
    assigned += floor;
  }

  let remaining = totalNeeded - assigned;
  const rankedRemainders = Object.entries(sourceCounts)
    .map(([source, count]) => ({
      source,
      remainder: ((count / totalBase) * totalNeeded) - (allocations[source] ?? 0),
    }))
    .sort((a, b) => b.remainder - a.remainder);

  for (const item of rankedRemainders) {
    if (remaining <= 0) break;
    allocations[item.source] += 1;
    remaining -= 1;
  }

  return allocations;
}

const SOURCE_COUNTS = BASE_SUITE.reduce<Record<string, number>>((acc, test) => {
  acc[test.source] = (acc[test.source] ?? 0) + 1;
  return acc;
}, {});

const EXTRA_COUNT = Math.max(0, TARGET_TOTAL - BASE_SUITE.length);
const EXTRA_ALLOCATIONS = allocateExtras(EXTRA_COUNT, SOURCE_COUNTS);

function buildExtraVariants(): FullTest[] {
  const grouped = Object.entries(
    BASE_SUITE.reduce<Record<string, FullTest[]>>((acc, test) => {
      (acc[test.source] ??= []).push(test);
      return acc;
    }, {}),
  );

  const extras: FullTest[] = [];

  for (const [source, tests] of grouped) {
    const allocation = EXTRA_ALLOCATIONS[source] ?? 0;
    for (let index = 0; index < allocation; index += 1) {
      const seed = tests[index % tests.length];
      const variantRound = Math.floor(index / tests.length) + 1;
      extras.push({
        ...seed,
        id: `${seed.id}-R${variantRound}-${(index % tests.length) + 1}`,
        query: buildRealisticVariant(seed.query, variantRound),
      });
    }
  }

  return extras;
}

const REALISTIC_SUITE = [...BASE_SUITE, ...buildExtraVariants()].slice(0, TARGET_TOTAL);

export const REALISTIC_POLICY_BENCHMARK_SUITE: FullTest[] = REALISTIC_SUITE.map((test, index) => ({
  ...test,
  id: `RP${String(index + 1).padStart(5, "0")}`,
}));

export const REALISTIC_POLICY_BENCHMARK_COUNT = REALISTIC_POLICY_BENCHMARK_SUITE.length;
