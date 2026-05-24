import { GoogleGenAI } from "@google/genai";

export interface GeminiGenerateRequest {
  model?: string;
  contents: unknown[];
  config?: Record<string, unknown>;
}

let cachedClient: GoogleGenAI | null = null;
let cachedKey = "";

function getGeminiApiKey() {
  const key = process.env.GEMINI_API_KEY || "";
  if (!key) {
    throw new Error("GEMINI_API_KEY not set.");
  }
  return key;
}

function getGeminiClient() {
  const key = getGeminiApiKey();
  if (!cachedClient || cachedKey !== key) {
    cachedClient = new GoogleGenAI({ apiKey: key });
    cachedKey = key;
  }
  return cachedClient;
}

export async function generateGeminiText(request: GeminiGenerateRequest) {
  if (!request || !Array.isArray(request.contents) || request.contents.length === 0) {
    throw new Error("Gemini request contents are required.");
  }

  const response = await getGeminiClient().models.generateContent({
    model: request.model || "gemini-2.0-flash",
    contents: request.contents as any,
    config: request.config as any,
  });

  return response.text ?? "";
}

export async function generateGeminiEmbedding(text: string) {
  if (!text) {
    throw new Error("Text is required for embedding.");
  }
  const result = await getGeminiClient().models.embedContent({
    model: "text-embedding-004",
    contents: text,
  });
  return result.embeddings?.[0]?.values ?? [];
}
