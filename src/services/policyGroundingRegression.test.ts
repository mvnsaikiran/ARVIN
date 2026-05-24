import { describe, expect, it, vi } from "vitest";

vi.unmock("./geminiService");

import { getEmployeeProfile } from "./employeeExperienceService";
import { resolveAssistantQuery } from "./assistantRuntime";

async function ask(message: string) {
  const profile = getEmployeeProfile("local-user-001");

  return resolveAssistantQuery({
    message,
    history: [],
    profile,
    language: "english",
    precisionMode: false,
  });
}

describe("policy grounding regression", () => {
  it("returns the next gender-policy reporting level after BUHR", async () => {
    const response = await ask("Under the gender policy, who is the next reporting level after BUHR?");

    expect(response.data?.policyId).toBe("gender-policy");
    expect(response.text).toMatch(/Line Manager/i);
    expect(response.text).toMatch(/Source: Gender Policy, Page 3/i);
  });

  it("keeps the same-day return freshening-up exception", async () => {
    const response = await ask("Does the domestic travel policy allow hotel or guest-house use on a same-day return trip just for freshening up?");

    expect(response.data?.policyId).toBe("domestic-travel");
    expect(response.text).toMatch(/not eligible/i);
    expect(response.text).toMatch(/freshen(?:ing)? up/i);
  });

  it("grounds whistleblower anonymity questions in whistleblower evidence rules", async () => {
    const response = await ask("Under the whistleblower policy, can an anonymous concern still be taken up for investigation?");

    expect(response.data?.policyId).toBe("whistleblower");
    expect(response.text).toMatch(/reasonably clear and specific/i);
    expect(response.text).toMatch(/verifiable evidence/i);
  });

  it("returns the delayed-flight modification rule", async () => {
    const response = await ask("If a flight gets delayed by more than 3 hours, can I modify or cancel it through myBiz?");

    expect(response.data?.policyId).toBe("domestic-travel");
    expect(response.text).toMatch(/more than \*\*3 hours\*\*/i);
    expect(response.text).toMatch(/cancel or modify/i);
    expect(response.text).toMatch(/myBiz/i);
  });

  it("returns the joining recovery rule for exits within one year", async () => {
    const response = await ask("If someone resigns within one year after joining reimbursements are paid, what recovery applies in final settlement?");

    expect(response.data?.policyId).toBe("joining-policy");
    expect(response.text).toMatch(/within 1 year/i);
    expect(response.text).toMatch(/full\s*&?\s*final/i);
    expect(response.text).toMatch(/Joining Bonus/i);
  });

  it("returns notice pay buyout rules correctly when asking about previous organization settlement proof", async () => {
    const response = await ask("Do I need to submit my previous organization's full and final settlement proof to get my notice pay buyout released?");

    expect(response.data?.policyId).toBe("joining-policy");
    expect(response.text).toMatch(/Notice Pay Buyout/i);
    expect(response.text).toMatch(/submission of a Full & Final/i);
    expect(response.text).not.toMatch(/Travel claims should be settled within/i);
  });

  it("returns local conveyance per km rates correctly even when using the word claim", async () => {
    const response = await ask("How much can I claim per km for using my personal motorcycle vs my car for local client visits?");

    expect(response.data?.policyId).toBe("local-conveyance");
    expect(response.text).toMatch(/Two-wheeler/i);
    expect(response.text).toMatch(/Rs. 5.00/i);
    expect(response.text).toMatch(/Four-wheeler/i);
    expect(response.text).toMatch(/Rs. 10.00/i);
    expect(response.text).not.toMatch(/Local conveyance claims must be submitted in Orapps/i);
  });

  it("returns correct travel booking channel restriction even if flight mode is mentioned", async () => {
    const response = await ask("Can I book my flight on Yatra or booking.com and claim reimbursement later?");

    expect(response.data?.policyId).toBe("domestic-travel");
    expect(response.text).toMatch(/MakeMyTrip/i);
    expect(response.text).toMatch(/myBiz/i);
    expect(response.text).toMatch(/not be reimbursed/i);
    expect(response.text).not.toMatch(/For M2:/i);
  });

  it("returns talent mobility exceptions correctly instead of general rotation triggers", async () => {
    const response = await ask("Who can approve an exception to skip the mandatory job rotation under Track B?");

    expect(response.data?.policyId).toBe("talent-mobility");
    expect(response.text).toMatch(/CHRO/i);
    expect(response.text).toMatch(/CEO/i);
    expect(response.text).toMatch(/cannot block/i);
  });

  it("returns same-day travel guest house freshen-up rules correctly instead of guest house list", async () => {
    const response = await ask("I am returning on the same day from my official trip. Can I book a guest house just to freshen up?");

    expect(response.data?.policyId).toBe("domestic-travel");
    expect(response.text).toMatch(/not eligible/i);
    expect(response.text).toMatch(/freshen(?:ing)? up/i);
    expect(response.text).not.toMatch(/Tulip Part-2/i);
  });

  it("defers cross-policy queries to RAG instead of a single deterministic resolver", async () => {
    const response = await ask("Can I claim relocation travel as part of my joining or local conveyance?");

    expect(response.data?.source).not.toBe("Deterministic Policy Resolver");
    expect(response.text).toMatch(/reimburse/i);
  });
});
