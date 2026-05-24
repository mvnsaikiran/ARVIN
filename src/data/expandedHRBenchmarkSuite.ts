import type { FullTest } from "./fullTestSuite";
import { BALANCED_POLICY_BENCHMARK_SUITE } from "./balancedPolicyBenchmarkSuite";
import { ENTERPRISE_CAPABILITY_BENCHMARK_SUITE } from "./enterpriseCapabilityBenchmarkSuite";

export const EXPANDED_HR_BENCHMARK_SUITE: FullTest[] = [
  ...BALANCED_POLICY_BENCHMARK_SUITE,
  ...ENTERPRISE_CAPABILITY_BENCHMARK_SUITE,
];

export const EXPANDED_HR_BENCHMARK_COUNT = EXPANDED_HR_BENCHMARK_SUITE.length;
