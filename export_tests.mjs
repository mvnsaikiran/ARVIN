// Export test suite to JSON for Python benchmark
import { readFileSync, writeFileSync } from 'fs';

const content = readFileSync('src/data/fullTestSuite.ts', 'utf8');

// Parse each test case by splitting on id: "TC"
const cases = [];
const lines = content.split('\n');
let current = null;
let inExactAnswer = false;
let backtickCount = 0;

for (const line of lines) {
  const idMatch = line.match(/id:\s*"(TC\d+)"/);
  if (idMatch) {
    if (current) cases.push(current);
    current = { id: idMatch[1], query: '', keyFacts: [], source: '', page: 0, category: '' };
    inExactAnswer = false;
    continue;
  }
  if (!current) continue;

  const queryMatch = line.match(/query:\s*"(.+)"/);
  if (queryMatch) { current.query = queryMatch[1]; continue; }

  const sourceMatch = line.match(/source:\s*"(.+)"/);
  if (sourceMatch) { current.source = sourceMatch[1]; continue; }

  const pageMatch = line.match(/page:\s*(\d+)/);
  if (pageMatch) { current.page = parseInt(pageMatch[1]); continue; }

  const categoryMatch = line.match(/category:\s*"(.+)"/);
  if (categoryMatch) { current.category = categoryMatch[1]; continue; }

  const keyFactsMatch = line.match(/keyFacts:\s*\[([^\]]*)\]/);
  if (keyFactsMatch) {
    current.keyFacts = [...keyFactsMatch[1].matchAll(/"([^"]+)"/g)].map(m => m[1]);
    continue;
  }
}
if (current) cases.push(current);

writeFileSync('test_suite.json', JSON.stringify(cases, null, 2));
console.log(`Exported ${cases.length} test cases to test_suite.json`);
