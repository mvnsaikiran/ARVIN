/**
 * Arvind HR Pulse — Benchmarking Suite
 * Runs test cases against the live chatbot and measures accuracy
 */
import React, { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Play, Square, Download, CheckCircle, XCircle,
  AlertCircle, BarChart3, ChevronDown, ChevronRight,
  RefreshCw, Filter, Search, Trophy, Target, Zap
} from "lucide-react";
import { BENCHMARK_TESTS, TOTAL_TEST_CASES, BenchmarkTest } from "../data/benchmarks";
import { resolveAssistantQuery } from "../services/assistantRuntime";
import { getEmployeeProfile } from "../services/employeeExperienceService";

interface TestResult {
  test: BenchmarkTest;
  actualAnswer: string;
  passed: boolean;
  matchedFacts: string[];
  missedFacts: string[];
  score: number;            // 0-100
  durationMs: number;
  error?: string;
}

interface RunStats {
  total: number;
  passed: number;
  failed: number;
  errors: number;
  avgScore: number;
  avgDuration: number;
  byCategory: Record<string, { total: number; passed: number; avgScore: number }>;
}

function scoreResult(actual: string, keyFacts: string[]): { passed: boolean; matched: string[]; missed: string[]; score: number } {
  const low = actual.toLowerCase();
  const matched = keyFacts.filter(f => low.includes(f.toLowerCase()));
  const missed = keyFacts.filter(f => !low.includes(f.toLowerCase()));
  const score = keyFacts.length > 0 ? Math.round((matched.length / keyFacts.length) * 100) : 100;
  return { passed: score >= 60, matched, missed, score };
}

function computeStats(results: TestResult[]): RunStats {
  const byCategory: Record<string, { total: number; passed: number; scores: number[] }> = {};
  let totalScore = 0;
  let totalDuration = 0;

  for (const r of results) {
    const cat = r.test.category;
    if (!byCategory[cat]) byCategory[cat] = { total: 0, passed: 0, scores: [] };
    byCategory[cat].total++;
    if (r.passed) byCategory[cat].passed++;
    byCategory[cat].scores.push(r.score);
    totalScore += r.score;
    totalDuration += r.durationMs;
  }

  return {
    total: results.length,
    passed: results.filter(r => r.passed).length,
    failed: results.filter(r => !r.passed && !r.error).length,
    errors: results.filter(r => !!r.error).length,
    avgScore: results.length > 0 ? Math.round(totalScore / results.length) : 0,
    avgDuration: results.length > 0 ? Math.round(totalDuration / results.length) : 0,
    byCategory: Object.fromEntries(
      Object.entries(byCategory).map(([cat, v]) => [
        cat,
        {
          total: v.total,
          passed: v.passed,
          avgScore: Math.round(v.scores.reduce((a, b) => a + b, 0) / v.scores.length),
        },
      ])
    ),
  };
}

const BADGE_COLORS: Record<string, string> = {
  "Domestic Travel": "bg-blue-100 text-blue-700",
  "Local Conveyance": "bg-green-100 text-green-700",
  "Grievance": "bg-orange-100 text-orange-700",
  "POSH": "bg-red-100 text-red-700",
  "Whistleblower": "bg-purple-100 text-purple-700",
  "Talent Mobility": "bg-amber-100 text-amber-700",
  "Joining Policy": "bg-cyan-100 text-cyan-700",
  "Gender Policy": "bg-pink-100 text-pink-700",
  "Contact Info": "bg-slate-100 text-slate-600",
};

export default function Benchmarking({ onBack }: { onBack: () => void }) {
  const [results, setResults] = useState<TestResult[]>([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentQuery, setCurrentQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [filterStatus, setFilterStatus] = useState<"all" | "pass" | "fail">("all");
  const [searchQ, setSearchQ] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [batchSize, setBatchSize] = useState(20);
  const abortRef = useRef(false);

  const stats = computeStats(results);
  const accuracy = results.length > 0 ? Math.round((stats.passed / stats.total) * 100) : 0;

  const categories = ["All", ...Object.keys(BADGE_COLORS)];

  const filteredResults = results.filter(r => {
    if (selectedCategory !== "All" && r.test.category !== selectedCategory) return false;
    if (filterStatus === "pass" && !r.passed) return false;
    if (filterStatus === "fail" && r.passed) return false;
    if (searchQ && !r.test.query.toLowerCase().includes(searchQ.toLowerCase())) return false;
    return true;
  });

  const runBenchmark = useCallback(async () => {
    abortRef.current = false;
    setRunning(true);
    setResults([]);
    setProgress(0);

    const tests = BENCHMARK_TESTS.slice(0, batchSize);
    const newResults: TestResult[] = [];

    for (let i = 0; i < tests.length; i++) {
      if (abortRef.current) break;
      const test = tests[i];
      setCurrentQuery(test.query);
      setProgress(Math.round((i / tests.length) * 100));

      const t0 = Date.now();
      try {
        const resp = await resolveAssistantQuery({
          message: test.query,
          history: [],
          profile: getEmployeeProfile("local-user-001"),
          language: "english",
          precisionMode: true,
        });
        const duration = Date.now() - t0;
        const actual = resp.text || "";
        const { passed, matched, missed, score } = scoreResult(actual, test.keyFacts);

        newResults.push({
          test,
          actualAnswer: actual,
          passed,
          matchedFacts: matched,
          missedFacts: missed,
          score,
          durationMs: duration,
        });
      } catch (e: any) {
        newResults.push({
          test,
          actualAnswer: "",
          passed: false,
          matchedFacts: [],
          missedFacts: test.keyFacts,
          score: 0,
          durationMs: Date.now() - t0,
          error: e.message || "Unknown error",
        });
      }

      setResults([...newResults]);
      // Rate limit: 500ms between calls
      if (i < tests.length - 1) await new Promise(r => setTimeout(r, 500));
    }

    setRunning(false);
    setProgress(100);
    setCurrentQuery("");
  }, [batchSize]);

  const stopBenchmark = () => {
    abortRef.current = true;
    setRunning(false);
  };

  const exportResults = () => {
    const rows = [
      ["ID", "Category", "Subcategory", "Query", "Status", "Score", "Matched Facts", "Missed Facts", "Duration (ms)", "Source", "Page"],
      ...results.map(r => [
        r.test.id,
        r.test.category,
        r.test.subcategory,
        `"${r.test.query.replace(/"/g, '""')}"`,
        r.passed ? "PASS" : r.error ? "ERROR" : "FAIL",
        r.score,
        `"${r.matchedFacts.join(", ")}"`,
        `"${r.missedFacts.join(", ")}"`,
        r.durationMs,
        r.test.source,
        r.test.page,
      ]),
    ];
    const csv = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hr_pulse_benchmark_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const accuracyColor = accuracy >= 90 ? "text-green-600" : accuracy >= 70 ? "text-amber-600" : "text-red-600";
  const accuracyBg = accuracy >= 90 ? "bg-green-50 border-green-200" : accuracy >= 70 ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200";

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <ChevronRight className="w-4 h-4 text-slate-500 rotate-180" />
          </button>
          <div>
            <h1 className="font-semibold text-slate-900">Benchmark Suite</h1>
            <p className="text-xs text-slate-500">{TOTAL_TEST_CASES.toLocaleString()} total test cases · {BENCHMARK_TESTS.length} in runner</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {results.length > 0 && (
            <button onClick={exportResults} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200">
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          )}
          <select
            value={batchSize}
            onChange={e => setBatchSize(Number(e.target.value))}
            disabled={running}
            className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white text-slate-700"
          >
            <option value={10}>10 tests</option>
            <option value={20}>20 tests</option>
            <option value={50}>50 tests</option>
            <option value={100}>100 tests</option>
            <option value={200}>200 tests (all)</option>
          </select>
          {running ? (
            <button onClick={stopBenchmark} className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium">
              <Square className="w-4 h-4" />
              Stop
            </button>
          ) : (
            <button onClick={runBenchmark} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium">
              <Play className="w-4 h-4" />
              {results.length > 0 ? "Re-run" : "Run Benchmark"}
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {running && (
        <div className="bg-white border-b border-slate-100 px-6 py-3 flex-shrink-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-500 truncate max-w-lg">Testing: {currentQuery}</span>
            <span className="text-xs font-medium text-indigo-600">{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5">
            <motion.div
              className="bg-indigo-600 h-1.5 rounded-full"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {/* Stats Cards */}
        {results.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className={`col-span-2 md:col-span-1 p-4 rounded-xl border ${accuracyBg} text-center`}>
              <div className={`text-4xl font-black ${accuracyColor}`}>{accuracy}%</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">ACCURACY</div>
              {accuracy >= 95 && <div className="text-xs text-green-600 mt-1 font-bold flex items-center justify-center gap-1"><Trophy className="w-3 h-3" /> Target Met!</div>}
            </div>
            <div className="p-4 rounded-xl border bg-white text-center">
              <div className="text-2xl font-bold text-slate-800">{stats.total}</div>
              <div className="text-xs text-slate-500 mt-1">Tested</div>
            </div>
            <div className="p-4 rounded-xl border bg-green-50 border-green-200 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.passed}</div>
              <div className="text-xs text-slate-500 mt-1">Passed</div>
            </div>
            <div className="p-4 rounded-xl border bg-red-50 border-red-200 text-center">
              <div className="text-2xl font-bold text-red-500">{stats.failed}</div>
              <div className="text-xs text-slate-500 mt-1">Failed</div>
            </div>
            <div className="p-4 rounded-xl border bg-white text-center">
              <div className="text-2xl font-bold text-slate-700">{stats.avgScore}%</div>
              <div className="text-xs text-slate-500 mt-1">Avg Score</div>
            </div>
          </div>
        )}

        {/* Category Breakdown */}
        {results.length > 0 && Object.keys(stats.byCategory).length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
            <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Category Breakdown
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.byCategory).sort((a, b) => b[1].avgScore - a[1].avgScore).map(([cat, s]) => {
                const pct = Math.round((s.passed / s.total) * 100);
                const color = pct >= 90 ? "bg-green-500" : pct >= 70 ? "bg-amber-500" : "bg-red-500";
                return (
                  <div key={cat} className="flex items-center gap-3">
                    <div className="w-36 text-xs text-slate-600 truncate font-medium">{cat}</div>
                    <div className="flex-1 bg-slate-100 rounded-full h-2">
                      <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
                    </div>
                    <div className="text-xs text-slate-500 w-20 text-right">{s.passed}/{s.total} ({pct}%)</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Filters */}
        {results.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg px-3 py-2">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search queries..."
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                className="text-sm outline-none w-48 text-slate-700"
              />
            </div>
            <div className="flex gap-1">
              {(["all", "pass", "fail"] as const).map(s => (
                <button key={s} onClick={() => setFilterStatus(s)}
                  className={`px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${filterStatus === s ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}>
                  {s.toUpperCase()}
                </button>
              ))}
            </div>
            <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}
              className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white text-slate-700">
              {categories.map(c => <option key={c}>{c}</option>)}
            </select>
            <div className="text-xs text-slate-500 self-center ml-1">{filteredResults.length} shown</div>
          </div>
        )}

        {/* Results List */}
        <div className="space-y-2">
          <AnimatePresence>
            {filteredResults.map(r => (
              <motion.div
                key={r.test.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedId(expandedId === r.test.id ? null : r.test.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                >
                  {r.error ? (
                    <AlertCircle className="w-4 h-4 text-orange-500 flex-shrink-0" />
                  ) : r.passed ? (
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${BADGE_COLORS[r.test.category] || "bg-slate-100 text-slate-600"}`}>
                        {r.test.subcategory || r.test.category}
                      </span>
                      <span className="text-[10px] text-slate-400">{r.test.id}</span>
                    </div>
                    <p className="text-sm text-slate-800 truncate">{r.test.query}</p>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <div className="flex gap-1">
                      {r.test.keyFacts.map(f => (
                        <span key={f} className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${r.matchedFacts.includes(f) ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                          {f.slice(0, 8)}
                        </span>
                      ))}
                    </div>
                    <span className={`text-sm font-bold w-10 text-right ${r.score >= 80 ? "text-green-600" : r.score >= 60 ? "text-amber-600" : "text-red-500"}`}>
                      {r.score}%
                    </span>
                    <span className="text-xs text-slate-400 w-14 text-right">{r.durationMs}ms</span>
                    {expandedId === r.test.id ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
                  </div>
                </button>

                {expandedId === r.test.id && (
                  <div className="px-4 pb-4 border-t border-slate-100">
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Expected Answer</p>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-xs text-slate-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                          {r.test.exactAnswer}
                        </div>
                        <p className="text-xs text-slate-400 mt-1">Source: {r.test.source}, Page {r.test.page}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">Chatbot Response</p>
                        <div className={`border rounded-lg p-3 text-xs text-slate-700 whitespace-pre-wrap max-h-48 overflow-y-auto ${r.passed ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                          {r.error ? `ERROR: ${r.error}` : r.actualAnswer || "(empty response)"}
                        </div>
                        {r.missedFacts.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs text-red-600 font-medium">Missing facts: {r.missedFacts.join(", ")}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Empty state */}
        {results.length === 0 && !running && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="p-4 bg-indigo-50 rounded-2xl mb-4">
              <Target className="w-10 h-10 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Ready to Benchmark</h3>
            <p className="text-slate-500 text-sm max-w-sm mb-1">
              Run the benchmark suite to test chatbot accuracy across <strong>{TOTAL_TEST_CASES.toLocaleString()} test cases</strong>.
            </p>
            <p className="text-slate-400 text-xs">Each test checks if the chatbot returns the correct policy facts.</p>
            <div className="mt-6 grid grid-cols-2 gap-3 text-xs text-slate-500 max-w-xs">
              {Object.entries(BADGE_COLORS).map(([cat, cls]) => (
                <div key={cat} className={`${cls} px-2 py-1 rounded text-center`}>{cat}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
