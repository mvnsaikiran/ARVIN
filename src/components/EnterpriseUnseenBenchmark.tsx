import { useCallback, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { BarChart3, ChevronRight, Download, Play, ShieldCheck, Square, XCircle } from "lucide-react";
import {
  ENTERPRISE_UNSEEN_BENCHMARK_COUNT,
  ENTERPRISE_UNSEEN_BENCHMARK_SUITE,
  enterpriseFactHit,
  type EnterpriseUnseenGroup,
  type EnterpriseUnseenTest,
} from "../data/enterpriseUnseenBenchmarkSuite";
import { getEmployeeProfile } from "../services/employeeExperienceService";
import { resolveAssistantQuery } from "../services/assistantRuntime";

interface Result {
  test: EnterpriseUnseenTest;
  actual: string;
  actualPolicyId: string;
  actualPolicyName: string;
  actualSource: string;
  passed: boolean;
  usable: boolean;
  score: number;
  matchedFacts: string[];
  missedFacts: string[];
  durationMs: number;
  fromBenchmarkCache: boolean;
}

function toCsvCell(value: string | number | boolean | undefined) {
  return `"${String(value ?? "").replace(/"/g, '""').replace(/\r?\n/g, "\\n")}"`;
}

function looksLikeClarification(actual: string, source: string) {
  const text = actual.toLowerCase();
  return (
    source.toLowerCase().includes("triage") ||
    source.toLowerCase().includes("clarification") ||
    /\b(which|what exact|which exact|clarify|more detail|specific topic|choose|tell me one thing)\b/.test(text)
  );
}

function looksLikeRefusal(actual: string) {
  const text = actual.toLowerCase();
  return (
    /\bnot clearly\b/.test(text) ||
    /\bcould not find\b/.test(text) ||
    /\bnot found\b/.test(text) ||
    /\bnot covered\b/.test(text) ||
    /\bavailable .*policy documents\b/.test(text) ||
    /\bcontact .*buhr\b/.test(text) ||
    /\bhr confirmation\b/.test(text)
  );
}

function scoreResult(test: EnterpriseUnseenTest, actual: string, actualPolicyId: string, actualSource: string) {
  if (test.expectedBehavior === "clarify") {
    const passed = looksLikeClarification(actual, actualSource);
    return {
      passed,
      usable: passed,
      score: passed ? 100 : 0,
      matchedFacts: passed ? ["clarification behavior"] : [],
      missedFacts: passed ? [] : ["clarification behavior"],
    };
  }

  if (test.expectedBehavior === "refuse") {
    const passed = looksLikeRefusal(actual);
    return {
      passed,
      usable: passed,
      score: passed ? 100 : 0,
      matchedFacts: passed ? ["safe refusal"] : [],
      missedFacts: passed ? [] : ["safe refusal"],
    };
  }

  const matchedFacts = test.keyFacts.filter((fact) => enterpriseFactHit(actual, fact));
  const missedFacts = test.keyFacts.filter((fact) => !enterpriseFactHit(actual, fact));
  const factScore = test.keyFacts.length > 0 ? Math.round((matchedFacts.length / test.keyFacts.length) * 100) : 100;
  const policyScore = !test.policyId || actualPolicyId === test.policyId ? 100 : 0;
  const combinedScore = Math.round((factScore * 0.8) + (policyScore * 0.2));

  return {
    passed: factScore === 100 && policyScore === 100,
    usable: factScore >= 67 && policyScore === 100,
    score: combinedScore,
    matchedFacts,
    missedFacts,
  };
}

function pct(part: number, total: number) {
  return total > 0 ? ((part / total) * 100).toFixed(1) : "0.0";
}

export default function EnterpriseUnseenBenchmark({ onBack }: { onBack: () => void }) {
  const [results, setResults] = useState<Result[]>([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentQuery, setCurrentQuery] = useState("");
  const [batchSize, setBatchSize] = useState(ENTERPRISE_UNSEEN_BENCHMARK_COUNT);
  const [delayMs, setDelayMs] = useState(0);
  const abortRef = useRef(false);

  const strongPassed = results.filter((result) => result.passed).length;
  const usablePassed = results.filter((result) => result.usable).length;
  const policyCorrect = results.filter((result) => (
    !result.test.policyId || result.actualPolicyId === result.test.policyId
  )).length;
  const cacheHits = results.filter((result) => result.fromBenchmarkCache).length;

  const groupBreakdown = useMemo(() => {
    const groups: Record<EnterpriseUnseenGroup, { total: number; strong: number; usable: number }> = {
      answerable: { total: 0, strong: 0, usable: 0 },
      ambiguous: { total: 0, strong: 0, usable: 0 },
      unsupported: { total: 0, strong: 0, usable: 0 },
      adversarial: { total: 0, strong: 0, usable: 0 },
    };
    for (const result of results) {
      groups[result.test.group].total += 1;
      if (result.passed) groups[result.test.group].strong += 1;
      if (result.usable) groups[result.test.group].usable += 1;
    }
    return groups;
  }, [results]);

  const policyBreakdown = useMemo(() => {
    const rows: Record<string, { total: number; strong: number; usable: number }> = {};
    for (const result of results) {
      const key = result.test.source;
      if (!rows[key]) rows[key] = { total: 0, strong: 0, usable: 0 };
      rows[key].total += 1;
      if (result.passed) rows[key].strong += 1;
      if (result.usable) rows[key].usable += 1;
    }
    return Object.entries(rows).sort((a, b) => (a[1].strong / a[1].total) - (b[1].strong / b[1].total));
  }, [results]);

  const run = useCallback(async () => {
    abortRef.current = false;
    setRunning(true);
    setResults([]);
    setProgress(0);

    const tests = ENTERPRISE_UNSEEN_BENCHMARK_SUITE.slice(0, batchSize);
    const profile = getEmployeeProfile("local-user-001");
    const newResults: Result[] = [];

    for (let index = 0; index < tests.length; index += 1) {
      if (abortRef.current) break;
      const test = tests[index];
      setCurrentQuery(`[${index + 1}/${tests.length}] ${test.query.slice(0, 80)}`);
      setProgress(Math.round((index / tests.length) * 100));

      const startedAt = Date.now();
      try {
        const response = await resolveAssistantQuery({
          message: test.query,
          history: [],
          profile,
          language: "english",
          knowledgeAssets: [],
          precisionMode: false,
        });
        const durationMs = Date.now() - startedAt;
        const actual = response.text || "";
        const actualPolicyId = String(response.data?.policyId ?? "");
        const actualPolicyName = String(response.data?.policyName ?? "");
        const actualSource = String(response.data?.source ?? "");
        const scored = scoreResult(test, actual, actualPolicyId, actualSource);

        newResults.push({
          test,
          actual,
          actualPolicyId,
          actualPolicyName,
          actualSource,
          durationMs,
          fromBenchmarkCache: actualSource.toLowerCase().includes("benchmark canonical"),
          ...scored,
        });
      } catch (error) {
        newResults.push({
          test,
          actual: error instanceof Error ? error.message : "Unknown benchmark error",
          actualPolicyId: "",
          actualPolicyName: "",
          actualSource: "Benchmark runner error",
          passed: false,
          usable: false,
          score: 0,
          matchedFacts: [],
          missedFacts: test.keyFacts,
          durationMs: Date.now() - startedAt,
          fromBenchmarkCache: false,
        });
      }

      if ((index + 1) % 10 === 0 || index === tests.length - 1) {
        setResults([...newResults]);
      }
      if (delayMs > 0 && index < tests.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }

    setProgress(100);
    setCurrentQuery("");
    setRunning(false);
  }, [batchSize, delayMs]);

  const exportCSV = () => {
    const rows = [
      [
        "ID", "Group", "Category", "Subcategory", "Expected Behavior", "Expected Policy", "Actual Policy",
        "Query", "Expected Answer", "Chatbot Answer", "Strong Pass", "Usable Pass", "Score", "Matched Facts",
        "Missed Facts", "Duration Ms", "Benchmark Cache", "Actual Source", "Page",
      ],
      ...results.map((result) => [
        result.test.id,
        result.test.group,
        result.test.category,
        result.test.subcategory,
        result.test.expectedBehavior,
        result.test.source,
        result.actualPolicyName || result.actualPolicyId,
        result.test.query,
        result.test.expectedAnswer,
        result.actual,
        result.passed,
        result.usable,
        result.score,
        result.matchedFacts.join(", "),
        result.missedFacts.join(", "),
        result.durationMs,
        result.fromBenchmarkCache,
        result.actualSource,
        result.test.page ?? "",
      ].map(toCsvCell)),
    ];
    const csv = rows.map((row) => row.join(",")).join("\n");
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    anchor.download = `enterprise_unseen_benchmark_${results.length}_tests_${new Date().toISOString().split("T")[0]}.csv`;
    anchor.click();
  };

  const strongAccuracy = pct(strongPassed, results.length);
  const usableAccuracy = pct(usablePassed, results.length);
  const accuracyColor = Number(strongAccuracy) >= 95 ? "text-green-600" : Number(strongAccuracy) >= 85 ? "text-amber-600" : "text-red-600";

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg" aria-label="Back to chat">
            <ChevronRight className="w-4 h-4 text-slate-500 rotate-180" />
          </button>
          <div>
            <h1 className="font-semibold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Enterprise Unseen Benchmark
            </h1>
            <p className="text-xs text-slate-500">
              {ENTERPRISE_UNSEEN_BENCHMARK_COUNT.toLocaleString()} chunk-built non-cache cases: answerable, ambiguous, unsupported, and adversarial policy questions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {results.length > 0 && (
            <button onClick={exportCSV} className="flex items-center gap-2 px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
              <Download className="w-4 h-4" /> Export CSV
            </button>
          )}
          <div className="flex items-center gap-2 text-sm">
            <label className="text-slate-500">Tests:</label>
            <select value={batchSize} onChange={(event) => setBatchSize(Number(event.target.value))}
              disabled={running} className="border border-slate-200 rounded px-2 py-1 text-sm">
              <option value={100}>100</option>
              <option value={500}>500</option>
              <option value={1000}>1,000</option>
              <option value={2000}>2,000</option>
              <option value={ENTERPRISE_UNSEEN_BENCHMARK_COUNT}>All 5,000</option>
            </select>
            <label className="text-slate-500 ml-2">Delay:</label>
            <select value={delayMs} onChange={(event) => setDelayMs(Number(event.target.value))}
              disabled={running} className="border border-slate-200 rounded px-2 py-1 text-sm">
              <option value={0}>0ms</option>
              <option value={50}>50ms</option>
              <option value={100}>100ms</option>
              <option value={250}>250ms</option>
            </select>
          </div>
          {running ? (
            <button onClick={() => { abortRef.current = true; setRunning(false); }}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium">
              <Square className="w-4 h-4" /> Stop
            </button>
          ) : (
            <button onClick={run}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium">
              <Play className="w-4 h-4" /> {results.length > 0 ? "Re-run" : "Run"}
            </button>
          )}
        </div>
      </div>

      {running && (
        <div className="bg-white border-b px-6 py-3 flex-shrink-0">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span className="truncate max-w-3xl">{currentQuery}</span>
            <span className="font-medium text-emerald-600">{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5">
            <motion.div className="bg-emerald-600 h-1.5 rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.25 }} />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {results.length > 0 ? (
          <>
            <div className="grid grid-cols-6 gap-4 mb-6">
              <div className="col-span-1 bg-white border rounded-xl p-4 text-center">
                <div className={`text-4xl font-black ${accuracyColor}`}>{strongAccuracy}%</div>
                <div className="text-xs text-slate-500 mt-1">STRICT PASS</div>
              </div>
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-emerald-600">{usableAccuracy}%</div>
                <div className="text-xs text-slate-500">Usable Accuracy</div>
              </div>
              <div className="bg-white border rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-slate-800">{results.length}</div>
                <div className="text-xs text-slate-500">Tested</div>
              </div>
              <div className="bg-white border rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-slate-800">{pct(policyCorrect, results.length)}%</div>
                <div className="text-xs text-slate-500">Policy Routing</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{strongPassed}</div>
                <div className="text-xs text-slate-500">Strict Passed</div>
              </div>
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-indigo-600">{cacheHits}</div>
                <div className="text-xs text-slate-500">Benchmark Cache</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="bg-white border rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" /> Accuracy by Test Type
                </h3>
                <div className="space-y-3">
                  {Object.entries(groupBreakdown).map(([group, stats]) => (
                    <div key={group} className="flex items-center gap-3">
                      <div className="w-24 text-xs text-slate-600 font-medium capitalize">{group}</div>
                      <div className="flex-1 bg-slate-100 rounded-full h-2">
                        <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${pct(stats.strong, stats.total)}%` }} />
                      </div>
                      <div className="text-xs text-slate-500 w-32 text-right">
                        {stats.strong}/{stats.total} strict
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white border rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" /> Weakest Sources First
                </h3>
                <div className="space-y-2 max-h-52 overflow-y-auto pr-2">
                  {policyBreakdown.map(([source, stats]) => (
                    <div key={source} className="flex items-center gap-3">
                      <div className="w-44 text-xs text-slate-600 font-medium truncate">{source}</div>
                      <div className="flex-1 bg-slate-100 rounded-full h-2">
                        <div className="bg-sky-500 h-2 rounded-full" style={{ width: `${pct(stats.strong, stats.total)}%` }} />
                      </div>
                      <div className="text-xs text-slate-500 w-24 text-right">
                        {pct(stats.strong, stats.total)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white border rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">
                  Strict Failures ({results.filter((result) => !result.passed).length})
                </span>
                <span className="text-xs text-slate-500">These are the cases to inspect first before deployment.</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-[30rem] overflow-y-auto">
                {results.filter((result) => !result.passed).slice(0, 250).map((result) => (
                  <div key={result.test.id} className="px-4 py-3">
                    <div className="flex items-center gap-2 mb-1">
                      <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                      <span className="text-xs font-medium text-slate-500">
                        [{result.test.group}] {result.test.id} - {result.test.source}
                      </span>
                      <span className="text-xs text-red-500 font-bold">{result.score}%</span>
                      <span className="text-xs text-slate-400">{result.durationMs}ms</span>
                    </div>
                    <p className="text-sm text-slate-800 ml-5">{result.test.query}</p>
                    <p className="text-xs text-red-500 ml-5 mt-1">Missing: {result.missedFacts.join(", ") || "expected behavior"}</p>
                    <p className="text-xs text-slate-500 ml-5 mt-1">Actual source: {result.actualSource || result.actualPolicyName || "none"}</p>
                  </div>
                ))}
                {results.filter((result) => !result.passed).length === 0 && (
                  <div className="px-4 py-8 text-center text-green-600 font-semibold">
                    All enterprise unseen cases passed.
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-5">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Enterprise Unseen Benchmark</h3>
            <p className="text-slate-500 text-sm max-w-xl mb-4">
              This benchmark runs {ENTERPRISE_UNSEEN_BENCHMARK_COUNT.toLocaleString()} questions generated from the policy JSONL chunks, not paraphrased from the 7,000 set.
              It is designed to reveal real-world readiness, not memorized benchmark prompts.
            </p>
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-900 max-w-xl text-left">
              Split: 4,000 chunk-grounded answerable questions, 500 broad/ambiguous questions, 300 unsupported policy-gap questions,
              and 200 adversarial routing questions. The run uses live chatbot behavior with benchmark cache disabled.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
