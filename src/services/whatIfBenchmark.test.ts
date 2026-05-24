import { describe, expect, it } from "vitest";
import { resolveDeterministicPolicyAnswer } from "./deterministicPolicyResolver";

describe("what-if scenarios & override rules benchmark", () => {
  it("resolves the Grade Promotion scenario with 100% accuracy", () => {
    const queries = [
      "What if I get promoted from M1 to M2? What is my lodging limit in Mumbai?",
      "If I am promoted from M1 to M2, what is my hotel stay limit in Mumbai?",
      "What is the lodging limit for a promoted M1 to M2 employee in Mumbai?",
      "What is my hotel limit in Mumbai if my grade changes from M1 to M2?",
    ];

    for (const query of queries) {
      const response = resolveDeterministicPolicyAnswer(query);
      expect(response).not.toBeNull();
      expect(response?.data?.policyId).toBe("domestic-travel");
      expect(response?.text).toContain("6,000");
      expect(response?.text).toContain("3,400");
      expect(response?.text).toContain("5,000"); // for Class II
    }
  });

  it("resolves the Joint/Combined Travel scenario with 100% accuracy", () => {
    const queries = [
      "What if an M1 employee travels jointly with a BMH9 director? What is their hotel stay limit in Mumbai?",
      "What is my lodging limit if I am M1 travelling with a BMH9 manager?",
      "What is the hotel limit for M1 travelling together with BMH9?",
      "If an M1 employee goes on combined travel with BMH9, what is the lodging entitlement?",
    ];

    for (const query of queries) {
      const response = resolveDeterministicPolicyAnswer(query);
      expect(response).not.toBeNull();
      expect(response?.data?.policyId).toBe("domestic-travel");
      expect(response?.text).toContain("At Actual");
    }
  });

  it("resolves the Same-Day Return scenario with 100% accuracy", () => {
    const queries = [
      "What if I return on the same day? Am I eligible for hotel lodging reimbursement?",
      "Am I eligible for hotel reimbursement for same-day return travel?",
      "Does the travel policy reimburse hotel stays for same day return?",
      "What is the accommodation eligibility for same-day return trips?",
    ];

    for (const query of queries) {
      const response = resolveDeterministicPolicyAnswer(query);
      expect(response).not.toBeNull();
      expect(response?.data?.policyId).toBe("domestic-travel");
      expect(response?.text).toContain("not eligible");
      expect(response?.text).toContain("freshening up");
    }
  });

  it("resolves the Ethics vs. HR Line scenario with 100% accuracy", () => {
    const queries = [
      "What if my supervisor is engaging in fraud? How should I report it?",
      "How do I report supervisor fraud?",
      "What is the procedure if I want to report a manager for illegal activity or fraud?",
      "Should I report my manager's ethical fraud to HR?",
    ];

    for (const query of queries) {
      const response = resolveDeterministicPolicyAnswer(query);
      expect(response).not.toBeNull();
      expect(response?.data?.policyId).toBe("whistleblower");
      expect(response?.text).toContain("Whistleblower Policy");
      expect(response?.text).toContain("Non-Retaliation Policy");
      expect(response?.text).toContain("KPMG");
    }
  });
});
