/**
 * Full Benchmark Runner — 6419 test cases
 * Runs in batches with rate limiting to avoid API quota
 */
import React, { useState, useRef, useCallback } from "react";
import { motion } from "motion/react";
import { Play, Square, Download, CheckCircle, XCircle, BarChart3, ChevronRight } from "lucide-react";
import { EXPANDED_HR_BENCHMARK_SUITE, EXPANDED_HR_BENCHMARK_COUNT } from "../data/expandedHRBenchmarkSuite";
import type { FullTest } from "../data/fullTestSuite";
import { resolveAssistantQuery } from "../services/assistantRuntime";
import { getEmployeeProfile } from "../services/employeeExperienceService";

interface Result {
  test: FullTest;
  actual: string;
  passed: boolean;
  score: number;
  matchedFacts: string[];
  missedFacts: string[];
  durationMs: number;
  fromCache: boolean;
}

function scoreResult(actual: string, keyFacts: string[]) {
  const low = actual.toLowerCase();
  const matched = keyFacts.filter(f => low.includes(f.toLowerCase()));
  const missed = keyFacts.filter(f => !low.includes(f.toLowerCase()));
  const score = keyFacts.length > 0 ? Math.round((matched.length / keyFacts.length) * 100) : 100;
  return { passed: score >= 60, matched, missed, score };
}

function toCsvCell(value: string | number) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

export default function FullBenchmark({ onBack }: { onBack: () => void }) {
  const [results, setResults] = useState<Result[]>([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentQuery, setCurrentQuery] = useState("");
  const [batchSize, setBatchSize] = useState(100);
  const [delayMs, setDelayMs] = useState(300);
  const abortRef = useRef(false);

  const passed = results.filter(r => r.passed).length;
  const accuracy = results.length > 0 ? (passed / results.length * 100).toFixed(1) : "0";

  // Category breakdown
  const byCategory: Record<string, { total: number; passed: number }> = {};
  for (const r of results) {
    const cat = r.test.category;
    if (!byCategory[cat]) byCategory[cat] = { total: 0, passed: 0 };
    byCategory[cat].total++;
    if (r.passed) byCategory[cat].passed++;
  }

  const run = useCallback(async () => {
    abortRef.current = false;
    setRunning(true);
    setResults([]);
    setProgress(0);

    const tests = EXPANDED_HR_BENCHMARK_SUITE.slice(0, batchSize);
    const newResults: Result[] = [];

    for (let i = 0; i < tests.length; i++) {
      if (abortRef.current) break;
      const test = tests[i];
      setCurrentQuery(`[${i + 1}/${tests.length}] ${test.query.slice(0, 60)}`);
      setProgress(Math.round((i / tests.length) * 100));

      const t0 = Date.now();
      try {
        const resp = await resolveAssistantQuery({
          message: test.query,
          history: [],
          profile: getEmployeeProfile(test.userUid ?? "local-user-001"),
          language: test.language ?? "english",
          knowledgeAssets: test.knowledgeAssets ?? [],
          precisionMode: true,
        });
        const dur = Date.now() - t0;
        const actual = resp.text || "";
        const { passed, matched, missed, score } = scoreResult(actual, test.keyFacts);
        const fromCache = dur < 50 && actual.length > 50; // cache = instant response

        newResults.push({ test, actual, passed, score, matchedFacts: matched, missedFacts: missed, durationMs: dur, fromCache });
      } catch (e: any) {
        newResults.push({
          test, actual: "", passed: false, score: 0,
          matchedFacts: [], missedFacts: test.keyFacts, durationMs: Date.now() - t0, fromCache: false,
        });
      }

      setResults([...newResults]);
      if (i < tests.length - 1) await new Promise(r => setTimeout(r, delayMs));
    }

    setRunning(false);
    setProgress(100);
    setCurrentQuery("");
  }, [batchSize, delayMs]);

  const exportCSV = () => {
    const rows = [
      ["ID","Category","Subcategory","Query","Policy","Expected Answer","Chatbot Answer","Status","Score","Matched Facts","Missed Facts","Duration (ms)","From Cache","Source","Page"],
      ...results.map(r => [
        toCsvCell(r.test.id),
        toCsvCell(r.test.category),
        toCsvCell(r.test.subcategory),
        toCsvCell(r.test.query),
        toCsvCell(r.test.source),
        toCsvCell(r.test.exactAnswer),
        toCsvCell(r.actual),
        r.passed ? "PASS" : "FAIL",
        r.score,
        toCsvCell(r.matchedFacts.join(", ")),
        toCsvCell(r.missedFacts.join(", ")),
        r.durationMs,
        r.fromCache ? "YES" : "NO",
        toCsvCell(r.test.source),
        r.test.page,
      ])
    ];
    const csv = rows.map(r => r.join(",")).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `full_benchmark_${batchSize}_tests_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  const accColor = Number(accuracy) >= 95 ? "text-green-600" : Number(accuracy) >= 85 ? "text-amber-600" : "text-red-600";

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg">
            <ChevronRight className="w-4 h-4 text-slate-500 rotate-180" />
          </button>
          <div>
            <h1 className="font-semibold text-slate-900">Expanded HR Benchmark Suite</h1>
            <p className="text-xs text-slate-500">{EXPANDED_HR_BENCHMARK_COUNT.toLocaleString()} total test cases across policy and enterprise HR capability flows</p>
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
            <select value={batchSize} onChange={e => setBatchSize(Number(e.target.value))}
              disabled={running} className="border border-slate-200 rounded px-2 py-1 text-sm">
              <option value={100}>100</option>
              <option value={500}>500</option>
              <option value={1000}>1,000</option>
              <option value={2000}>2,000</option>
              <option value={7000}>First 7,000</option>
              <option value={EXPANDED_HR_BENCHMARK_COUNT}>All {EXPANDED_HR_BENCHMARK_COUNT.toLocaleString()}</option>
            </select>
            <label className="text-slate-500 ml-2">Delay:</label>
            <select value={delayMs} onChange={e => setDelayMs(Number(e.target.value))}
              disabled={running} className="border border-slate-200 rounded px-2 py-1 text-sm">
              <option value={200}>200ms (faster)</option>
              <option value={300}>300ms (safe)</option>
              <option value={500}>500ms (slow)</option>
            </select>
          </div>
          {running ? (
            <button onClick={() => { abortRef.current = true; setRunning(false); }}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium">
              <Square className="w-4 h-4" /> Stop
            </button>
          ) : (
            <button onClick={run}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium">
              <Play className="w-4 h-4" /> {results.length > 0 ? "Re-run" : "Run"}
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      {running && (
        <div className="bg-white border-b px-6 py-3 flex-shrink-0">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span className="truncate max-w-xl">{currentQuery}</span>
            <span className="font-medium text-indigo-600">{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5">
            <motion.div className="bg-indigo-600 h-1.5 rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {/* Stats */}
        {results.length > 0 && (
          <>
            <div className="grid grid-cols-5 gap-4 mb-6">
              <div className="col-span-1 bg-white border rounded-xl p-4 text-center">
                <div className={`text-4xl font-black ${accColor}`}>{accuracy}%</div>
                <div className="text-xs text-slate-500 mt-1">ACCURACY</div>
              </div>
              <div className="bg-white border rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-slate-800">{results.length}</div>
                <div className="text-xs text-slate-500">Tested</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{passed}</div>
                <div className="text-xs text-slate-500">Passed</div>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-red-500">{results.length - passed}</div>
                <div className="text-xs text-slate-500">Failed</div>
              </div>
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-indigo-600">{results.filter(r => r.fromCache).length}</div>
                <div className="text-xs text-slate-500">From Cache</div>
              </div>
            </div>

            {/* Category breakdown */}
            <div className="bg-white border rounded-xl p-5 mb-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" /> Accuracy by Category
              </h3>
              <div className="space-y-2">
                {Object.entries(byCategory).sort((a, b) => {
                  const pa = a[1].passed / a[1].total;
                  const pb = b[1].passed / b[1].total;
                  return pa - pb;
                }).map(([cat, s]) => {
                  const pct = Math.round((s.passed / s.total) * 100);
                  const color = pct >= 95 ? "bg-green-500" : pct >= 80 ? "bg-amber-500" : "bg-red-500";
                  return (
                    <div key={cat} className="flex items-center gap-3">
                      <div className="w-40 text-xs text-slate-600 font-medium truncate">{cat}</div>
                      <div className="flex-1 bg-slate-100 rounded-full h-2">
                        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
                      </div>
                      <div className="text-xs text-slate-500 w-28 text-right">{s.passed}/{s.total} ({pct}%)</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Results table - show only failures */}
            <div className="bg-white border rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">
                  Failures ({results.filter(r => !r.passed).length})
                </span>
              </div>
              <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                {results.filter(r => !r.passed).map(r => (
                  <div key={r.test.id} className="px-4 py-3">
                    <div className="flex items-center gap-2 mb-1">
                      <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                      <span className="text-xs font-medium text-slate-500">[{r.test.category}] {r.test.id}</span>
                      <span className="text-xs text-red-500 font-bold">{r.score}%</span>
                      <span className="text-xs text-slate-400">{r.durationMs}ms</span>
                    </div>
                    <p className="text-sm text-slate-800 ml-5">{r.test.query}</p>
                    <p className="text-xs text-red-500 ml-5 mt-1">Missing: {r.missedFacts.join(", ")}</p>
                  </div>
                ))}
                {results.filter(r => !r.passed).length === 0 && results.length > 0 && (
                  <div className="px-4 py-8 text-center text-green-600 font-semibold">
                    🎉 All tests passed!
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Empty state */}
        {results.length === 0 && !running && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="text-5xl mb-4">🎯</div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Expanded HR Benchmark</h3>
            <p className="text-slate-500 text-sm max-w-md mb-4">
              Run up to <strong>{EXPANDED_HR_BENCHMARK_COUNT.toLocaleString()} test cases</strong> against the live chatbot.
            </p>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800 max-w-md text-left">
              <strong>⚠️ Note:</strong> Running the full expanded suite takes longer than the original 7,000-case policy run.
              Start with 100-500 tests to verify accuracy before running the full suite.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
