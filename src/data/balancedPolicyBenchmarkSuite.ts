import { FULL_TEST_SUITE, type FullTest } from "./fullTestSuite";

export const BALANCED_POLICY_TARGETS = {
  "Domestic Travel Policy": 1600,
  "Talent Mobility Policy": 1000,
  "POSH Policy": 900,
  "Grievance Mechanism Policy": 800,
  "Joining Policy": 800,
  "Local Conveyance Policy": 700,
  "Whistleblower Policy": 600,
  "Gender Policy": 600,
} as const;

const QUERY_PREFIXES = [
  "",
  "Please explain ",
  "Need clarity on ",
  "As per policy ",
  "Can you clarify ",
  "I want to know ",
  "Tell me clearly ",
  "Help me understand ",
];

const QUERY_SUFFIXES = [
  "",
  " please",
  " in simple terms",
  " as per HR policy",
  " with policy reference",
  " for my understanding",
  " in brief",
  " in detail",
];

function normalizeSpaces(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function makeVariantQuery(baseQuery: string, variantIndex: number): string {
  const clean = normalizeSpaces(baseQuery).replace(/[?!.]+$/g, "");
  const prefix = QUERY_PREFIXES[variantIndex % QUERY_PREFIXES.length];
  const suffix = QUERY_SUFFIXES[Math.floor(variantIndex / QUERY_PREFIXES.length) % QUERY_SUFFIXES.length];
  return `${normalizeSpaces(`${prefix}${clean}${suffix}`)}?`;
}

function buildSourceSuite(source: keyof typeof BALANCED_POLICY_TARGETS): FullTest[] {
  const baseTests = FULL_TEST_SUITE.filter((test) => test.source === source);
  const targetCount = BALANCED_POLICY_TARGETS[source];

  if (baseTests.length >= targetCount) {
    return baseTests.slice(0, targetCount);
  }

  const tests: FullTest[] = [...baseTests];
  let extraIndex = 0;

  while (tests.length < targetCount) {
    const seed = baseTests[extraIndex % baseTests.length];
    const variantRound = Math.floor(extraIndex / baseTests.length) + 1;

    tests.push({
      ...seed,
      id: `${seed.id}-B${variantRound}-${(extraIndex % baseTests.length) + 1}`,
      query: makeVariantQuery(seed.query, variantRound),
    });

    extraIndex += 1;
  }

  return tests;
}

const BUILT_BALANCED_SUITE = [
  ...buildSourceSuite("Domestic Travel Policy"),
  ...buildSourceSuite("Talent Mobility Policy"),
  ...buildSourceSuite("POSH Policy"),
  ...buildSourceSuite("Grievance Mechanism Policy"),
  ...buildSourceSuite("Joining Policy"),
  ...buildSourceSuite("Local Conveyance Policy"),
  ...buildSourceSuite("Whistleblower Policy"),
  ...buildSourceSuite("Gender Policy"),
];

export const BALANCED_POLICY_BENCHMARK_SUITE: FullTest[] = BUILT_BALANCED_SUITE.map((test, index) => ({
  ...test,
  id: `BP${String(index + 1).padStart(5, "0")}`,
}));

export const BALANCED_POLICY_BENCHMARK_COUNT = BALANCED_POLICY_BENCHMARK_SUITE.length;
