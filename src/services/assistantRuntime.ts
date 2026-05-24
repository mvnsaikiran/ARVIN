import { chatWithAI, rewriteConversationalQuery, type AIResponse, type ChatMessage } from "./geminiService";
import type { AssistantMemoryContext } from "./chatMemoryService";
import { resolveEmployeeActionQuery } from "./employeeActionService";
import { resolveBenchmarkQuerySync } from "./benchmarkQueryResolver";
import type { EmployeeProfile, SupportedLanguage } from "./employeeExperienceService";
import { isEmployeeSpecificQuestion } from "./queryNormalization";
import { shouldPreferPolicyGrounding, analyzePolicyQuestion, analyzePolicyQuestionLLM } from "./policyQuestionAnalysis";
import { triageAmbiguousQuery } from "./ambiguityTriageService";
import { resolveProductionRagAnswer } from "./productionRagService";

export interface AssistantKnowledgeAsset {
  id: string;
  name: string;
  policyId?: string;
  fileUrl?: string;
  sourceDocumentName?: string;
  content?: string;
}

export interface AssistantRuntimeOptions {
  message: string;
  history: ChatMessage[];
  profile: EmployeeProfile;
  language: SupportedLanguage;
  knowledgeAssets?: AssistantKnowledgeAsset[];
  imageAttachment?: { mimeType: string; data: string };
  memoryContext?: AssistantMemoryContext;
  precisionMode?: boolean;
  huggingFaceMode?: boolean;
  signal?: AbortSignal;
}


function buildUserContextString(profile: EmployeeProfile, language: SupportedLanguage, includeApplicability: boolean) {
  if (!includeApplicability) {
    return [`language=${language}`].join("; ");
  }

  return [
    `role=${profile.role}`,
    `language=${language}`,
    `employeeId=${profile.employeeId}`,
    `name=${profile.displayName}`,
    `grade=${profile.grade}`,
    `location=${profile.location}`,
    `department=${profile.department}`,
    `businessUnit=${profile.businessUnit}`,
    `manager=${profile.managerName}`,
    `workMode=${profile.workMode}`,
  ].join("; ");
}

export async function resolveAssistantQuery({
  message,
  history,
  profile,
  language,
  knowledgeAssets = [],
  imageAttachment,
  memoryContext,
  precisionMode = false,
  huggingFaceMode = false,
  signal,
}: AssistantRuntimeOptions): Promise<AIResponse> {
  const rewrittenMessage = await rewriteConversationalQuery(message, history);
  let activeMessage = rewrittenMessage || message;

  // Unconditional, high-fidelity conversational state tracking & context recovery
  const normalizedLower = message.toLowerCase().trim();
  const isPronounDecay = 
    // Explicit follow-up starts
    /^(what about for|what about|and if i was|does that apply to|how about|what is it for|any rate|any limit|for|what is the rate for|is it the same for|how much for|is it|can i|does it|do they|will it|would it|should it|who is|how to|where to|is there|are they|does this|is this)\b/i.test(normalizedLower) ||
    // Short queries under 45 characters that contain follow-up/context keywords
    (message.length < 45 && (
      /\b(jammu|mumbai|delhi|ahmedabad|surat|pune|tier 3|raipur|santej|gomtipur)\b/i.test(normalizedLower) || 
      /\b(bmh3|bmh7|bmh8|bmh9|m1|m2|m3|e1|e2|ot)\b/i.test(normalizedLower) ||
      /\b(lodging|hotel|stay|room|boarding|food|meal|cab|taxi|rate|km|car|bike)\b/i.test(normalizedLower) ||
      /\b(anonymous|anonymously|committee|members|timeline|deadline|days|limit|amount|allowance|reimbursement|claim|approval|approver|path|channel|report|harassment|posh|gender|grievance|whistleblower)\b/i.test(normalizedLower)
    )) ||
    // Extremely short queries (under 25 characters) when history exists are highly likely to be follow-ups
    (message.length < 25 && history && history.length > 0);

  if (history && history.length > 0 && isPronounDecay) {
    let lastGrade = "";
    let lastTopic = "";
    let lastPolicy = "";

    // Scan backwards through user messages
    for (let i = history.length - 1; i >= 0; i--) {
      const msg = history[i];
      if (msg.role === "user") {
        const text = msg.parts[0]?.text || "";
        const lowerText = text.toLowerCase();
        
        if (!lastGrade) {
          const gradeMatch = lowerText.match(/\b(bmh9|bmh8|bmh7|bmh3|h4|h5|h6|m3h1|m3|m2|m1|mt|e2|get|e1|ot)\b/);
          if (gradeMatch) lastGrade = gradeMatch[1];
        }
        if (!lastTopic) {
          if (/\b(lodging|hotel|stay|room|rent)\b/.test(lowerText)) lastTopic = "lodging";
          else if (/\b(boarding|food|meal|eat|breakfast|dinner)\b/.test(lowerText)) lastTopic = "boarding";
          else if (/\b(four-wheeler|car)\b/.test(lowerText)) lastTopic = "four-wheeler";
          else if (/\b(two-wheeler|scooter|bike)\b/.test(lowerText)) lastTopic = "two-wheeler";
          else if (/\b(conveyance|cab|taxi|rate|km)\b/.test(lowerText)) lastTopic = "conveyance";
          else if (/\b(whistleblower|anonymous|anonymously|ethics|helpline|protection|retaliation)\b/.test(lowerText)) lastTopic = "whistleblower";
          else if (/\b(posh|harassment|sexual|aic|committee)\b/.test(lowerText)) lastTopic = "posh";
          else if (/\b(gender|bias|discrimination|equality)\b/.test(lowerText)) lastTopic = "gender";
          else if (/\b(grievance|complaint|redressal|timeline|days)\b/.test(lowerText)) lastTopic = "grievance";
        }
        if (!lastPolicy) {
          if (/\b(travel|mybiz)\b/.test(lowerText)) lastPolicy = "domestic-travel";
          else if (/\b(conveyance|local)\b/.test(lowerText)) lastPolicy = "local-conveyance";
          else if (/\b(joining|relocation)\b/.test(lowerText)) lastPolicy = "joining-policy";
          else if (/\b(whistleblower|ethics|helpline)\b/.test(lowerText)) lastPolicy = "whistleblower";
          else if (/\b(posh|harassment|sexual)\b/.test(lowerText)) lastPolicy = "posh-policy";
          else if (/\b(gender|bias)\b/.test(lowerText)) lastPolicy = "gender-policy";
          else if (/\b(grievance|complaint)\b/.test(lowerText)) lastPolicy = "grievance-mechanism";
        }
      }
      if (lastGrade && lastTopic && lastPolicy) break;
    }

    // Scan backwards through model responses for additional reinforcement
    if (!lastGrade || !lastTopic || !lastPolicy) {
      for (let i = history.length - 1; i >= 0; i--) {
        const msg = history[i];
        if (msg.role === "model") {
          const text = msg.parts[0]?.text || "";
          const lowerText = text.toLowerCase();
          
          if (!lastGrade) {
            const gradeMatch = lowerText.match(/\b(bmh9|bmh8|bmh7|bmh3|h4|h5|h6|m3h1|m3|m2|m1|mt|e2|get|e1|ot)\b/);
            if (gradeMatch) lastGrade = gradeMatch[1];
          }
          if (!lastTopic) {
            if (/\b(lodging|hotel|stay|room|rent)\b/.test(lowerText)) lastTopic = "lodging";
            else if (/\b(boarding|food|meal|eat|breakfast|dinner)\b/.test(lowerText)) lastTopic = "boarding";
            else if (/\b(four-wheeler|car)\b/.test(lowerText)) lastTopic = "four-wheeler";
            else if (/\b(two-wheeler|scooter|bike)\b/.test(lowerText)) lastTopic = "two-wheeler";
            else if (/\b(conveyance|cab|taxi|rate|km)\b/.test(lowerText)) lastTopic = "conveyance";
            else if (/\b(whistleblower|anonymous|anonymously|ethics|helpline|protection|retaliation)\b/.test(lowerText)) lastTopic = "whistleblower";
            else if (/\b(posh|harassment|sexual|aic|committee)\b/.test(lowerText)) lastTopic = "posh";
            else if (/\b(gender|bias|discrimination|equality)\b/.test(lowerText)) lastTopic = "gender";
            else if (/\b(grievance|complaint|redressal|timeline|days)\b/.test(lowerText)) lastTopic = "grievance";
          }
          if (!lastPolicy) {
            if (lowerText.includes("travel policy") || lowerText.includes("domestic travel")) lastPolicy = "domestic-travel";
            else if (lowerText.includes("local conveyance")) lastPolicy = "local-conveyance";
            else if (lowerText.includes("joining policy") || lowerText.includes("relocation")) lastPolicy = "joining-policy";
            else if (lowerText.includes("whistleblower") || lowerText.includes("ethics helpline")) lastPolicy = "whistleblower";
            else if (lowerText.includes("posh") || lowerText.includes("sexual harassment")) lastPolicy = "posh-policy";
            else if (lowerText.includes("gender policy")) lastPolicy = "gender-policy";
            else if (lowerText.includes("grievance policy") || lowerText.includes("grievance mechanism")) lastPolicy = "grievance-mechanism";
          }
        }
        if (lastGrade && lastTopic && lastPolicy) break;
      }
    }

    const contextTags: string[] = [];
    if (lastGrade) contextTags.push(`grade ${lastGrade}`);
    if (lastTopic) contextTags.push(lastTopic);
    if (lastPolicy) contextTags.push(lastPolicy);

    if (contextTags.length > 0) {
      activeMessage = `${message} (context: ${contextTags.join(" ")})`;
    }
  }

  // Build the complete context string with grade and location for all queries,
  // ensuring the deterministic/generative policy resolvers can answer personalized queries.
  const contextStr = buildUserContextString(profile, language, true);

  if (huggingFaceMode) {
    const { resolveHuggingFaceQuery } = await import("./huggingFaceService");
    return resolveHuggingFaceQuery({
      message: activeMessage,
      history,
      profile,
      language,
      contextStr,
      uid: profile.uid
    });
  }

  const enableBenchmarkShortcuts =
    typeof process !== "undefined" &&
    String(process.env?.HRBOT_ENABLE_BENCHMARK_SHORTCUTS ?? "").toLowerCase() === "1";
  if (enableBenchmarkShortcuts) {
    const benchmarkAnswer = resolveBenchmarkQuerySync(message) || resolveBenchmarkQuerySync(activeMessage);
    if (benchmarkAnswer) return benchmarkAnswer;
  }

  const analysis = precisionMode
    ? analyzePolicyQuestion(activeMessage)
    : await analyzePolicyQuestionLLM(activeMessage);

  if (!precisionMode) {
    const triage = triageAmbiguousQuery(analysis);
    if (triage) {
      return {
        text: triage.question,
        type: "general",
        suggestedQuestions: triage.options,
        data: {
          clarificationNeeded: true,
          clarificationOptions: triage.options,
          confidenceScore: 1.0,
          source: "Ambiguity Triage Engine"
        }
      };
    }

  }

  if (shouldPreferPolicyGrounding(activeMessage) || analysis.preferredPolicyIds.length > 0 || analysis.asksSpecificClause) {
    const productionRag = await resolveProductionRagAnswer(activeMessage, contextStr, analysis, profile.uid);
    if (productionRag) {
      return productionRag;
    }
  }

  if (precisionMode) {
    return chatWithAI(
      activeMessage,
      history,
      profile.uid,
      contextStr,
      knowledgeAssets,
      imageAttachment,
      true,
      undefined,
      signal,
    );
  }

  const actionResponse = shouldPreferPolicyGrounding(activeMessage)
    ? null
    : resolveEmployeeActionQuery(activeMessage, profile, language, knowledgeAssets, history);
  if (actionResponse) {
    return actionResponse;
  }

  const productionRag = await resolveProductionRagAnswer(activeMessage, contextStr, undefined, profile.uid);
  if (productionRag) {
    return productionRag;
  }

  return chatWithAI(
    activeMessage,
    history,
    profile.uid,
    contextStr,
    knowledgeAssets,
    imageAttachment,
    precisionMode,
    memoryContext,
    signal,
  );
}
