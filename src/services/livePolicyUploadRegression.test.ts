import { describe, expect, it } from "vitest";

import { getEmployeeProfile } from "./employeeExperienceService";
import { buildPolicyIdFromFileName, buildUploadedPolicyUrl } from "./policyIngestionService";
import { buildExtractiveAnswer } from "./productionRagService";
import { resolveAssistantQuery } from "./assistantRuntime";

describe("live policy upload regression", () => {
  it("builds stable ids and encoded URLs for uploaded policy files", () => {
    const fileName = "Leave & Attendance Policy_2026 - Corporate.pdf";

    expect(buildPolicyIdFromFileName(fileName)).toBe("leave-attendance-policy-2026-corporate");
    expect(buildUploadedPolicyUrl(fileName)).toBe("/uploaded-policies/Leave%20%26%20Attendance%20Policy_2026%20-%20Corporate.pdf");
  });

  it("keeps uploaded policy citations clickable in local extractive answers", () => {
    const response = buildExtractiveAnswer(
      "What is the leave carry-forward rule?",
      [
        {
          chunk: {
            id: 9001,
            policyId: "leave-attendance-policy-2026-corporate",
            policyName: "Leave & Attendance Policy 2026 - Corporate",
            fileUrl: "/uploaded-policies/Leave%20%26%20Attendance%20Policy_2026%20-%20Corporate.pdf",
            sourceDocumentName: "Leave & Attendance Policy_2026 - Corporate.pdf",
            pageNum: 4,
            section: "LEAVE CARRY FORWARD",
            chunkType: "rule",
            text: "Earned leave can be carried forward up to the policy limit stated in this section.",
            keywords: ["leave", "carry", "forward"],
          },
          rrfScore: 1,
          rerankScore: 88,
          matchedTerms: ["leave", "carry", "forward"],
        },
      ],
      { label: "ANSWERABLE", reason: "" },
    );

    expect(response.data?.policyUrl).toBe("/uploaded-policies/Leave%20%26%20Attendance%20Policy_2026%20-%20Corporate.pdf");
    expect(response.data?.citations?.[0]?.policyUrl).toBe("/uploaded-policies/Leave%20%26%20Attendance%20Policy_2026%20-%20Corporate.pdf");
    expect(response.data?.citations?.[0]?.sourceDocumentName).toBe("Leave & Attendance Policy_2026 - Corporate.pdf");
  });

  it("still routes policy questions through grounded retrieval in precision mode", async () => {
    const profile = getEmployeeProfile("local-user-001");

    const response = await resolveAssistantQuery({
      message: "Under the local conveyance policy, what is the two-wheeler reimbursement rate per km?",
      history: [],
      profile,
      language: "english",
      precisionMode: true,
    });

    expect(response.data?.policyId).toBe("local-conveyance");
    expect(response.text).toMatch(/Two-wheeler/i);
    expect(response.text).toMatch(/5\.00|Rs\.\s*5\.00/i);
  });
});
