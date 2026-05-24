/**
 * geminiProxy.ts — swapped from Gemini to Claude via Python RAG backend.
 * Request/response contract is identical so no frontend changes are needed.
 */

const PYTHON_BACKEND = process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8001";

export interface GeminiGenerateRequest {
  model?: string;
  contents: unknown[];
  config?: Record<string, unknown>;
}

export async function generateGeminiText(request: GeminiGenerateRequest): Promise<string> {
  if (!request || !Array.isArray(request.contents) || request.contents.length === 0) {
    throw new Error("Request contents are required.");
  }

  const response = await fetch(`${PYTHON_BACKEND}/api/claude/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: request.contents,
      config: request.config ?? {},
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Python backend error ${response.status}: ${err}`);
  }

  const data = await response.json() as { text?: string; error?: string };
  if (data.error) throw new Error(data.error);
  return data.text ?? "";
}

// Embeddings handled internally by the Python backend — not needed here.
export async function generateGeminiEmbedding(_text: string): Promise<number[]> {
  return [];
}
