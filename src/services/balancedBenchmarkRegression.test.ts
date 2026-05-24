import { describe, expect, it } from "vitest";

import { BALANCED_POLICY_BENCHMARK_SUITE } from "../data/balancedPolicyBenchmarkSuite";
import { getEmployeeProfile } from "./employeeExperienceService";
import { resolveAssistantQuery } from "./assistantRuntime";
import { resolveDeterministicPolicyAnswer } from "./deterministicPolicyResolver";
import { hybridPolicySearch, resolveProductionRagAnswer, applyCRAGReflection, buildExtractiveAnswer } from "./productionRagService";
import { formatTableChunkText } from "../data/policies";

const SOURCE_TO_POLICY_ID: Record<string, string> = {
  "Domestic Travel Policy": "domestic-travel",
  "Talent Mobility Policy": "talent-mobility",
  "POSH Policy": "posh-policy",
  "Grievance Mechanism Policy": "grievance-mechanism",
  "Joining Policy": "joining-policy",
  "Local Conveyance Policy": "local-conveyance",
  "Whistleblower Policy": "whistleblower",
  "Gender Policy": "gender-policy",
};

describe("balanced benchmark regression", () => {
  it(
    "returns the canonical answer for every balanced benchmark prompt in standard mode",
    async () => {
      const profile = getEmployeeProfile("local-user-001");
      const failures: Array<{ id: string; query: string; expectedPolicy: string; actualPolicy: string }> = [];

      for (const test of BALANCED_POLICY_BENCHMARK_SUITE) {
        const response = await resolveAssistantQuery({
          message: test.query,
          history: [],
          profile,
          language: test.language ?? "english",
          knowledgeAssets: test.knowledgeAssets ?? [],
          precisionMode: false,
        });

        const expectedPolicyId = SOURCE_TO_POLICY_ID[test.source] ?? "";
        const actualPolicyId = response.data?.policyId ?? "";

        if (actualPolicyId !== expectedPolicyId) {
          failures.push({
            id: test.id,
            query: test.query,
            expectedPolicy: expectedPolicyId,
            actualPolicy: actualPolicyId,
          });
        }
      }

      expect(
        failures,
        failures
          .slice(0, 10)
          .map((failure) => `${failure.id}: ${failure.query}\nexpected: ${failure.expectedPolicy} vs actual: ${failure.actualPolicy}`)
          .join("\n\n"),
      ).toEqual([]);
    },
    120000,
  );
});

describe("enterprise-grade robustness upgrades", () => {
  it("resolves queries with significant typos using the typo-tolerant deterministic resolver", () => {
    // "fligt dlay" -> cancellation/delay response
    const res1 = resolveDeterministicPolicyAnswer("what to do on a fligt dlay?");
    expect(res1).not.toBeNull();
    expect(res1?.data?.policyId).toBe("domestic-travel");
    expect(res1?.text).toContain("delay");

    // "lodgin limit for grade m2 in ahmedabad" -> travel allowances
    const res2 = resolveDeterministicPolicyAnswer("what is my lodgin limit for grade m2 in ahmedabad?");
    expect(res2).not.toBeNull();
    expect(res2?.data?.policyId).toBe("domestic-travel");
    expect(res2?.text).toContain("5000");

    // "ccltn" -> cancellation rules
    const res3 = resolveDeterministicPolicyAnswer("ccltn rule");
    expect(res3).not.toBeNull();
    expect(res3?.data?.policyId).toBe("domestic-travel");
  });

  it("applies context-aware hard partitioning correctly in hybridPolicySearch", async () => {
    // A query explicitly mentioning POSH should boost chunks from posh-policy.
    const poshChunks = await hybridPolicySearch("tell me about posh committee");
    const uniquePolicies = Array.from(new Set(poshChunks.map(c => c.chunk.policyId)));
    expect(uniquePolicies).toContain("posh-policy");
    expect(uniquePolicies.every(p => p === "posh-policy")).toBe(true);
  });

  it("formats raw text tables into beautiful markdown structured tables using formatTableChunkText", () => {
    const rawTable = "Grade  Class I  Class II\nBMH3  8000  6000\nM3  6000  5000";
    const formatted = formatTableChunkText(rawTable);
    expect(formatted).toContain("| Grade | Class I | Class II |");
    expect(formatted).toContain("| --- | --- | --- |");
    expect(formatted).toContain("| BMH3 | 8000 | 6000 |");
    expect(formatted).toContain("| M3 | 6000 | 5000 |");
  });

  it("triggers cross-policy synthesis when queries overlap across multiple policies", () => {
    const mockChunks = [
      {
        chunk: {
          id: 1,
          policyId: "joining-policy",
          policyName: "Joining Policy",
          fileUrl: "",
          pageNum: 2,
          section: "RELOCATION BENEFITS",
          text: "Packers and movers rate is 50 per km under 700 km.",
          tokens: [],
        },
        rrfScore: 1,
        rerankScore: 100,
        matchedTerms: [],
      },
      {
        chunk: {
          id: 2,
          policyId: "talent-mobility",
          policyName: "Talent Mobility Policy",
          fileUrl: "",
          pageNum: 4,
          section: "MAB ALLOWANCE",
          text: "The MAB allowance is paid for 12 months.",
          tokens: [],
        },
        rrfScore: 0.8,
        rerankScore: 90,
        matchedTerms: [],
      }
    ];

    const res = buildExtractiveAnswer("compare packages and mobility", mockChunks as any, { label: "ANSWERABLE", reason: "" });
    expect(res).not.toBeNull();
    expect(res?.data?.source).toBe("Cross-Policy Synthesizer");
    expect(res?.text).toContain("### 🌐 Cross-Policy Synthesized Information");
    expect(res?.text).toContain("Joining Policy");
    expect(res?.text).toContain("Talent Mobility Policy");
  });

  it("detects and self-corrects minor numerical hallucinations using CRAG Reflection", () => {
    const mockChunks = [
      {
        chunk: {
          id: 1,
          policyId: "domestic-travel",
          policyName: "Domestic Travel Policy",
          fileUrl: "",
          pageNum: 7,
          text: "The lodging limit for M1 in Class I cities is 3400 per day and boarding is 2300.",
          tokens: [],
        },
        rrfScore: 1,
        rerankScore: 1,
        matchedTerms: [],
      }
    ];

    const hallucinatedText = "The lodging limit for M1 is ₹3500 and boarding is ₹2300.";
    const correctedText = applyCRAGReflection(hallucinatedText, mockChunks as any);
    
    expect(correctedText).toContain("3400");
    expect(correctedText).not.toContain("3500");
  });
});
