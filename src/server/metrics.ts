// src/server/metrics.ts
import express from "express";

const router = express.Router();

// Helper to generate mock data (replace with real data sources later)
function randomInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

router.get("/api/metrics/policy-resolution", (_req, res) => {
  const deterministic = randomInt(80, 100);
  const llm = 100 - deterministic;
  res.json({ deterministic, llm });
});

router.get("/api/metrics/user-experience", (_req, res) => {
  const csat = randomInt(85, 100);
  const nps = randomInt(50, 90);
  const avgResponseMs = randomInt(300, 1500);
  const dropOffRate = Math.round(Math.random() * 10);
  res.json({ csat, nps, avgResponseMs, dropOffRate });
});

router.get("/api/metrics/usage", (_req, res) => {
  const sessions = randomInt(100, 500);
  const activeUsers = randomInt(20, 100);
  const topQueries = ["travel allowance", "lodging policy", "expense claim", "HR grievance", "POSH"];
  res.json({ sessions, activeUsers, topQueries });
});

export default router;
