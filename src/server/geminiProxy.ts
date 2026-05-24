import { GoogleGenAI } from "@google/genai";

const PYTHON_BACKEND = process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8001";

export interface GeminiGenerateRequest {
  model?: string;
  contents: unknown[];
  config?: Record<string, unknown>;
}

export async function generateGeminiText(request: GeminiGenerateRequest): Promise<string> {
  if (!request || !Array.isArray(request.contents) || request.contents.length === 0) {
    throw new Error("Gemini request contents are required.");
  }

  // Route through Python RAG backend (ChromaDB retrieval + Gemini LLM)
  try {
    const res = await fetch(`${PYTHON_BACKEND}/api/claude/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents: request.contents, config: request.config ?? {} }),
    });
    if (res.ok) {
      const data = await res.json() as { text?: string };
      if (data.text) return data.text;
    }
  } catch {
    // Python backend unreachable — fall through to direct Gemini
  }

  // Fallback: call Gemini directly (keeps benchmark + chat working even if backend is down)
  const key = process.env.GEMINI_API_KEY || "";
  if (!key) throw new Error("GEMINI_API_KEY not set.");
  const ai = new GoogleGenAI({ apiKey: key });
  const response = await ai.models.generateContent({
    model: request.model || "gemini-2.0-flash",
    contents: request.contents as any,
    config: request.config as any,
  });
  return response.text ?? "";
}

export async function generateGeminiEmbedding(text: string): Promise<number[]> {
  if (!text) throw new Error("Text is required for embedding.");
  const key = process.env.GEMINI_API_KEY || "";
  if (!key) return [];
  const ai = new GoogleGenAI({ apiKey: key });
  const result = await ai.models.embedContent({
    model: "text-embedding-004",
    contents: text,
  });
  return result.embeddings?.[0]?.values ?? [];
}
