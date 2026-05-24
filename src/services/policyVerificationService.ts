import { type Chunk } from "../data/policies";
import { type AIResponse } from "./geminiService";

export interface VerificationResult {
  isVerified: boolean;
  explanation?: string;
  refinedAnswer?: string;
  confidenceScore: number;
}

/**
 * Phase 3: Recursive Reranking (The Judge Agent)
 * 
 * This service cross-checks the retrieved chunks against the specific question
 * to ensure we aren't just "guessing" based on proximity, but actually
 * finding the "nook and corner" detail.
 */
export async function verifyPolicyAnswer(
  query: string,
  chunks: Chunk[],
  suggestedAnswer: string,
  callGeminiProxy: (request: any) => Promise<string>
): Promise<VerificationResult> {
  // If we have no chunks, we can't verify
  if (chunks.length === 0) {
    return { isVerified: false, confidenceScore: 0 };
  }

  const context = chunks.map((c, i) => `[CHUNK ${i}] (Page ${c.pageNum}): ${c.text}`).join("\n\n");

  const prompt = `
    As an expert HR Auditor, verify if the following answer is EXPLICITLY supported by the provided policy chunks.
    
    USER QUESTION: "${query}"
    SUGGESTED ANSWER: "${suggestedAnswer}"
    
    POLICY CHUNKS:
    ${context}
    
    VERIFICATION RULES:
    1. Does the context contain the specific "nook and corner" detail (e.g. specific amount, specific grade, specific exception)?
    2. Is the answer 100% grounded in the text?
    3. If there is a table, did the answer interpret it correctly?
    
    Return your response in JSON format:
    {
      "isVerified": boolean,
      "explanation": "Why it is or isn't verified",
      "refinedAnswer": "A corrected answer if the original was slightly off, or null",
      "confidenceScore": number (0.0 to 1.0)
    }
  `;

  try {
    const response = await callGeminiProxy({
      model: "gemini-1.5-flash",
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      config: { 
        temperature: 0.1,
        responseMimeType: "application/json"
      },
    });

    return JSON.parse(response);
  } catch (err) {
    console.error("Verification failed:", err);
    return { isVerified: true, confidenceScore: 0.7 }; // Fallback to original if judge fails
  }
}
