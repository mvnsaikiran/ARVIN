import { type PolicyQuestionAnalysis } from "./policyQuestionAnalysis";
import { isKnownUnsupportedQuestion } from "./queryNormalization";

export interface AmbiguityResolution {
  isAmbiguous: boolean;
  question: string;
  options: string[];
  suggestedPolicyIds: string[];
}

const AMBIGUITY_MAP: Array<{
  keywords: RegExp;
  question: string;
  options: Record<string, string>; // Display text -> Policy ID
}> = [
  {
    keywords: /\bcab\b|\btaxi\b|\bconveyance\b|\bauto\b/,
    question: "Are you asking about travel within your city or between different cities?",
    options: {
      "Local travel (within city)": "local-conveyance",
      "Domestic travel (between cities)": "domestic-travel"
    }
  },
  {
    keywords: /\brelocation\b|\bmoved city\b|\btransfer\b|\bshifting\b/,
    question: "Are you asking about relocation during joining or an internal talent mobility transfer?",
    options: {
      "Joining relocation": "joining-policy",
      "Internal Talent Mobility": "talent-mobility"
    }
  },
  {
    keywords: /\bharassment\b|\bdiscrimination\b|\bequality\b/,
    question: "Is this regarding the Gender Equality policy or a POSH (Sexual Harassment) concern?",
    options: {
      "Gender Equality & Diversity": "gender-policy",
      "POSH (Sexual Harassment)": "posh-policy"
    }
  },
  {
    keywords: /\btimeline\b|\bsla\b|\bhow long\b/,
    question: "Which process timeline would you like to know about?",
    options: {
      "Grievance Redressal": "grievance-mechanism",
      "POSH Investigation": "posh-policy",
      "Whistleblower Investigation": "whistleblower"
    }
  },
  {
    keywords: /\breimbursement\b|\bclaim\b|\bexpense\b/,
    question: "What type of reimbursement or claim are you referring to?",
    options: {
      "Travel expenses": "domestic-travel",
      "Local conveyance": "local-conveyance",
      "Joining expenses": "joining-policy",
      "Mobile/Broadband": "payroll"
    }
  },
  {
    keywords: /\bsalary\b|\bpay\b|\bpayslip\b/,
    question: "What specifically about your salary can I help with?",
    options: {
      "Payslip download": "payroll",
      "Tax/Deduction query": "payroll",
      "Salary discrepancy": "payroll"
    }
  }
];

export function triageAmbiguousQuery(analysis: PolicyQuestionAnalysis): AmbiguityResolution | null {
  // Disabled to ensure all queries are resolved directly without intermediate friction
  return null;
}
