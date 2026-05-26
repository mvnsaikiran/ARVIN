// Stub — full test suite is generated locally and not committed to the repo.
// The chatbot runtime does not need this data; only benchmark scripts use it.

export interface FullTest {
  id: string;
  query: string;
  exactAnswer: string;
  keyFacts: string[];
  source: string;
  page: number;
  category: string;
  subcategory: string;
  userUid?: string;
  language?: "english" | "hindi" | "gujarati";
  knowledgeAssets?: { id: string; name: string; content?: string }[];
}

export const FULL_TEST_SUITE: FullTest[] = [];
